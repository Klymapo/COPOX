# ============================================================
# ALTH_META — Chibi Low-Poly Base
# v0.8.4a — SILHOUETTE REFINEMENT A
#
# Small candidate step built on v0.8.3.
# Focus only on silhouette:
# - independent head front/back depth
# - narrower lower face
# - stronger torso/pelvis continuity
# - refined leg silhouette
# - larger hands
# - longer toe box
#
# Blender 4.x | Text Editor -> Alt+P
# ============================================================

import bpy
import bmesh
import math
from mathutils import Vector, Euler

MM = 0.001
COLLECTION_NAME = "ALTH_META"
REMOVE_OLD = True
ADD_FACE = True
ADD_HANDS = True
ALTURA_TOTAL = 95.0

# ============================================================
# 1. CANDIDATE MEASUREMENTS
# ============================================================

M = {
    "cabeza": {
        "ancho": 40.0,
        "alto": 34.5,
        "mandibula_ancho": 36.5,
        # Head depth is now controlled per ring by front/back Y.
    },
    "cuello": {"ancho": 9.5, "prof": 8.5, "alto": 4.2},
    "torso": {
        "pecho": 30.0,
        "cintura": 25.8,
        "cadera": 25.8,
        "alto": 19.0,
    },
    "pelvis": {"ancho": 25.8, "prof": 17.4, "alto": 6.2},
    "brazo": {
        "upper_largo": 11.0,
        "fore_largo": 10.0,
        "hombro_h": 9.8,
        "hombro_d": 8.4,
        "biceps_h": 9.2,
        "biceps_d": 7.8,
        "codo_h": 8.1,
        "codo_d": 7.1,
        "fore_h": 8.6,
        "fore_d": 7.2,
        "muneca_h": 7.1,
        "muneca_d": 6.3,
    },
    "palma": {
        "largo": 7.5,
        "ancho_muneca": 6.2,
        "ancho_dedos": 9.4,
        "prof_muneca": 3.4,
        "prof_dedos": 4.0,
    },
    "dedos": {
        "indice": {"largo": 5.5, "ancho": 1.9},
        "medio": {"largo": 6.0, "ancho": 2.0},
        "anular": {"largo": 5.5, "ancho": 1.9},
        "menique": {"largo": 4.7, "ancho": 1.75},
        "pulgar": {"largo": 5.1, "ancho": 2.1},
        "prof": 1.9,
    },
    "pierna": {
        "largo": 24.0,
        "hip_w": 11.4,
        "hip_d": 9.0,
        "thigh_w": 10.8,
        "thigh_d": 8.7,
        "knee_w": 9.0,
        "knee_d": 7.7,
        "calf_w": 9.8,
        "calf_d": 8.1,
        "ankle_w": 7.8,
        "ankle_d": 7.2,
    },
    "zapato": {"largo": 18.0, "ancho": 11.8, "alto": 9.0, "suela": 1.8},
    "oreja": {"ancho": 6.5, "prof": 3.8, "alto": 8.5},
    "ojo": {"ancho": 8.5, "alto": 9.5, "prof": 1.2, "radio": 2.25, "centro_x": 6.2},
    "iris": {"ancho": 3.9, "alto": 6.5, "prof": 0.75},
    "ceja": {"ancho": 9.2, "alto": 1.9, "prof": 0.85},
    "nariz": {"ancho": 3.8, "alto": 2.7, "prof": 1.8},
    "boca": {"ancho": 7.5, "grosor": 0.42},
}

Z = {
    "suelo": 0.0,
    "zapato_ini": 0.0,
    "zapato_fin": 9.0,
    "pierna_ini": 8.3,
    "pierna_fin": 32.3,
    "pelvis_ini": 31.1,
    "pelvis_fin": 37.3,
    "torso_ini": 35.6,
    "torso_fin": 54.6,
    "cuello_ini": 54.0,
    "cuello_fin": 58.2,
    "cabeza_ini": 60.5,
    "cabeza_fin": 95.0,
    "hombro": 52.2,
    "ojos": 78.5,
    "cejas": 84.0,
    "nariz": 72.8,
    "boca": 68.3,
    "orejas": 77.0,
}

X = {"hombro": 15.2, "cadera": 8.2, "ojo": 6.2, "oreja": 20.5}

