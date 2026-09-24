# -*- coding: utf-8 -*-
"""
g-cli/scripts/generate_industry_charts.py
生成中国钠离子电池层状氧化物正极材料发展前景与产业政策白皮书全套高精度产业图表
"""

import os
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, FancyArrowPatch

# 注册中文字体
font_paths = ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']
for fp in font_paths:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)

mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['savefig.dpi'] = 220
mpl.rcParams['savefig.bbox'] = 'tight'

OUT_DIR = r"C:\Users\Administrator\g-cli\assets\images"
PICTURES_DIR = r"C:\Users\Administrator\Pictures"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PICTURES_DIR, exist_ok=True)

def save_fig(fig, name):
    p1 = os.path.join(OUT_DIR, name)
    p2 = os.path.join(PICTURES_DIR, name)
    fig.savefig(p1, facecolor='#ffffff', edgecolor='none')
    try:
        import shutil
        shutil.copy2(p1, p2)
    except Exception:
        pass
    plt.close(fig)
    print(f"[OK] Generated: {name}")

# =========================================================================
# 1. 钠电三大正极材料路线综合性能与产业化评级雷达图
# =========================================================================
def draw_routes_radar():
    labels = ['能量密度 (Wh/kg)', '倍率性能 (充放电速度)', '理论/量产成本优势', 
              '产业链与产线兼容度', '循环寿命 (周)', '空气/结构稳定性']
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    # 数据归一化评分 (1-10分)
    # 层状氧化物: 高能量密度、高兼容度、成本优势大，但需改性提升高电压稳定性与空气稳定性
    layered_oxide = [9.2, 8.5, 9.0, 9.5, 7.5, 7.0]
    layered_oxide += layered_oxide[:1]

    # 聚阴离子 (如 NFPP): 循环超长、极稳定，但能量密度和电子导电率偏低
    polyanion = [6.5, 7.0, 7.2, 7.5, 9.5, 9.2]
    polyanion += polyanion[:1]

    # 普鲁士蓝类: 理论成本极低、电压高，但结晶水控制与工业化合成一致性难度极大
    prussian_blue = [7.5, 7.2, 8.0, 6.0, 5.5, 5.0]
    prussian_blue += prussian_blue[:1]

    fig, ax = plt.subplots(figsize=(8.5, 8.5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], labels, fontsize=10.5, fontweight='bold', color='#1e293b')
    ax.set_rlabel_position(0)
    plt.yticks([2, 4, 6, 8, 10], ["2", "4", "6", "8", "10"], color="#64748b", size=9)
    plt.ylim(0, 10.5)

    # 绘制三条曲线
    ax.plot(angles, layered_oxide, color='#0284c7', linewidth=2.8, linestyle='solid', label='层状氧化物 (Layered Oxide) - 综合领跑')
    ax.fill(angles, layered_oxide, color='#0284c7', alpha=0.22)

    ax.plot(angles, polyanion, color='#16a34a', linewidth=2.4, linestyle='--', label='聚阴离子化合物 (如 NFPP) - 长循环保驾')
    ax.fill(angles, polyanion, color='#16a34a', alpha=0.15)

    ax.plot(angles, prussian_blue, color='#ea580c', linewidth=2.0, linestyle=':', label='普鲁士蓝/白化合物 - 产业化滞后')
    ax.fill(angles, prussian_blue, color='#ea580c', alpha=0.10)

    plt.title("钠离子电池三大主流正极材料路线核心维度对比\n(层状氧化物凭借高能量密度与锂电产线 90%+ 兼容度率先规模化)", 
              fontsize=12.5, fontweight='bold', pad=25, color='#0f172a')
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), frameon=True, facecolor='#f8fafc', edgecolor='#cbd5e1', ncol=1, fontsize=9.5)
    save_fig(fig, '01_cathode_routes_radar.png')

