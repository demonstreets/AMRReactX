#include <mechanism.H>
#include <iostream>
#include <iomanip>
int main(){double p,t,y[9],w[9],cp,e;std::cout<<std::setprecision(17);while(std::cin>>p>>t){for(auto &v:y)std::cin>>v;CKWYP(p*10,t,y,w);CKCPBS(t,y,cp);CKUBMS(t,y,e);std::cout<<cp*1e-4<<" "<<e*1e-4;for(auto v:w)std::cout<<" "<<v*1e3;std::cout<<"\n";}return 0;}
