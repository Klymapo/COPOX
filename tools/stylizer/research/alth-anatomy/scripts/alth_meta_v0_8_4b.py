# ============================================================
# ALTH_META — Chibi Low-Poly Base
# v0.8.4b — SILHOUETTE REFINEMENT B
#
# Focus:
# - reduce rear head depth / narrow lower face
# - hide neck further
# - integrate torso + pelvis silhouette
# - stronger shoulder / forearm profile
# - larger readable hands
# - clearer calf / knee / ankle rhythm
# - longer toe box without increasing shoe height
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

M = {
    "cabeza": {"ancho": 40.0, "alto": 34.5, "prof": 29.8, "mandibula_ancho": 36.2, "mandibula_prof": 28.8},
    "cuello": {"ancho": 9.0, "prof": 8.0, "alto": 4.0},
    "torso": {"pecho": 30.5, "cintura": 25.0, "cadera": 25.2, "prof_pecho": 17.8, "prof_cintura": 16.4, "prof_cadera": 16.8, "alto": 19.3},
    "pelvis": {"ancho": 25.0, "prof": 17.0, "alto": 5.8},
    "brazo": {"upper_largo": 11.0, "fore_largo": 10.0, "hombro_h": 10.2, "hombro_d": 8.6, "biceps_h": 9.3, "biceps_d": 7.9, "codo_h": 8.0, "codo_d": 7.0, "fore_h": 8.8, "fore_d": 7.3, "muneca_h": 7.0, "muneca_d": 6.2},
    "palma": {"largo": 7.5, "ancho_muneca": 6.2, "ancho_dedos": 9.4, "prof_muneca": 3.5, "prof_dedos": 4.0},
    "dedos": {
        "indice": {"largo": 5.5, "ancho": 1.9},
        "medio": {"largo": 6.0, "ancho": 2.0},
        "anular": {"largo": 5.5, "ancho": 1.9},
        "menique": {"largo": 4.7, "ancho": 1.7},
        "pulgar": {"largo": 5.1, "ancho": 2.1},
        "prof": 1.9,
    },
    "pierna": {"largo": 24.0, "hip_w": 11.0, "hip_d": 8.9, "thigh_w": 10.6, "thigh_d": 8.5, "knee_w": 9.1, "knee_d": 7.6, "calf_w": 9.7, "calf_d": 8.1, "ankle_w": 7.9, "ankle_d": 7.1},
    "zapato": {"largo": 18.0, "ancho": 11.9, "alto": 9.0, "suela": 1.8},
    "oreja": {"ancho": 6.5, "prof": 3.8, "alto": 8.4},
    "ojo": {"ancho": 8.4, "alto": 9.7, "prof": 1.2, "radio": 2.3, "centro_x": 6.15},
    "iris": {"ancho": 3.9, "alto": 6.5, "prof": 0.75},
    "ceja": {"ancho": 9.2, "alto": 1.9, "prof": 0.85},
    "nariz": {"ancho": 3.8, "alto": 2.7, "prof": 1.8},
    "boca": {"ancho": 7.5, "grosor": 0.42},
}

Z = {
    "suelo": 0.0, "zapato_ini": 0.0, "zapato_fin": 9.0,
    "pierna_ini": 8.3, "pierna_fin": 32.3,
    "pelvis_ini": 31.0, "pelvis_fin": 36.8,
    "torso_ini": 35.8, "torso_fin": 55.1,
    "cuello_ini": 55.1, "cuello_fin": 59.1,
    "cabeza_ini": 60.5, "cabeza_fin": 95.0,
    "hombro": 53.0, "ojos": 78.5, "cejas": 84.0,
    "nariz": 72.8, "boca": 68.3, "orejas": 77.0,
}

X = {"hombro": 15.5, "cadera": 8.15, "ojo": 6.15, "oreja": 20.4}

STYLE = {
    "head_bevel": 4.0, "head_segments": 4,
    "torso_bevel": 2.3, "torso_segments": 3,
    "pelvis_bevel": 1.6, "arm_bevel": 1.6,
    "leg_bevel": 1.5, "hand_bevel": 0.9,
    "finger_bevel": 0.45, "shoe_bevel": 1.6,
    "ear_bevel": 1.2, "nose_bevel": 0.65,
    "shoe_angle": 4.5,
}

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
    if mat is None:
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
    for poly in ob.data.polygons:
        poly.use_smooth = False
    return ob