STYLE = {
    "head_bevel": 4.0,
    "head_segments": 4,
    "torso_bevel": 2.3,
    "torso_segments": 3,
    "pelvis_bevel": 1.7,
    "arm_bevel": 1.6,
    "leg_bevel": 1.5,
    "hand_bevel": 0.9,
    "finger_bevel": 0.45,
    "shoe_bevel": 1.6,
    "ear_bevel": 1.2,
    "nose_bevel": 0.65,
    "shoe_angle": 4.5,
}

# ============================================================
# 2. MATERIALS
# ============================================================

def material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    return mat

MAT_SKIN = material("META_Skin", (0.72, 0.47, 0.36, 1))
MAT_BODY = material("META_Body", (0.38, 0.43, 0.50, 1))
MAT_SHOE = material("META_Shoe", (0.055, 0.055, 0.06, 1))
MAT_DARK = material("META_Dark", (0.035, 0.025, 0.020, 1))
MAT_WHITE = material("META_EyeWhite", (0.94, 0.94, 0.92, 1))
MAT_EYE = material("META_Eye", (0.12, 0.055, 0.025, 1))

# ============================================================
# 3. BASIC HELPERS
# ============================================================

def limpiar():
    if not REMOVE_OLD:
        return
    for ob in list(bpy.data.objects):
        if ob.name.startswith("META_") or ob.name.startswith("ALTH_"):
            bpy.data.objects.remove(ob, do_unlink=True)


def get_collection():
    col = bpy.data.collections.get(COLLECTION_NAME)
    if col is None:
        col = bpy.data.collections.new(COLLECTION_NAME)
    if col.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(col)
    return col


def mesh_obj(name, bm, col):
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def set_material(ob, mat):
    if not mat:
        return
    if len(ob.data.materials) == 0:
        ob.data.materials.append(mat)
    else:
        ob.data.materials[0] = mat


def add_bevel(ob, width_mm, segments=2):
    if width_mm <= 0:
        return ob
    mod = ob.modifiers.new("META_Bevel", "BEVEL")
    mod.width = width_mm * MM
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(25)
    mod.use_clamp_overlap = True
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def create_box(name, dims, loc, col, bevel=0, segments=2, mat=None, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((dims[0]*MM, dims[1]*MM, dims[2]*MM)), verts=bm.verts[:])
    ob = mesh_obj(name, bm, col)
    ob.location = Vector((loc[0]*MM, loc[1]*MM, loc[2]*MM))
    ob.rotation_euler = Euler(tuple(math.radians(v) for v in rot), "XYZ")
    set_material(ob, mat)
    add_bevel(ob, bevel, segments)
    return ob


def create_profile_body(name, profiles, height, bottom_z, col, bevel, segments, mat, loc_x=0.0, loc_y=0.0):
    """profiles = [(t, width, depth), ...]"""
    bm = bmesh.new()
    rings = []
    for t, width, depth in profiles:
        z = t * height * MM
        w, d = width/2*MM, depth/2*MM
        rings.append([
            bm.verts.new((-w, -d, z)), bm.verts.new((w, -d, z)),
            bm.verts.new((w, d, z)), bm.verts.new((-w, d, z)),
        ])
    _bridge_rings(bm, rings)
    ob = mesh_obj(name, bm, col)
    ob.location = Vector((loc_x*MM, loc_y*MM, bottom_z*MM))
    set_material(ob, mat)
    add_bevel(ob, bevel, segments)
    return ob


def create_asymmetric_profile_body(name, profiles, height, bottom_z, col, bevel, segments, mat):
    """profiles = [(t, width, front_y, back_y), ...]. Front is negative Y."""
    bm = bmesh.new()
    rings = []
    for t, width, front_y, back_y in profiles:
        z = t * height * MM
        w = width/2*MM
        yf, yb = front_y*MM, back_y*MM
        rings.append([
            bm.verts.new((-w, yf, z)), bm.verts.new((w, yf, z)),
            bm.verts.new((w, yb, z)), bm.verts.new((-w, yb, z)),
        ])
    _bridge_rings(bm, rings)
    ob = mesh_obj(name, bm, col)
    ob.location.z = bottom_z * MM
    set_material(ob, mat)
    add_bevel(ob, bevel, segments)
    return ob


