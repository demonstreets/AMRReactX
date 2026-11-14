#pragma once
#include <AMReX_REAL.H>
#include <AMReX_Gpu.H>
#include <cmath>

namespace MyPele::Academic::VOF {

struct GeometricPlane {
    amrex::Real n[3] = {1,0,0};
    amrex::Real c = 0;
    int dim = 2;
};

// Volume under n.x <= c in a unit Cartesian cell. Piecewise polynomial
// integration on the smaller complementary polytope avoids subtracting
// nearly equal cubes when a plane is almost parallel to a cell face.
// Degenerate normals are treated analytically, not with division by epsilon.
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real plane_unit_volume(const amrex::Real* n, amrex::Real c, int dim)
{
    using R=amrex::Real;
    R a[3]={0,0,0},sum=0,scale=0;
    for(int d=0;d<dim;++d) scale+=std::abs(n[d]);
    if (!(scale>0)) return c>=0 ? 1:0;
    c/=scale;
    int active=0;
    for(int d=0;d<dim;++d) {
        const R nd=n[d]/scale;
        if(nd<0) c-=nd;
        if(std::abs(nd)>0) { a[active++]=std::abs(nd);sum+=std::abs(nd); }
    }
    if(c<=0) return 0;
    if(c>=sum) return 1;
    const bool complement=c>sum/2;
    if(complement) c=sum-c;
    for(int i=0;i<active;++i)for(int j=i+1;j<active;++j)
        if(a[j]<a[i]) {const R tmp=a[j];a[j]=a[i];a[i]=tmp;}
    R volume=0;
    if(active==1) volume=c/a[0];
    else if(active==2) volume=c<a[0] ? (c/a[0])*(c/a[1])/2:(c-a[0]/2)/a[1];
    else {
        const R l=a[0],m=a[1],n=a[2];
        if(c<l) volume=(c/l)*(c/m)*(c/n)/6;
        else if(c<m) volume=(3*c*(c-l)+l*l)/(6*m*n);
        else if(c>=l+m) volume=(c-(l+m)/2)/n;
        else {
            const R tm=c-m,tn=c>n ? c-n:0;
            volume=(3*c*(c-l)+l*l-tm*tm*(tm/l)-tn*tn*(tn/l))/(6*m*n);
        }
    }
    // Only geometrical roundoff is clipped here, never an evolved VOF field.
    volume=volume<0 ? 0:(volume>1 ? 1:volume);
    return complement ? 1-volume:volume;
}

AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
GeometricPlane reconstruct_geometric_plane(const amrex::Real* normal,amrex::Real alpha,int dim)
{
    GeometricPlane p;p.dim=dim;
    amrex::Real scale=0,lo=0,hi=0;
    for(int d=0;d<dim;++d)scale+=std::abs(normal[d]);
    for(int d=0;d<3;++d) {
        p.n[d]= d<dim ? (scale>0 ? normal[d]/scale:(d==0 ? 1:0)):0;
        if(p.n[d]<0)lo+=p.n[d];else hi+=p.n[d];
    }
    if(alpha<=0) {p.c=lo;return p;}
    if(alpha>=1) {p.c=hi;return p;}
    for(int iter=0;iter<58;++iter) {
        const amrex::Real mid=(lo+hi)/2;
        if(plane_unit_volume(p.n,mid,dim)<alpha)lo=mid;else hi=mid;
    }
    p.c=(lo+hi)/2;
    return p;
}

// Reconstruct a two-dimensional plane from a 3x3 volume stencil (x fastest).
// Candidate slopes are one-sided/centered differences of column heights.
// Select the candidate whose exact cut volumes best fit the full stencil.
// This preserves a planar interface, including oblique cuts, to roundoff.
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
GeometricPlane reconstruct_stencil_plane_2d(const amrex::Real* a)
{
    using R=amrex::Real;
    R young[3]={a[0]+2*a[3]+a[6]-a[2]-2*a[5]-a[8],
                a[0]+2*a[1]+a[2]-a[6]-2*a[7]-a[8],0};
    auto best=reconstruct_geometric_plane(young,a[4],2);
    if(a[4]<=0 || a[4]>=1)return best;
    R rows[3]={},cols[3]={};
    for(int j=0;j<3;++j)for(int i=0;i<3;++i){rows[j]+=a[i+3*j];cols[i]+=a[i+3*j];}
    const R sx=young[0]<0 ? -1:1,sy=young[1]<0 ? -1:1;
    R candidates[7][3]={{young[0],young[1],0},
        {sx,rows[0]-rows[1],0},{sx,rows[1]-rows[2],0},{sx,(rows[0]-rows[2])/2,0},
        {cols[0]-cols[1],sy,0},{cols[1]-cols[2],sy,0},{(cols[0]-cols[2])/2,sy,0}};
    R best_error=1.e100;
    for(int k=0;k<7;++k) {
        const auto p=reconstruct_geometric_plane(candidates[k],a[4],2);
        R error=0;
        for(int j=-1;j<=1;++j)for(int i=-1;i<=1;++i) {
            const R predicted=plane_unit_volume(p.n,p.c-p.n[0]*i-p.n[1]*j,2);
            const R difference=predicted-a[i+1+3*(j+1)];error+=difference*difference;
        }
        if(error<best_error){best_error=error;best=p;}
    }
    return best;
}

// Liquid volume swept through the right (positive Courant number) or left
// (negative Courant number) face, per donor-cell volume. Caller enforces |C|<=1.
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
amrex::Real geometric_swept_volume(const GeometricPlane& p,int direction,amrex::Real courant)
{
    const amrex::Real width=std::abs(courant);
    if(width==0) return 0;
    if(!(width<=1 && direction>=0 && direction<p.dim)) return -1;
    amrex::Real transformed[3]={p.n[0],p.n[1],p.n[2]};
    transformed[direction]*=width;
    const amrex::Real offset=courant>0 ? 1-width:0;
    return width*plane_unit_volume(transformed,p.c-p.n[direction]*offset,p.dim);
}

} // namespace MyPele::Academic::VOF
