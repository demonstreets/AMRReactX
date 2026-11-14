"""Independent finite-rate ZND reference in SI units; no fitted reaction rates."""
import pathlib,json,numpy as np,cantera as ct
from scipy.optimize import brentq
from scipy.integrate import solve_ivp

r=pathlib.Path('/home/cj/my-pele')
b=r/'repair_validation/twophase_20260910'
d=b/'reference_znd_v1';d.mkdir(exist_ok=False)
g=ct.Solution(str(r/'external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_lu_88sk/mechanism.yaml'))
cj=json.loads((b/'reference_chemistry_v1/CJ.json').read_text())[0]
g.TPX=300,50662.5,{'nc7h16':.6,'o2':11,'n2':41.36}
Y0=g.Y.copy();rho0=g.density;p0=g.P;h0=g.enthalpy_mass
D=cj['D_m_s']*1.02;m=rho0*D;momentum=p0+m*D;energy=h0+.5*D*D
def frozen_residual(rho):
    p=momentum-m*m/rho
    g.TDY=p/(rho*ct.gas_constant*np.sum(Y0/g.molecular_weights)),rho,Y0
    return g.enthalpy_mass+.5*(m/rho)**2-energy
grid=rho0*np.linspace(1.001,15,500)
brackets=[(a,z) for a,z in zip(grid[:-1],grid[1:]) if frozen_residual(a)*frozen_residual(z)<0]
rho_vn=brentq(frozen_residual,*brackets[-1]);frozen_residual(rho_vn)
vn={'rho':rho_vn,'p':g.P,'T':g.T,'u':D-m/rho_vn}
def state(q):
    rho=q[0];y=q[1:-1];p=momentum-m*m/rho
    R=ct.gas_constant*np.sum(y/g.molecular_weights)
    g.TDY=p/(rho*R),rho,y
    return rho,m/rho,R
def rhs(t,q):
    rho,w,R=state(q)
    dy=g.net_production_rates*g.molecular_weights/rho
    gamma=g.cp_mass/g.cv_mass;c2=gamma*g.P/rho
    h=g.partial_molar_enthalpies/g.molecular_weights
    dR=ct.gas_constant*np.sum(dy/g.molecular_weights)
    drho=gamma*rho*(-R*np.dot(h,dy)/g.cp_mass+g.T*dR)/(w*w-c2)
    return np.r_[drho,dy,w]
q0=np.r_[rho_vn,Y0,0.]
sol=solve_ivp(rhs,[0,1.e-4],q0,method='BDF',rtol=2.e-9,atol=np.r_[1.e-9,np.full(g.n_species,1.e-16),1.e-12],dense_output=True,max_step=1.e-6)
if not sol.success:raise RuntimeError(sol.message)
times=np.r_[0.,np.geomspace(1.e-12,sol.t[-1],5000)]
q=sol.sol(times);rows=[];res=[]
for t,z in zip(times,q.T):
    rho,w,R=state(z)
    rows.append(np.r_[z[-1],rho,g.P,g.T,D-w,g.Y])
    res.append(abs(g.enthalpy_mass+.5*w*w-energy)/max(abs(energy),1.))
arr=np.asarray(rows)
np.savetxt(d/'profile_SI.txt',arr,header='distance_behind_shock_m rho_kg_m3 p_Pa T_K u_m_s '+' '.join(g.species_names))
metadata={'mechanism':'heptane_lu_88sk','species_names':g.species_names,'D':D,'CJ':cj['D_m_s'],'overdrive_speed_ratio':1.02,'upstream':{'rho':rho0,'p':p0,'T':300.,'u':0.,'Y':Y0.tolist()},'von_neumann':vn,'max_energy_relative_residual':max(res),'raw_min_species':float(q[1:-1].min()),'max_species_sum_error':float(np.max(abs(q[1:-1].sum(axis=0)-1))),'length_m':float(arr[-1,0]),'time_s':float(times[-1]),'evaluations':sol.nfev,'end_temperature':float(arr[-1,3])}
(d/'metadata.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata))
