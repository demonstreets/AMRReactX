import pathlib,subprocess,shlex,json,os
import argparse
parser=argparse.ArgumentParser(description="Compile and run composite AMR/EB source-volume tests using a current CPU MPI LMeX build log")
parser.add_argument('--compile-log',type=pathlib.Path,required=True)
parser.add_argument('--output',type=pathlib.Path,required=True)
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
case=root/'examples/engineering/h2_leak_3d'
outdir=args.output.resolve()
outdir.mkdir(exist_ok=False)
lines=args.compile_log.read_text().splitlines()
compile_line=next(s for s in lines if s.startswith('mpicxx ') and ' -c pelelmex_prob.cpp ' in s)
link_line=next(s for s in reversed(lines) if s.startswith('mpicxx ') and ' -o ' in s and ' -c ' not in s)
args=shlex.split(compile_line)
source=root/'test/integration/test_source_volume_amr.cpp'
obj=outdir/'source_volume_test.o';exe=outdir/'source_volume_test.ex'
args[args.index('pelelmex_prob.cpp')]=str(source)
args[args.index('-o')+1]=str(obj)
args=[arg for arg in args if arg not in ('-MMD','-MP')]
def run(cmd,**kw):
 p=subprocess.run(cmd,cwd=case,capture_output=True,text=True,timeout=100,**kw)
 return {'command':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr[-12000:]}
out={'compile':run(args)}
if out['compile']['exit']==0:
 link=shlex.split(link_line)
 link[link.index('-o')+1]=str(exe)
 oldmain=[a for a in link if a.endswith('/main.o')]
 assert len(oldmain)==1,oldmain
 link[link.index(oldmain[0])]=str(obj)
 out['link']=run(link)
 if out['link']['exit']==0:
  env=os.environ.copy();env.pop('DISPLAY',None);env['OMP_NUM_THREADS']='1'
  for nrank in [1,2,8]:
   out['mpi_'+str(nrank)]=run(['timeout','45','mpirun','--bind-to','none','-np',str(nrank),str(exe)],env=env)
(outdir/'result.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))

assert all(out.get(key, {}).get("exit") == 0 for key in ("compile","link","mpi_1","mpi_2","mpi_8")), out
