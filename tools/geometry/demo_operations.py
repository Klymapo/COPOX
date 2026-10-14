#!/usr/bin/env python3
"""Demo determinista sin ningún activo de Hunyuan/Beta/Gamma.
Tres operaciones geométricas reales, renders sintéticos y un GLB de prueba SIN rig.
No fusiona ni toca modelos de producción.
"""
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from copox.geometry.kernel import boundary_loops
from copox.geometry.surface_sculpt import flatten_surface
from copox.geometry.anatomic_cut import cut_plane
from copox.geometry.surface_stitch import MeshPart,stitch_parts

OUT=Path("docs/geometry/demo")
OUT.mkdir(parents=True,exist_ok=True)

def sphere(u=48,v=28):
    vertices=[]
    for i in range(v+1):
        lat=-math.pi/2+math.pi*(i+.00001)/(v+.00002)
        for j in range(u):
            a=2*math.pi*j/u
            vertices.append([.24*math.cos(lat)*math.cos(a),.26*math.sin(lat),.245*math.cos(lat)*math.sin(a)])
    vertices=np.asarray(vertices,float)
    faces=[]
    for i in range(v):
        for j in range(u):
            a=i*u+j;b=i*u+(j+1)%u;c=(i+1)*u+j;d=(i+1)*u+(j+1)%u
            faces.extend([(a,b,c),(b,d,c)])
    return vertices,np.array(faces,int)

def make_bridge():
    n=16;theta=np.arange(n)*2*np.pi/n
    ring=np.c_[.16*np.cos(theta),.16*np.sin(theta),np.zeros(n)]
    a=np.vstack([ring,[[0,0,0]]])
    b=np.vstack([ring+[0,0,.35],[[0,0,.35]]])
    fa=np.array([[n,(i+1)%n,i] for i in range(n)],int)
    fb=np.array([[n,i,(i+1)%n] for i in range(n)],int)
    attrs_a={"NORMAL":np.tile([0,0,-1.],(n+1,1)),
             "TEXCOORD_0":np.vstack([np.c_[.5+.5*np.cos(theta),.5+.5*np.sin(theta)],[[.5,.5]]])}
    attrs_b={"NORMAL":np.tile([0,0,1.],(n+1,1)),
             "TEXCOORD_0":attrs_a["TEXCOORD_0"].copy()}
    ma=MeshPart(a,fa,attrs_a,material_id=0)
    mb=MeshPart(b,fb,attrs_b,material_id=1)
    return stitch_parts(ma,mb,boundary_loops(fa)[0],boundary_loops(fb)[0],max_gap=.40,bridge_material=2)

def wire_render(image,vertices,faces,box,label,yaw,scale=400,color=(150,181,201)):
    draw=ImageDraw.Draw(image)
    x0,y0,x1,y1=box
    draw.rectangle((x0,y0,x1,y1),fill=(238,240,244))
    draw.text((x0+9,y0+9),label,fill=(35,45,58))
    co,si=np.cos(yaw),np.sin(yaw)
    p=np.asarray(vertices)
    screen_x=p[:,0]*co+p[:,2]*si
    depth=p[:,2]*co-p[:,0]*si
    screen_y=p[:,1]
    center=((x0+x1)/2,(y0+y1)/2+10)
    xy=np.c_[center[0]+screen_x*scale,center[1]-screen_y*scale]
    order=np.argsort(depth[faces].mean(axis=1))
    for i in order:
        tri=faces[i];a,b,c=p[tri]
        normal=np.cross(b-a,c-a)
        length=np.linalg.norm(normal)
        if length<1e-11:continue
        normal/=length
        lit=np.clip(.58+.37*abs(np.dot(normal,[.27,.57,.78])),.48,1)
        fill=tuple(int(z*lit) for z in color)
        coords=[tuple(xy[j].round().astype(int)) for j in tri]
        draw.polygon(coords,fill=fill)
        # Draw only fine edges: genuine triangulation, not AI-generated.
        draw.line(coords+[coords[0]],fill=(109,127,145),width=1)

