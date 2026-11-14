#include <Wd6Rosenbrock.H>
#include <iostream>
#include <iomanip>
int main() {
  using namespace academic::wd6;
  Real T,P,x[6],end,dt,rtol;
  while(std::cin>>T>>P>>x[0]>>x[1]>>x[2]>>x[3]>>x[4]>>x[5]>>end>>dt>>rtol) {
    Real c[6],mw[6],mass=0.,sum=0.;get_mw(mw);
    for(int n=0;n<6;++n)sum+=x[n];
    for(int n=0;n<6;++n){c[n]=x[n]/sum*(P*.1)/(R*T);mass+=c[n]*mw[n];}
    Real energy,capacity,u[6];thermo(c,T,energy,capacity,u);
    Statistics stats;
    const int count=static_cast<int>(std::round(end/dt));
    for(int k=0;k<=count;++k) {
      if(k>0 && !integrate(c,T,dt,energy,mass,rtol,1.e-13,stats))return 2;
      std::cout<<std::setprecision(17)<<k*dt<<' '<<T;
      for(int n=0;n<6;++n)std::cout<<' '<<c[n]*mw[n]/mass;
      std::cout<<' '<<stats.accepted<<' '<<stats.rejected<<'\n';
    }
  }
}