def _bridge_rings(bm, rings):
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(4):
            k = (j + 1) % 4
            bm.faces.new((a[j], a[k], b[k], b[j]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bm.normal_update()

def create_box(name, dims, loc, col, bevel=0, segments=2, mat=None, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((dims[0]*MM, dims[1]*MM, dims[2]*MM)), verts=bm.verts[:])
    ob = mesh_obj(name, bm, col)
    ob.location = Vector((loc[0]*MM, loc[1]*MM, loc[2]*MM))
    ob.rotation_euler = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), "XYZ")
    set_material(ob, mat)
    add_bevel(ob, bevel, segments)
    return ob

def create_profile_body(name, profiles, height, bottom_z, col, bevel, segments, mat, loc_x=0.0, loc_y=0.0):
    bm = bmesh.new(); rings = []
    for t, width, depth in profiles:
        z = t * height * MM; w = width/2*MM; d = depth/2*MM
        rings.append([bm.verts.new((-w,-d,z)), bm.verts.new((w,-d,z)), bm.verts.new((w,d,z)), bm.verts.new((-w,d,z))])
    _bridge_rings(bm, rings)
    ob = mesh_obj(name, bm, col)
    ob.location = Vector((loc_x*MM, loc_y*MM, bottom_z*MM))
    set_material(ob, mat); add_bevel(ob, bevel, segments)
    return ob

def create_asymmetric_profile_body(name, profiles, height, bottom_z, col, bevel, segments, mat):
    bm = bmesh.new(); rings = []
    for t, width, front_y, back_y in profiles:
        z = t * height * MM; w = width/2*MM; yf = front_y*MM; yb = back_y*MM
        rings.append([bm.verts.new((-w,yf,z)), bm.verts.new((w,yf,z)), bm.verts.new((w,yb,z)), bm.verts.new((-w,yb,z))])
    _bridge_rings(bm, rings)
    ob = mesh_obj(name, bm, col)
    ob.location.z = bottom_z * MM
    set_material(ob, mat); add_bevel(ob, bevel, segments)
    return ob

def create_profile_segment(name, p0, p1, profiles, col, bevel, segments, mat):
    p0 = Vector(p0); p1 = Vector(p1); vec = p1 - p0; length = vec.length
    if length <= 0:
        raise ValueError(name + ": zero length")
    bm = bmesh.new(); rings = []
    for t, width, depth in profiles:
        z = (t - 0.5) * length * MM; w = width/2*MM; d = depth/2*MM
        rings.append([bm.verts.new((-w,-d,z)), bm.verts.new((w,-d,z)), bm.verts.new((w,d,z)), bm.verts.new((-w,d,z))])
    _bridge_rings(bm, rings)
    ob = mesh_obj(name, bm, col)
    ob.location = ((p0+p1)/2) * MM
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0,0,1)).rotation_difference(vec.normalized())
    set_material(ob, mat); add_bevel(ob, bevel, segments)
    return ob

def create_rounded_rect_prism(name, width, height, depth, radius, loc, col, mat, corner_segments=4):
    radius = min(radius, width/2, height/2); hw = width/2; hh = height/2
    corners = [(hw-radius,hh-radius,0,90),(-hw+radius,hh-radius,90,180),(-hw+radius,-hh+radius,180,270),(hw-radius,-hh+radius,270,360)]
    outline = []
    for cx, cz, a0, a1 in corners:
        for i in range(corner_segments+1):
            if outline and i == 0: continue
            a = math.radians(a0 + (a1-a0)*(i/corner_segments))
            outline.append((cx + radius*math.cos(a), cz + radius*math.sin(a)))
    bm = bmesh.new(); front = []; back = []; yf = -depth/2*MM; yb = depth/2*MM
    for x,z in outline:
        front.append(bm.verts.new((x*MM,yf,z*MM))); back.append(bm.verts.new((x*MM,yb,z*MM)))
    bm.faces.new(front[::-1]); bm.faces.new(back)
    for i in range(len(front)):
        j = (i+1)%len(front); bm.faces.new((front[i],front[j],back[j],back[i]))
    bm.normal_update(); ob = mesh_obj(name,bm,col)
    ob.location = Vector((loc[0]*MM,loc[1]*MM,loc[2]*MM)); set_material(ob,mat)
    return ob

def create_ellipse_prism(name, width, height, depth, loc, col, mat, segments=16):
    bm = bmesh.new(); front = []; back = []; yf = -depth/2*MM; yb = depth/2*MM
    for i in range(segments):
        a = 2*math.pi*i/segments; x = math.cos(a)*width/2*MM; z = math.sin(a)*height/2*MM
        front.append(bm.verts.new((x,yf,z))); back.append(bm.verts.new((x,yb,z)))
    bm.faces.new(front[::-1]); bm.faces.new(back)
    for i in range(segments):
        j=(i+1)%segments; bm.faces.new((front[i],front[j],back[j],back[i]))
    bm.normal_update(); ob=mesh_obj(name,bm,col)
    ob.location=Vector((loc[0]*MM,loc[1]*MM,loc[2]*MM)); set_material(ob,mat)
    return ob

