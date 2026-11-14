#if __has_include(<AMReX_Config.H>)
#include <AMReX_Config.H>
#endif
#include "signed_distance.H"
#include <algorithm>
#include <cmath>
#include <limits>
namespace pele {
namespace {
void closestPt(double px,double py,double pz,double ax,double ay,double az,
               double bx,double by,double bz,double cx,double cy,double cz,
               double&qx,double&qy,double&qz,double&d){
    double abx=bx-ax,aby=by-ay,abz=bz-az,acx=cx-ax,acy=cy-ay,acz=cz-az;
    double apx=px-ax,apy=py-ay,apz=pz-az;
    double d00=abx*abx+aby*aby+abz*abz,d01=abx*acx+aby*acy+abz*acz;
    double d11=acx*acx+acy*acy+acz*acz,d20=apx*abx+apy*aby+apz*abz,d21=apx*acx+apy*acy+apz*acz;
    double den=d00*d11-d01*d01;
    constexpr double eps=1e-30;
    bool interior=false;
    if(std::abs(den)>eps){
        double v=(d11*d20-d01*d21)/den,w=(d00*d21-d01*d20)/den,u=1.-v-w;
        if(u>=0&&v>=0&&w>=0){
            qx=ax+v*abx+w*acx;qy=ay+v*aby+w*acy;qz=az+v*abz+w*acz;
            interior=true;
        }
    }
    if(!interior){
        double best=std::numeric_limits<double>::max();
        for(int e=0;e<3;e++){double eax,eay,eaz,ebx,eby,ebz;
            if(e==0){eax=ax;eay=ay;eaz=az;ebx=bx;eby=by;ebz=bz;}
            else if(e==1){eax=bx;eay=by;eaz=bz;ebx=cx;eby=cy;ebz=cz;}
            else{eax=cx;eay=cy;eaz=cz;ebx=ax;eby=ay;ebz=az;}
            double evx=ebx-eax,evy=eby-eay,evz=ebz-eaz;
            double edge_den=evx*evx+evy*evy+evz*evz;
            double t=(edge_den>eps)?((px-eax)*evx+(py-eay)*evy+(pz-eaz)*evz)/edge_den:0.;
            t=std::max(0.,std::min(1.,t));
            double ccx=eax+t*evx,ccy=eay+t*evy,ccz=eaz+t*evz;
            double dd=(px-ccx)*(px-ccx)+(py-ccy)*(py-ccy)+(pz-ccz)*(pz-ccz);
            if(dd<best){best=dd;qx=ccx;qy=ccy;qz=ccz;}
        }
    }
    d=std::sqrt((px-qx)*(px-qx)+(py-qy)*(py-qy)+(pz-qz)*(pz-qz));
}
}

#if __has_include(<AMReX_Config.H>)
void computeSphereSDF(amrex::MultiFab& sdf,
                      const amrex::Geometry& geom,
                      const amrex::Array<amrex::Real,3>& center,
                      amrex::Real radius,
                      const amrex::IntVect& /*ng*/)
{
    const auto dx = geom.CellSize();
    const auto prob_lo = geom.ProbLo();
    amrex::Real cx = center[0], cy = center[1], cz = center[2];

    for (amrex::MFIter mfi(sdf); mfi.isValid(); ++mfi) {
        const amrex::Box& bx = mfi.growntilebox();
        auto arr = sdf.array(mfi);
        amrex::ParallelFor(bx, [=] AMREX_GPU_DEVICE (int i, int j, int k) {
            amrex::Real x = prob_lo[0] + (i + 0.5) * dx[0];
            amrex::Real y = prob_lo[1] + (j + 0.5) * dx[1];
            amrex::Real z = prob_lo[2] + (k + 0.5) * dx[2];
            arr(i,j,k) = sdf_sphere(x, y, z, cx, cy, cz, radius);
        });
    }
}
#endif

double SDFComputer::computePoint(double x,double y,double z)const{
    double best_dist=std::numeric_limits<double>::max();
    double best_qx=0,best_qy=0,best_qz=0;
    const double* best_normal=nullptr;
    for(const auto&f:m_facets){
        double qx,qy,qz,d;
        closestPt(x,y,z,f.vertices[0][0],f.vertices[0][1],f.vertices[0][2],
                  f.vertices[1][0],f.vertices[1][1],f.vertices[1][2],
                  f.vertices[2][0],f.vertices[2][1],f.vertices[2][2],qx,qy,qz,d);
        if(d<best_dist){
            best_dist=d;best_qx=qx;best_qy=qy;best_qz=qz;
            best_normal=f.normal;
        }
    }
    if(best_normal){
        double dx=x-best_qx,dy=y-best_qy,dz=z-best_qz;
        double dot=dx*best_normal[0]+dy*best_normal[1]+dz*best_normal[2];
        if(dot<0)best_dist=-best_dist;
    }
    return best_dist;
}
}