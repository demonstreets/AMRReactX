"""Check the independently written ZND reference against SDToolbox's pressure-density ODE."""
from pathlib import Path
import sys,json
import cantera as ct
import numpy as np
b=Path(__file__).resolve().parent;root=b.parent
sys.path.insert(0,str(b/'vendor'))
from sdtoolbox.znd import zndsolve
meta=json.loads((root/'reference_v1/metadata.json').read_text())
mechanism='/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/LiDryer/mechanism.yaml'
g=ct.Solution(mechanism);g0=ct.Solution(mechanism)
g0.TPY=meta['upstream']['T'],meta['upstream']['p'],meta['upstream']['Y']
g.TPY=meta['von_neumann']['T'],meta['von_neumann']['p'],meta['upstream']['Y']
times=np.r_[0,np.geomspace(1e-12,1e-5,12000)]
result=zndsolve(g,g0,meta['D'],t_end=1e-5,max_step=1e-8,t_eval=times,relTol=2e-10,
                absTol=np.r_[1e-4,1e-10,1e-13,np.full(9,1e-19)],advanced_output=True,Method='BDF')
ref=np.loadtxt(root/'reference_v1/profile_SI.txt');keep=(ref[:,0]>=0)&(ref[:,0]<=.003)
record={'method':'SDToolbox zndsolve unmodified ODE source with Cantera LiDryer, independently evolved pressure and density; same upstream, D and frozen shock state as original reference.',
        'SDT_sampled_induction_m':result['ind_len_ZND'],'SDT_sampled_reaction_fwhm_m':result['exo_len_ZND'],
        'max_abs_difference_to_original_reference':{key:float(np.max(abs(ref[keep,col]-np.interp(ref[keep,0],result['distance'],result[key])))) for key,col in [('P',2),('T',3),('rho',1)]}}
np.savez_compressed(b/'sdt_crosscheck_profile.npz',time_s=result['time'],xi_m=result['distance'],T_K=result['T'],p_Pa=result['P'],rho=result['rho'],thermicity_s_inv=result['thermicity'],Y=result['species'].T)
x=result['distance'];sig=result['thermicity'];n=int(sig.argmax());left=n;right=n
while left>0 and sig[left-1]>=sig[n]/2:left-=1
while right<len(sig)-1 and sig[right+1]>=sig[n]/2:right+=1
lo=float(np.interp(sig[n]/2,sig[left-1:left+1],x[left-1:left+1]));hi=float(np.interp(sig[n]/2,sig[right:right+2][::-1],x[right:right+2][::-1]))
record['common_linear_half_height_definition']={'induction_m':float(x[n]),'reaction_fwhm_m':hi-lo,'half_rise_m':lo,'half_fall_m':hi}
(b/'reference_crosscheck.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