# =========================================================================
# 2. 中国大陆新型储能与钠离子电池最新政策全景框架 (2024-2027)
# =========================================================================
def draw_policy_landscape():
    fig, ax = plt.subplots(figsize=(13.2, 7.5))
    ax.axis('off')

    # 背景框
    ax.add_patch(Rectangle((0.015, 0.015), 0.97, 0.97, facecolor='#f8fafc', edgecolor='#cbd5e1', lw=1.5))
    ax.text(0.5, 0.94, "中国大陆新型储能与钠离子电池产业最新政策顶层设计与落地支撑体系", 
            ha='center', fontsize=14, fontweight='bold', color='#0f172a')
    ax.text(0.5, 0.895, "工信部、国家能源局、发改委等部委政策联合驱动：从技术攻关走向百兆瓦时级规模化储能与动力示范", 
            ha='center', fontsize=10, color='#475569')

    # 四大板块
    blocks = [
        ("国家级纲领与行动方案", "#0284c7", [
            "• 工信部等八部门《新型储能制造业高质量发展行动方案》(2025.02 印发)",
            "  - 明确将高容量正极材料、高性能负极材料作为关键核心攻关方向",
            "  - 明确支持大规模钠电池储能系统集成研发，培育千亿级链主企业",
            "• 发改委、国家能源局《关于加快推动新型储能发展的指导意见》",
            "  - 推动钠离子电池开展工程化中试、规模化示范与产业化验证"
        ]),
        ("国家标准与行业标准体系", "#0d9488", [
            "• 工信部行业标准《便携式设备用钠离子电池和电池组安全要求》",
            "• 能源行业标准《电力储能用钠离子电池安全技术规范》加速推进与评审",
            "• 中国轻工联《钠离子电池通用规范》(SJ/T 11922-2023) 建立基础门槛",
            "• 储能电站消防安全准入与强制性国家认证全面对齐锂电同等严格标尺"
        ]),
        ("重大示范工程与电网入网政策", "#16a34a", [
            "• 国家能源局新型储能试点示范项目：正式将 100MWh 钠电电站纳入国家级示范",
            "• 电网调峰调频辅助服务补偿机制健全：赋予钠电储能构网型运行合法收益",
            "• 两个细则考核优惠：对参与一次调频响应速度优异的钠电储能给予优先补偿",
            "• 独立储能容量电价与容量租赁模式在湖北、山东、广西率先破局"
        ]),
        ("地方政府补贴与产业园区配套", "#d97706", [
            "• 长三角经济圈 (江苏、浙江)：首台(套)重大技术装备补贴最高达 1000 万元",
            "• 湖北省：针对潜江百兆瓦时级等示范项目给予上网电价倾斜与投资补贴",
            "• 粤港澳大湾区 (广东)：重点扶持新型储能产业创新中心与前驱体供应链",
            "• 晋/蒙/鲁：结合当地煤化工与富余钠源打造高纯正极原料垂直一体化产业园"
        ])
    ]

    coords = [(0.03, 0.48), (0.51, 0.48), (0.03, 0.05), (0.51, 0.05)]
    for (title, col, items), (bx, by) in zip(blocks, coords):
        # 卡片框
        ax.add_patch(Rectangle((bx, by), 0.46, 0.39, facecolor='#ffffff', edgecolor=col, lw=2))
        # 标头底色
        ax.add_patch(Rectangle((bx, by+0.32), 0.46, 0.07, facecolor=col, edgecolor=col))
        ax.text(bx+0.02, by+0.355, title, fontsize=11, fontweight='bold', color='#ffffff', va='center')
        
        y_text = by + 0.27
        for line in items:
            ax.text(bx+0.015, y_text, line, fontsize=8.2, color='#1e293b', va='center')
            y_text -= 0.056

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    save_fig(fig, '02_policy_landscape_2025.png')

