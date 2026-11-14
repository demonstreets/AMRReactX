#include <mechanism.H>
#include <iostream>
#include <iomanip>
#include <cmath>
int main() {
  static_assert(NUM_SPECIES==6,"requires the separately named WD6 mechanism");
  std::cout<<std::setprecision(17);
  double T,P,X[6];
  while(std::cin>>T>>P) {
    for(auto& value:X)if(!(std::cin>>value))return 2;
    double Y[6],rho,wdot[6],sc[6],J[49];
    CKXTY(X,Y);CKRHOX(P,T,X,rho);CKWYP(P,T,Y,wdot);
    for(int k=0;k<6;++k)sc[k]=1.e6*rho*Y[k]*imw(k);
    aJacobian(J,sc,T,0);
    std::cout<<rho;
    for(double value:wdot){if(!std::isfinite(value))return 3;std::cout<<' '<<value;}
    for(double value:J){if(!std::isfinite(value))return 4;std::cout<<' '<<value;}
    std::cout<<'\n';
  }
}
