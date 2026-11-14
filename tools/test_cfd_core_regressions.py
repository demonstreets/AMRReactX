import pathlib,subprocess,tempfile,json
root=pathlib.Path(__file__).resolve().parents[1]
out={}
def run(cmd,**kw):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90,**kw)
 return {'command':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
with tempfile.TemporaryDirectory(prefix='cfd_repair_regression_') as td:
 pathlib.Path(td,'AMReX_Config.H').write_text((root/'test/unit/AMReX_Config.H.in').read_text())
 base=root/'external/PeleC/Submodules/PelePhysics/Submodules/amrex/Src/Base'
 cmd=['g++','-std=c++20','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DAMREX_SPACEDIM=2','-DBL_SPACEDIM=2','-DAMREX_GPU_MAX_THREADS=0','-DNUM_ADV=1','-DNUM_SPECIES=3']
 for d in [base,pathlib.Path(td),root/'test/unit',root/'external/PeleC/Source',root/'src/academic/vof',root/'src/academic/twophase']: cmd+=['-I'+str(d)]
 text=(root/'external/PeleC/Source/Godunov.H').read_text()
 segment=text[text.index('    amrex::Real Ystar[NUM_SPECIES];'):text.index('    // Tangential momenta via passive advection')]
 cpp='''#include "TwoPhaseHLLC.H"
#include "VOF_FCT.H"
#include <vector>
#include <iostream>
#include <cmath>
int main(){
 std::vector<double> a(8*NVAR,-999.);amrex::Array4<double> flx(a.data(),{0,0,0},{8,1,1},NVAR);
 int i=0,j=0,k=0;int f_idx[3]={UMX,UMY,UMZ};
 double rhol=1.,rhor=1.,ul=1.,ur=1.,pl=1e5,pr=1e5,eL=2.5e5,eR=2.5e5,ustar;
 double spl[3]={.2,.3,.5},spr[3]={.2,.3,.5};PhaseEOSParams eosL_use={1.4,0},eosR_use={1.4,0};
'''+segment+'''
 for(int n=0;n<3;++n){
  if(std::abs(flx(0,0,0,UFS+n)-spl[n])>1e-12) return 1;
  for(int x=1;x<8;++x) if(flx(x,0,0,UFS+n)!=-999.) return 2;
 }
 std::vector<double> b(25,.5);amrex::Array4<double> alpha(b.data(),{0,0,0},{5,5,1},1);
 for(int y=0;y<5;++y)for(int x=0;x<5;++x)alpha(x,y,0)=.1+.1*x;
 double fx,fy,fz;amrex::GpuArray<double,2> dx={1.,1.};
 vof_mules_body_force(2,2,0,alpha,dx,fx,fy,fz,0);
 if(std::abs(fx-.021)>1e-12 || fy!=0. || fz!=0.)return 3;
 std::cout<<"PASS actual Godunov HLLC scatter: three species, eight cells, untouched neighbors; scalar-alpha helper under ASan/UBSan\\n";
}
'''
 exe=td+'/core'
 out['build']=run(cmd+['-x','c++','-','-o',exe],input=cpp)
 if out['build']['exit']==0: out['run']=run([exe])
 hydro=(root/'external/PeleC/Source/Hydro.cpp').read_text()
 out['hydro_contract']={'uses_fillpatched_S': 'get_new_data(State_Type).const_array(mfi)' not in hydro,
 'ghost_assert': 'S.nGrow() >= 2' in hydro, 'mules_rejected':'pele.use_mules is unsupported' in hydro,
 'no_artificial_mules_force':'vof_mules_body_force(' not in hydro}
print(json.dumps(out))

assert out["build"]["exit"] == 0 and out.get("run", {}).get("exit") == 0, out
assert all(out["hydro_contract"].values()), out
