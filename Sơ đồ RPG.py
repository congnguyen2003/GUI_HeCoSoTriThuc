# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 🔮 SUY DIỄN – VẼ ĐỒ THỊ PHỤ THUỘC GIỮA CÁC LUẬT (RPG)
# ============================================================

from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
import re
import random

# ============================================================
# 1️⃣ ĐỌC TẬP LUẬT TỪ FILE TXT
# ============================================================
def doc_luat_tu_file(filepath):
    rules = {}
    GT, KL = set(), set()

    if not Path(filepath).exists():
        print(f"❌ Không tìm thấy file: {filepath}")
        raise FileNotFoundError(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    idx = 1
    for line in lines:
        if '->' in line:
            left, right = map(str.strip, line.split('->'))
            left = re.split(r'\^|∧|\s+', left)
            left = [i for i in left if i]
            rules[f"r{idx}"] = {"left": left, "right": right}
            idx += 1
        elif line.lower().startswith('gt'):
            GT = set(re.findall(r"[a-zA-Z0-9]+", line.split('=')[1]))
        elif line.lower().startswith('kl'):
            KL = set(re.findall(r"[a-zA-Z0-9]+", line.split('=')[1]))
    return rules, GT, KL


# ============================================================
# 2️⃣ XÂY DỰNG ĐỒ THỊ PHỤ THUỘC RPG
# ============================================================
def build_rpg(rules):
    G = nx.DiGraph()
    for r in rules:
        G.add_node(r)
    for ri, info_i in rules.items():
        for rj, info_j in rules.items():
            if ri != rj and info_i["right"] in info_j["left"]:
                G.add_edge(ri, rj, label=info_i["right"])
    return G


# ============================================================
# 3️⃣ XÁC ĐỊNH R_GT VÀ R_KL
# ============================================================
def tim_R_GT_R_KL(rules, GT, KL):
    R_GT = {r for r, info in rules.items() if all(p in GT for p in info["left"])}
    R_KL = {r for r, info in rules.items() if info["right"] in KL}
    return R_GT, R_KL


# ============================================================
# 4️⃣ VẼ ĐỒ THỊ RPG (GIÃN CỰC RỘNG, KHÔNG CHỒNG NODE)
# ============================================================
def ve_rpg_dep(G, R_GT, R_KL):
    plt.close('all')
    plt.figure().clear()
    plt.rcParams.update(plt.rcParamsDefault)

    # 💡 Dùng layout spring với lực đẩy mạnh, node tự tách xa nhau
    pos = nx.spring_layout(G, k=2.5, iterations=300, seed=42)

    # Dịch vị trí ngẫu nhiên để tránh trùng tọa độ
    for n in pos:
        pos[n][0] += random.uniform(-0.4, 0.4)
        pos[n][1] += random.uniform(-0.4, 0.4)

    # Tạo phân tầng trực quan
    for n in G.nodes:
        if n in R_GT:
            pos[n][1] += 3.0
        elif n in R_KL:
            pos[n][1] -= 3.0

    plt.figure(figsize=(20, 13))
    ax = plt.gca()
    ax.set_facecolor("#fdfdfd")

    color_gt = "#FF5722"   # cam đậm
    color_kl = "#4CAF50"   # xanh lá
    color_mid = "#2196F3"  # xanh dương

    node_colors = []
    for n in G.nodes:
        if n in R_GT:
            node_colors.append(color_gt)
        elif n in R_KL:
            node_colors.append(color_kl)
        else:
            node_colors.append(color_mid)

    # 🟢 Vẽ node
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=2600,
        node_shape='o',
        edgecolors='black',
        linewidths=1.5,
        alpha=0.95
    )

    nx.draw_networkx_labels(G, pos, font_size=11, font_weight='bold', font_color='white')

    # 🟠 Vẽ cạnh
    nx.draw_networkx_edges(
        G, pos,
        arrows=True,
        arrowsize=28,
        width=2.2,
        edge_color='#444',
        connectionstyle="arc3,rad=0.18",
        alpha=0.9
    )

    # 🔠 Nhãn cạnh
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_color='#004D40',
        font_size=9,
        bbox={"facecolor": "#E0F2F1", "alpha": 0.8, "edgecolor": "none", "boxstyle": "round,pad=0.5"}
    )

    # 🧭 Tiêu đề + chú giải
    plt.title("ĐỒ THỊ PHỤ THUỘC GIỮA CÁC LUẬT (RPG GIÃN CỰC RỘNG)", fontsize=20, fontweight='bold', color='#0D47A1', pad=25)

    legend_y = max(p[1] for p in pos.values()) + 1.5
    plt.text(-5, legend_y, "🟠 R_GT (từ GT)", fontsize=12, color=color_gt, weight="bold")
    plt.text(-2, legend_y, "🟢 R_KL (đến KL)", fontsize=12, color=color_kl, weight="bold")
    plt.text(1, legend_y, "🔵 Trung gian", fontsize=12, color=color_mid, weight="bold")

    plt.axis('off')
    plt.tight_layout()
    plt.show()


# ============================================================
# 5️⃣ CHƯƠNG TRÌNH CHÍNH
# ============================================================
if __name__ == "__main__":
    filepath = Path(r"D:\Năm 5 Kì 2\Cơ sở tri thức\rules.txt")

    if not filepath.exists():
        filepath = Path("rules.txt")
        if not filepath.exists():
            print(f"❌ File không tồn tại: {filepath.resolve()}")
            sys.exit(1)

    rules, GT, KL = doc_luat_tu_file(filepath)

    print(f"📘 Đã đọc {len(rules)} luật từ file '{filepath.name}'.")
    print(f"GT = {GT}")
    print(f"KL = {KL}")

    G = build_rpg(rules)
    R_GT, R_KL = tim_R_GT_R_KL(rules, GT, KL)
    ve_rpg_dep(G, R_GT, R_KL)
