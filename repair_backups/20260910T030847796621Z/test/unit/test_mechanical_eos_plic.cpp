#include "PelePhysics.H"
#include "MechanicalEquilibriumEOS.H"
#include "GeometricPLIC.H"
#include "PLIC.H"
#include <iostream>
#include <random>
#include <stdexcept>

using namespace MyPele::Academic::TwoPhase;
using namespace MyPele::Academic::VOF;

void require(bool test,const char* message) {if(!test)throw std::runtime_error(message);}
bool near(double x,double y,double tolerance=1.e-10) {
    return std::abs(x-y)<=tolerance*std::max({1.e-90,std::abs(x),std::abs(y)});
}

int main() {
    auto gas=pele::physics::PhysicsType::eos();
    LiquidCaloricEOS liquid{4.4,6.e9,4.18e7,-2.e10};
    double Y[NUM_SPECIES]={};Y[H2_ID]=.03;Y[O2_ID]=.22;Y[N2_ID]=.75;
    int states=0;
    for(double p:{1.e5,1.e6,1.e8,1.e9})
    for(double Tg:{150.,300.,1200.,3000.,6000.})
    for(double Tl:{200.,300.,600.})
    for(double alpha:{0.,1.e-10,.001,.1,.5,.9,1.-1.e-10,1.}) {
        double rg,eg;gas.PYT2R(p,Y,Tg,rg);gas.RTY2E(rg,Tg,Y,eg);
        const double rl=(p+liquid.pinf)/((liquid.gamma-1)*liquid.cv*Tl);
        const double el=liquid.reference_energy+liquid.cv*Tl+liquid.pinf/rl;
        const double mg=(1-alpha)*rg,ml=alpha*rl,E=mg*eg+ml*el;
        auto s=recover_mechanical_state(mg,ml,alpha,E,Y,gas,liquid,p*.7);
        require(s.valid,"valid physical state rejected");
        // Pressure recovery in a nearly pure stiff liquid is conditioned by
        // subtraction of reference energies; absolute pressure tolerance applies.
        require(std::abs(s.p-p)<2.e-8*std::max(p,liquid.pinf),"pressure recovery");
        if(mg>0) require(std::abs(s.Tg-Tg)<2.e-6*std::max(Tg,300.),"gas temperature recovery");
        if(ml>0)require(near(s.Tl,Tl,2.e-9),"liquid temperature recovery");
        if(alpha==0) {double cg;gas.RTY2Cs(rg,Tg,Y,cg);require(near(s.c,cg,1.e-9),"pure gas acoustics");}
        if(alpha>0 && alpha<1) {
            // Independent infinitesimal adiabatic volume compliance: compress
            // each phase by its bulk modulus at fixed phasic entropy/mass.
            const double compliance=(1-alpha)/(s.rhog*s.cg*s.cg)+alpha/(s.rhol*s.cl*s.cl);
            require(near(s.c*s.c,1/((mg+ml)*compliance)),"acoustics");
            const double dalpha_dp=alpha*(compliance-1/(s.rhol*s.cl*s.cl));
            require(std::abs(s.K_liquid+dalpha_dp/compliance)<5.e-14,"volume compressibility sign");
        }
        ++states;
    }
    require(!recover_mechanical_state(1.,1.,0.,1.,Y,gas,liquid).valid,"lost liquid phase accepted");
    require(!recover_mechanical_state(1.,-1.,.5,1.,Y,gas,liquid).valid,"negative mass accepted");
    require(!recover_mechanical_state(1.,1.,.5,-1.e100,Y,gas,liquid).valid,"energy extrapolation accepted");
    std::mt19937_64 rng(20260910);std::uniform_real_distribution<double> U(0.,1.);
    double max_geometry_error=0;
    for(int test=0;test<1000;++test) {
        double n[3]={2*U(rng)-1,2*U(rng)-1,0};const double alpha=U(rng);
        const auto p=reconstruct_geometric_plane(n,alpha,2);
        const double mag=std::hypot(p.n[0],p.n[1]);
        const double reference=unit_square_area_less_equal({p.n[0],p.n[1]},p.c/mag);
        max_geometry_error=std::max(max_geometry_error,std::abs(reference-alpha));
        require(std::abs(reference-alpha)<2.e-12,"PLIC independent polygon area");
        for(int direction=0;direction<2;++direction) {
            const double cut=U(rng);
            const double l=geometric_swept_volume(p,direction,-cut);
            const double r=geometric_swept_volume(p,direction,1-cut);
            require(std::abs(l+r-alpha)<2.e-12,"PLIC swept partition");
        }
    }
    for(double epsilon:{0.,1.e-15,1.e-10,1.e-5,.1,1.})
    for(double alpha:{1.e-10,.001,.2,.5,.9,1.-1.e-10}) {
        double n[3]={1,epsilon,-epsilon};
        const auto p=reconstruct_geometric_plane(n,alpha,3);
        require(std::abs(plane_unit_volume(p.n,p.c,3)-alpha)<2.e-12,"3D inverse geometry");
        for(int d=0;d<3;++d)
            require(std::abs(geometric_swept_volume(p,d,-.37)+geometric_swept_volume(p,d,.63)-alpha)<3.e-12,
                    "3D swept partition");
    }
    // Independent tetrahedron volume for x+y+z <= c<1.
    double diagonal[3]={1,1,1};
    for(double c:{.1,.4,.8,1.})require(near(plane_unit_volume(diagonal,c,3),c*c*c/6),"tetrahedron volume");
    std::cout<<"PASS actual Fuego mechanical EOS "<<states<<" physical states; PLIC polygon error "<<max_geometry_error<<"\n";
}
