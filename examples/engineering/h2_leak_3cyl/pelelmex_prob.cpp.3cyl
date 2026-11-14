#include <PeleLMeX.H>
#include <AMReX_ParmParse.H>
#include <AMReX_EB2.H>
#include <AMReX_EB2_IF.H>
#include "pelelmex_prob.H"
void PeleLM::readProbParm(){amrex::ParmParse pp("prob");pp.query("P_mean",prob_parm->P_mean);pp.query("T_mean",prob_parm->T_mean);pp.query("wind_u",prob_parm->wind_u);pp.query("wind_v",prob_parm->wind_v);pp.query("leak_xc",prob_parm->leak_xc);pp.query("leak_yc",prob_parm->leak_yc);pp.query("leak_zc",prob_parm->leak_zc);pp.query("leak_rate",prob_parm->leak_rate);pp.query("leak_radius",prob_parm->leak_radius);pp.query("leak_vel_x",prob_parm->leak_vel_x);pp.query("leak_vel_y",prob_parm->leak_vel_y);pp.query("leak_vel_z",prob_parm->leak_vel_z);pp.query("leak_T",prob_parm->leak_T);}
void PeleLM::freeProbParm(){} void pc_prob_close(){}
extern "C"{void amrex_probinit(const int*,const int*,const int*,const amrex::Real*,const amrex::Real*){}}
void MyProblemSpecificFunctions::EBUserDefined(const amrex::Geometry& g,const int r,const int m){amrex::EB2::CylinderIF c1(8,1,2,amrex::RealArray{8,15,20},false);amrex::EB2::CylinderIF c2(8,1,2,amrex::RealArray{25,15,20},false);amrex::EB2::CylinderIF c3(8,1,2,amrex::RealArray{48,15,20},false);auto u=amrex::EB2::makeUnion(c1,c2);auto u2=amrex::EB2::makeUnion(u,c3);auto gs=amrex::EB2::makeShop(u2);amrex::EB2::Build(gs,g,r,m);}
