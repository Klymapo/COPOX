import struct,json,numpy as np
from pathlib import Path
CT={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
NT={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
class GLB:
 def __init__(self,path):
  self.path=Path(path)
  dat=self.path.read_bytes(); assert dat[:4]==b'glTF'
  self.version,self.size=struct.unpack_from('<II',dat,4)
  assert self.size==len(dat)
  offset=12;chunks=[]
  while offset<len(dat):
   n,t=struct.unpack_from('<I4s',dat,offset);offset+=8;chunks.append((t,dat[offset:offset+n]));offset+=n
  self.doc=json.loads([x for typ,x in chunks if typ==b'JSON'][0])
  self.bin=[x for typ,x in chunks if typ==b'BIN\0'][0]
 def acc(self,id):
  a=self.doc['accessors'][id];v=self.doc['bufferViews'][a['bufferView']];dt=np.dtype(CT[a['componentType']]).newbyteorder('<');n=a['count'];k=NT[a['type']];byte=v['byteOffset']+a.get('byteOffset',0);stride=v.get('byteStride',dt.itemsize*k)
  vals=np.ndarray((n,k),dtype=dt,buffer=self.bin,offset=byte,strides=(stride,dt.itemsize)).copy()
  return vals[:,0] if k==1 else vals
 def prim(self,i):
  p=self.doc['meshes'][0]['primitives'][i]
  return p,self.acc(p['indices']).reshape(-1,3).astype(int),{k:self.acc(a) for k,a in p['attributes'].items()}
 def write_changes(self,out,positions=None,normals=None,faces=None,extra_faces=None):
  '''Only modify primitive 0 indices & position if provided.'''
  d=json.loads(json.dumps(self.doc));raw=bytearray(self.bin)
  def add(arr,typ,ct,target):
   nonlocal raw
   ar=np.asarray(arr,dtype=CT[ct]);raw.extend(b'\0'*((-len(raw))%4));off=len(raw);raw.extend(ar.tobytes())
   view={'buffer':0,'byteOffset':off,'byteLength':ar.nbytes,'target':target};d['bufferViews'].append(view)
   idx=len(d['bufferViews'])-1
   aa={'bufferView':idx,'componentType':ct,'count':len(ar),'type':typ}
   if typ=='VEC3':
    aa['min']=ar.min(axis=0).tolist();aa['max']=ar.max(axis=0).tolist()
   d['accessors'].append(aa);return len(d['accessors'])-1
  p=d['meshes'][0]['primitives'][0]
  if positions is not None: p['attributes']['POSITION']=add(positions,'VEC3',5126,34962)
  if normals is not None: p['attributes']['NORMAL']=add(normals,'VEC3',5126,34962)
  if faces is not None:p['indices']=add(np.asarray(faces,dtype=np.uint32).ravel(),'SCALAR',5125,34963)
  d['buffers'][0]['byteLength']=len(raw)
  bjs=json.dumps(d,separators=(',',':')).encode();bjs+=b' '*((-len(bjs))%4)
  raw.extend(b'\0'*((-len(raw))%4))
  block=b'glTF'+struct.pack('<II',2,12+8+len(bjs)+8+len(raw))+struct.pack('<I4s',len(bjs),b'JSON')+bjs+struct.pack('<I4s',len(raw),b'BIN\0')+raw
  Path(out).write_bytes(block);return out
