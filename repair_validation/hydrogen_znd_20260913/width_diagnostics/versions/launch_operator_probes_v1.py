"""Bounded isolated hydro and chemistry probes; do not alter completed ZND cases."""
from pathlib import Path
import json, re, hashlib, subprocess
import cantera as ct
import numpy as np

b = Path(__file__).resolve().parent; root = b.parent
scratch = Path('/dev/shm/my_pele_hydrogen_znd_20260913/width_diagnostics')
scratch.mkdir(exist_ok=True)
meta = json.loads((root/'reference_v1/metadata.json').read_text())
g = ct.Solution('/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer/mechanism.yaml')
g.TPY = meta['von_neumann']['T'], meta['von_neumann']['p'], meta['upstream']['Y']
reactor = ct.IdealGasReactor(g, clone=True); net = ct.ReactorNet([reactor]); net.rtol=1e-11; net.atol=1e-20
while reactor.T < 3200 and net.time < 1e-5: net.step()
assert reactor.T >= 3200
chem_stop = net.time
(b/'chem_probe_target.json').write_text(json.dumps({'stop_time_s':chem_stop,'Cantera_end_T_K':reactor.T,'target':'Nominal VN constant-volume ignition through 3200 K, within mechanism common thermo range.'},indent=2))
row = np.r_[0., meta['von_neumann']['rho'],meta['von_neumann']['p'],meta['von_neumann']['T'],meta['von_neumann']['u'],meta['upstream']['Y']]
header = 'distance_behind_shock_m rho_kg_m3 p_Pa T_K u_m_s '+' '.join(g.species_names)
frozen = b/'uniform_VN_profile_SI.txt'; np.savetxt(frozen,np.array([row,np.r_[.1,row[1:]]]),header=header)
chemrow = row.copy();chemrow[4]=0
chemprofile=b/'uniform_VN_rest_profile_SI.txt';np.savetxt(chemprofile,np.array([chemrow,np.r_[.1,chemrow[1:]]]),header=header)
template = (root/'hydrogen_9600_cfl30_v1/inputs').read_text()
binary = root/'build_source/hydrogen_znd_v1'
records = []
for name,nx,ranks,hydro,react,stop,profile in [
    ('hydro_only_2400_v1',2400,16,1,0,1e-6,frozen),
    ('hydro_only_9600_v1',9600,16,1,0,1e-6,frozen),
    ('chemistry_only_v1',32,1,0,1,chem_stop,chemprofile)]:
    d=b/name;d.mkdir(exist_ok=False);plot=scratch/name;plot.mkdir(exist_ok=False)
    changes={'stop_time':format(stop,'.17g'),'amr.n_cell':f'{nx} 2','pelec.do_hydro':str(hydro),'pelec.do_react':str(react),
             'prob.profile':str(profile),'amr.plot_file':str(plot/'plt'),'amr.plot_per':format(stop/10,'.17g')}
    if not hydro:changes['prob.front']='2.5'
    text=template
    for key,value in changes.items():
        text,count=re.subn(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+value,text,flags=re.M);assert count==1,key
    if not hydro:text+='\npelec.fixed_dt = '+format(stop/1000,'.17g')+'\n'
    (d/'inputs').write_text(text)
    case={'name':name,'nx':nx,'ny':2,'dx_m':.024/nx,'stop_time_s':stop,'command':['mpirun','-np',str(ranks),str(binary),'inputs'],
          'plot_root':str(plot),'do_hydro':hydro,'do_react':react,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
          'inputs_sha256':hashlib.sha256(text.encode()).hexdigest(),'profile_sha256':hashlib.sha256(profile.read_bytes()).hexdigest()}
    (d/'case.json').write_text(json.dumps(case,indent=2));(d/'run_case.py').write_text((root/'hydrogen_9600_cfl30_v1/run_case.py').read_text())
    f=(d/'launcher.log').open('w');p=subprocess.Popen(['python3',str(d/'run_case.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    records.append({'name':name,'launcher_pid':p.pid,'stop_time_s':stop})
(b/'operator_probe_launches.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
