import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from typing import List, Tuple, Set, Dict, Optional
import re

# plotting
import networkx as nx
import matplotlib.pyplot as plt

DATA_DIR = os.path.dirname(__file__)
RULES_FILE = os.path.join(DATA_DIR, 'rules.json')
EVENTS_FILE = os.path.join(DATA_DIR, 'events.json')
RULES_TXT = os.path.join(DATA_DIR, 'rules.txt')


def load_rules():
    
    # Prefer JSON rules file if present and valid
    try:
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # normalize: ensure list of dicts and integer ids where possible
                if isinstance(data, list):
                    rules = []
                    for r in data:
                        if not isinstance(r, dict):
                            continue
                        rid = r.get('id')
                        try:
                            rid = int(rid) if rid is not None else None
                        except Exception:
                            rid = None
                        # normalize antecedent/consequent to caret-separated strings
                        ants = []
                        cons = []
                        if 'antecedent' in r:
                            ants = [s.strip() for s in re.split(r'\^|,', str(r.get('antecedent') or '')) if s.strip()]
                        if 'consequent' in r:
                            cons = [s.strip() for s in re.split(r'\^|,', str(r.get('consequent') or '')) if s.strip()]
                        rules.append({'id': rid, 'antecedent': '^'.join(ants), 'consequent': '^'.join(cons)})
                    # if all rules have numeric ids, sort by id ascending
                    if all(r.get('id') is not None for r in rules):
                        rules.sort(key=lambda x: x.get('id'))
                    # ensure ids are sequential starting at 1
                    for i, r in enumerate(rules, start=1):
                        r['id'] = i
                    return rules
                else:
                    # unexpected format, fallthrough to other readers
                    pass
    except Exception:
        # fallthrough to try rules.txt
        pass

    # Try rules.txt: first try JSON, otherwise parse legacy text
    if os.path.exists(RULES_TXT):
        txt = open(RULES_TXT, 'r', encoding='utf-8').read()
        # try JSON first
        try:
            return json.loads(txt)
        except Exception:
            rules = []
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                # line may start with an index then whitespace/tab, then rule like a^b->c
                parts = line.split(None, 1)
                if len(parts) == 2:
                    idx_part, rule_part = parts
                else:
                    # maybe no index, take whole line as rule
                    idx_part = None
                    rule_part = parts[0]
                # split antecedent and consequent
                if '->' in rule_part:
                    ant, cons = rule_part.split('->', 1)
                elif '-' in rule_part and '>' in rule_part:
                    ant, cons = rule_part.split('->', 1)
                else:
                    # cannot parse, skip
                    continue
                # normalize separators (allow ^ or ,) into caret-separated strings
                ant_items = [s.strip() for s in re.split(r'\^|,', ant) if s.strip()]
                cons_items = [s.strip() for s in re.split(r'\^|,', cons) if s.strip()]
                try:
                    rid = int(idx_part) if idx_part is not None else None
                except Exception:
                    rid = None
                rule = {
                    'id': rid if rid is not None else (len(rules) + 1),
                    'antecedent': '^'.join(ant_items),
                    'consequent': '^'.join(cons_items)
                }
                rules.append(rule)
            # ensure sequential ids
            for i, r in enumerate(rules, start=1):
                r['id'] = i
            return rules

    return []


