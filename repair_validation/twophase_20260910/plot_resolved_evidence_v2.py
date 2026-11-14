import pathlib, sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator

r=pathlib.Path('/home/cj/my-pele')
b=r/'repair_validation/twophase_20260910'
sys.path.insert(0,str(r/'tools'))
import amrex_reader
from validate_resolved_two_phase import exact_material_riemann

def ends(name):
    p=sorted(p for p in (b/name).glob('plt*') if (p/'Header').exists())
    return [amrex_reader.read_plotfile(str(q)) for q in [p[0],p[-1]]]

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'figure.dpi':160})
fig, ax=plt.subplots(2,2,figsize=(11,8.2),layout='constrained')
initial,final=ends('translation128_v4')
im=ax[0,0].imshow(final['fields']['alpha_liquid'].T,origin='lower',extent=(0,1,0,1),
                   cmap='Blues',vmin=0,vmax=1,interpolation='nearest')
theta=np.linspace(0,2*np.pi,400)
ax[0,0].plot(.5+.15*np.cos(theta),.5+.15*np.sin(theta),color='#e28735',lw=1,
             label='Exact return interface')
ax[0,0].set(title='A  Full-period interface return, 128 x 128',xlabel='x',ylabel='y')
ax[0,0].legend(loc='upper right',fontsize=8)
fig.colorbar(im,ax=ax[0,0],label='Liquid volume fraction',shrink=.8)

nx=np.array([32,64,128]);errs=[];budget=[]
for n in nx:
    a,z=ends(f'translation{n}_v4')
    errs.append(np.mean(abs(z['fields']['alpha_liquid']-a['fields']['alpha_liquid'])))
    budget.append(max(abs(z['fields'][k].sum()-a['fields'][k].sum())/abs(a['fields'][k].sum())
                      for k in ['gas_mass_density','liquid_mass_density','total_energy_density']))
ax[0,1].loglog(nx,errs,'o-',color='#176685',label='Measured fraction L1 error')
ax[0,1].loglog(nx,errs[0]*(nx/nx[0])**-2.,'--',color='.55',label='Second-order guide')
ax[0,1].set(title='B  Shape-error convergence',xlabel='Cells per direction',ylabel='L1 error')
ax[0,1].set_xticks(nx,[str(n) for n in nx]);ax[0,1].legend(fontsize=8)
ax[0,1].text(.05,.08,f'Max phase-mass / energy error: {max(budget):.1e}',transform=ax[0,1].transAxes)

for n,c in [(400,'#b7cad4'),(1600,'#5f94ad'),(3200,'#176685')]:
    _,z=ends(f'waterair{n}_v4');x=np.asarray(z['x'])
    p=z['fields']['pressure'].mean(axis=1)
    ax[1,0].plot(x,p*1e-7,color=c,lw=1.3,label=f'{n} axial cells')
exact,_=exact_material_riemann(x,z['time'],70.,(1.,0.,1e10,4.4,6e9),(.05,0.,1e6,1.4,0.))
ax[1,0].plot(x,exact['pressure']*1e-7,'--',color='#d27c30',lw=1,label='Exact two-EOS Riemann')
ax[1,0].set(title='C  Material shock at 22.9 microseconds',xlabel='x (cm)',ylabel='Pressure (MPa)',
            xlim=(68,78),ylim=(0,30))
ax[1,0].legend(fontsize=8)

c=(1/(500.5*(.5/1.4+.5/48.4)))**.5
phases=[];speeds=[]
for n in nx:
    a,z=ends(f'acoustic{n}_v4');x=np.asarray(z['x'])
    f0=np.sum((a['fields']['pressure'].mean(axis=1)-1)*np.exp(-2j*np.pi*x))
    ft=np.sum((z['fields']['pressure'].mean(axis=1)-1)*np.exp(-2j*np.pi*x))
    ph=np.angle(ft/f0);phases.append(abs(ph+2*np.pi*c*z['time']))
    speeds.append(-ph/(2*np.pi*z['time']))
ax[1,1].loglog(nx,phases,'o-',color='#176685',label='Measured acoustic phase error')
ax[1,1].loglog(nx,phases[0]*(nx/nx[0])**-2.,'--',color='.55',label='Second-order guide')
ax[1,1].set(title='D  Wood acoustic-wave convergence',xlabel='Axial cells',ylabel='Phase error (radians)')
ax[1,1].set_xticks(nx,[str(n) for n in nx]);ax[1,1].legend(fontsize=8)
ax[1,1].text(.05,.08,f'Exact Wood speed: {c:.8f}\n128-cell speed: {speeds[-1]:.8f}',transform=ax[1,1].transAxes)
fig.suptitle('Resolved mechanical-equilibrium gas-liquid model: raw-field verification',fontsize=13)
for a in [ax[0,1],ax[1,1]]:
    a.xaxis.set_minor_locator(NullLocator())
out=b/'resolved_verification_v4_clean.png'
assert not out.exists()
fig.savefig(out)
print(json.dumps({'figure':str(out),'shape_errors':[float(v) for v in errs],
                  'phase_errors':[float(v) for v in phases]}))
