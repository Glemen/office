"""
Blender 4.x / 5.x Procedural Generator — Chibi AI Agent Office (GLB + BLEND)
Thiết kế nhân vật Chibi & phòng làm việc gỗ ấm theo ảnh tham chiếu,
gắn Quốc huy / Biểu trưng (assets/emblem.png) trang trọng trên tường sau.

Chạy bằng Blender trên máy:
    blender-launcher --background --python build_studio_glb.py
Đầu ra:
    assets/studio.glb   (dùng trực tiếp cho Web 3D Three.js)
    assets/studio.blend (file gốc Blender để chỉnh sửa thêm)
"""
import bpy
import math
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)
EMBLEM_PATH = ASSETS_DIR / "emblem.png"
OUT_GLB = ASSETS_DIR / "studio.glb"
OUT_BLEND = ASSETS_DIR / "studio.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def rad(d):
    return math.radians(d)


# ============================================================
# VẬT LIỆU PBR
# ============================================================
def make_mat(name, rgba, rough=0.55, metal=0.0, emit_rgba=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit_rgba and emit_strength > 0:
        bsdf.inputs["Emission Color"].default_value = emit_rgba
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m


MAT = {
    "tile": make_mat("TileFloor", (0.90, 0.84, 0.75, 1.0), rough=0.22, metal=0.02),
    "grout": make_mat("TileGrout", (0.78, 0.72, 0.64, 1.0), rough=0.8),
    "rug": make_mat("CreamRug", (0.87, 0.83, 0.77, 1.0), rough=0.95),
    "wall": make_mat("WallCream", (0.93, 0.90, 0.85, 1.0), rough=0.88),
    "walnut": make_mat("WalnutWood", (0.28, 0.16, 0.09, 1.0), rough=0.38, metal=0.03),
    "walnut_dark": make_mat("WalnutDark", (0.20, 0.11, 0.06, 1.0), rough=0.45),
    "slat": make_mat("WoodSlat", (0.36, 0.21, 0.11, 1.0), rough=0.48),
    "gold_led": make_mat("GoldLED", (1.0, 0.86, 0.62, 1.0), rough=0.2, emit_rgba=(1.0, 0.78, 0.42, 1.0), emit_strength=3.5),
    "lamp_glow": make_mat("LampGlow", (1.0, 0.96, 0.88, 1.0), rough=0.1, emit_rgba=(1.0, 0.92, 0.78, 1.0), emit_strength=4.0),
    "black_matte": make_mat("BlackMatte", (0.06, 0.065, 0.075, 1.0), rough=0.45, metal=0.15),
    "pc_case": make_mat("PCCase", (0.08, 0.09, 0.11, 1.0), rough=0.38, metal=0.35),
    "pc_led": make_mat("PCBlueLED", (0.12, 0.65, 1.0, 1.0), rough=0.1, emit_rgba=(0.12, 0.65, 1.0, 1.0), emit_strength=5.0),
    "chrome": make_mat("Chrome", (0.88, 0.90, 0.93, 1.0), rough=0.14, metal=0.95),
    "mesh_chair": make_mat("ChairMesh", (0.09, 0.095, 0.11, 1.0), rough=0.72),
    "window_glass": make_mat("WindowGlass", (0.82, 0.91, 0.98, 1.0), rough=0.08, emit_rgba=(0.86, 0.94, 1.0, 1.0), emit_strength=1.2),
    "pot_white": make_mat("PotWhite", (0.93, 0.92, 0.90, 1.0), rough=0.32),
    "pebble": make_mat("Pebble", (0.85, 0.82, 0.78, 1.0), rough=0.7),
    "leaf": make_mat("LeafGreen", (0.14, 0.44, 0.12, 1.0), rough=0.42),
    "leaf_bright": make_mat("LeafBright", (0.20, 0.56, 0.15, 1.0), rough=0.38),
    "book_cover": make_mat("BookCover", (0.14, 0.17, 0.24, 1.0), rough=0.65),
    "paper": make_mat("PaperWhite", (0.96, 0.96, 0.95, 1.0), rough=0.8),
    "pen_blue": make_mat("PenBlue", (0.12, 0.35, 0.78, 1.0), rough=0.35),
    # Nhân vật Chibi
    "skin": make_mat("ChibiSkin", (0.97, 0.82, 0.72, 1.0), rough=0.45),
    "blush": make_mat("ChibiBlush", (0.96, 0.68, 0.66, 1.0), rough=0.6),
    "hair_brown": make_mat("HairBrown", (0.16, 0.10, 0.07, 1.0), rough=0.36),
    "hair_dark": make_mat("HairDark", (0.10, 0.07, 0.05, 1.0), rough=0.34),
    "eye_dark": make_mat("EyeDark", (0.05, 0.03, 0.02, 1.0), rough=0.05, metal=0.1),
    "eye_white": make_mat("EyeWhite", (1.0, 1.0, 1.0, 1.0), rough=0.05, emit_rgba=(1, 1, 1, 1), emit_strength=0.4),
    "shirt_white": make_mat("ShirtWhite", (0.95, 0.96, 0.98, 1.0), rough=0.65),
    "lanyard_blue": make_mat("LanyardBlue", (0.09, 0.32, 0.76, 1.0), rough=0.45),
    "pants_dark": make_mat("PantsDark", (0.08, 0.09, 0.12, 1.0), rough=0.78),
    "shoe": make_mat("ShoeBlack", (0.05, 0.05, 0.06, 1.0), rough=0.32),
    "gold_frame": make_mat("GoldFrame", (0.85, 0.68, 0.25, 1.0), rough=0.25, metal=0.85),
    "badge_idle": make_mat("BadgeIdle", (0.55, 0.60, 0.68, 1.0), rough=0.3),
}


def make_emblem_mat():
    m = bpy.data.materials.new("EmblemMat")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Metallic"].default_value = 0.12
    if EMBLEM_PATH.exists():
        img = bpy.data.images.load(str(EMBLEM_PATH))
        img.pack()
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    return m


MAT["emblem"] = make_emblem_mat()


# ============================================================
# HÀM DỰNG HÌNH SẠCH (CÓ SMOOTH & PARENTING)
# ============================================================
def set_parent(obj, parent):
    if parent:
        obj.parent = parent


def add_empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    e.rotation_euler = rot
    scene.collection.objects.link(e)
    set_parent(e, parent)
    return e


def add_box(name, loc, size, mat, rot=(0, 0, 0), bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = o.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(mat)
    set_parent(o, parent)
    return o


def add_cyl(name, loc, r, h, mat, rot=(0, 0, 0), verts=20, smooth=True, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    if smooth:
        bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    set_parent(o, parent)
    return o


def add_sphere(name, loc, radii, mat, rot=(0, 0, 0), segs=24, rings=16, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, rotation=rot, segments=segs, ring_count=rings)
    o = bpy.context.active_object
    o.name = name
    o.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    set_parent(o, parent)
    return o


def add_plane(name, loc, size, mat, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    set_parent(o, parent)
    return o


# ============================================================
# 1. KIẾN TRÚC PHÒNG (SÀN GẠCH KEM, THẢM, LAM GỖ LED VÀNG, CỬA SỔ, LOGO HIỆU)
# ============================================================
def build_room():
    room = add_empty("Room")
    # Sàn gạch men kem sáng + đường ron nhẹ
    add_box("Floor", (0, 0, -0.08), (11.0, 9.0, 0.16), MAT["tile"], parent=room)
    for gx in (-4, -3, -2, -1, 0, 1, 2, 3, 4):
        add_box(f"GroutX_{gx}", (gx, 0, 0.002), (0.012, 8.8, 0.004), MAT["grout"], parent=room)
    for gy in (-3, -2, -1, 0, 1, 2, 3):
        add_box(f"GroutY_{gy}", (0, gy, 0.002), (10.8, 0.012, 0.004), MAT["grout"], parent=room)

    # Thảm kem dệt dưới bàn họp
    add_box("Rug", (0, 0, 0.012), (5.3, 4.1, 0.02), MAT["rug"], bevel=0.008, parent=room)

    # Tường sau (+Y = 4.2) và tường trái (-X = -5.2)
    add_box("WallBack", (0, 4.25, 2.0), (11.0, 0.18, 4.0), MAT["wall"], parent=room)
    add_box("WallLeft", (-5.25, 0, 2.0), (0.18, 9.0, 4.0), MAT["wall"], parent=room)

    # Ốp gỗ chân tường ngang (wainscoting) cao 1.05m giống ảnh tham chiếu
    add_box("WainscotBack", (0, 4.13, 0.52), (10.6, 0.06, 1.04), MAT["walnut"], parent=room)
    add_box("WainscotCapBack", (0, 4.11, 1.05), (10.6, 0.10, 0.04), MAT["walnut_dark"], parent=room)
    add_box("WainscotLeft", (-5.13, 0, 0.52), (0.06, 8.6, 1.04), MAT["walnut"], parent=room)
    add_box("WainscotCapLeft", (-5.11, 0, 1.05), (0.10, 8.6, 0.04), MAT["walnut_dark"], parent=room)

    # Mảng lam gỗ dọc phía sau-trái + dải đèn LED vàng hắt viền giống ảnh
    add_box("SlatBackPanel", (-2.6, 4.12, 2.45), (3.4, 0.05, 2.8), MAT["walnut_dark"], parent=room)
    for k in range(21):
        sx = -4.2 + k * 0.16
        add_box(f"Slat_{k}", (sx, 4.08, 2.45), (0.08, 0.06, 2.75), MAT["slat"], parent=room)
    # Viền LED vàng ấm bên phải mảng lam gỗ
    add_box("SlatLED_V", (-0.88, 4.13, 2.45), (0.04, 0.04, 2.78), MAT["gold_led"], parent=room)

    # Cửa sổ khung đen lớn phía sau-phải
    win = add_empty("WindowBackRight", (3.1, 4.12, 2.45), parent=room)
    add_box("WinGlass", (0, 0.02, 0), (3.6, 0.04, 2.55), MAT["window_glass"], parent=win)
    add_box("WinTop", (0, -0.02, 1.28), (3.72, 0.10, 0.08), MAT["black_matte"], parent=win)
    add_box("WinBot", (0, -0.02, -1.28), (3.72, 0.10, 0.08), MAT["black_matte"], parent=win)
    for mx in (-1.82, -0.45, 0.90, 1.82):
        add_box(f"WinBar_{mx}", (mx, -0.02, 0), (0.07, 0.10, 2.58), MAT["black_matte"], parent=win)

    # ============================================================
    # BIỂU TRƯNG / LOGO HIỆU TRANG TRỌNG TRÊN TƯỜNG SAU (GIỮA PHÒNG)
    # ============================================================
    emblem_grp = add_empty("WallEmblem", (0.25, 4.10, 2.42), parent=room)
    add_cyl("EmblemPlaque", (0, 0.02, 0), 0.74, 0.04, MAT["walnut_dark"], rot=(rad(90), 0, 0), verts=48, parent=emblem_grp)
    add_cyl("EmblemRim", (0, 0.015, 0), 0.77, 0.025, MAT["gold_frame"], rot=(rad(90), 0, 0), verts=48, parent=emblem_grp)
    add_plane("EmblemLogo", (0, -0.02, 0), (1.20, 0.96), MAT["emblem"], rot=(rad(90), 0, 0), parent=emblem_grp)
    # Đèn rọi tranh mạ vàng phía trên biểu trưng
    add_box("EmblemLightBar", (0, -0.10, 0.90), (0.68, 0.06, 0.035), MAT["gold_frame"], bevel=0.005, parent=emblem_grp)
    add_box("EmblemLightGlow", (0, -0.10, 0.88), (0.62, 0.03, 0.012), MAT["gold_led"], parent=emblem_grp)

    # Tủ hồ sơ lưu trữ gỗ óc chó sát tường trái + Đồng hồ treo tường chạy giờ thực
    cab = add_empty("ArchiveCabinet", (-4.82, -0.35, 0), parent=room)
    add_box("CabBody", (0, 0, 1.08), (0.48, 2.50, 2.16), MAT["walnut"], bevel=0.01, parent=cab)
    binder_mats = [
        make_mat("BinderRed", (0.58, 0.12, 0.12, 1.0), rough=0.6),
        make_mat("BinderBlue", (0.10, 0.25, 0.52, 1.0), rough=0.6),
        make_mat("BinderGreen", (0.12, 0.38, 0.22, 1.0), rough=0.6),
        MAT["gold_frame"],
    ]
    for sh_idx, sz in enumerate((0.68, 1.25, 1.80)):
        add_box(f"CabShelf_{sh_idx}", (0.03, 0, sz - 0.20), (0.42, 2.38, 0.035), MAT["walnut_dark"], parent=cab)
        for b in range(11):
            if b in (4, 8):
                continue
            by = -1.02 + b * 0.20
            add_box(
                f"Binder_{sh_idx}_{b}",
                (0.08, by, sz),
                (0.26, 0.075, 0.32),
                binder_mats[(b + sh_idx) % len(binder_mats)],
                parent=cab,
            )

    # Đồng hồ treo tường viền vàng đồng trên tường trái (có kim quay giờ thực trong Three.js!)
    clk = add_empty("WallClock", (-5.12, -2.55, 2.55), rot=(0, 0, rad(-90)), parent=room)
    add_cyl("ClockRim", (0, 0.01, 0), 0.34, 0.05, MAT["gold_frame"], rot=(rad(90), 0, 0), verts=36, parent=clk)
    add_cyl("ClockFace", (0, -0.02, 0), 0.30, 0.02, MAT["paper"], rot=(rad(90), 0, 0), verts=36, parent=clk)
    h_piv = add_empty("ClockHour", (0, -0.035, 0), parent=clk)
    add_box("ClockHourMesh", (0, 0, 0.075), (0.022, 0.008, 0.16), MAT["black_matte"], parent=h_piv)
    m_piv = add_empty("ClockMinute", (0, -0.042, 0), parent=clk)
    add_box("ClockMinMesh", (0, 0, 0.105), (0.015, 0.008, 0.22), MAT["black_matte"], parent=m_piv)
    s_piv = add_empty("ClockSecond", (0, -0.048, 0), parent=clk)
    add_box("ClockSecMesh", (0, 0, 0.115), (0.008, 0.006, 0.24), binder_mats[0], parent=s_piv)

    # Cây xanh trong chậu sứ trắng có sỏi trắng ở góc sau-trái
    build_plant("CornerPlant", (-4.35, 3.35, 0), 1.0, room)


def build_plant(name, loc, scale, parent):
    g = add_empty(name, loc, parent=parent)
    add_cyl(f"{name}_pot", (0, 0, 0.25 * scale), 0.24 * scale, 0.50 * scale, MAT["pot_white"], verts=24, parent=g)
    add_cyl(f"{name}_soil", (0, 0, 0.48 * scale), 0.21 * scale, 0.03 * scale, MAT["pebble"], verts=20, parent=g)
    for k in range(11):
        ang = k * (2 * math.pi / 11) + (k % 2) * 0.2
        r_off = (0.14 + (k % 3) * 0.08) * scale
        h_off = (0.72 + (k % 4) * 0.16) * scale
        add_sphere(
            f"{name}_leaf{k}",
            (math.cos(ang) * r_off, math.sin(ang) * r_off, h_off),
            (0.16 * scale, 0.09 * scale, 0.28 * scale),
            MAT["leaf_bright"] if k % 2 == 0 else MAT["leaf"],
            rot=(math.sin(ang) * 0.55, -math.cos(ang) * 0.55, ang),
            segs=14,
            rings=10,
            parent=g,
        )


# ============================================================
# 2. BÀN HỌP GỖ ÓC CHÓ + ĐÈN THẢ TRẦN + PHỤ KIỆN GIỮA BÀN
# ============================================================
def build_table():
    tbl = add_empty("MainTable")
    # Mặt bàn gỗ óc chó bo nhẹ cạnh
    add_box("TableTop", (0, 0, 0.74), (3.85, 1.85, 0.07), MAT["walnut"], bevel=0.015, parent=tbl)
    # 4 chân bàn đen hơi nghiêng hiện đại
    for lx, ly in ((-1.72, -0.78), (1.72, -0.78), (-1.72, 0.78), (1.72, 0.78)):
        add_box(f"TableLeg_{lx}_{ly}", (lx, ly, 0.36), (0.075, 0.075, 0.72), MAT["black_matte"], parent=tbl)

    # Đèn thả trần thanh ngang đen hiện đại phát sáng ấm
    lamp = add_empty("PendantLamp", (0, 0, 2.58), parent=tbl)
    add_box("LampBody", (0, 0, 0), (2.45, 0.12, 0.075), MAT["black_matte"], bevel=0.006, parent=lamp)
    add_box("LampStrip", (0, 0, -0.04), (2.36, 0.07, 0.015), MAT["lamp_glow"], parent=lamp)
    for cx in (-0.88, 0.88):
        add_cyl(f"LampWire_{cx}", (cx, 0, 0.78), 0.008, 1.5, MAT["black_matte"], verts=8, parent=lamp)

    # Phụ kiện giữa bàn: chậu cây mini trắng, hộp bút đen + bút xanh, 2 cuốn sổ xếp chồng
    build_plant("MiniPlant", (0.0, 0.06, 0.775), 0.34, tbl)
    add_cyl("PenCup", (-0.34, -0.06, 0.835), 0.045, 0.11, MAT["black_matte"], verts=16, parent=tbl)
    for p in range(4):
        add_cyl(
            f"Pen_{p}",
            (-0.34 + (p - 1.5) * 0.015, -0.06 + (p % 2 - 0.5) * 0.015, 0.88),
            0.006,
            0.14,
            MAT["pen_blue"],
            rot=(rad(8 * (p - 1)), rad(6), 0),
            verts=8,
            parent=tbl,
        )
    # 2 cuốn sổ bìa tối + ruột giấy trắng
    add_box("Book1", (0.34, -0.10, 0.795), (0.28, 0.20, 0.032), MAT["book_cover"], bevel=0.004, parent=tbl)
    add_box("Book1Pages", (0.34, -0.10, 0.795), (0.27, 0.19, 0.024), MAT["paper"], parent=tbl)
    add_box("Book2", (0.34, -0.10, 0.828), (0.27, 0.195, 0.028), MAT["book_cover"], bevel=0.004, parent=tbl)


# ============================================================
# 3. BỘ MÁY TÍNH ĐỂ BÀN (MÀN HÌNH + THÙNG PC ĐÈN XANH + BÀN PHÍM + CHUỘT)
# ============================================================
def build_desktop_pc(idx, x, y, facing_neg_y):
    # facing_neg_y=True: ngồi phía sau (+Y) nhìn về -Y; False: ngồi phía trước (-Y) nhìn về +Y
    rot_z = 0.0 if facing_neg_y else math.pi
    g = add_empty(f"DesktopPC_{idx}", (x, y, 0.775), rot=(0, 0, rot_z))

    # Màn hình + chân đế
    add_box(f"MonBase_{idx}", (0, 0.02, 0.01), (0.22, 0.15, 0.016), MAT["black_matte"], bevel=0.003, parent=g)
    add_box(f"MonNeck_{idx}", (0, 0.04, 0.11), (0.055, 0.03, 0.20), MAT["black_matte"], parent=g)
    add_box(f"MonFrame_{idx}", (0, 0.02, 0.26), (0.56, 0.032, 0.34), MAT["black_matte"], bevel=0.006, parent=g)

    # Mặt màn hình có tên chuẩn `MonitorScreen{idx}` để Three.js gắn CanvasTexture trực tiếp!
    # Mặt màn hình hướng về phía người ngồi (+Y trong local space)
    scr_mat = make_mat(f"ScreenMat_{idx}", (0.10, 0.35, 0.82, 1.0), rough=0.15, emit_rgba=(0.12, 0.42, 0.90, 1.0), emit_strength=0.9)
    add_plane(f"MonitorScreen{idx}", (0, 0.040, 0.26), (0.52, 0.30), scr_mat, rot=(rad(-90), 0, math.pi), parent=g)

    # Thùng PC Mini Tower đặt cạnh màn hình với dải LED xanh dọc giống hệt ảnh
    add_box(f"PCCase_{idx}", (0.42, -0.02, 0.16), (0.16, 0.28, 0.32), MAT["pc_case"], bevel=0.008, parent=g)
    add_box(f"PCLED_{idx}", (0.42, 0.122, 0.16), (0.014, 0.006, 0.26), MAT["pc_led"], parent=g)

    # Bàn phím + chuột gần người ngồi (+Y)
    add_box(f"Keyboard_{idx}", (0, 0.24, 0.012), (0.36, 0.13, 0.018), MAT["black_matte"], bevel=0.003, parent=g)
    add_sphere(f"Mouse_{idx}", (-0.25, 0.24, 0.016), (0.032, 0.050, 0.018), MAT["black_matte"], segs=14, rings=10, parent=g)


# ============================================================
# 4. GHẾ CÔNG THÁI HỌC LƯỚI ĐEN CHÂN CHROME 5 CÁNH
# ============================================================
def build_chair(idx, x, y, rot_z):
    g = add_empty(f"Chair_{idx}", (x, y, 0), rot=(0, 0, rot_z))
    for k in range(5):
        a = k * (2 * math.pi / 5)
        add_box(f"CLeg_{idx}_{k}", (math.cos(a) * 0.17, math.sin(a) * 0.17, 0.075), (0.34, 0.035, 0.028), MAT["chrome"], rot=(0, 0, a), parent=g)
        add_cyl(f"CWheel_{idx}_{k}", (math.cos(a) * 0.32, math.sin(a) * 0.32, 0.032), 0.032, 0.026, MAT["black_matte"], rot=(rad(90), 0, a), verts=12, parent=g)
    add_cyl(f"CPole_{idx}", (0, 0, 0.25), 0.032, 0.36, MAT["black_matte"], verts=14, parent=g)
    add_box(f"CSeat_{idx}", (0, 0.02, 0.45), (0.50, 0.48, 0.075), MAT["mesh_chair"], bevel=0.02, parent=g)
    # Khung lưng + lưới đen
    add_box(f"CBack_{idx}", (0, -0.22, 0.78), (0.48, 0.055, 0.54), MAT["mesh_chair"], bevel=0.02, parent=g)
    add_box(f"CBackTrimL_{idx}", (-0.23, -0.22, 0.78), (0.03, 0.065, 0.52), MAT["chrome"], parent=g)
    add_box(f"CBackTrimR_{idx}", (0.23, -0.22, 0.78), (0.03, 0.065, 0.52), MAT["chrome"], parent=g)
    # Tay vịn
    for ax in (-0.26, 0.26):
        add_box(f"CArmP_{idx}_{ax}", (ax, -0.02, 0.57), (0.04, 0.04, 0.18), MAT["black_matte"], parent=g)
        add_box(f"CArmT_{idx}_{ax}", (ax, 0.02, 0.66), (0.055, 0.30, 0.035), MAT["black_matte"], bevel=0.01, parent=g)


# ============================================================
# 5. NHÂN VẬT CHIBI DỄ THƯƠNG (ĐẦU TO, MẮT LONG LANH, TÓC BỒNG / BÚI, ÁO SƠ MI + DÂY ĐEO THẺ)
# ============================================================
def build_chibi_worker(idx, name, x, y, rot_z, is_female=False):
    root = add_empty(f"Worker{idx}", (x, y, 0), rot=(0, 0, rot_z))

    # Vòng highlight dưới ghế (điều khiển opacity trong Three.js)
    ring_mat = make_mat(f"RingMat_{idx}", (0.60, 0.36, 0.15, 1.0), rough=0.3, emit_rgba=(0.85, 0.52, 0.18, 1.0), emit_strength=1.5)
    add_cyl(f"Worker{idx}_Ring", (0, 0, 0.025), 0.55, 0.008, ring_mat, verts=32, parent=root)

    # Chân & giày ngồi trên ghế (hướng về +Y)
    for sx in (-0.09, 0.09):
        add_cyl(f"W{idx}_Thigh_{sx}", (sx, 0.14, 0.52), 0.075, 0.30, MAT["pants_dark"], rot=(rad(90), 0, 0), verts=14, parent=root)
        add_cyl(f"W{idx}_Shin_{sx}", (sx, 0.27, 0.32), 0.065, 0.34, MAT["pants_dark"], verts=14, parent=root)
        add_sphere(f"W{idx}_Shoe_{sx}", (sx, 0.31, 0.15), (0.065, 0.10, 0.05), MAT["shoe"], segs=14, rings=10, parent=root)

    # Khớp thân trên (pivot tại eo z=0.56 để cúi người gõ phím mượt!)
    upper = add_empty(f"Worker{idx}_Upper", (0, 0, 0.56), parent=root)

    # Áo sơ mi trắng + cổ áo + dây đeo thẻ xanh + thẻ nhân viên
    add_cyl(f"W{idx}_Torso", (0, 0, 0.19), 0.15, 0.38, MAT["shirt_white"], verts=20, parent=upper)
    add_sphere(f"W{idx}_Shoulder", (0, 0, 0.36), (0.19, 0.13, 0.08), MAT["shirt_white"], segs=18, rings=12, parent=upper)
    add_cyl(f"W{idx}_Collar", (0, 0, 0.40), 0.10, 0.05, MAT["shirt_white"], verts=18, parent=upper)
    add_cyl(f"W{idx}_Lanyard", (0, 0.01, 0.39), 0.108, 0.022, MAT["lanyard_blue"], verts=20, parent=upper)
    # Thẻ tên trước ngực (+Y)
    add_box(f"W{idx}_IDCard", (0.05, 0.152, 0.24), (0.055, 0.012, 0.075), MAT["paper"], bevel=0.002, parent=upper)
    add_box(f"W{idx}_IDStripe", (0.05, 0.156, 0.268), (0.052, 0.008, 0.014), MAT["lanyard_blue"], parent=upper)

    # Hai cánh tay có khớp vai riêng (`Worker{idx}_ArmL`, `Worker{idx}_ArmR`)
    for side, ax in (("L", -0.19), ("R", 0.19)):
        arm = add_empty(f"Worker{idx}_Arm{side}", (ax, 0.02, 0.34), parent=upper)
        add_cyl(f"W{idx}_Sleeve{side}", (0, 0.15, -0.06), 0.056, 0.30, MAT["shirt_white"], rot=(rad(72), 0, 0), verts=14, parent=arm)
        add_sphere(f"W{idx}_Hand{side}", (0, 0.31, -0.10), (0.052, 0.058, 0.042), MAT["skin"], segs=14, rings=10, parent=arm)

    # Khớp đầu Chibi (pivot tại cổ z=0.42)
    head_joint = add_empty(f"Worker{idx}_Head", (0, 0, 0.42), parent=upper)
    # Đầu Chibi to tròn dễ thương
    add_sphere(f"W{idx}_HeadMesh", (0, 0, 0.24), (0.245, 0.235, 0.235), MAT["skin"], segs=28, rings=20, parent=head_joint)
    # Tai hai bên
    add_sphere(f"W{idx}_EarL", (-0.235, 0.0, 0.22), (0.042, 0.036, 0.055), MAT["skin"], segs=12, rings=8, parent=head_joint)
    add_sphere(f"W{idx}_EarR", (0.235, 0.0, 0.22), (0.042, 0.036, 0.055), MAT["skin"], segs=12, rings=8, parent=head_joint)

    # Đôi mắt to long lanh (nhóm vào Worker{idx}_Eyes để nháy mắt tự nhiên!) + má hồng + lông mày
    eyes_joint = add_empty(f"Worker{idx}_Eyes", (0, 0.205, 0.22), parent=head_joint)
    for ex in (-0.085, 0.085):
        add_sphere(f"W{idx}_Eye_{ex}", (ex, 0.0, 0.0), (0.042, 0.025, 0.048), MAT["eye_dark"], segs=16, rings=12, parent=eyes_joint)
        add_sphere(f"W{idx}_Shine_{ex}", (ex + 0.014, 0.021, 0.018), (0.013, 0.009, 0.015), MAT["eye_white"], segs=10, rings=8, parent=eyes_joint)
        add_sphere(f"W{idx}_Blush_{ex}", (ex * 1.45, 0.195, 0.165), (0.035, 0.015, 0.020), MAT["blush"], segs=12, rings=8, parent=head_joint)
        add_box(f"W{idx}_Brow_{ex}", (ex, 0.212, 0.295), (0.065, 0.014, 0.014), MAT["hair_dark"], rot=(0, rad(-6 if ex < 0 else 6), 0), bevel=0.004, parent=head_joint)

    # Tóc Chibi bồng bềnh (nữ búi cao, nam mái rẽ bồng)
    hmat = MAT["hair_dark"] if (idx % 2 == 1) else MAT["hair_brown"]
    add_sphere(f"W{idx}_HairCap", (0, -0.02, 0.28), (0.265, 0.255, 0.225), hmat, segs=24, rings=18, parent=head_joint)
    # Tóc mái bồng phía trước
    for mx, mz, rx in ((-0.11, 0.35, 0.08), (0.0, 0.37, 0.09), (0.11, 0.35, 0.08)):
        add_sphere(f"W{idx}_Bang_{mx}", (mx, 0.17, mz), (rx, 0.09, 0.085), hmat, segs=16, rings=12, parent=head_joint)
    if is_female:
        # Búi tóc cao đáng yêu giống nhân vật nữ trong ảnh!
        add_sphere(f"W{idx}_Bun", (0, -0.04, 0.53), (0.12, 0.12, 0.105), hmat, segs=20, rings=14, parent=head_joint)
        add_cyl(f"W{idx}_BunBand", (0, -0.04, 0.455), 0.095, 0.025, MAT["lanyard_blue"], verts=18, parent=head_joint)
    else:
        # Chỏm tóc bồng phía trên cho nhân vật nam
        add_sphere(f"W{idx}_TopTuft", (-0.04, 0.02, 0.47), (0.14, 0.13, 0.075), hmat, segs=16, rings=12, parent=head_joint)

    # Chấm trạng thái nổi trên đầu (`Worker{idx}_Badge`)
    bmat = make_mat(f"BadgeMat_{idx}", (0.60, 0.65, 0.72, 1.0), rough=0.25, emit_rgba=(0.60, 0.65, 0.72, 1.0), emit_strength=0.8)
    add_sphere(f"Worker{idx}_Badge", (0, 0, 1.72), (0.055, 0.055, 0.055), bmat, segs=16, rings=12, parent=root)


# ============================================================
# CHẠY DỰNG CẢNH & XUẤT STUDIO.GLB + STUDIO.BLEND
# ============================================================
build_room()
build_table()

# 4 vị trí đối diện nhau quanh bàn giống ảnh tham chiếu:
# Sau-trái (Minh), Sau-phải (Lan - nữ búi tóc), Trước-trái (Tuấn), Trước-phải (Vy - nữ búi tóc)
SEATS = [
    (0, "Minh", -1.05,  1.28, math.pi, False, (-1.05,  0.42, True)),
    (1, "Lan",   1.05,  1.28, math.pi, True,  ( 1.05,  0.42, True)),
    (2, "Tuấn", -1.05, -1.28, 0.0,     False, (-1.05, -0.42, False)),
    (3, "Vy",    1.05, -1.28, 0.0,     True,  ( 1.05, -0.42, False)),
]

for idx, name, cx, cy, rot_z, is_fem, (px, py, f_neg) in SEATS:
    build_chair(idx, cx, cy, rot_z)
    build_chibi_worker(idx, name, cx, cy, rot_z, is_female=is_fem)
    build_desktop_pc(idx, px, py, f_neg)

# Lưu file Blender gốc + xuất GLB (Y-up tự động cho Three.js, nhúng sẵn ảnh emblem.png!)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(
    filepath=str(OUT_GLB),
    export_format='GLB',
    export_yup=True,
    export_apply=False,
    export_materials='EXPORT',
    export_image_format='AUTO',
)
print("BUILT_OK:", OUT_GLB, OUT_BLEND)
