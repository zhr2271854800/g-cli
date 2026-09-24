# -*- coding: utf-8 -*-
"""
g-cli/scripts/render_layered_oxides_blender.py
使用 Blender 5.2.2 + Tesla V100 GPU (Cycles CUDA) 自动光线追踪渲染
顶刊级 (Nature/Science 风格) 钠离子电池层状氧化物 3D 微观晶体结构与机理插图
"""

import bpy
import bmesh
import math
import os
import sys

# 1. 基础输出路径配置
OUT_DIR = r"C:\Users\Administrator\g-cli\assets\images"
PICTURES_DIR = r"C:\Users\Administrator\Pictures"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)

def setup_cycles_v100(scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 128
    scene.cycles.preview_samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for d in prefs.devices:
        if 'V100' in d.name and d.type == 'CUDA':
            d.use = True
            print(f"[CYCLES] 启用 GPU: {d.name} ({d.type})")
        else:
            d.use = False

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for m in bpy.data.materials:
        bpy.data.materials.remove(m)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

def create_material(name, base_color, metallic=0.0, roughness=0.2, transmission=0.0, emission=None, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    node_bsdf.inputs['Base Color'].default_value = base_color
    node_bsdf.inputs['Metallic'].default_value = metallic
    node_bsdf.inputs['Roughness'].default_value = roughness
    if 'Transmission Weight' in node_bsdf.inputs:
        node_bsdf.inputs['Transmission Weight'].default_value = transmission
    elif 'Transmission' in node_bsdf.inputs:
        node_bsdf.inputs['Transmission'].default_value = transmission
        
    if emission:
        if 'Emission Color' in node_bsdf.inputs:
            node_bsdf.inputs['Emission Color'].default_value = emission[0]
            node_bsdf.inputs['Emission Strength'].default_value = emission[1]
    
    if alpha < 1.0:
        node_bsdf.inputs['Alpha'].default_value = alpha
        
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    return mat

def create_octahedron_mesh(name, center, r_xy=1.1, r_z=1.1):
    cx, cy, cz = center
    verts = [
        (cx + r_xy, cy, cz),
        (cx - r_xy, cy, cz),
        (cx, cy + r_xy, cz),
        (cx, cy - r_xy, cz),
        (cx, cy, cz + r_z),
        (cx, cy, cz - r_z)
    ]
    faces = [
        (4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0),
        (5, 0, 2), (5, 2, 1), (5, 1, 3), (5, 3, 0)
    ]
    mesh = bpy.data.meshes.new(name=name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def setup_studio_lighting(floor_z=-4.5):
    # 纯白/浅灰环境反射
    world = bpy.data.worlds.new("StudioWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.98, 0.98, 0.99, 1.0)
        bg.inputs['Strength'].default_value = 1.2
    bpy.context.scene.world = world

    # 影棚地台 (白色哑光反光地板，产生柔和倒影与接触阴影)
    bpy.ops.mesh.primitive_plane_add(size=80.0, location=(0, 0, floor_z))
    floor = bpy.context.active_object
    mat_floor = create_material("StudioFloor", (0.95, 0.96, 0.98, 1.0), roughness=0.35, metallic=0.05)
    floor.data.materials.append(mat_floor)

    # 主光源 Key Light (高能柔光箱)
    key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
    key_data.energy = 1600.0
    key_data.size = 18.0
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (12, -14, 18)
    key_obj.rotation_euler = (math.radians(48), math.radians(12), math.radians(38))

    # 轮廓补光 Rim Light (冷光轮廓)
    rim_data = bpy.data.lights.new(name="RimLight", type='AREA')
    rim_data.energy = 1100.0
    rim_data.size = 14.0
    rim_data.color = (0.88, 0.94, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = (-14, 12, 16)
    rim_obj.rotation_euler = (math.radians(-42), math.radians(-18), math.radians(-135))

    # 正面微补光 Front Soft Fill
    fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
    fill_data.energy = 600.0
    fill_data.size = 20.0
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (0, -18, 8)
    fill_obj.rotation_euler = (math.radians(65), 0, 0)

# =========================================================================
# 场景 1: O3-NaFeO2/NFM 真实三维层状晶格 (Nature 风格半透明多面体层与发光离子)
# =========================================================================
def render_o3_lattice():
    clear_scene()
    scene = bpy.context.scene
    setup_cycles_v100(scene)
    setup_studio_lighting()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

    # 材质定义
    mat_poly_tm = create_material("PolyTM", (0.05, 0.65, 0.55, 0.45), roughness=0.15, transmission=0.72)
    mat_fe = create_material("AtomFe", (0.18, 0.52, 0.72, 1.0), metallic=0.75, roughness=0.25)
    mat_mn = create_material("AtomMn", (0.65, 0.22, 0.78, 1.0), metallic=0.75, roughness=0.25)
    mat_o = create_material("AtomO", (0.92, 0.28, 0.25, 1.0), roughness=0.3)
    mat_na = create_material("AtomNa", (0.98, 0.72, 0.12, 1.0), metallic=0.6, roughness=0.2, emission=((1.0, 0.8, 0.2, 1.0), 0.8))
    mat_path = create_material("GlowPath", (0.1, 0.85, 1.0, 1.0), emission=((0.1, 0.9, 1.0, 1.0), 5.0))

    a = 2.4
    h_tm = 1.3
    layer_gap = 3.6
    
    # 构建 3 层晶格: Layer 0 (TM1), Layer 1 (Na), Layer 2 (TM2), Layer 3 (Na), Layer 4 (TM3)
    tm_layers_z = [-layer_gap, 0, layer_gap]
    na_layers_z = [-layer_gap/2, layer_gap/2]

    # 生成 TM 层 (八面体网络)
    for l_idx, lz in enumerate(tm_layers_z):
        offset_x = (l_idx % 2) * (a * 0.5)
        offset_y = (l_idx % 2) * (a * 0.288)
        for i in range(-2, 3):
            for j in range(-2, 3):
                x = (i * a + j * a * 0.5) + offset_x
                y = (j * a * math.sqrt(3)/2) + offset_y
                z = lz
                
                # 创建半透明配位八面体
                oct_obj = create_octahedron_mesh(f"Oct_{l_idx}_{i}_{j}", (x, y, z), r_xy=1.05, r_z=h_tm)
                oct_obj.data.materials.append(mat_poly_tm)

                # 中心过渡金属离子
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=(x, y, z))
                tm_atom = bpy.context.active_object
                tm_atom.data.materials.append(mat_fe if (i+j)%2 == 0 else mat_mn)

                # 6 个顶点氧原子
                ox_pts = [(x+1.05, y, z), (x-1.05, y, z), (x, y+1.05, z), (x, y-1.05, z), (x, y, z+h_tm), (x, y, z-h_tm)]
                for ox in ox_pts:
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=ox)
                    o_atom = bpy.context.active_object
                    o_atom.data.materials.append(mat_o)

    # 生成 Na 离子层
    for l_idx, lz in enumerate(na_layers_z):
        offset_x = (l_idx + 1) * (a * 0.4)
        for i in range(-2, 3):
            for j in range(-2, 3):
                # 随机留空位以体现脱钠态
                if (i + j + l_idx) % 5 == 0:
                    continue
                x = (i * a + j * a * 0.5) + offset_x
                y = (j * a * math.sqrt(3)/2)
                z = lz
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.48, location=(x, y, z))
                na_atom = bpy.context.active_object
                na_atom.data.materials.append(mat_na)

    # 添加钠离子层内跃迁高亮光辉路径 (Diffusion trajectory)
    curve_data = bpy.data.curves.new('NaPath', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.08
    polyline = curve_data.splines.new('BEZIER')
    polyline.bezier_points.add(2)
    
    # 路径三个关键点 (从八面体位 -> 跨越过渡态四面体瓶颈 -> 邻近八面体位)
    p0 = (-a*0.6, 0.0, na_layers_z[1])
    p1 = (0.0, 0.5, na_layers_z[1] + 0.35)
    p2 = (a*0.6, 0.0, na_layers_z[1])
    
    for idx, pt in enumerate([p0, p1, p2]):
        bp = polyline.bezier_points[idx]
        bp.co = pt
        bp.handle_left = (pt[0]-0.2, pt[1], pt[2])
        bp.handle_right = (pt[0]+0.2, pt[1], pt[2])
        
    curve_obj = bpy.data.objects.new('NaPathObj', curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.data.materials.append(mat_path)

    # 跃迁中的激发态 Na 离子
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.52, location=p1)
    jump_na = bpy.context.active_object
    mat_jump = create_material("JumpNa", (1.0, 0.9, 0.2, 1.0), metallic=0.3, emission=((1.0, 0.85, 0.3, 1.0), 4.0))
    jump_na.data.materials.append(mat_jump)

    # 摄像机机位
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_obj = bpy.data.objects.new("MainCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (11.5, -13.5, 9.5)
    cam_obj.rotation_euler = (math.radians(62), 0, math.radians(40))
    scene.camera = cam_obj

    # 渲染保存
    out_file = os.path.join(OUT_DIR, "blender_o3_lattice_nature.png")
    scene.render.filepath = out_file
    print(f"[*] 正在渲染 O3 层状正极真实晶格光追图: {out_file}...")
    bpy.ops.render.render(write_still=True)
    
    # 备份至 Pictures
    try:
        import shutil
        shutil.copy2(out_file, os.path.join(PICTURES_DIR, "blender_o3_lattice_nature.png"))
    except Exception:
        pass
    print("[+] O3 真实晶格渲染完毕！")

# =========================================================================
# 场景 2: 姜-泰勒 (Jahn-Teller) 畸变八面体空间应变特写
# =========================================================================
def render_jahn_teller():
    clear_scene()
    scene = bpy.context.scene
    setup_cycles_v100(scene)
    setup_studio_lighting()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

    mat_regular = create_material("PolyRegular", (0.15, 0.45, 0.75, 0.4), roughness=0.1, transmission=0.8)
    mat_distorted = create_material("PolyDistorted", (0.85, 0.35, 0.1, 0.45), roughness=0.1, transmission=0.75)
    mat_tm_mn3 = create_material("TM_Mn3", (0.8, 0.2, 0.2, 1.0), metallic=0.8, roughness=0.2)
    mat_tm_mn4 = create_material("TM_Mn4", (0.2, 0.4, 0.8, 1.0), metallic=0.8, roughness=0.2)
    mat_o = create_material("AtomO", (0.95, 0.25, 0.2, 1.0), roughness=0.3)
    mat_strain_z = create_material("StrainZ", (1.0, 0.1, 0.1, 1.0), emission=((1.0, 0.2, 0.1, 1.0), 3.0))

    # 左侧: 规则正八面体 (Mn4+, d3 无畸变)
    c1 = (-3.2, 0, 0)
    oct1 = create_octahedron_mesh("OctRegular", c1, r_xy=1.8, r_z=1.8)
    oct1.data.materials.append(mat_regular)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=c1)
    bpy.context.active_object.data.materials.append(mat_tm_mn4)
    for p in [(c1[0]+1.8, 0, 0), (c1[0]-1.8, 0, 0), (c1[0], 1.8, 0), (c1[0], -1.8, 0), (c1[0], 0, 1.8), (c1[0], 0, -1.8)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=p)
        bpy.context.active_object.data.materials.append(mat_o)

    # 右侧: 强烈轴向拉长八面体 (Mn3+/Fe4+, d4 eg1 严重姜-泰勒畸变 z-out)
    c2 = (3.2, 0, 0)
    oct2 = create_octahedron_mesh("OctDistorted", c2, r_xy=1.4, r_z=2.5)
    oct2.data.materials.append(mat_distorted)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=c2)
    bpy.context.active_object.data.materials.append(mat_tm_mn3)
    for p in [(c2[0]+1.4, 0, 0), (c2[0]-1.4, 0, 0), (c2[0], 1.4, 0), (c2[0], -1.4, 0), (c2[0], 0, 2.5), (c2[0], 0, -2.5)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=p)
        bpy.context.active_object.data.materials.append(mat_o)

    # 标出拉长 z-键的高亮发光脉冲圆柱
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=5.0, location=c2)
    z_bar = bpy.context.active_object
    z_bar.data.materials.append(mat_strain_z)

    # 摄像机
    cam_data = bpy.data.cameras.new("JTCam")
    cam_obj = bpy.data.objects.new("JTCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0, -10.5, 2.0)
    cam_obj.rotation_euler = (math.radians(82), 0, 0)
    scene.camera = cam_obj

    out_file = os.path.join(OUT_DIR, "blender_jahn_teller_3d.png")
    scene.render.filepath = out_file
    print(f"[*] 正在渲染 3D 姜-泰勒畸变机理光追图: {out_file}...")
    bpy.ops.render.render(write_still=True)
    try:
        import shutil
        shutil.copy2(out_file, os.path.join(PICTURES_DIR, "blender_jahn_teller_3d.png"))
    except Exception:
        pass
    print("[+] 姜-泰勒 3D 光追渲染完毕！")

# =========================================================================
# 场景 3: P2 型开阔三棱柱网络与超快钠离子迁移
# =========================================================================
def render_p2_prism():
    clear_scene()
    scene = bpy.context.scene
    setup_cycles_v100(scene)
    setup_studio_lighting()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

    mat_prism = create_material("PolyPrism", (0.1, 0.65, 0.4, 0.42), roughness=0.12, transmission=0.78)
    mat_na_f = create_material("NaFace", (0.95, 0.6, 0.1, 1.0), metallic=0.7, roughness=0.2)
    mat_na_e = create_material("NaEdge", (0.2, 0.8, 0.5, 1.0), metallic=0.7, roughness=0.2)
    mat_o = create_material("AtomO", (0.9, 0.25, 0.2, 1.0), roughness=0.3)

    # 构建三棱柱网格
    def create_trigonal_prism(name, center, r=1.6, h=2.2):
        cx, cy, cz = center
        h2 = h / 2
        # 上下两个等边三角形
        angles = [0, 2*math.pi/3, 4*math.pi/3]
        verts = [(cx + r*math.cos(a), cy + r*math.sin(a), cz + h2) for a in angles] + \
                [(cx + r*math.cos(a), cy + r*math.sin(a), cz - h2) for a in angles]
        faces = [
            (0, 1, 2), (5, 4, 3), # 顶底
            (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0) # 侧面四边形
        ]
        mesh = bpy.data.meshes.new(name=name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj, verts

    # 左中右排布 3 个三棱柱通道
    for idx, x_pos in enumerate([-3.2, 0.0, 3.2]):
        prism_obj, verts = create_trigonal_prism(f"Prism_{idx}", (x_pos, 0, 0))
        prism_obj.data.materials.append(mat_prism)
        # 6 个氧原子
        for v in verts:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=v)
            bpy.context.active_object.data.materials.append(mat_o)
        # 棱柱中心 Na 离子 (Na_f 共面 vs Na_e 共棱)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.52, location=(x_pos, 0, 0))
        na_atom = bpy.context.active_object
        na_atom.data.materials.append(mat_na_f if idx % 2 == 0 else mat_na_e)

    # 摄像机
    cam_data = bpy.data.cameras.new("P2Cam")
    cam_obj = bpy.data.objects.new("P2Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0, -11.0, 3.5)
    cam_obj.rotation_euler = (math.radians(75), 0, 0)
    scene.camera = cam_obj

    out_file = os.path.join(OUT_DIR, "blender_p2_prism_nature.png")
    scene.render.filepath = out_file
    print(f"[*] 正在渲染 P2 开阔三棱柱通道光追图: {out_file}...")
    bpy.ops.render.render(write_still=True)
    try:
        import shutil
        shutil.copy2(out_file, os.path.join(PICTURES_DIR, "blender_p2_prism_nature.png"))
    except Exception:
        pass
    print("[+] P2 三棱柱光追渲染完毕！")

def main():
    print("=" * 60)
    print("[*] 启动 Blender 5.2 + Tesla V100 GPU 顶刊级光追批量渲染任务...")
    print("=" * 60)
    render_o3_lattice()
    render_jahn_teller()
    render_p2_prism()
    print("=" * 60)
    print(f"[SUCCESS] 所有 Blender 3D 光追渲染全部完成！")
    print(f"[PATH] 输出至: {OUT_DIR}")
    print("=" * 60)

if __name__ == '__main__':
    main()