def save_rules(rules):
    try:
        # renumber rules sequentially by current list order
        for i, r in enumerate(rules, start=1):
            r['id'] = i

        # write JSON file
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

        # also write a human-readable rules.txt (one rule per line with id)
        try:
            with open(RULES_TXT, 'w', encoding='utf-8') as f:
                for r in rules:
                    ants = [s.strip() for s in re.split(r'\^|,', str(r.get('antecedent') or '')) if s.strip()]
                    cons = [s.strip() for s in re.split(r'\^|,', str(r.get('consequent') or '')) if s.strip()]
                    ant = '^'.join(ants)
                    con = '^'.join(cons)
                    f.write(f"{r.get('id')}\t{ant}->{con}\n")
        except Exception:
            # fallback: also write JSON to rules.txt so load can still parse
            with open(RULES_TXT, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print('Error saving rules:', e)
        return False


def load_events():
    try:
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception:
        return []


def forward_chaining(facts: Set[str], rules: List[Dict], goal: Optional[str] = None, verbose: bool = False,
                     calc: str = 'min', ds_type: str = 'Stack') -> Tuple[bool, Set[str], List[Tuple[str, str]]]:
   
    facts = set(facts)
    trace = []
    changed = True
    # prepare rules as (set(premises), set(consequents))
    proc_rules = []
    for r in rules:
        ants = {s.strip() for s in re.split(r'\^|,', str(r.get('antecedent') or '')) if s.strip()}
        cons = {s.strip() for s in re.split(r'\^|,', str(r.get('consequent') or '')) if s.strip()}
        if ants and cons:
            proc_rules.append((ants, cons, r.get('id')))

    # DS behavior: Stack -> LIFO (use reversed iteration), Queue -> FIFO
    order = list(range(len(proc_rules)))

    while changed:
        changed = False
        for idx in order:
            ants, cons, rid = proc_rules[idx]
            if ants.issubset(facts):
                # fire rule
                new = cons - facts
                if new:
                    for c in new:
                        facts.add(c)
                        trace.append((f'R{rid}', c))
                    changed = True
                    if verbose:
                        print(f"Fire R{rid}: {ants} -> {cons} ; add {new}")
                    if goal and goal in facts:
                        return True, facts, trace
        # for Stack/Queue we could reorder rules but for simplicity we just iterate
        # TODO: implement priority ordering/indices if needed

    if goal is not None:
        return (goal in facts), facts, trace
    return (None, facts, trace)


def backward_chaining(facts: Set[str], rules: List[Dict], goal: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """A simple backward chaining that tries to prove goal by recursively proving premises.
    Returns (proved, proof_chain)
    """
    known = set(facts)
    visited = set()

    # prepare mapping consequent -> list of (antecedents, id)
    cons_map = {}
    for r in rules:
        ants = {s.strip() for s in re.split(r'\^|,', str(r.get('antecedent') or '')) if s.strip()}
        cons = {s.strip() for s in re.split(r'\^|,', str(r.get('consequent') or '')) if s.strip()}
        for c in cons:
            cons_map.setdefault(c, []).append((ants, r.get('id')))

    proof = []

    def prove(x):
        if x in known:
            return True
        if x in visited:
            return False
        visited.add(x)
        for ants, rid in cons_map.get(x, []):
            ok = True
            for a in ants:
                if not prove(a):
                    ok = False
                    break
            if ok:
                proof.append(f'R{rid} -> {x}')
                known.add(x)
                return True
        return False

    res = prove(goal)
    return res, proof


def build_fpg_graph(rules: List[Dict], facts: Set[str], goals: Set[str], only_relevant: bool = True) -> nx.DiGraph:
    G = nx.DiGraph()

    # optionally compute relevant rules using backward reachability from goals
    relevant = set()
    if only_relevant:
        to_prove = set(goals)
        changed = True
        while changed:
            changed = False
            for r in rules:
                cons = {s.strip() for s in str(r.get('consequent') or '').split(',') if s.strip()}
                ants = {s.strip() for s in str(r.get('antecedent') or '').split(',') if s.strip()}
                if cons & to_prove:
                    rid = r.get('id')
                    if rid not in relevant:
                        relevant.add(rid)
                        to_prove.update(ants)
                        changed = True

    for r in rules:
        rid = r.get('id')
        if only_relevant and rid not in relevant:
            continue
        ants = [s.strip() for s in re.split(r'\^|,', str(r.get('antecedent') or '')) if s.strip()]
        cons = [s.strip() for s in re.split(r'\^|,', str(r.get('consequent') or '')) if s.strip()]
        for a in ants:
            for c in cons:
                G.add_edge(a, c, rule=rid)

    # mark node attributes
    for n in G.nodes():
        if n in facts:
            G.nodes[n]['type'] = 'fact'
        elif n in goals:
            G.nodes[n]['type'] = 'goal'
        else:
            G.nodes[n]['type'] = 'derived'

    return G


def draw_graph_matplotlib(G: nx.DiGraph, title: str = 'Graph'):
    if G.number_of_nodes() == 0:
        messagebox.showinfo(title, 'Không có node để vẽ')
        return
    pos = nx.shell_layout(G)
    plt.figure(figsize=(10, 7))
    color_map = []
    for n in G.nodes():
        t = G.nodes[n].get('type')
        if t == 'fact':
            color_map.append('#8da0cb')
        elif t == 'goal':
            color_map.append('#fc8d62')
        else:
            color_map.append('#a6d854')

    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=900, edgecolors='black')
    nx.draw_networkx_labels(G, pos, font_size=10)
    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=20, connectionstyle='arc3,rad=0.05')
    edge_labels = {(u, v): f"R{d['rule']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    plt.title(title)
    plt.axis('off')
    plt.show()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Hệ cơ sở tri thức - GUI (merged)')
        self.geometry('1000x600')

        # left control frame
        left = ttk.Frame(self, padding=10)
        left.pack(side='left', fill='y')

        ttk.Label(left, text='Chức năng:').pack(pady=(0, 10))
        btns = [
            ('Nhập luật', self.add_rule),
            ('Sửa luật', self.edit_rule),
            ('Xóa luật', self.delete_rule),
            ('Nhập/Sửa Sự kiện', self.edit_events),
            ('Vẽ FPG', self.show_fpg_options),
            ('Vẽ RPG', self.show_rpg_options),
            ('Suy diễn TIẾN', lambda: self.open_inference_dialog('TIẾN')),
            ('Suy diễn LÙI', lambda: self.open_inference_dialog('LÙI')),
        ]
        for t, cmd in btns:
            ttk.Button(left, text=t, width=22, command=cmd).pack(pady=4)

        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=6)

        right = ttk.Frame(self, padding=10)
        right.pack(side='left', fill='both', expand=True)

        ttk.Label(right, text='Luật:').pack(anchor='w')
        self.rules_box = tk.Text(right, height=15, wrap='none')
        self.rules_box.pack(fill='x', pady=(0, 10))

        ttk.Label(right, text='Sự kiện (facts):').pack(anchor='w')
        self.events_box = tk.Text(right, height=6, wrap='none')
        self.events_box.pack(fill='x', pady=(0, 10))

        ttk.Button(right, text='Làm mới', command=self.refresh).pack(anchor='e')

        self.refresh()

    # --- Events editor ---
    def edit_events(self):
        events = load_events()
        dlg = tk.Toplevel(self)
        dlg.title('Sự kiện (facts)')
        dlg.transient(self)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill='both', expand=True)
        txt = tk.Text(frm, height=10)
        txt.pack(fill='both', expand=True)
        txt.insert('1.0', '\n'.join(events))

        def on_ok():
            txts = [l.strip() for l in txt.get('1.0', 'end').splitlines() if l.strip()]
            try:
                with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(txts, f, ensure_ascii=False, indent=2)
            except Exception as e:
                messagebox.showerror('Lỗi', f'Không thể lưu sự kiện: {e}')
            dlg.destroy()

        bfrm = ttk.Frame(frm)
        bfrm.pack(pady=6)
        ttk.Button(bfrm, text='OK', command=on_ok).pack(side='left', padx=6)
        ttk.Button(bfrm, text='Hủy', command=dlg.destroy).pack(side='left', padx=6)
        dlg.wait_window()
        self.refresh()

    # --- Inference dialog ---
    def open_inference_dialog(self, direction: str):
        dlg = tk.Toplevel(self)
        dlg.title(f'Suy diễn {direction}')
        dlg.transient(self)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text='Chọn chỉ số:').grid(row=0, column=0, sticky='w')
        calc_var = tk.StringVar(value='min')
        ttk.Radiobutton(frm, text='min', variable=calc_var, value='min').grid(row=0, column=1, sticky='w')
        ttk.Radiobutton(frm, text='max', variable=calc_var, value='max').grid(row=0, column=2, sticky='w')

        ttk.Label(frm, text='Chọn tập thỏa:').grid(row=1, column=0, sticky='w')
        ds_var = tk.StringVar(value='Stack')
        ttk.Radiobutton(frm, text='Stack', variable=ds_var, value='Stack').grid(row=1, column=1, sticky='w')
        ttk.Radiobutton(frm, text='Queue', variable=ds_var, value='Queue').grid(row=1, column=2, sticky='w')

        ttk.Label(frm, text='Nhập facts (dấu phẩy ngăn):').grid(row=2, column=0, sticky='w')
        facts_var = tk.StringVar(value='')
        ttk.Entry(frm, textvariable=facts_var, width=40).grid(row=2, column=1, columnspan=2, sticky='w')

        ttk.Label(frm, text='Nhập goal (nếu có):').grid(row=3, column=0, sticky='w')
        goal_var = tk.StringVar(value='')
        ttk.Entry(frm, textvariable=goal_var, width=40).grid(row=3, column=1, columnspan=2, sticky='w')

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=3, pady=8)

        def on_ok():
            calc = calc_var.get()
            ds = ds_var.get()
            facts_text = facts_var.get().strip()
            facts = {s.strip() for s in facts_text.split(',') if s.strip()} if facts_text else set(load_events())
            goal = goal_var.get().strip() or None
            dlg.destroy()
            self.handle_inference(direction, calc, ds, facts, goal)

        ttk.Button(btns, text='OK', command=on_ok).pack(side='left', padx=6)
        ttk.Button(btns, text='Hủy', command=dlg.destroy).pack(side='left', padx=6)

        dlg.wait_window()

    def handle_inference(self, direction: str, calc: str, ds_type: str, facts: Set[str], goal: Optional[str]):
        rules = load_rules()
        if direction == 'TIẾN' or direction == 'TIEN' or direction == 'TIẾN':
            reached, final_facts, trace = forward_chaining(facts, rules, goal=goal, verbose=False, calc=calc, ds_type=ds_type)
            message = f'Kết quả: goal={reached}\nFacts cuối: {sorted(final_facts)}'
            messagebox.showinfo('Suy diễn TIẾN', message)
            # draw FPG and RPG
            Gf = build_fpg_graph(rules, facts=set(facts), goals=set([goal]) if goal else set(), only_relevant=True)
            draw_graph_matplotlib(Gf, title='FPG (relevant)')
            # RPG: rule precedence graph (rules as nodes, edges if rule A produces facts used by B)
            Gr = nx.DiGraph()
            # add rule nodes
            for r in rules:
                Gr.add_node(f"R{r.get('id')}")
            # build edges
            for a in rules:
                a_id = a.get('id')
                a_cons = {s.strip() for s in str(a.get('consequent') or '').split(',') if s.strip()}
                for b in rules:
                    b_id = b.get('id')
                    b_ants = {s.strip() for s in str(b.get('antecedent') or '').split(',') if s.strip()}
                    if a_cons & b_ants:
                        Gr.add_edge(f"R{a_id}", f"R{b_id}")
            draw_graph_matplotlib(Gr, title='RPG')
        else:
            # backward
            if not goal:
                messagebox.showerror('Lỗi', 'Suy diễn lùi cần nhập goal')
                return
            proved, proof = backward_chaining(facts, rules, goal, verbose=False)
            messagebox.showinfo('Suy diễn LÙI', f'Kết quả: {proved}\nProof: {proof}')
            Gf = build_fpg_graph(rules, facts=set(facts), goals={goal}, only_relevant=True)
            draw_graph_matplotlib(Gf, title='FPG (backward relevant)')

    # --- Graph options dialogs ---
    def show_fpg_options(self):
        rules = load_rules()
        if not rules:
            messagebox.showinfo('FPG', 'Không có luật để vẽ')
            return
        events = load_events()
        facts = set(events)
        # ask for goal(s)
        s = simpledialog.askstring('FPG', 'Nhập goal (hoặc để trống để vẽ tất cả):')
        goals = {s.strip()} if s and s.strip() else set()
        G = build_fpg_graph(rules, facts, goals, only_relevant=bool(goals))
        draw_graph_matplotlib(G, title='FPG')

    def show_rpg_options(self):
        rules = load_rules()
        if not rules:
            messagebox.showinfo('RPG', 'Không có luật để vẽ')
            return
        # build RPG same as in handle_inference
        Gr = nx.DiGraph()
        for r in rules:
            Gr.add_node(f"R{r.get('id')}")
        for a in rules:
            a_id = a.get('id')
            a_cons = {s.strip() for s in str(a.get('consequent') or '').split(',') if s.strip()}
            for b in rules:
                b_id = b.get('id')
                b_ants = {s.strip() for s in str(b.get('antecedent') or '').split(',') if s.strip()}
                if a_cons & b_ants:
                    Gr.add_edge(f"R{a_id}", f"R{b_id}", rule_pair=f"R{a_id}->R{b_id}")
        draw_graph_matplotlib(Gr, title='RPG')

    # --- rule CRUD ---
    def _open_rule_editor(self, title: str, rule: dict = None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.transient(self)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill='both', expand=True)

        # ID is shown but for new rules it will be auto-assigned on save.
        ttk.Label(frm, text='ID:').grid(row=0, column=0, sticky='e')
        id_var = tk.StringVar(value=str(rule.get('id') if rule else ''))
        id_entry = ttk.Entry(frm, textvariable=id_var, state='readonly' if rule else 'disabled')
        id_entry.grid(row=0, column=1, sticky='w')

        ttk.Label(frm, text='Antecedent (comma-separated):').grid(row=1, column=0, sticky='e')
        ant_var = tk.StringVar(value=(rule.get('antecedent') if rule else ''))
        ttk.Entry(frm, textvariable=ant_var, width=40).grid(row=1, column=1, sticky='w')

        ttk.Label(frm, text='Consequent (comma-separated):').grid(row=2, column=0, sticky='e')
        cons_var = tk.StringVar(value=(rule.get('consequent') if rule else ''))
        ttk.Entry(frm, textvariable=cons_var, width=40).grid(row=2, column=1, sticky='w')

        result = {'ok': False, 'rule': None}

        def on_ok():
            antecedent = ant_var.get().strip()
            consequent = cons_var.get().strip()
            if not antecedent or not consequent:
                messagebox.showerror('Lỗi', 'Antecedent và Consequent không được để trống')
                return
            # For new rules, id will be assigned by save_rules (sequential numbering)
            if rule:
                rid = rule.get('id')
            else:
                rid = None
            result['ok'] = True
            result['rule'] = {'id': rid, 'antecedent': antecedent, 'consequent': consequent}
            dlg.destroy()

        b = ttk.Frame(frm)
        b.grid(row=4, column=0, columnspan=2, pady=8)
        ttk.Button(b, text='OK', command=on_ok).pack(side='left', padx=6)
        ttk.Button(b, text='Hủy', command=dlg.destroy).pack(side='left', padx=6)
        dlg.wait_window()
        return result['rule'] if result['ok'] else None

    def add_rule(self):
        new = self._open_rule_editor('Nhập luật mới')
        if not new:
            return
        rules = load_rules()
        # new['id'] will be None for a new rule; save_rules will renumber sequentially
        rules.append(new)
        if save_rules(rules):
            self.refresh()
            messagebox.showinfo('Thành công', 'Đã thêm luật mới')
        else:
            messagebox.showerror('Lỗi', 'Không thể lưu luật')

    def _select_rule_by_id(self, prompt='Chọn ID luật:'):
        rules = load_rules()
        ids = [r.get('id') for r in rules]
        if not ids:
            messagebox.showinfo('Thông báo', 'Không có luật')
            return None
        sid = simpledialog.askstring('Chọn luật', prompt + '\nCác ID hiện có: ' + ','.join(map(str, ids)))
        if not sid:
            return None
        try:
            rid = int(sid)
        except Exception:
            messagebox.showerror('Lỗi', 'ID không hợp lệ')
            return None
        rule = next((r for r in rules if r.get('id') == rid), None)
        if not rule:
            messagebox.showerror('Lỗi', 'Không tìm thấy luật')
            return None
        return rule

    def edit_rule(self):
        rule = self._select_rule_by_id('Nhập ID luật cần sửa:')
        if not rule:
            return
        edited = self._open_rule_editor('Sửa luật', rule=rule)
        if not edited:
            return
        rules = load_rules()
        for i, r in enumerate(rules):
            if r.get('id') == edited['id']:
                rules[i] = edited
                break
        if save_rules(rules):
            self.refresh()
            messagebox.showinfo('Thành công', 'Đã cập nhật luật')
        else:
            messagebox.showerror('Lỗi', 'Không thể lưu luật')

    def delete_rule(self):
        rule = self._select_rule_by_id('Nhập ID luật cần xóa:')
        if not rule:
            return
        if not messagebox.askyesno('Xác nhận', f"Xóa luật ID {rule.get('id')}?"):
            return
        rules = load_rules()
        rules = [r for r in rules if r.get('id') != rule.get('id')]
        if save_rules(rules):
            self.refresh()
            messagebox.showinfo('Thành công', 'Đã xóa luật')
        else:
            messagebox.showerror('Lỗi', 'Không thể lưu luật')

    def refresh(self):
        rules = load_rules()
        events = load_events()
        self.rules_box.delete('1.0', tk.END)
        for r in rules:
            self.rules_box.insert(tk.END, f"ID {r.get('id')} : {r.get('antecedent')} -> {r.get('consequent')}\n")
        self.events_box.delete('1.0', tk.END)
        for e in events:
            self.events_box.insert(tk.END, f"- {e}\n")


def run():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    run()
