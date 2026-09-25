# -*- coding: utf-8 -*-
"""
g-cli/scripts/render_interactive_3d_layers.py
基于真实 CIF 晶体学标准坐标的三维交互式层状正极晶格可视化
- 严格遵循真实空间群与 Wyckoff 占位:
    * O3 (R-3m): Na 处于 3a (大八面体间隙, Na-O = 2.40 A), Fe 处于 3b (小八面体骨架, Fe-O = 2.03 A)
    * P2 (P6_3/mmc): Mn 处于 2a (MnO6 八面体, Mn-O = 1.95 A), Na 处于 2d/2b 开阔三棱柱通道
- 晶胞比例 4x4x1 (横向 ~12 A, 纵向 11-16 A) 真实平板层状比例
- 自动计算并高亮:
    * O3 钠离子的八面体配位 (NaO6, 顶底两组三角形互呈 60 度错位)
    * P2 钠离子的三棱柱配位 (NaO6, 顶底两组三角形垂直对齐无错位)
- 导出交互式 HTML (支持360度旋转、滚轮缩放、悬停查看原子与层高坐标) 及高清静态 PNG
"""

import os
import shutil
import numpy as np
from ase.io import read
from scipy.spatial import ConvexHull
import plotly.graph_objects as go

# ── 路径配置 ──────────────────────────────────────────────────
BASE_DIR = r"C:\Users\Administrator\g-cli"
CIF_O3   = os.path.join(BASE_DIR, "structures", "01_O3_NaFeO2.cif")
CIF_P2   = os.path.join(BASE_DIR, "structures", "02_P2_Na0.67MnO2.cif")
HTML_OUT = os.path.join(BASE_DIR, "assets", "3d_layers_interactive.html")
PNG_OUT  = os.path.join(BASE_DIR, "assets", "images", "11_3d_layers_plotly.png")
PICTURES = r"C:\Users\Administrator\Pictures"

os.makedirs(os.path.join(BASE_DIR, "assets", "images"), exist_ok=True)
os.makedirs(PICTURES, exist_ok=True)

# ── 元素视觉样式 ──────────────────────────────────────────────
COLORS = {
    "Na": "#F1C40F",  # 金黄
    "Fe": "#2980B9",  # 宝石蓝
    "Mn": "#8E44AD",  # 优雅紫
    "O":  "#E74C3C",  # 珊瑚红
}
RADII = {
    "Na": 8.0,
    "Fe": 7.0,
    "Mn": 7.0,
    "O":  4.5,
}

# ── 读取与构建超胞 ────────────────────────────────────────────
def build_supercell(cif_path, repeat=(4, 4, 1)):
    atoms = read(cif_path)
    return atoms.repeat(repeat)

# ── 计算过渡金属-氧 (TM-O) 八面体骨架键 ────────────────────────
def compute_tm_o_bonds(pos, syms, tm_sym="Fe", cutoff=2.18):
    tm_idx = [i for i, s in enumerate(syms) if s == tm_sym]
    o_idx  = [i for i, s in enumerate(syms) if s == "O"]
    bonds = []
    for ti in tm_idx:
        for oi in o_idx:
            d = np.linalg.norm(pos[ti] - pos[oi])
            if 1.5 < d < cutoff:
                bonds.append((ti, oi))
    return bonds

# ── 寻找具有完整 6 配位环境的中心 Na 离子 ──────────────────────
def find_central_na_cage(pos, syms, cutoff=2.60):
    na_idx = [i for i, s in enumerate(syms) if s == "Na"]
    o_idx  = [i for i, s in enumerate(syms) if s == "O"]
    center = np.mean(pos, axis=0)
    
    best_na = None
    best_dist = 999.0
    best_ligands = []
    
    for ni in na_idx:
        d_center = np.linalg.norm(pos[ni] - center)
        dists = [(oi, np.linalg.norm(pos[ni] - pos[oi])) for oi in o_idx]
        dists.sort(key=lambda x: x[1])
        if len(dists) >= 6 and dists[0][1] > 2.2 and dists[5][1] < cutoff:
            if d_center < best_dist:
                best_dist = d_center
                best_na = ni
                best_ligands = [x[0] for x in dists[:6]]
                
    return best_na, best_ligands

