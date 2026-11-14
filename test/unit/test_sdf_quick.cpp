#include "signed_distance.H"
#include <iostream>
#include <cmath>
int main(){
    double d1=pele::sdf_sphere(0.,0.,0.,0.,0.,0.,2.);
    double d2=pele::sdf_sphere(2.,0.,0.,0.,0.,0.,2.);
    double d3=pele::sdf_sphere(3.,0.,0.,0.,0.,0.,2.);
    bool ok=std::abs(d1+2.)<1e-9&&std::abs(d2)<1e-9&&std::abs(d3-1.)<1e-9;
    pele::STLFacet f;f.normal[0]=0;f.normal[1]=0;f.normal[2]=-1;
    f.vertices[0][0]=0;f.vertices[0][1]=0;f.vertices[0][2]=0;
    f.vertices[1][0]=1;f.vertices[1][1]=0;f.vertices[1][2]=0;
    f.vertices[2][0]=0;f.vertices[2][1]=1;f.vertices[2][2]=0;
    pele::SDFComputer sdf;sdf.setFacets({f});
    double d=sdf.computePoint(0.3,0.3,0.1);
    bool ok2=(d<-0.05&&d>-0.15);
    std::cout<<(ok&&ok2?"ALL SDF PASS":"SDF FAIL")<<std::endl;
    return (ok&&ok2)?0:1;
}