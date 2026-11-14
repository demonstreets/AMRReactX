"""Read AMReX particle blocks using Header offsets, including multiple grids/file."""
from __future__ import annotations
import pathlib
from contextlib import ExitStack
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
    rows=[];integer_rows=[]
    with ExitStack() as stack:
        streams={}
        for level,nboxes in enumerate(ngrid):
            for _ in range(nboxes):
                fileno,np_here,offset=map(int,next(lines).split())
                if np_here==0:continue
                if np_here<0:raise ValueError('negative particle block count')
                path=root/f'Level_{level}'/f'DATA_{fileno:05d}'
                if path not in streams:
                    streams[path]=(stack.enter_context(path.open('rb')),path.stat().st_size)
                stream,size=streams[path]
                real_offset=offset+np_here*(2+ni)*4
                needed=np_here*(dim+nr)*8
                if offset<0 or real_offset<0 or real_offset+needed>size:raise ValueError('particle block exceeds file')
                # A file can contain hundreds of grids. Read only this block,
                # rather than allocating and rereading the entire file per grid.
                stream.seek(offset)
                integer_values=np.fromfile(stream,dtype='<i4',count=np_here*(2+ni)).reshape(np_here,2+ni)
                values=np.fromfile(stream,dtype='<f8',count=np_here*(dim+nr)).reshape(np_here,dim+nr)
                if not np.all(np.isfinite(values)):raise ValueError('nonfinite particle payload')
                rows.append(values);integer_rows.append(integer_values)
    values=np.concatenate(rows,axis=0) if rows else np.empty((0,dim+nr))
    integers=np.concatenate(integer_rows,axis=0) if integer_rows else np.empty((0,2+ni),dtype=np.int32)
    if len(values)!=count:raise ValueError('native particle count mismatch')
    names=[f'coordinate_{i}' for i in range(dim)]+real_names
    return {'fields':dict(zip(names,values.T)),'count':count,'dimension':dim,'next_id':nextid,'integer_names':int_names,
            'identity_words':integers[:,:2], 'integer_fields':dict(zip(int_names,integers[:,2:].T))}
