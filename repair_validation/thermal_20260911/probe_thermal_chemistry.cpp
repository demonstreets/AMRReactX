#include <Wd6Rosenbrock.H>
#include <iostream>
#include <iomanip>
#include <string>

int main() {
  using namespace academic::wd6;
  std::string id;
  Real T,rho,e,dt,rtol,atol,Y[6];
  std::cout<<std::setprecision(17);
  while(std::cin>>id>>T>>rho>>e>>dt>>rtol>>atol) {
    for(auto& value:Y)if(!(std::cin>>value))return 2;
    Real c[6],mw[6];get_mw(mw);
    const Real mass=rho*1000.,target=rho*e;
    for(int n=0;n<6;++n)c[n]=mass*Y[n]/mw[n];
    Statistics stats;
    const bool ok=integrate(c,T,dt,target,mass,rtol,atol,stats);
    for(int n=0;n<6;++n)Y[n]=c[n]*mw[n]/mass;
    Real flow_T=T;int ierr=0;
    GET_T_GIVEN_EY(e*1.e4,Y,flow_T,ierr);
    Real final_energy,capacity,u[6];thermo(c,T,final_energy,capacity,u);
    std::cout<<id<<' '<<rtol<<' '<<atol<<' '<<ok<<' '<<T<<' '<<flow_T;
    for(auto value:Y)std::cout<<' '<<value;
    std::cout<<' '<<final_energy-target<<' '<<stats.accepted<<' '<<stats.rejected<<' '<<ierr<<'\n';
  }
}