def _bridge_rings(bm, rings):
    for i in range(len(rings)-1):
        a, b = rings[i], rings[i+1]
        for j in range(4):
            k = (j+1) % 4
            bm.faces.new((a[j], a[k], b[k], b[j]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bm.normal_update()


def create_profile_segment(name, p0, p1, profiles, col, bevel, segments, mat):
    p0, p1 = Vector(p0), Vector(p1)
    vec = p1 - p0
    length = vec.length
    if length <= 0:
        raise ValueError(name + ": zero length")
    bm = bmesh.new()
    rings = []
    for t, width, depth in profiles:
        z = (t - 0.5) * length * MM
        w, d = width/2*MM, depth/2*MM
        rings.append([
            bm.verts.new((-w, -d, z)), bm.verts.new((w, -d, z)),
            bm.verts.new((w, d, z)), bm.verts.new((-w, d, z)),
        ])
    _bridge_rings(bm, rings)
    ob = mesh_obj(name, bm, col)
    ob.location = ((p0+p1)/2) * MM
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0,0,1)).rotation_difference(vec.normalized())
    set_material(ob, mat)
    add_bevel(ob, bevel, segments)
    return ob

# ============================================================
# 4. FACE HELPERS
# ============================================================

def create_rounded_rect_prism(name, width, height, depth, radius, loc, col, mat, corner_segments=4):
    radius = min(radius, width/2, height/2)
    hw, hh = width/2, height/2
    corners = [
        (hw-radius, hh-radius, 0, 90), (-hw+radius, hh-radius, 90, 180),
        (-hw+radius, -hh+radius, 180, 270), (hw-radius, -hh+radius, 270, 360),
    ]
    outline = []
    for cx, cz, a0, a1 in corners:
        for i in range(corner_segments+1):
            if outline and i == 0:
                continue
            a = math.radians(a0 + (a1-a0)*(i/corner_segments))
            outline.append((cx + radius*math.cos(a), cz + radius*math.sin(a)))
    bm = bmesh.new(); front=[]; back=[]
    yf, yb = -depth/2*MM, depth/2*MM
    for x,z in outline:
        front.append(bm.verts.new((x*MM, yf, z*MM)))
        back.append(bm.verts.new((x*MM, yb, z*MM)))
    bm.faces.new(front[::-1]); bm.faces.new(back)
    for i in range(len(front)):
        j=(i+1)%len(front); bm.faces.new((front[i],front[j],back[j],back[i]))
    bm.normal_update()
    ob=mesh_obj(name,bm,col)
    ob.location=Vector((loc[0]*MM,loc[1]*MM,loc[2]*MM))
    set_material(ob,mat)
    return ob


def create_ellipse_prism(name, width, height, depth, loc, col, mat, segments=16):
    bm=bmesh.new(); front=[]; back=[]
    yf,yb=-depth/2*MM, depth/2*MM
    for i in range(segments):
        a=2*math.pi*i/segments
        x=math.cos(a)*width/2*MM; z=math.sin(a)*height/2*MM
        front.append(bm.verts.new((x,yf,z))); back.append(bm.verts.new((x,yb,z)))
    bm.faces.new(front[::-1]); bm.faces.new(back)
    for i in range(segments):
        j=(i+1)%segments; bm.faces.new((front[i],front[j],back[j],back[i]))
    bm.normal_update()
    ob=mesh_obj(name,bm,col)
    ob.location=Vector((loc[0]*MM,loc[1]*MM,loc[2]*MM))
    set_material(ob,mat)
    return ob


def create_mouth(col, root, face_front_y):
    curve=bpy.data.curves.new("META_MouthCurve","CURVE")
    curve.dimensions="3D"; curve.bevel_depth=M["boca"]["grosor"]*MM; curve.bevel_resolution=0
    spl=curve.splines.new("POLY"); spl.points.add(2)
    coords=[
        (-M["boca"]["ancho"]/2,face_front_y-0.45,Z["boca"]+0.3),
        (0,face_front_y-0.50,Z["boca"]-0.25),
        (M["boca"]["ancho"]/2,face_front_y-0.45,Z["boca"]+0.1),
    ]
    for p,co in zip(spl.points,coords): p.co=(co[0]*MM,co[1]*MM,co[2]*MM,1)
    ob=bpy.data.objects.new("META_Mouth",curve); col.objects.link(ob); ob.data.materials.append(MAT_DARK); ob.parent=root

# ============================================================
# 5. HAND
# ============================================================

