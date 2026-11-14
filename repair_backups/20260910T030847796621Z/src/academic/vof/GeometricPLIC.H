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