# ── 构建晶胞框线 (说明六方 120 度晶系特征) ──────────────────────
def build_wireframe(cell, origin):
    v0 = origin
    v1 = origin + cell[0]
    v2 = origin + cell[1]
    v3 = origin + cell[0] + cell[1]
    v4 = origin + cell[2]
    v5 = origin + cell[0] + cell[2]
    v6 = origin + cell[1] + cell[2]
    v7 = origin + cell[0] + cell[1] + cell[2]
    lines = [
        (v0, v1), (v1, v3), (v3, v2), (v2, v0),
        (v4, v5), (v5, v7), (v7, v6), (v6, v4),
        (v0, v4), (v1, v5), (v2, v6), (v3, v7)
    ]
    bx, by, bz = [], [], []
    for p1, p2 in lines:
        bx += [p1[0], p2[0], None]
        by += [p1[1], p2[1], None]
        bz += [p1[2], p2[2], None]
    return bx, by, bz

# ── 构建结构 Trace 集合 ───────────────────────────────────────
def generate_traces(supercell, x_shift=0.0, struct_type="O3"):
    pos = supercell.positions.copy()
    pos[:, 0] += x_shift
    syms = supercell.get_chemical_symbols()
    tm_sym = "Fe" if struct_type == "O3" else "Mn"
    
    traces = []
    
    # 1. 晶胞轮廓框线
    bx, by, bz = build_wireframe(supercell.cell, np.array([x_shift, 0, 0]))
    traces.append(go.Scatter3d(
        x=bx, y=by, z=bz, mode="lines",
        line=dict(color="rgba(180, 190, 205, 0.45)", width=1.5, dash="dash"),
        showlegend=False, hoverinfo="skip"
    ))
    
    # 2. TM-O 共价八面体骨架键
    cutoff = 2.18 if struct_type == "O3" else 2.10
    bonds = compute_tm_o_bonds(supercell.positions, syms, tm_sym=tm_sym, cutoff=cutoff)
    lx, ly, lz = [], [], []
    for ti, oi in bonds:
        p1, p2 = pos[ti], pos[oi]
        lx += [p1[0], p2[0], None]
        ly += [p1[1], p2[1], None]
        lz += [p1[2], p2[2], None]
    traces.append(go.Scatter3d(
        x=lx, y=ly, z=lz, mode="lines",
        line=dict(color="rgba(120, 140, 160, 0.5)", width=2.5),
        showlegend=False, hoverinfo="skip"
    ))
    
    # 3. 高亮特征 Na 6配位笼 (八面体 vs 三棱柱)
    c_na, c_ligands = find_central_na_cage(supercell.positions, syms)
    if c_na is not None and len(c_ligands) == 6:
        na_p = pos[c_na]
        hx, hy, hz = [], [], []
        for li in c_ligands:
            lp = pos[li]
            hx += [na_p[0], lp[0], None]
            hy += [na_p[1], lp[1], None]
            hz += [na_p[2], lp[2], None]
        
        poly_col = "#E67E22" if struct_type == "O3" else "#8E44AD"
        cage_name = "O3 八面体配位 (NaO6)" if struct_type == "O3" else "P2 三棱柱配位 (NaO6)"
        traces.append(go.Scatter3d(
            x=hx, y=hy, z=hz, mode="lines",
            line=dict(color=poly_col, width=4.5),
            name=f"配位特征: {cage_name}",
            showlegend=True, hoverinfo="skip"
        ))
        
        # 配位多面体半透明外包网格 (ConvexHull)
        pts = pos[c_ligands]
        hull = ConvexHull(pts)
        traces.append(go.Mesh3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            i=hull.simplices[:, 0], j=hull.simplices[:, 1], k=hull.simplices[:, 2],
            color=poly_col, opacity=0.25,
            showlegend=False, hoverinfo="skip"
        ))
        
    # 4. 原子球层 (按元素分层展示)
    elements = [tm_sym, "O", "Na"]
    for elem in elements:
        idx = [i for i, s in enumerate(syms) if s == elem]
        if not idx:
            continue
        ep = pos[idx]
        name_map = {
            "Fe": "Fe3+ (过渡金属层)",
            "Mn": "Mn3+/4+ (过渡金属层)",
            "O":  "O2- (密堆积氧层)",
            "Na": f"Na+ ({struct_type} 钠层离子)"
        }
        traces.append(go.Scatter3d(
            x=ep[:, 0], y=ep[:, 1], z=ep[:, 2],
            mode="markers",
            name=name_map[elem],
            marker=dict(
                size=RADII[elem],
                color=COLORS[elem],
                opacity=0.92 if elem != "O" else 0.70,
                line=dict(width=0.6, color="white")
            ),
            hovertemplate=(
                f"<b>{name_map[elem]}</b><br>"
                f"物相: {struct_type} 型<br>"
                "X: %{x:.2f} A | Y: %{y:.2f} A<br>"
                "层高 Z: %{z:.2f} A<extra></extra>"
            )
        ))
        
    return traces