# =========================================================================
# 3. 钠电度电成本 (LCOS) 下降路径与对碳酸锂价格的抗波动分析
# =========================================================================
def draw_cost_analysis():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))

    # 左图: 规模化放量下的钠电电芯成本下降预测 (元/Wh)
    years = [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2030]
    cell_cost = [0.85, 0.65, 0.45, 0.36, 0.30, 0.26, 0.23, 0.20]
    lfp_ref = [0.75, 0.52, 0.38, 0.35, 0.34, 0.33, 0.32, 0.30]

    ax1.plot(years, cell_cost, 'o-', color='#0284c7', lw=3, label='层状氧化物钠电电芯成本 (GWh规模化摊薄)')
    ax1.plot(years, lfp_ref, 's--', color='#64748b', lw=2, label='磷酸铁锂 (LFP) 电芯成本 (碳酸锂约7-8万元/吨)')
    ax1.axhline(0.25, color='#16a34a', linestyle=':', lw=1.5, label='终极目标成本线 (0.25 元/Wh)')
    ax1.set_title("钠电池电芯制造成本演进与规模化降本路径", fontsize=11.5, fontweight='bold', color='#0f172a')
    ax1.set_xlabel("年份", fontsize=10)
    ax1.set_ylabel("电芯制造成本 (元/Wh)", fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(fontsize=9, loc='upper right')
    ax1.annotate("2025年跨过经济性平衡拐点\n与锂电直接抗衡", xy=(2025, 0.36), xytext=(2024.5, 0.55),
                 arrowprops=dict(arrowstyle="->", color='#0284c7', lw=2),
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#e0f2fe", edgecolor="#0284c7"),
                 fontsize=9, fontweight='bold')

    # 右图: 碳酸锂不同价格下，钠电池层状氧化物的经济性替代优势
    li_prices = [4, 6, 8, 10, 15, 20, 30] # 万元/吨
    lfp_cost_sim = [0.30 + p*0.008 for p in li_prices]
    na_cost_sim = [0.28 for _ in li_prices] # 钠资源不依赖锂价，成本几乎刚性独立

    ax2.plot(li_prices, lfp_cost_sim, 'd-', color='#ea580c', lw=2.5, label='LFP 电芯成本 (对锂价高度敏感)')
    ax2.plot(li_prices, na_cost_sim, 'o-', color='#0284c7', lw=3, label='层状氧化物钠电 (原料无锂，价格绝对稳定)')
    ax2.fill_between(li_prices, na_cost_sim, lfp_cost_sim, where=[l >= n for l, n in zip(lfp_cost_sim, na_cost_sim)],
                     color='#bae6fd', alpha=0.45, label='钠电池成本绝对优势红利区')
    ax2.set_title("碳酸锂价格波动对正极材料经济性的影响对比", fontsize=11.5, fontweight='bold', color='#0f172a')
    ax2.set_xlabel("碳酸锂市场价格 (万元/吨)", fontsize=10)
    ax2.set_ylabel("电池综合制造成本 (元/Wh)", fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(fontsize=9, loc='upper left')

    fig.suptitle("中国钠离子电池层状氧化物正极技术经济学与全生命周期成本优势分析", fontsize=13, fontweight='bold', y=0.98)
    save_fig(fig, '03_cost_and_economics.png')

# =========================================================================
# 4. 中国大陆百兆瓦时级重大钠离子储能示范项目全景落地矩阵
# =========================================================================
def draw_projects_matrix():
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.axis('off')

    headers = ["示范工程名称", "装机规模", "正极技术路线", "并网/投运时间", "运营主体与供应链", "核心战略示范意义"]
    data = [
        ["大唐湖北潜江储能电站", "50MW / 100MWh", "O3 型层状氧化物", "2024年6月投产", "大唐集团 / 中科海钠", "全球首个百兆瓦时级独立储能电站，商用里程碑"],
        ["云南文山宝池储能站", "200MW / 400MWh", "层状氧化物 (锂钠混构)", "2025年中投运", "南方电网 / 行业头部", "全球首套构网型钠离子混合储能系统，稳定特高压电网"],
        ["广西南宁伏林储能站", "10MW / 10MWh", "层状氧化物", "2024年5月投产", "南方电网广西电网", "电网侧大容量钠电首套系统化应用，长时抗高湿测试"],
        ["三峡能源安徽阜阳储能", "30MW / 60MWh", "层状氧化物 / 聚阴离子", "2024年底并网", "三峡集团 / 行业联合", "国家级能源局重点示范，火电联合调频与新能源配储"],
        ["江淮钇为 / 奇瑞新能源", "动力电池包 (25-32kWh)", "蜂巢 / 中科海钠层氧", "2024年批量交付", "主流自主品牌主机厂", "乘用车 A00 级装车首发，零下 20℃ 低温续航卓越"]
    ]

    col_widths = [0.18, 0.14, 0.16, 0.12, 0.18, 0.22]
    tab = ax.table(cellText=data, colLabels=headers, loc='center', cellLoc='center',
                   colWidths=col_widths, cellColours=None)
    tab.scale(1, 2.5)
    tab.set_fontsize(10)
    
    # 调整表格样式: 深色稳重表头与斑马纹
    for (i, j), cell in tab.get_celld().items():
        cell.set_edgecolor('#cbd5e1')
        if i == 0:
            cell.set_facecolor('#0f172a')
            cell.set_text_props(weight='bold', color='#ffffff', size=10.2)
        else:
            cell.set_text_props(color='#1e293b', size=9.2)
            if i % 2 == 1:
                cell.set_facecolor('#f8fafc')
            else:
                cell.set_facecolor('#ffffff')

    ax.set_title("中国大陆标志性百兆瓦时 (MWh) 级重大钠离子储能与动力示范项目落地汇总表 (2024-2025)", 
                 fontsize=13, fontweight='bold', pad=25, color='#0f172a')
    save_fig(fig, '04_projects_matrix.png')

# =========================================================================
# 5. 层状氧化物正极产业链完整拓扑与头部玩家生态
# =========================================================================
def draw_industry_chain():
    fig, ax = plt.subplots(figsize=(13.2, 6.4))
    ax.axis('off')

    stages = [
        ("1. 上游大宗原料", "#0284c7", ["碳酸钠 (工业纯碱)", "硫酸锰 / 高纯电解锰", "铁源 (草酸亚铁/还原铁)", "硫酸镍 / 氧化镍", "协同掺杂源 (Li/Mg/Ti/Cu)"]),
        ("2. 前驱体与共沉淀", "#0d9488", ["Ni-Fe-Mn 三元氢氧化物", "共沉淀合成釜连续精控", "氮气/微量氧气氛保护", "球形度与粒径 (D50) 优化", "格林达 / 容百 / 华友"]),
        ("3. 高温烧结正极材料", "#d97706", ["高温固相两段式煅烧", "表面空气稳定性钝化包覆", "双位点元素协同固溶改性", "中科海钠 / 容百科技", "传艺科技 / 钠创新能源"]),
        ("4. 钠电电芯与Pack制造", "#16a34a", ["正极涂布 (锂电产线90%兼容)", "硬碳负极高匹配体系", "高盐浓度阻燃电解液", "宁德时代 / 亿纬锂能", "比亚迪 / 鹏辉能源"]),
        ("5. 终端应用场景渗透", "#7c3aed", ["百兆瓦时级电网侧独立储能", "工商业与户用分布式储能", "两轮电动车 (雅迪/台铃)", "A00 级微型代步纯电乘用车", "高寒地区通讯基站长时备电"])
    ]

    x_starts = [0.02, 0.22, 0.42, 0.62, 0.82]
    w = 0.165
    for idx, (title, color, items) in enumerate(stages):
        x = x_starts[idx]
        # 主标题卡
        ax.add_patch(Rectangle((x, 0.78), w, 0.13, facecolor=color, edgecolor='none'))
        ax.text(x + w/2, 0.845, title, ha='center', va='center', fontsize=10.5, fontweight='bold', color='#ffffff')
        
        # 详细内容列表框
        ax.add_patch(Rectangle((x, 0.10), w, 0.65, facecolor='#f8fafc', edgecolor=color, lw=1.8))
        for item_idx, itm in enumerate(items):
            y_pos = 0.67 - item_idx * 0.115
            ax.text(x + 0.008, y_pos, f"• {itm}", fontsize=8.2, color='#1e293b', va='center')

        # 箭头连接
        if idx < len(stages) - 1:
            ax.annotate("", xy=(x + w + 0.032, 0.48), xytext=(x + w + 0.003, 0.48),
                        arrowprops=dict(arrowstyle="->", lw=2.5, color='#94a3b8'))

    ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.0)
    fig.suptitle("中国钠离子电池层状氧化物正极材料完整产业链生态全景图", fontsize=13.5, fontweight='bold', y=0.97, color='#0f172a')
    save_fig(fig, '05_industry_chain.png')

def main():
    print("=" * 60)
    print("[*] 正在生成白皮书专属产业前景与政策全景图表...")
    print("=" * 60)
    draw_routes_radar()
    draw_policy_landscape()
    draw_cost_analysis()
    draw_projects_matrix()
    draw_industry_chain()
    print("=" * 60)
    print(f"[SUCCESS] 产业前景与政策插图已全部生成完毕！")
    print(f"[PATH] 输出至: {OUT_DIR}")
    print("=" * 60)

if __name__ == '__main__':
    main()
