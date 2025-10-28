"""
--------------------------------------------------------------
Chức năng:
1. Hỗ trợ hai kiểu agenda: STACK (LIFO) và QUEUE (FIFO)
2. Hỗ trợ chọn luật theo chỉ số nhỏ nhất (min) hoặc lớn nhất (max)
3. Xây dựng và vẽ đồ thị FPG (Forward Proof Graph) và RPG (Reverse Proof Graph)
--------------------------------------------------------------
Yêu cầu thư viện: networkx, matplotlib
Cài đặt bằng:
    pip install networkx matplotlib
--------------------------------------------------------------
"""

from collections import deque
import networkx as nx
import matplotlib.pyplot as plt

# ==================== CÁC HÀM CHÍNH ==================== #

def tim_luat_kha_dung(facts, rules):
    """Trả về danh sách chỉ số các luật có thể áp dụng (premises có trong facts)."""
    ket_qua = []
    for i, (premises, conclusion) in enumerate(rules):
        if premises.issubset(facts) and conclusion not in facts:
            ket_qua.append(i)
    return ket_qua


def chon_luat(danh_sach, kieu_chon):
    """Chọn luật theo kiểu: min / max / first."""
    if not danh_sach:
        return None
    if kieu_chon == 'min':
        return min(danh_sach)
    if kieu_chon == 'max':
        return max(danh_sach)
    return danh_sach[0]


def suy_dien_tien(facts, rules, goal=None, agenda='queue', rule_select='min', verbose=False):
    """
    Suy diễn tiến dựa trên tập luật và fact ban đầu.

    Tham số:
        facts: danh sách fact ban đầu
        rules: danh sách (premises, conclusion)
        goal: fact cần đạt (nếu có)
        agenda: 'queue' (FIFO) hoặc 'stack' (LIFO)
        rule_select: 'min', 'max', hoặc 'first'
        verbose: in ra quá trình suy diễn
    """

    facts = set(facts)

    # Khởi tạo agenda
    if agenda == 'queue':
        container = deque()
        push = container.append
        pop = container.popleft
    elif agenda == 'stack':
        container = []
        push = container.append
        pop = container.pop
    else:
        raise ValueError("agenda phải là 'queue' hoặc 'stack'")

    # Thêm luật khả dụng ban đầu
    for i in tim_luat_kha_dung(facts, rules):
        push(i)

    da_xet = set()

    while container:
        # Chọn luật phù hợp
        if rule_select in ('min', 'max'):
            danh_sach = list(container)
            idx = chon_luat(danh_sach, rule_select)
            container.remove(idx)
        else:
            idx = pop()

        premises, conclusion = rules[idx]

        # Áp dụng luật nếu có thể
        if premises.issubset(facts) and conclusion not in facts:
            facts.add(conclusion)
            if verbose:
                print(f"✔ Suy ra: {conclusion} (từ luật #{idx})")

            # Kiểm tra goal
            if goal and conclusion == goal:
                print("🎯 Đạt mục tiêu!")
                return True, facts

            # Thêm luật mới khả dụng
            for j in tim_luat_kha_dung(facts, rules):
                if j not in da_xet:
                    push(j)
                    da_xet.add(j)

    return (goal in facts if goal else None), facts


# ==================== HỖ TRỢ MIN/MAX ==================== #

def chi_so_min(facts, rules):
    ds = tim_luat_kha_dung(set(facts), rules)
    return min(ds) if ds else None

def chi_so_max(facts, rules):
    ds = tim_luat_kha_dung(set(facts), rules)
    return max(ds) if ds else None


# ==================== ĐỒ THỊ FPG / RPG ==================== #

def tao_do_thi_FPG(rules):
    G = nx.DiGraph()
    for i, (premises, conclusion) in enumerate(rules):
        rule_node = f"R{i}"
        G.add_node(rule_node, type='rule')
        G.add_node(conclusion, type='fact')
        G.add_edge(rule_node, conclusion)
        for p in premises:
            G.add_node(p, type='fact')
            G.add_edge(p, rule_node)
    return G


def tao_do_thi_RPG(rules):
    return tao_do_thi_FPG(rules).reverse(copy=True)


def ve_do_thi(G, title='Đồ thị Suy diễn', filename=None):
    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G, seed=42)
    facts = [n for n, d in G.nodes(data=True) if d.get('type') == 'fact']
    rules = [n for n, d in G.nodes(data=True) if d.get('type') == 'rule']
    nx.draw_networkx_nodes(G, pos, nodelist=facts, node_color='lightblue', node_shape='o')
    nx.draw_networkx_nodes(G, pos, nodelist=rules, node_color='lightgreen', node_shape='s')
    nx.draw_networkx_edges(G, pos, arrows=True)
    nx.draw_networkx_labels(G, pos)
    plt.title(title)
    plt.axis('off')
    if filename:
        plt.savefig(filename, bbox_inches='tight')
    plt.show()


# ==================== CHẠY THỬ ==================== #
if __name__ == '__main__':
    rules = [
        (set(['A', 'B']), 'C'),
        (set(['C']), 'D'),
        (set(['E']), 'B'),
        (set(['D', 'E']), 'X')
    ]
    facts = ['A', 'E']

    print('--- Suy diễn tiến (agenda=queue, rule_select=min) ---')
    ket_qua, tap_fact = suy_dien_tien(facts, rules, goal='X', agenda='queue', rule_select='min', verbose=True)
    print('Kết quả:', ket_qua)
    print('Tập fact cuối cùng:', tap_fact)

    print('\nChỉ số luật nhỏ nhất:', chi_so_min(tap_fact, rules))
    print('Chỉ số luật lớn nhất:', chi_so_max(tap_fact, rules))

    print('\n--- Đồ thị FPG và RPG ---')
    FPG = tao_do_thi_FPG(rules)
    RPG = tao_do_thi_RPG(rules)
    ve_do_thi(FPG, 'Forward Proof Graph (FPG)')
    ve_do_thi(RPG, 'Reverse Proof Graph (RPG)')