def create_hand(side, wrist, col, root):
    sign = 1 if side == "R" else -1
    palm_end = Vector((wrist.x + sign*M["palma"]["largo"], wrist.y, wrist.z))
    palm = create_profile_segment(
        f"META_Palm_{side}", wrist, palm_end,
        [(0.00,M["palma"]["ancho_muneca"],M["palma"]["prof_muneca"]),
         (0.40,7.6,3.7),
         (1.00,M["palma"]["ancho_dedos"],M["palma"]["prof_dedos"])],
        col, STYLE["hand_bevel"], 2, MAT_SKIN)
    palm.parent=root
    fingers=[("Index",M["dedos"]["indice"],3.0),("Middle",M["dedos"]["medio"],1.0),("Ring",M["dedos"]["anular"],-1.0),("Pinky",M["dedos"]["menique"],-3.0)]
    for name,f,zoff in fingers:
        length=f["largo"]
        ob=create_box(
            f"META_{name}_{side}",
            (length,M["dedos"]["prof"],f["ancho"]),
            (palm_end.x + sign*(length/2-0.55),palm_end.y,palm_end.z+zoff),
            col,STYLE["finger_bevel"],2,MAT_SKIN)
        ob.parent=root
    thumb_start=Vector((wrist.x+sign*2.1,wrist.y,wrist.z-3.3))
    thumb_end=Vector((thumb_start.x+sign*4.0,thumb_start.y,thumb_start.z-3.0))
    thumb=create_profile_segment(f"META_Thumb_{side}",thumb_start,thumb_end,[(0.0,2.2,2.1),(1.0,1.75,1.8)],col,STYLE["finger_bevel"],2,MAT_SKIN)
    thumb.parent=root

# ============================================================
# 6. BUILD
# ============================================================