def create_mouth(col, root, face_front_y):
    curve = bpy.data.curves.new("META_MouthCurve", "CURVE")
    curve.dimensions = "3D"; curve.resolution_u = 1; curve.bevel_depth = M["boca"]["grosor"]*MM; curve.bevel_resolution = 0
    spline = curve.splines.new("POLY"); spline.points.add(2)
    y = face_front_y - 0.55
    coords = [(-M["boca"]["ancho"]/2,y,Z["boca"]+0.30),(0,y-0.05,Z["boca"]-0.25),(M["boca"]["ancho"]/2,y,Z["boca"]+0.10)]
    for point, co in zip(spline.points, coords):
        point.co = (co[0]*MM,co[1]*MM,co[2]*MM,1)
    ob = bpy.data.objects.new("META_Mouth", curve); col.objects.link(ob); ob.data.materials.append(MAT_DARK); ob.parent = root
    return ob

def create_hand(side, wrist, col, root):
    sign = 1 if side == "R" else -1
    palm_end = Vector((wrist.x + sign*M["palma"]["largo"], wrist.y, wrist.z))
    palm = create_profile_segment(f"META_Palm_{side}", wrist, palm_end, [(0.00,6.2,3.5),(0.30,7.4,3.8),(0.65,8.6,3.95),(1.00,9.4,4.0)], col, STYLE["hand_bevel"], 2, MAT_SKIN)
    palm.parent = root
    fingers = [("Index",M["dedos"]["indice"],3.00),("Middle",M["dedos"]["medio"],1.00),("Ring",M["dedos"]["anular"],-1.00),("Pinky",M["dedos"]["menique"],-3.00)]
    for finger_name, finger, z_off in fingers:
        length = finger["largo"]; center_x = palm_end.x + sign*(length/2 - 0.55)
        ob = create_box(f"META_{finger_name}_{side}", (length,M["dedos"]["prof"],finger["ancho"]), (center_x,palm_end.y,palm_end.z+z_off), col, STYLE["finger_bevel"], 2, MAT_SKIN)
        ob.parent = root
    thumb_start = Vector((wrist.x + sign*2.0, wrist.y, wrist.z - 3.3))
    thumb_end = Vector((thumb_start.x + sign*4.1, thumb_start.y, thumb_start.z - 3.0))
    thumb = create_profile_segment(f"META_Thumb_{side}", thumb_start, thumb_end, [(0.00,2.25,2.10),(0.45,2.10,1.95),(1.00,1.75,1.75)], col, STYLE["finger_bevel"], 2, MAT_SKIN)
    thumb.parent = root

def hide_relationship_lines():
    try:
        for area in bpy.context.screen.areas:
            if area.type != "VIEW_3D": continue
            for space in area.spaces:
                if space.type == "VIEW_3D": space.overlay.show_relationship_lines = False
    except Exception:
        pass

