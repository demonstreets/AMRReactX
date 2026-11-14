import pathlib,subprocess,time,numpy as np,cantera as ct,json
r=pathlib.Path('/home/cj/my-pele');b=r/'repair_validation/twophase_20260910';d=b/'wd6_cell_state_validation_tol4_v1';probe=b/'wd6_rosenbrock_probe_v2/probe';g=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_wd6/mechanism.yaml'))
states=[]
for T,P in [(700,1e5),(1000,1e5),(1800,1e5),(2500,1e5),(1400,1.4e6),(2200,2e6)]:
 g.TPX=T,P,{'nc7h16':.6,'o2':11,'n2':41.36};states.append((T,P,g.X.copy(),2e-4,1e-7))
profile=np.loadtxt(b/'reference_wd6_v1/profile_SI.txt')
for j in [0,100,500,1500,3000,5000]:
 row=profile[j];g.TPY=row[3],row[2],row[5:];states.append((g.T,g.P,g.X.copy(),1e-5,1e-8))
result=[]
for i,(T,P,X,end,dt) in enumerate(states):
 for tol in [1e-4]:
  line=' '.join(map(str,[T,P*10,*X,end,dt,tol]))+'\n';start=time.time();p=subprocess.run([str(probe)],input=line,capture_output=True,text=True,timeout=100)
  item=dict(state=i,T_K=T,P_Pa=P,rtol=tol,exit=p.returncode,wall_s=time.time()-start)
  if p.returncode:item['stderr']=p.stderr[-1000:];result.append(item);print(item,flush=True);continue
  a=np.loadtxt(p.stdout.splitlines());np.savetxt(d/('trace_'+str(i)+'_'+str(tol)+'.txt'),a);g.TPX=T,P,X;react=ct.IdealGasReactor(g,clone=True);net=ct.ReactorNet([react]);net.rtol=1e-10;net.atol=1e-14 if i==4 else 1e-20;terr=0.;yerr=0.
  try:
   for row in a:net.advance(row[0]);terr=max(terr,abs(row[1]-react.T));yerr=max(yerr,max(abs(row[2:8]-react.phase.Y)))
  except ct.CanteraError as error:
   item.update(reference_failed=True,reference_error=str(error),passed=False);result.append(item);print(item,flush=True);continue
  item.update(max_T_error_K=terr,max_Y_error=yerr,passed=bool(terr<=1. and yerr<=.001));result.append(item);print(item,flush=True)
 (d/'results.json').write_text(json.dumps(result,indent=2))