def sheet(path,cases,scale=400):
    w=800;h=810
    canvas=Image.new("RGB",(w,h),(250,250,249))
    views=[("Frente",0),("3/4",math.pi/4),("Perfil",math.pi/2),("Espalda",math.pi)]
    for row,(label,verts,faces) in enumerate(cases):
        for col,(view,yaw) in enumerate(views):
            wire_render(canvas,verts,faces,(col*200,row*400,(col+1)*200-2,(row+1)*400-2),
                        f"{label}: {view}",yaw,scale=scale)
    canvas.save(path)

def save_simple_glb(path,vertices,faces):
    """Export de una sola primitiva, sin materiales múltiples ni skinning."""
    v=np.asarray(vertices,dtype="<f4");f=np.asarray(faces,dtype="<u4").reshape(-1)
    binary=bytearray(v.tobytes());off=len(binary);binary.extend(f.tobytes())
    document={"asset":{"version":"2.0","generator":"COPOX synthetic geometry demo"},
      "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0}],
      "meshes":[{"primitives":[{"attributes":{"POSITION":0},"indices":1,"mode":4}]}],
      "accessors":[
        {"bufferView":0,"componentType":5126,"count":len(v),"type":"VEC3",
         "min":v.min(axis=0).astype(float).tolist(),"max":v.max(axis=0).astype(float).tolist()},
        {"bufferView":1,"componentType":5125,"count":len(f),"type":"SCALAR"}],
      "bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":off,"target":34962},
                     {"buffer":0,"byteOffset":off,"byteLength":len(f)*4,"target":34963}],
      "buffers":[{"byteLength":len(binary)}]}
    jb=json.dumps(document,separators=(',',':')).encode("utf-8")
    jb+=b" "*(-len(jb)%4)
    binary.extend(bytes([0])*(-len(binary)%4))
    payload=struct.pack("<4sII",b"glTF",2,28+len(jb)+len(binary))
    payload+=struct.pack("<I4s",len(jb),b"JSON")+jb
    payload+=struct.pack("<I4s",len(binary),bytes([66,73,78,0]))+binary
    path.write_bytes(payload)
    assert payload[:4]==b"glTF" and struct.unpack_from("<I",payload,8)[0]==len(payload)
    return hashlib.sha256(payload).hexdigest()

original,faces=sphere()
sculpt=flatten_surface(original,direction=[0,0,1],target_projection=.190,
  region_center=[0,.09,.18],region_radii=[.23,.19,.25],strength=.95,
  falloff=.42, max_displacement=.060)
sheet(OUT/"01_scully_antes_despues.png",
      [("Original",original,faces),("Scully",sculpt.positions,faces)],scale=305)

cut=cut_plane({"POSITION":original,"NORMAL":np.zeros_like(original)+[0,0,1.]},
       faces, [0,1,0], .045)
sheet(OUT/"02_anatomic_cut.png",
      [("Esfera",original,faces),("Corte y<=.045",cut.attributes["POSITION"],cut.faces)],scale=305)

stitch=make_bridge()
sheet(OUT/"03_surface_stitch.png",
      [("Dos tapas",np.vstack((stitch.positions[:17],stitch.positions[17:])),
          np.vstack((stitch.faces[:16],stitch.faces[16:32]))),
       ("Stitch",stitch.positions,stitch.faces)],scale=375)

sha=save_simple_glb(OUT/"surface_stitch_sintetico.glb",stitch.positions,stitch.faces)
report={"source":"100% parametric synthetic Python geometry; no Hunyuan input",
 "scully":{"changed_vertices":sculpt.changed_vertices,
           "maximum_displacement_m":sculpt.maximum_displacement},
 "anatomic_cut":{"clipped_faces":cut.clipped_faces,
                "removed_faces":cut.removed_faces,"added_vertices":cut.added_vertices},
 "surface_stitch":stitch.report,
 "glb_demo":{"path":"surface_stitch_sintetico.glb","sha256":sha,
             "rigged":False,"multiple_materials_exported":False},
 "limitations":["Synthetic demonstration, not Maniqui production",
   "Surface Stitch GLB demo exports geometry without original material splits",
   "No tested skeleton, facial morph targets or Godot"]}
(OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,ensure_ascii=False,indent=2))
