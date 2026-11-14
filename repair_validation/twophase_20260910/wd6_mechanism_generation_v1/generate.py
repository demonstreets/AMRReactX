"""Build a separately named WD global mechanism for published-model comparisons."""
import pathlib,json,hashlib,subprocess,os
import cantera as ct
r=pathlib.Path('/home/cj/my-pele')
physics=r/'external/PeleC/Submodules/PelePhysics'
source=physics/'Mechanisms/heptane_lu_88sk/mechanism.yaml'
base=ct.Solution(str(source))
names=['nc7h16','o2','co','h2o','co2','n2']
species=[base.species(name) for name in names]
reference=ct.Solution(thermo='ideal-gas',kinetics='gas',species=species,reactions=[])
texts=[
'''units: {length: cm, quantity: mol, time: s, activation-energy: cal/mol}
equation: nc7h16 + 7.5 o2 => 7 co + 8 h2o
rate-constant: {A: 6.3e11, b: 0.0, Ea: 30000.0}
orders: {nc7h16: 0.25, o2: 1.5}
''',
'''units: {length: cm, quantity: mol, time: s, activation-energy: cal/mol}
equation: co + 0.5 o2 => co2
rate-constant: {A: 3.981071705534969e14, b: 0.0, Ea: 40000.0}
orders: {co: 1.0, h2o: 0.5, o2: 0.25}
nonreactant-orders: true
''',
'''units: {length: cm, quantity: mol, time: s, activation-energy: cal/mol}
equation: co2 => co + 0.5 o2
rate-constant: {A: 5.0e8, b: 0.0, Ea: 40000.0}
''']
reactions=[ct.Reaction.from_yaml(text,reference) for text in texts]
gas=ct.Solution(name='gas',thermo='ideal-gas',kinetics='gas',species=species,reactions=reactions,transport_model='mixture-averaged')
gas.TPX=300.,50662.5,{'nc7h16':.6,'o2':11.,'n2':41.36}
out=physics/'Mechanisms/heptane_wd6'
out.mkdir(exist_ok=False)
gas.update_user_header({'description':'Westbrook-Dryer 1981 global n-heptane mechanism: fuel oxidation plus forward/reverse CO oxidation. Separate validation model, not the 88-species skeletal mechanism.',
 'reference':'C. K. Westbrook and F. L. Dryer, Combustion Science and Technology 27 (1981) 31-43, DOI 10.1080/00102208108946970, Table IV and Eqs. 9-11.',
 'thermodynamic_source':'Six unmodified species from the existing PelePhysics heptane_lu_88sk mechanism; original WD paper did not supply these NASA polynomials.',
 'kinetic_equilibrium_note':'The empirical CO reverse rate is specified independently; kinetic equilibrium is not identical to thermodynamic Gibbs equilibrium.'})
gas.write_yaml(out/'mechanism.yaml',precision=17)
(out/'Make.package').write_text('CEXE_sources += mechanism.cpp\nCEXE_headers += mechanism.H\n')
metadata={'name':'heptane_wd6','species':names,'global_steps':2,'directional_rates':3,
 'rate_source_doi':'10.1080/00102208108946970','source_locations':['Table IV n-heptane row','Equation 10','Equation 11'],
 'source_units':'cm, s, mol, kcal (converted explicitly to cal/mol in input)',
 'thermodynamic_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'yaml_sha256':hashlib.sha256((out/'mechanism.yaml').read_bytes()).hexdigest(),
 'scope':'Published global-model comparison; no radical or low-temperature intermediate chemistry',
 'kinetic_equilibrium':'Empirical CO forward/reverse rates; do not label Gibbs-equilibrium CJ as the exact kinetic eigenvalue.'}
(out/'provenance.json').write_text(json.dumps(metadata,indent=2))
env=os.environ.copy();env['PYTHONPATH']=str(physics/'Support/ceptr')+':'+env.get('PYTHONPATH','')
result=subprocess.run(['python3','-m','ceptr.ceptr','-f',str(out/'mechanism.yaml')],env=env,capture_output=True,text=True)
(out/'generation.log').write_text(result.stdout+'\n'+result.stderr)
print(json.dumps({'directory':str(out),'generator_exit':result.returncode,'tail':(result.stdout+'\n'+result.stderr)[-2200:]}))
raise SystemExit(result.returncode)

