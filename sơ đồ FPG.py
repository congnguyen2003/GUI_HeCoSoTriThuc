
import math
import networkx as nx
import matplotlib.pyplot as plt

# === DANH SÁCH 16 LUẬT (premises, conclusion, NOTE, func) ===
rules = [
    (["a", "b", "C"], "c", "c = sqrt(a² + b² - 2ab*cos(C))",
        lambda vals: math.sqrt(vals["a"]**2 + vals["b"]**2 - 2*vals["a"]*vals["b"]*math.cos(math.radians(vals["C"])))),

    (["a", "b", "ma"], "c", "c = sqrt(2a² + 2b² - 4ma²)",
        lambda vals: math.sqrt(2*vals["a"]**2 + 2*vals["b"]**2 - 4*vals["ma"]**2)),

    (["a", "b", "mb"], "c", "c = sqrt(2a² + 2b² - 4mb²)",
        lambda vals: math.sqrt(2*vals["a"]**2 + 2*vals["b"]**2 - 4*vals["mb"]**2)),

    (["A", "B"], "C", "C = 180° - A - B",
        lambda vals: 180 - vals["A"] - vals["B"]),

    (["a", "hc"], "B", "B = arcsin(a*sin(C)/c) (dùng đường cao hc)", None),

    (["b", "hc"], "A", "A = arcsin(b*sin(C)/c) (dùng đường cao hc)", None),

    (["a", "R"], "A", "A = arcsin(a/(2R))",
        lambda vals: math.degrees(math.asin(vals["a"]/(2*vals["R"])))),

    (["b", "R"], "B", "B = arcsin(b/(2R))",
        lambda vals: math.degrees(math.asin(vals["b"]/(2*vals["R"])))),

    (["a", "b", "c"], "P", "P = a + b + c",
        lambda vals: vals["a"] + vals["b"] + vals["c"]),

    (["a", "b", "C"], "p", "p = (a+b+c)/2", None),

    (["a", "b", "C"], "mc", "mc = 0.5*sqrt(2a² + 2b² - c²)", None),

    (["a", "ha"], "S", "S = 0.5*a*ha",
        lambda vals: 0.5*vals["a"]*vals["ha"]),

    (["A", "B", "C"], "S", "S = 0.5*a*b*sin(C)", None),

    (["a", "b", "c", "p"], "S", "S = sqrt(p(p-a)(p-b)(p-c)) (Heron)",
        lambda vals: math.sqrt(vals["p"]*(vals["p"]-vals["a"])*(vals["p"]-vals["b"])*(vals["p"]-vals["c"]))),

    (["b", "S"], "hb", "hb = 2S/b",
        lambda vals: 2*vals["S"]/vals["b"]),

    (["S", "p"], "r", "r = S/p",
        lambda vals: vals["S"]/vals["p"])
]

# === HÀM TÌM LUẬT CẦN THIẾT ===
def find_relevant_rules(rules, GT, KL):
    needed = set()
    to_prove = set(KL)
    changed = True
    while changed:
        changed = False
        for i, (prem, concl, note, func) in enumerate(rules, 1):
            if concl in to_prove and i not in needed:
                needed.add(i)
                to_prove.update(prem)
                changed = True
    return needed

# === HÀM VẼ FPG (Facts Precedence Graph) ===
def draw_fpg(rules, GT, KL, show_only_relevant=True):
    relevant_rule_ids = find_relevant_rules(rules, GT, KL)
    G = nx.DiGraph()

    for i, (premises, conclusion, note, func) in enumerate(rules, start=1):
        if show_only_relevant and i not in relevant_rule_ids:
            continue
        for p in premises:
            G.add_edge(p, conclusion, rule=i)

    all_nodes = list(G.nodes())
    colors = []
    for node in all_nodes:
        if node in GT:
            colors.append("#8da0cb")  # giả thiết
        elif node in KL:
            colors.append("#fc8d62")  # kết luận
        else:
            colors.append("#a6d854")  # trung gian

    pos = nx.shell_layout(G)
    plt.figure(figsize=(11, 8))
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=1300, edgecolors="black")
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Vẽ cạnh có mũi tên rõ ràng
    nx.draw_networkx_edges(
        G,
        pos,
        arrowstyle='-|>',
        arrows=True,
        arrowsize=25,          # 👈 tăng kích thước mũi tên
        edge_color="gray",
        width=2,
        connectionstyle='arc3,rad=0.05'  # 👈 bo cong nhẹ để dễ nhìn
    )

    edge_labels = {(u, v): f"R{d['rule']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    title = "Facts Precedence Graph (FPG)"
    if show_only_relevant:
        title += " – Luật liên quan"
    plt.title(title, fontsize=14, fontweight="bold")
    plt.axis("off")
    plt.show()


# === CHẠY DEMO ===
GT = ["a", "b", "c"]
KL = ["r"]
draw_fpg(rules, GT, KL, show_only_relevant=True)