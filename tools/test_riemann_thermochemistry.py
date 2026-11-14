import pathlib,subprocess,shlex,json
import argparse
parser=argparse.ArgumentParser(description="Exercise production Riemann code with the actual Fuego thermochemistry")
parser.add_argument('--compile-log',type=pathlib.Path,required=True)
parser.add_argument('--output',type=pathlib.Path,required=True)
args_cli=parser.parse_args()
r=pathlib.Path(__file__).resolve().parents[1]
d=args_cli.output.resolve();d.mkdir(parents=True,exist_ok=False)
case=r/'examples/engineering/h2_leak_3d'
line=next(x for x in args_cli.compile_log.read_text().splitlines() if x.startswith('mpicxx ') and ' -c pelelmex_prob.cpp ' in x)
code=(r/'external/PeleC/Source/Riemann.H').read_text().replace('#include "PeleC.H"','#include <AMReX.H>\n#include <AMReX_Math.H>\n#include "Constants.H"\n#include <iostream>')
code+=r''' 
int main() {
 double y[NUM_SPECIES]={};y[H2O_ID]=1.;auto eos=pele::physics::PhysicsType::eos();
 for(double vel: {0.,100000.,284000.,500000.}) {
  double rho=.00176155,p=1.8e7,c;eos.RPY2Cs(rho,p,y,c);
  double us,fr,fy[NUM_SPECIES],fu,fv,fw,fe,fi,qu,qv,qw,qp,qg;
  riemann(rho,-vel,0,0,p,y,rho,vel,0,0,p,y,1,c,us,fr,fy,fu,fv,fw,fe,fi,qu,qv,qw,qp,qg);
  for(double value:{us,fr,fu,fv,fw,fe,fi,qu,qv,qw,qp,qg}) if(!std::isfinite(value)) return 1;
  if(fr!=0. || fe!=0.)return 2;
 }
 // Unequal reconstructed compositions must never create wall mass/energy flow.
 double yl[NUM_SPECIES]={};yl[H2_ID]=.1;yl[O2_ID]=.9;
 double us,fr,fy[NUM_SPECIES],fu,fv,fw,fe,fi,qu,qv,qw,qp,qg;
 riemann(.001,10000,0,0,1e6,yl,.001,-10000,0,0,1e6,y,0,1e5,us,fr,fy,fu,fv,fw,fe,fi,qu,qv,qw,qp,qg);
 if(fr!=0. || fe!=0. || fi!=0. || qu!=0.)return 3;
 for(double f:fy)if(f!=0.)return 4;
 std::cout<<"PASS actual Fuego/Riemann: finite expansion fluxes and impermeable wall fluxes\n";
}
'''
src=d/'probe.cpp';src.write_text(code)
args=shlex.split(line);args[args.index('pelelmex_prob.cpp')]=str(src)
args[args.index('-o')+1]=str(d/'probe');args=[x for x in args if x not in ('-c','-MMD','-MP')]
args+=['-I'+str(r/'external/PeleC/Source')]
p=subprocess.run(args,cwd=case,capture_output=True,text=True,timeout=60)
out={'compile_exit':p.returncode,'stderr':p.stderr[-12000:]}
if p.returncode==0:
 p=subprocess.run([str(d/'probe')],capture_output=True,text=True,timeout=20);out.update(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
print(json.dumps(out))

assert out["compile_exit"] == 0 and out.get("exit") == 0, out