def build_meta():
    limpiar(); col = get_collection()
    root = bpy.data.objects.new("META_ROOT", None); col.objects.link(root); root.empty_display_type = "PLAIN_AXES"; root.empty_display_size = 6*MM

    for side, sign in (("R",1),("L",-1)):
        x = sign*X["cadera"]; shoe_y = -4.2
        shoe = create_profile_body(f"META_Shoe_{side}", [(0.00,M["zapato"]["ancho"],M["zapato"]["largo"]),(0.22,11.7,17.8),(0.55,10.8,16.4),(1.00,9.8,14.0)], M["zapato"]["alto"], Z["zapato_ini"], col, STYLE["shoe_bevel"], 3, MAT_SHOE, loc_x=x, loc_y=shoe_y)
        shoe.rotation_euler.z = math.radians(-sign*STYLE["shoe_angle"]); shoe.parent = root
        sole = create_box(f"META_Sole_{side}", (M["zapato"]["ancho"]+0.8,M["zapato"]["largo"]+0.8,M["zapato"]["suela"]), (x,shoe_y,M["zapato"]["suela"]/2), col, 0.45, 2, MAT_DARK, rot=(0,0,-sign*STYLE["shoe_angle"]))
        sole.parent = root

    for side, sign in (("R",1),("L",-1)):
        leg = create_profile_body(f"META_Leg_{side}", [(0.00,7.9,7.1),(0.18,8.7,7.5),(0.38,9.7,8.1),(0.52,9.1,7.6),(0.78,10.6,8.5),(1.00,11.0,8.9)], M["pierna"]["largo"], Z["pierna_ini"], col, STYLE["leg_bevel"], 3, MAT_BODY, loc_x=sign*X["cadera"])
        leg.parent = root

    pelvis = create_profile_body("META_Pelvis", [(0.00,24.3,16.5),(0.40,25.0,17.0),(1.00,24.7,16.8)], M["pelvis"]["alto"], Z["pelvis_ini"], col, STYLE["pelvis_bevel"], 3, MAT_BODY); pelvis.parent = root
    torso = create_profile_body("META_Torso", [(0.00,25.2,16.8),(0.18,24.8,16.4),(0.42,25.0,16.4),(0.70,28.8,17.2),(1.00,30.5,17.8)], M["torso"]["alto"], Z["torso_ini"], col, STYLE["torso_bevel"], STYLE["torso_segments"], MAT_BODY); torso.parent = root

    neck = create_box("META_Neck", (M["cuello"]["ancho"],M["cuello"]["prof"],M["cuello"]["alto"]), (0,0,(Z["cuello_ini"]+Z["cuello_fin"])/2), col, 1.2, 3, MAT_SKIN); neck.parent = root

    head_profiles = [(0.00,36.2,-14.15,14.65),(0.12,37.8,-14.35,14.75),(0.30,39.0,-14.55,15.05),(0.58,40.0,-14.65,15.15),(1.00,39.3,-14.35,14.85)]
    head = create_asymmetric_profile_body("META_Head", head_profiles, M["cabeza"]["alto"], Z["cabeza_ini"], col, STYLE["head_bevel"], STYLE["head_segments"], MAT_SKIN); head.parent = root
    face_front_y = -14.65

    for side, sign in (("R",1),("L",-1)):
        ear = create_box(f"META_Ear_{side}", (M["oreja"]["ancho"],M["oreja"]["prof"],M["oreja"]["alto"]), (sign*X["oreja"],0.7,Z["orejas"]), col, STYLE["ear_bevel"], 3, MAT_SKIN); ear.parent = root

    total_arm = M["brazo"]["upper_largo"] + M["brazo"]["fore_largo"]
    for side, sign in (("R",1),("L",-1)):
        shoulder = Vector((sign*(X["hombro"]-1.0),0,Z["hombro"]))
        wrist = Vector((shoulder.x + sign*total_arm,0,shoulder.z))
        arm = create_profile_segment(f"META_Arm_{side}", shoulder, wrist, [(0.00,10.2,8.6),(0.10,9.9,8.4),(0.32,9.3,7.9),(0.52,8.0,7.0),(0.74,8.8,7.3),(1.00,7.0,6.2)], col, STYLE["arm_bevel"], 3, MAT_SKIN); arm.parent = root
        if ADD_HANDS: create_hand(side, wrist, col, root)

    if ADD_FACE:
        for side, sign in (("R",1),("L",-1)):
            eye_x = sign*M["ojo"]["centro_x"]
            eye = create_rounded_rect_prism(f"META_EyeWhite_{side}", M["ojo"]["ancho"], M["ojo"]["alto"], M["ojo"]["prof"], M["ojo"]["radio"], (eye_x,face_front_y-0.65,Z["ojos"]), col, MAT_WHITE, 4); eye.parent = root
            iris = create_ellipse_prism(f"META_Iris_{side}", M["iris"]["ancho"], M["iris"]["alto"], M["iris"]["prof"], (eye_x+sign*0.20,face_front_y-1.35,Z["ojos"]-0.30), col, MAT_EYE, 16); iris.parent = root
            brow = create_box(f"META_Brow_{side}", (M["ceja"]["ancho"],M["ceja"]["prof"],M["ceja"]["alto"]), (eye_x,face_front_y-0.85,Z["cejas"]), col, 0.45, 2, MAT_DARK, rot=(0,0,sign*2)); brow.parent = root
        nose = create_box("META_Nose", (M["nariz"]["ancho"],M["nariz"]["prof"],M["nariz"]["alto"]), (0,face_front_y-M["nariz"]["prof"]/2-0.25,Z["nariz"]), col, STYLE["nose_bevel"], 3, MAT_SKIN); nose.parent = root
        create_mouth(col, root, face_front_y)

    hide_relationship_lines(); bpy.ops.object.select_all(action="DESELECT"); root.select_set(True); bpy.context.view_layer.objects.active = root
    print("\n✅ ALTH_META v0.8.4b — SILHOUETTE REFINEMENT B")
    print("Head 40W × ~29.8D × 34.5H | Torso 30.5 chest | Palm 7.5L × 9.4W | Shoe 18L")

build_meta()