def main():
    print("[*] 读取 O3-NaFeO2 CIF 并构建 4x4x1 超胞...")
    o3 = build_supercell(CIF_O3, repeat=(4, 4, 1))
    print(f"    O3 原子数: {len(o3)}, c 轴高度: {o3.cell[2,2]:.2f} A")
    
    print("[*] 读取 P2-Na0.67MnO2 CIF 并构建 4x4x1 超胞...")
    p2 = build_supercell(CIF_P2, repeat=(4, 4, 1))
    print(f"    P2 原子数: {len(p2)}, c 轴高度: {p2.cell[2,2]:.2f} A")
    
    # 并列放置对比 (向右偏移 18 A)
    x_shift_p2 = 18.0
    traces_o3 = generate_traces(o3, x_shift=0.0, struct_type="O3")
    traces_p2 = generate_traces(p2, x_shift=x_shift_p2, struct_type="P2")
    
    # 顶部学术注释
    annotations = [
        dict(
            x=np.mean(o3.positions[:, 0]),
            y=np.mean(o3.positions[:, 1]),
            z=o3.cell[2, 2] + 2.5,
            text="<b>O3 型结构 (α-NaFeO2)</b><br>空间群: <i>R-3m</i> | ABCABC 紧密堆积<br>Na+ 处于<b>八面体 (Octahedral)</b> 间隙",
            showarrow=False,
            font=dict(size=14, color="#1A5276")
        ),
        dict(
            x=np.mean(p2.positions[:, 0]) + x_shift_p2,
            y=np.mean(p2.positions[:, 1]),
            z=p2.cell[2, 2] + 2.5,
            text="<b>P2 型结构 (Na0.67MnO2)</b><br>空间群: <i>P63/mmc</i> | ABBA 对称堆积<br>Na+ 处于<b>三棱柱 (Prismatic)</b> 开放通道",
            showarrow=False,
            font=dict(size=14, color="#5B2C6F")
        )
    ]
    
    fig = go.Figure(data=traces_o3 + traces_p2)
    fig.update_layout(
        title=dict(
            text="<b>钠离子电池层状正极真实三维晶体结构交互解析 (O3 vs P2)</b><br>"
                 "<sup>基于 CIF 晶体学标准坐标 · 真实六方晶格 (γ=120°) · 支持 360° 拖动旋转 / 滚轮缩放 / 悬停查看原子与层高</sup>",
            x=0.5, font=dict(size=17, color="#2C3E50")
        ),
        scene=dict(
            xaxis=dict(title="X (A)", showbackground=False, gridcolor="#E5E8E8"),
            yaxis=dict(title="Y (A)", showbackground=False, gridcolor="#E5E8E8"),
            zaxis=dict(title="Z / c 轴 (A) [多层堆叠方向]", showbackground=False, gridcolor="#E5E8E8"),
            bgcolor="rgba(250, 252, 255, 1)",
            camera=dict(
                eye=dict(x=1.35, y=-1.65, z=0.75),
                center=dict(x=0.2, y=0, z=0)
            ),
            annotations=annotations,
            aspectmode="data"
        ),
        legend=dict(
            title=dict(text="<b>晶体学图例</b>"),
            x=0.01, y=0.98,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#BDC3C7", borderwidth=1,
            font=dict(size=12)
        ),
        margin=dict(l=0, r=0, t=90, b=0),
        paper_bgcolor="#FFFFFF",
        width=1600, height=920
    )
    
    print("[*] 正在导出交互式 HTML: " + HTML_OUT)
    fig.write_html(HTML_OUT, include_plotlyjs="cdn")
    print("    [OK] HTML 导出成功")
    
    print("[*] 正在导出高清静态 PNG: " + PNG_OUT)
    fig.write_image(PNG_OUT, scale=2)
    shutil.copy(PNG_OUT, os.path.join(PICTURES, "11_3d_layers_plotly.png"))
    print("    [OK] PNG 导出并同步至 Pictures")
    print("\n[SUCCESS] 全部生成完成！可在浏览器中直接打开 HTML 进行交互旋转。")

if __name__ == "__main__":
    main()
