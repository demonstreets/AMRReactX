from pathlib import Path
import sys,json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/home/cj/my-pele');b=r/'repair_validation/thermal_model_20260911';sys.path.insert(0,str(r/'tools'));import amrex_reader
summaries=json.loads((b/'grid_final_fields_v1/summary.json').read_text());vmax=np.ceil(max(q['Tmax_K'] for q in summaries)/500)*500
fig,axes=plt.subplots(2,2,figsize=(15,6.5),gridspec_kw={'width_ratios':[2,1]},constrained_layout=True)
for row,(summary,label) in enumerate(zip(summaries,['Reference 0.05 mm','Refined 0.025 mm'])):
 d=amrex_reader.read_plotfile(summary['plot']);T=d['fields']['Temp'];x=d['x']*10;y=d['y']*10;dx,dy=np.array(d['dx'])*10;px,py=summary['peak_xy_mm'];extent=[0,140,0,40]
 im=axes[row,0].imshow(T.T,origin='lower',extent=extent,vmin=300,vmax=vmax,cmap='inferno',interpolation='nearest',aspect='equal');axes[row,0].plot(px,py,'o',mec='cyan',mfc='none',ms=7,mew=1)
 axes[row,0].set(title=f'{label}: full domain, t = {d["time"]*1e6:.3f} us',xlabel='x (mm)',ylabel='y (mm)')
 ylo=max(0,py-.3);yhi=min(40,ylo+.6);ix=(x>=px-.5)&(x<=px+.5);iy=(y>=ylo)&(y<=yhi);values=T[np.ix_(ix,iy)].T;local_extent=[x[ix][0]-dx/2,x[ix][-1]+dx/2,y[iy][0]-dy/2,y[iy][-1]+dy/2]
 axes[row,1].imshow(values,origin='lower',extent=local_extent,vmin=300,vmax=vmax,cmap='inferno',interpolation='nearest',aspect='equal')
 if values.min()<5000<values.max():axes[row,1].contour(x[ix],y[iy],values,levels=[5000],colors='cyan',linewidths=.7)
 axes[row,1].plot(px,py,'+',color='cyan',ms=7);axes[row,1].set(title=f'Own peak neighborhood: {summary["Tmax_K"]:.1f} K\n({px:.4f}, {py:.4f}) mm',xlabel='x (mm)',ylabel='y (mm)')
fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.8,label='Temperature (K)');fig.suptitle('Full-domain context and each run\'s own hottest-cell neighborhood\nCommon temperature scale; zoom centers differ when hotspots move')
fig.savefig(b/'grid_final_fields_v1/global_peaks.png',dpi=180)
