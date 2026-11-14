"""Validate raw resolved-interface fields; exact Riemann solution is independent of the FV code."""
from __future__ import annotations
import argparse,json,pathlib,re
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
    parser.add_argument('--mode',choices=['fields','translation','water_air_shock','acoustic_mixture'],default='fields')
    parser.add_argument('--period',type=float,default=2.,help='prescribed full-return advection period')
    parser.add_argument('--inputs',type=pathlib.Path,help='configuration file; defaults to RUN/inputs')
    parser.add_argument('--partial',action='store_true',help='explicit raw-field inspection without a completed-run claim')
    parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args()
    config={}
    input_file=args.inputs or args.run/'inputs'
    if input_file.is_file():
        for line in input_file.read_text().splitlines():
            match=re.match(r'^\s*([^#=\s]+)\s*=\s*([^#]+)',line)
            if match:config[match[1]]=match[2].strip()
    command_file=args.run/'command.json'
    if command_file.is_file():
        command=json.loads(command_file.read_text())
        if isinstance(command,dict):command=command['command']
        for item in command:
            if '=' in item:
                key,value=item.split('=',1);config[key.strip()]=value.strip()
    status_file=args.run/'exit_code'
    exit_code=int(status_file.read_text()) if status_file.is_file() else None
    requested=float(config['tp.stop_time']) if 'tp.stop_time' in config else None
    if not args.partial and (exit_code!=0 or requested is None):
        raise ValueError('successful exit_code and configured tp.stop_time required; --partial is only for explicit inspection')
    result,initial,final=inspect(args.run)
    completed=bool(exit_code==0 and requested is not None and final['time']>=requested*(1.-1.e-10))
    result.update(exit_code=exit_code,requested_time_s=requested,completed_requested_time=completed,
                  partial_analysis=args.partial)
    if args.mode=='translation':
        result['closed_budget_relative_errors']={k:abs(result['plots'][-1][k]-result['plots'][0][k])/max(abs(result['plots'][0][k]),1.e-100)
                                                  for k in ('gas_mass','liquid_mass','energy')}
        result['constant_pressure_max_error']=float(np.max(np.abs(final['fields']['pressure']-initial['fields']['pressure']))/np.max(initial['fields']['pressure']))
        result['constant_velocity_max_error']=max(float(np.max(np.abs(final['fields'][name]-initial['fields'][name]))) for name in ['x_velocity','y_velocity'])
        result['return_shape_L1']=float(np.mean(np.abs(final['fields']['alpha_liquid']-initial['fields']['alpha_liquid'])))
        result['final_time']=final['time']
        # Shape metric is a return-map error only for a full prescribed period.
        duration=final['time']-initial['time']
        result['compared_interval_s']=[initial['time'],final['time']]
        result['complete_period']=bool(abs(duration-args.period)<1.e-12*max(1.,abs(args.period)))
        result['maximum_closed_budget_relative_errors']={k:max(abs(row[k]-result['plots'][0][k])/max(abs(result['plots'][0][k]),1.e-100) for row in result['plots']) for k in ('gas_mass','liquid_mass','energy')}
        result['budget_and_equilibrium_pass']=max(result['maximum_closed_budget_relative_errors'].values())<1.e-10 and result['constant_pressure_max_error']<1.e-8 and result['constant_velocity_max_error']<1.e-8
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
    elif args.mode=='acoustic_mixture':
        if config.get('tp.gas_eos')!='gamma_law' or config.get('tp.shape')!='acoustic_wave':
            raise ValueError('acoustic reference requires the gamma-law small-amplitude mixture-wave case')
        pressure=float(config['tp.pressure']);alpha=float(config['tp.alpha'])
        rhog=float(config['tp.gas_density']);rhol=float(config['tp.liquid_density'])
        bg=float(config['tp.gas_gamma'])*pressure
        bl=float(config['tp.liquid_gamma'])*(pressure+float(config['tp.liquid_pinf']))
        density=(1.-alpha)*rhog+alpha*rhol
        speed=float(np.sqrt(1./(density*((1.-alpha)/bg+alpha/bl))))
        length=float(config['geometry.prob_hi'].split()[0])-float(config['geometry.prob_lo'].split()[0])
        wave_number=2.*np.pi/length;elapsed=final['time']-initial['time']
        if elapsed<=0.:raise ValueError('positive acoustic observation interval required')
        coefficients=[]
        for raw in [initial,final]:
            field=raw['fields']['pressure'];profile=field.mean(axis=tuple(range(1,field.ndim)))
            coefficients.append(np.mean((profile-profile.mean())*np.exp(-1j*wave_number*np.asarray(raw['x']))))
        if abs(coefficients[0])<1.e-14*pressure:raise ValueError('initial acoustic mode is absent')
        background=float(config.get('tp.velocity','0 0').split()[0])
        phase_error=float(np.angle(coefficients[1]/coefficients[0]*np.exp(1j*wave_number*(speed+background)*elapsed)))
        result.update(wood_speed=speed,measured_speed=speed+background-phase_error/(wave_number*elapsed),
                      phase_error=phase_error,amplitude_ratio=float(abs(coefficients[1]/coefficients[0])),
                      final_time=final['time'],note='Linear acoustic phase reference, on the phase branch nearest Wood propagation. A resolution sequence is required; this does not impose a universal convergence threshold.')
    if args.output.exists():raise ValueError('refusing to overwrite validation evidence')
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    if args.mode=='translation' and (not result['complete_period'] or not result['budget_and_equilibrium_pass']):raise SystemExit(2)
    if not args.partial and not completed:raise SystemExit(3)

if __name__=='__main__':main()
