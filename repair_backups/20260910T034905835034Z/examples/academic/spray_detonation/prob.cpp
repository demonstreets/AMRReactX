#include "prob.H"
#include <fstream>
#include <sstream>
#include <cmath>

extern "C" void amrex_probinit(const int*,const int*,const int*,const amrex_real* lo,const amrex_real* hi) {
#if NUM_GAS_REACTIONS == 0
  amrex::Abort("spray_detonation requires finite-rate reacting chemistry");
#endif
  auto& q=*PeleC::h_prob_parm_device;
  amrex::ParmParse pp("prob");std::string filename;pp.get("profile",filename);
  pp.query("front",q.front);pp.query("perturbation",q.perturbation);q.width=hi[1]-lo[1];
  pp.query("p0",q.p0);pp.query("T0",q.T0);
  amrex::Vector<amrex::Real> y;pp.getarr("upstream_Y",y);
  if(y.size()!=NUM_SPECIES)amrex::Abort("upstream_Y must match the compiled species count");
  amrex::Real sum=0.;for(int n=0;n<NUM_SPECIES;++n){if(!std::isfinite(y[n])||y[n]<0)amrex::Abort("invalid upstream composition");q.Y0[n]=y[n];sum+=y[n];}
  if(std::abs(sum-1)>1.e-12)amrex::Abort("upstream composition does not sum to one");
  std::ifstream f(filename);std::string header;if(!std::getline(f,header))amrex::Abort("missing ZND profile");
  std::istringstream hs(header);std::string word;hs>>word;
  if(word!="#")amrex::Abort("ZND profile requires a named SI-unit header");
  const char* columns[]={"distance_behind_shock_m","rho_kg_m3","p_Pa","T_K","u_m_s"};
  for(auto name:columns){hs>>word;if(word!=name)amrex::Abort("unexpected ZND column or units");}
  amrex::Vector<std::string> names;CKSYMS_STR(names);
  for(auto const& name:names){hs>>word;if(word!=name)amrex::Abort("ZND profile species ordering differs from mechanism");}
  amrex::Vector<amrex::Real> data;std::string line;constexpr int stride=NUM_SPECIES+5;
  amrex::Real previous=-1.;
  while(std::getline(f,line)) {
    if(line.empty())continue;std::istringstream in(line);amrex::Real row[stride];
    for(auto& value:row)if(!(in>>value)||!std::isfinite(value))amrex::Abort("invalid ZND row");
    if(in>>word)amrex::Abort("extra ZND profile columns");
    if(row[0]<=previous||row[1]<=0||row[2]<=0||row[3]<=0)amrex::Abort("invalid ZND position or thermodynamics");
    previous=row[0];sum=0.;for(int n=0;n<NUM_SPECIES;++n){if(row[5+n]<0)amrex::Abort("negative ZND species");sum+=row[5+n];}
    if(std::abs(sum-1)>1.e-10)amrex::Abort("ZND species sum error");
    // Convert SI reference columns to PeleC CGS only at this boundary.
    row[0]*=100.;row[1]*=.001;row[2]*=10.;row[4]*=100.;
    data.insert(data.end(),row,row+stride);++q.rows;
  }
  if(q.rows<2)amrex::Abort("ZND profile requires at least two points");
  auto& device=PeleC::prob_parm_host->profile;device.resize(data.size());
  amrex::Gpu::copy(amrex::Gpu::hostToDevice,data.begin(),data.end(),device.begin());q.profile=device.data();
  amrex::Print()<<"Finite-rate ZND initialization: "<<q.rows<<" rows, "<<NUM_SPECIES<<" species, "<<NUM_GAS_REACTIONS<<" reactions; no imposed wave speed.\n";
}
void pc_prob_close() {}
void PeleC::problem_post_timestep() {}
void PeleC::problem_post_init() {}
void PeleC::problem_post_restart() {}
