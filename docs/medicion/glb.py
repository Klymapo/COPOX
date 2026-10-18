import json,struct,numpy as np
CT={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(p):
    b=open(p,'rb').read()
    L=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+L])
    o=20+L; bl=struct.unpack('<I',b[o:o+4])[0]; binc=b[o+8:o+8+bl]
    return j,binc
def acc(j,binc,i):
    a=j['accessors'][i]; n=NC[a['type']]; dt=CT[a['componentType']]
    if 'bufferView' not in a: return np.zeros((a['count'],n),dt)
    bv=j['bufferViews'][a['bufferView']]; off=bv.get('byteOffset',0)+a.get('byteOffset',0)
    isz=np.dtype(dt).itemsize*n; st=bv.get('byteStride',isz)
    if st==isz: arr=np.frombuffer(binc,dt,a['count']*n,off).reshape(a['count'],n)
    else:
        raw=np.frombuffer(binc,np.uint8,st*(a['count']-1)+isz,off)
        arr=np.lib.stride_tricks.as_strided(raw,(a['count'],isz),(st,1)).copy().view(dt).reshape(a['count'],n)
    if a.get('normalized'): arr=arr.astype(np.float32)/np.iinfo(dt).max
    return arr
