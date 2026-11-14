"""Validate raw resolved-interface fields; exact Riemann solution is independent of the FV code."""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.optimize import brentq
import amrex_reader

def exact_material_riemann(x,t,diaphragm,left,right):
    """Exact two-material ideal/stiffened-gas Euler Riemann solution.

    State tuple is (rho, u, p, gamma, pinf). Shock Hugoniot and rarefaction
    isentrope are solved directly; no numerical solver outputs enter this model.
    """
    def sound(s):
        rho,u,p,g,pi=s
        return np.sqrt(g*(p+pi)/rho)
    def f(p,s):
        rho,u,pk,g,pi=s
        if p>pk:
            A=2/((g+1)*rho);B=(g-1)*pk/(g+1)+2*g*pi/(g+1)
            return (p-pk)*np.sqrt(A/(p+B))
        return 2*sound(s)/(g-1)*(((p+pi)/(pk+pi))**((g-1)/(2*g))-1)
    def residual(p):return f(p,left)+f(p,right)+right[1]-left[1]
    lo=max(0.,-min(left[4],right[4]))+1.e-20
    hi=max(left[2],right[2])
    while residual(hi)<0:hi*=2
    ps=brentq(residual,lo,hi,xtol=max(1.e-12,hi*1.e-14),rtol=1.e-14)
    us=.5*(left[1]+right[1]+f(ps,right)-f(ps,left))
    def star_density(s):
        rho,u,p,g,pi=s;ratio=(ps+pi)/(p+pi)
        if ps>p:
            beta=(g-1)/(g+1)
            return rho*(ratio+beta)/(beta*ratio+1)
        return rho*ratio**(1/g)
    out={k:np.zeros_like(x,dtype=float) for k in ('density','pressure','x_velocity','alpha_liquid')}
    for idx,xx in enumerate(x):
        xi=(xx-diaphragm)/t
        useleft=xi<=us;s=left if useleft else right;rho,u,p,g,pi=s;c=sound(s)
        out['alpha_liquid'][idx]=float(useleft)
        if ps>p:
            shock=u+(-1 if useleft else 1)*c*np.sqrt((g+1)*(ps+pi)/(2*g*(p+pi))+(g-1)/(2*g))
            ahead=xi<shock if useleft else xi>shock
            values=(rho,p,u) if ahead else (star_density(s),ps,us)
        else:
            cs=c*((ps+pi)/(p+pi))**((g-1)/(2*g))
            head=u-c if useleft else u+c;tail=us-cs if useleft else us+cs
            ahead=xi<head if useleft else xi>head
            behind=xi>tail if useleft else xi<tail
            if ahead:values=(rho,p,u)
            elif behind:values=(star_density(s),ps,us)
            else:
                if useleft:
                    uf=2/(g+1)*(c+(g-1)*u/2+xi)
                    cf=2/(g+1)*(c+(g-1)*(u-xi)/2)
                else:
                    uf=2/(g+1)*(-c+(g-1)*u/2+xi)
                    cf=2/(g+1)*(c-(g-1)*(u-xi)/2)
                values=(rho*(cf/c)**(2/(g-1)),(p+pi)*(cf/c)**(2*g/(g-1))-pi,uf)
        out['density'][idx],out['pressure'][idx],out['x_velocity'][idx]=values
    return out,{'star_pressure':float(ps),'star_velocity':float(us)}

def inspect(run):
    code=int((run/'exit_code').read_text())
    if code!=0:raise ValueError(f'run exited {code}')
    plots=sorted(p for p in run.glob('plt*') if p.is_dir() and (p/'Header').exists())
    if len(plots)<2:raise ValueError('at least initial and final raw fields required')
    rows=[]
    for p in plots:
        d=amrex_reader.read_plotfile(str(p));f=d['fields'];mg=f['gas_mass_density'];ml=f['liquid_mass_density'];a=f['alpha_liquid']
        if any(not np.all(np.isfinite(v)) for v in f.values()):raise ValueError('nonfinite raw field')
        if np.min(mg)<0 or np.min(ml)<0 or np.min(a)<0 or np.max(a)>1:raise ValueError('negative phase mass or invalid fraction')
        if np.min(f['density'])<=0 or np.min(f['pressure'])<=0:raise ValueError('nonpositive density/pressure')
        for mask,key in [(mg>0,'gas_temperature'),(ml>0,'liquid_temperature')]:
            if np.any(mask) and np.min(f[key][mask])<=0:raise ValueError('occupied phase has nonpositive temperature')
        species=[v for k,v in f.items() if k.startswith('gas_species_mass_')]
        if not species or min(float(v.min()) for v in species)<0:raise ValueError('negative/missing gas species')
        closure=float(np.max(np.abs(sum(species)-mg)/np.maximum(mg,1.e-100)))
        if closure>1.e-10:raise ValueError('gas species mass closure')
        volume=float(np.prod(d['dx'][:d['ndim']]))
        rows.append({'plot':p.name,'time':d['time'],'shape':list(mg.shape),'gas_mass':float(mg.sum()*volume),
                     'liquid_mass':float(ml.sum()*volume),'energy':float(f['total_energy_density'].sum()*volume),
                     'species_closure':closure,'alpha_min':float(a.min()),'alpha_max':float(a.max())})
    initial=amrex_reader.read_plotfile(str(plots[0]));final=amrex_reader.read_plotfile(str(plots[-1]))
    return {'raw_fields_valid':True,'plots':rows},initial,final

def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=pathlib.Path)
    parser.add_argument('--mode',choices=['fields','translation','water_air_shock'],default='fields')
    parser.add_argument('--period',type=float,default=2.,help='prescribed full-return advection period')
    parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args()
    result,initial,final=inspect(args.run)
    if args.mode=='translation':
        result['closed_budget_relative_errors']={k:abs(result['plots'][-1][k]-result['plots'][0][k])/max(abs(result['plots'][0][k]),1.e-100)
                                                  for k in ('gas_mass','liquid_mass','energy')}
        result['constant_pressure_max_error']=float(np.max(np.abs(final['fields']['pressure']-initial['fields']['pressure']))/np.max(initial['fields']['pressure']))
        result['constant_velocity_max_error']=max(float(np.max(np.abs(final['fields'][name]-initial['fields'][name]))) for name in ['x_velocity','y_velocity'])
        result['return_shape_L1']=float(np.mean(np.abs(final['fields']['alpha_liquid']-initial['fields']['alpha_liquid'])))
        result['final_time']=final['time']
        # Shape metric is a return-map error only for a full prescribed period.
        result['complete_period']=bool(abs(final['time']-args.period)<1.e-12*max(1.,abs(args.period)))
        result['budget_and_equilibrium_pass']=max(result['closed_budget_relative_errors'].values())<1.e-10 and result['constant_pressure_max_error']<1.e-8 and result['constant_velocity_max_error']<1.e-8
    elif args.mode=='water_air_shock':
        exact,star=exact_material_riemann(np.asarray(final['x']),final['time'],70.,
            (1.,0.,1.e10,4.4,6.e9),(.05,0.,1.e6,1.4,0.))
        result['independent_exact_star']=star
        result['normalized_L1']={}
        for name,reference in exact.items():
            numerical=final['fields'][name].mean(axis=tuple(range(1,final['fields'][name].ndim)))
            result['normalized_L1'][name]=float(np.mean(np.abs(numerical-reference))/max(np.mean(np.abs(reference)),1.e-100))
        result['final_time']=final['time']
        result['note']='A resolution sequence, not one grid, is required for convergence acceptance.'
    if args.output.exists():raise ValueError('refusing to overwrite validation evidence')
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
