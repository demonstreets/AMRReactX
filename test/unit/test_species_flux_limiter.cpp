#include "SpeciesFluxLimiter.H"
#include <array>
#include <vector>
#include <cmath>
#include <iostream>
#include <cstdlib>

void require(bool condition, const char* message) {
  if (!condition) { std::cerr << message << '\n'; std::exit(1); }
}

int main() {
  using Cell = std::array<double,3>;
  {
    double donor[3] = {.2,.3,.5}, face[3] = {-.1,.5,.6};
    require(pc_bounded_face_composition<3>(face,donor), "valid donor rejected");
    require(face[0] == 0. && std::abs(face[1]+face[2]-1.) < 1.e-14,
            "face composition is not in the species simplex");
    donor[0] = -7.e-5;
    require(!pc_bounded_face_composition<3>(face,donor), "negative evolved donor was hidden");
  }
  for (double velocity : {1.0,-1.0}) {
    constexpr int nx=64;
    constexpr double dt=.4, dx=1.;
    std::vector<Cell> state(nx), next(nx), flux(nx);
    Cell initial_mass{};
    for(int i=0;i<nx;++i) {
      state[i] = (i>=12 && i<30) ? Cell{.8,.0,.2} : Cell{.0,.8,.2};
      for(int n=0;n<3;++n) initial_mass[n]+=state[i][n];
    }
    for(int step=0;step<120;++step) {
      for(int face_index=0;face_index<nx;++face_index) {
        const int donor_index = velocity>0 ? (face_index+nx-1)%nx : face_index;
        const int back = (donor_index + (velocity>0 ? nx-1 : 1))%nx;
        Cell donor=state[donor_index], face{};
        for(int n=0;n<3;++n) face[n]=1.5*donor[n]-.5*state[back][n];
        require(pc_bounded_face_composition<3>(face.data(),donor.data()), "invalid transported donor");
        pc_bounded_species_flux<3>(velocity,1.,donor.data(),face.data(),dx,dt,1,flux[face_index].data());
        require(std::abs(flux[face_index][0]+flux[face_index][1]+flux[face_index][2]-velocity)<2.e-14,
                "species flux sum differs from density flux");
      }
      for(int i=0;i<nx;++i) for(int n=0;n<3;++n) {
        next[i][n]=state[i][n]-dt/dx*(flux[(i+1)%nx][n]-flux[i][n]);
        require(next[i][n]>=-1.e-13 && next[i][n]<=1.+1.e-13,
                "bounded flux generated negative or excessive species");
      }
      state.swap(next);
    }
    Cell final_mass{};
    for(const auto& cell : state)for(int n=0;n<3;++n)final_mass[n]+=cell[n];
    for(int n=0;n<3;++n)require(std::abs(final_mass[n]-initial_mass[n])<1.e-11,
                                "periodic species mass not conserved");
  }
  std::cout << "PASS: species simplex, invalid donor rejection, bidirectional periodic conservation and bounds\n";
}