def build_meta():
    limpiar(); col=get_collection()
    root=bpy.data.objects.new("META_ROOT",None); col.objects.link(root); root.empty_display_type="PLAIN_AXES"; root.empty_display_size=6*MM

    # Shoes: preserve width/height; extend almost entirely forward (-Y).
    for side,sign in (("R",1),("L",-1)):
        x=sign*X["cadera"]
        shoe_y=-4.5
        shoe=create_profile_body(
            f"META_Shoe_{side}",
            [(0.00,11.8,18.0),(0.25,11.6,17.6),(1.00,10.0,14.5)],
            M["zapato"]["alto"],0,col,STYLE["shoe_bevel"],3,MAT_SHOE,loc_x=x,loc_y=shoe_y)
        shoe.rotation_euler.z=math.radians(-sign*STYLE["shoe_angle"]); shoe.parent=root
        sole=create_box(f"META_Sole_{side}",(12.6,18.8,M["zapato"]["suela"]),(x,shoe_y,M["zapato"]["suela"]/2),col,0.45,2,MAT_DARK,rot=(0,0,-sign*STYLE["shoe_angle"])); sole.parent=root

    # Legs: same length, more knee/calf rhythm and slightly narrower ankle.
    for side,sign in (("R",1),("L",-1)):
        leg=create_profile_body(
            f"META_Leg_{side}",
            [(0.00,M["pierna"]["ankle_w"],M["pierna"]["ankle_d"]),
             (0.18,8.6,7.5),
             (0.36,M["pierna"]["calf_w"],M["pierna"]["calf_d"]),
             (0.52,M["pierna"]["knee_w"],M["pierna"]["knee_d"]),
             (0.76,M["pierna"]["thigh_w"],M["pierna"]["thigh_d"]),
             (1.00,M["pierna"]["hip_w"],M["pierna"]["hip_d"])],
            M["pierna"]["largo"],Z["pierna_ini"],col,STYLE["leg_bevel"],3,MAT_BODY,loc_x=sign*X["cadera"])
        leg.parent=root

    # Pelvis is shorter and overlaps torso more strongly.
    pelvis=create_profile_body(
        "META_Pelvis",
        [(0.00,24.8,16.8),(0.45,25.8,17.4),(1.00,25.4,17.0)],
        M["pelvis"]["alto"],Z["pelvis_ini"],col,STYLE["pelvis_bevel"],3,MAT_BODY)
    pelvis.parent=root

    # Torso: more continuous sides; no obvious belt-like lower block.
    torso=create_profile_body(
        "META_Torso",
        [(0.00,25.8,17.2),(0.18,25.6,16.9),(0.38,25.8,16.8),(0.65,28.2,17.4),(1.00,30.0,18.0)],
        M["torso"]["alto"],Z["torso_ini"],col,STYLE["torso_bevel"],STYLE["torso_segments"],MAT_BODY)
    torso.parent=root

    neck=create_box("META_Neck",(M["cuello"]["ancho"],M["cuello"]["prof"],M["cuello"]["alto"]),(0,0,(Z["cuello_ini"]+Z["cuello_fin"])/2),col,1.2,3,MAT_SKIN); neck.parent=root

    # Head: front and back are controlled separately. Face stays comparatively flat;
    # most remaining volume is carried toward the back of the skull.
    HEAD_PROFILES=[
        (0.00,36.5,-14.0,14.8),
        (0.12,37.4,-14.3,15.1),
        (0.30,39.0,-14.6,15.5),
        (0.58,40.0,-14.8,16.0),
        (0.82,39.8,-14.7,16.2),
        (1.00,39.2,-14.3,16.0),
    ]
    head=create_asymmetric_profile_body("META_Head",HEAD_PROFILES,M["cabeza"]["alto"],Z["cabeza_ini"],col,STYLE["head_bevel"],STYLE["head_segments"],MAT_SKIN); head.parent=root
    face_front_y=-14.8

    for side,sign in (("R",1),("L",-1)):
        ear=create_box(f"META_Ear_{side}",(M["oreja"]["ancho"],M["oreja"]["prof"],M["oreja"]["alto"]),(sign*X["oreja"],0.8,Z["orejas"]),col,STYLE["ear_bevel"],3,MAT_SKIN); ear.parent=root

    # Arms remain the approved v0.8.3 continuous profile.
    total_arm=M["brazo"]["upper_largo"]+M["brazo"]["fore_largo"]
    for side,sign in (("R",1),("L",-1)):
        shoulder=Vector((sign*(X["hombro"]-0.8),0,Z["hombro"]))
        wrist=Vector((shoulder.x+sign*total_arm,0,shoulder.z))
        arm=create_profile_segment(
            f"META_Arm_{side}",shoulder,wrist,
            [(0.00,M["brazo"]["hombro_h"],M["brazo"]["hombro_d"]),(0.10,9.6,8.2),(0.32,M["brazo"]["biceps_h"],M["brazo"]["biceps_d"]),(0.52,M["brazo"]["codo_h"],M["brazo"]["codo_d"]),(0.72,M["brazo"]["fore_h"],M["brazo"]["fore_d"]),(1.00,M["brazo"]["muneca_h"],M["brazo"]["muneca_d"])],
            col,STYLE["arm_bevel"],3,MAT_SKIN)
        arm.parent=root
        if ADD_HANDS: create_hand(side,wrist,col,root)

    if ADD_FACE:
        for side,sign in (("R",1),("L",-1)):
            eye_x=sign*M["ojo"]["centro_x"]
            eye=create_rounded_rect_prism(f"META_EyeWhite_{side}",M["ojo"]["ancho"],M["ojo"]["alto"],M["ojo"]["prof"],M["ojo"]["radio"],(eye_x,face_front_y-0.65,Z["ojos"]),col,MAT_WHITE,4); eye.parent=root
            iris=create_ellipse_prism(f"META_Iris_{side}",M["iris"]["ancho"],M["iris"]["alto"],M["iris"]["prof"],(eye_x+sign*0.2,face_front_y-1.35,Z["ojos"]-0.3),col,MAT_EYE,16); iris.parent=root
            brow=create_box(f"META_Brow_{side}",(M["ceja"]["ancho"],M["ceja"]["prof"],M["ceja"]["alto"]),(eye_x,face_front_y-0.85,Z["cejas"]),col,0.45,2,MAT_DARK,rot=(0,0,sign*2)); brow.parent=root
        nose=create_box("META_Nose",(M["nariz"]["ancho"],M["nariz"]["prof"],M["nariz"]["alto"]),(0,face_front_y-M["nariz"]["prof"]/2-0.25,Z["nariz"]),col,STYLE["nose_bevel"],3,MAT_SKIN); nose.parent=root
        create_mouth(col,root,face_front_y)

    try:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D": space.overlay.show_relationship_lines=False
    except Exception:
        pass

    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True); bpy.context.view_layer.objects.active=root
    print("✅ ALTH_META v0.8.4a — Silhouette Refinement A")
    print("Candidate only: v0.8.3 remains the retained baseline until visual approval.")

build_meta()
