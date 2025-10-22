# -*- coding: utf-8 -*-
"""
MÔ PHỎNG SUY DIỄN LÙI (Backward Chaining)
-----------------------------------------
Dựa theo nội dung slide “Chọn luật trong quá trình suy diễn”
 - Chiến lược chỉ số min / max
 - Chiến lược đồ thị FPG (Facts Precedence Graph)
"""

import networkx as nx
import matplotlib.pyplot as plt

# ==========================================
# TẬP LUẬT MẪU
# ==========================================
rules = {
    1: ({"a", "b"}, "c"),
    2: ({"a"}, "b"),
    3: ({"c", "d"}, "e"),
    4: ({"b"}, "e"),
    5: ({"g", "e"}, "f"),
    6: ({"c", "e"}, "f"),
}

# ==========================================
# XÂY DỰNG ĐỒ THỊ FPG (Facts Precedence Graph)
# ==========================================
def build_fpg(rules):
    """
    Mỗi sự kiện là một đỉnh, mỗi luật tạo ra các cung:
    f (vế trái) → q (vế phải)
    """
    G = nx.DiGraph()
    for i, (left, right) in rules.items():
        for f in left:
            G.add_edge(f, right, rule=f"r{i}")
    return G


def d_fpg(G, start, end):
    """Khoảng cách ngắn nhất từ sự kiện start → end"""
    try:
        return nx.shortest_path_length(G, start, end)
    except nx.NetworkXNoPath:
        return float("inf")


def heuristic_fpg(G, rule_id, goal):
    """Hàm lượng giá h(r,GT) = max{d(f,GT) | f ∈ left(r)}"""
    left, _ = rules[rule_id]
    return max(d_fpg(G, goal, f) for f in left)


# ==========================================
# SUY DIỄN LÙI (Backward Chaining)
# ==========================================
def backward_chain(goal, known, strategy="min", depth=0, G=None, used=None):
    indent = "  " * depth
    if used is None:
        used = set()

    print(f"{indent}=> Cần chứng minh: {goal}")

    # Nếu đã biết
    if goal in known:
        print(f"{indent}✓ {goal} đã biết trong GT.")
        return True

    # Tìm các luật có kết luận là goal
    applicable = [r for r, (prem, concl) in rules.items() if concl == goal and r not in used]
    if not applicable:
        print(f"{indent}✗ Không có luật nào suy ra {goal}. Quay lui.")
        return False

    # Chiến lược chọn luật
    if strategy == "min":
        r_chosen = min(applicable)
    elif strategy == "max":
        r_chosen = max(applicable)
    elif strategy == "fpg" and G is not None:
        # Tính h(r,GT) cho từng luật
        h_values = {r: heuristic_fpg(G, r, goal) for r in applicable}
        r_chosen = min(h_values, key=h_values.get)
        print(f"{indent}→ h(r,GT): {h_values}")
    else:
        r_chosen = applicable[0]

    used.add(r_chosen)
    premises, conclusion = rules[r_chosen]
    print(f"{indent}- Chọn luật r{r_chosen}: {premises} → {conclusion}")

    # Kiểm tra các điều kiện vế trái
    all_proven = True
    for p in premises:
        if not backward_chain(p, known, strategy, depth + 1, G, used):
            all_proven = False
            print(f"{indent}  Quay lui khỏi r{r_chosen}")
            break

    if all_proven:
        print(f"{indent}✓ Suy ra được {goal} nhờ r{r_chosen}")
        known.add(goal)
        return True

    print(f"{indent}✗ Không thể chứng minh {goal}. Quay lui.")
    return False


# ==========================================
# CHẠY THỬ
# ==========================================
if __name__ == "__main__":
    GT = {"a"}      # Giả thiết ban đầu
    KL = {"f"}      # Kết luận cần chứng minh
    goal = next(iter(KL))

    print("=== SUY DIỄN LÙI (BACKWARD CHAINING) ===")
    for i, (prem, concl) in rules.items():
        print(f"r{i}: {prem} → {concl}")
    print(f"\nGT = {GT}, KL = {KL}\n")

    # 1️⃣ Chỉ số Min
    print("------ CHIẾN LƯỢC CHỈ SỐ MIN ------")
    backward_chain(goal, set(GT), strategy="min")

    # 2️⃣ Chỉ số Max
    print("\n------ CHIẾN LƯỢC CHỈ SỐ MAX ------")
    backward_chain(goal, set(GT), strategy="max")

    # 3️⃣ FPG (Heuristic)
    print("\n------ CHIẾN LƯỢC FPG ------")
    G = build_fpg(rules)
    backward_chain(goal, set(GT), strategy="fpg", G=G)

    # Vẽ đồ thị FPG
    plt.figure(figsize=(7, 5))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color="lightgreen", node_size=1600, font_size=11)
    edge_labels = nx.get_edge_attributes(G, "rule")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="blue")
    plt.title("Đồ thị FPG (Facts Precedence Graph)")
    plt.show()
