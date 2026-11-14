"""Read AMReX particle blocks using Header offsets, including multiple grids/file."""
from __future__ import annotations
import pathlib
import numpy as np

def read_native_spray(plot):
    root=pathlib.Path(plot)/'particles'
    lines=iter((root/'Header').read_text().splitlines())
    version=next(lines).strip()
    if version!='Version_Two_Dot_One_double':raise ValueError(f'unsupported particle format {version}')
    dim=int(next(lines));nr=int(next(lines));real_names=[next(lines).strip() for _ in range(nr)]
    ni=int(next(lines));int_names=[next(lines).strip() for _ in range(ni)]
    checkpoint=int(next(lines));count=int(next(lines));nextid=int(next(lines));finest=int(next(lines))
    if checkpoint!=1:raise ValueError('particle ID layout must be explicitly present')
    ngrid=[int(next(lines)) for _ in range(finest+1)]
    rows=[]
    for level,nboxes in enumerate(ngrid):
        for _ in range(nboxes):
            fileno,np_here,offset=map(int,next(lines).split())
            if np_here==0:continue
            path=root/f'Level_{level}'/f'DATA_{fileno:05d}'
            raw=path.read_bytes();real_offset=offset+np_here*(2+ni)*4
            needed=np_here*(dim+nr)*8
            if real_offset<0 or real_offset+needed>len(raw):raise ValueError('particle block exceeds file')
            values=np.frombuffer(raw,dtype='<f8',count=np_here*(dim+nr),offset=real_offset).reshape(np_here,dim+nr).copy()
            if not np.all(np.isfinite(values)):raise ValueError('nonfinite particle payload')
            rows.append(values)
    values=np.concatenate(rows,axis=0) if rows else np.empty((0,dim+nr))
    if len(values)!=count:raise ValueError('native particle count mismatch')
    names=[f'coordinate_{i}' for i in range(dim)]+real_names
    return {'fields':dict(zip(names,values.T)),'count':count,'dimension':dim,'next_id':nextid,'integer_names':int_names}
