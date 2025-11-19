import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import re
from pathlib import Path

class InferenceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Suy diễn Tri thức")
        self.root.geometry("1200x800")
        
        self.rules_file = "rules.txt"
        self.rules = {}
        self.GT = set()
        self.KL = set()
        
        self.create_menu()
        self.create_notebook()
        self.load_rules()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Mở file luật", command=self.open_file)
        file_menu.add_command(label="Lưu file luật", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit)
        
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Quản lý luật
        self.tab_rules = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rules, text="1. Quản lý Luật")
        self.create_rules_tab()
        
        # Tab 2: Đồ thị FPG
        self.tab_fpg = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fpg, text="2. Đồ thị FPG")
        self.create_fpg_tab()
        
        # Tab 3: Đồ thị RPG
        self.tab_rpg = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rpg, text="3. Đồ thị RPG")
        self.create_rpg_tab()
        
        # Tab 4: Suy diễn Tiến
        self.tab_forward = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_forward, text="4. Suy diễn Tiến")
        self.create_forward_tab()
        
        # Tab 5: Suy diễn Lùi
        self.tab_backward = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_backward, text="5. Suy diễn Lùi")
        self.create_backward_tab()
    
    # ============ TAB 1: QUẢN LÝ LUẬT ============
    def create_rules_tab(self):
        # Frame trái: Danh sách luật
        left_frame = ttk.LabelFrame(self.tab_rules, text="Danh sách Luật", padding=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        self.rules_text = scrolledtext.ScrolledText(left_frame, width=50, height=30)
        self.rules_text.pack(fill='both', expand=True)
        
        # Frame phải: Thêm/Sửa/Xóa
        right_frame = ttk.LabelFrame(self.tab_rules, text="Chỉnh sửa", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="Số thứ tự:").grid(row=0, column=0, sticky='w', pady=5)
        self.rule_id_entry = ttk.Entry(right_frame, width=10)
        self.rule_id_entry.grid(row=0, column=1, sticky='w', pady=5)
        
        ttk.Label(right_frame, text="Vế trái (vd: a^b^C):").grid(row=1, column=0, sticky='w', pady=5)
        self.rule_left_entry = ttk.Entry(right_frame, width=30)
        self.rule_left_entry.grid(row=1, column=1, sticky='w', pady=5)
        
        ttk.Label(right_frame, text="Vế phải (vd: c):").grid(row=2, column=0, sticky='w', pady=5)
        self.rule_right_entry = ttk.Entry(right_frame, width=30)
        self.rule_right_entry.grid(row=2, column=1, sticky='w', pady=5)
        
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Thêm Luật", command=self.add_rule).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Sửa Luật", command=self.edit_rule).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Xóa Luật", command=self.delete_rule).pack(side='left', padx=5)
        
        ttk.Separator(right_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(right_frame, text="Giả thiết (GT):").grid(row=5, column=0, sticky='w', pady=5)
        self.gt_entry = ttk.Entry(right_frame, width=30)
        self.gt_entry.grid(row=5, column=1, sticky='w', pady=5)
        
        ttk.Label(right_frame, text="Kết luận (KL):").grid(row=6, column=0, sticky='w', pady=5)
        self.kl_entry = ttk.Entry(right_frame, width=30)
        self.kl_entry.grid(row=6, column=1, sticky='w', pady=5)
        
        ttk.Button(right_frame, text="Cập nhật GT/KL", command=self.update_gt_kl).grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(right_frame, text="Tải lại từ file", command=self.load_rules).grid(row=8, column=0, columnspan=2, pady=5)
    
    def load_rules(self):
        """Đọc luật từ file"""
        self.rules = {}
        self.GT = set()
        self.KL = set()
        
        if not Path(self.rules_file).exists():
            return
        
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
        
        for line in lines:
            if '->' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    idx = parts[0]
                    rule = parts[1]
                    left, right = map(str.strip, rule.split('->'))
                    self.rules[idx] = {'left': left, 'right': right}
            elif line.lower().startswith('gt'):
                gt_str = line.split('=')[1].strip() if '=' in line else ''
                self.GT = set(re.findall(r"[a-zA-Z0-9]+", gt_str))
            elif line.lower().startswith('kl'):
                kl_str = line.split('=')[1].strip() if '=' in line else ''
                self.KL = set(re.findall(r"[a-zA-Z0-9]+", kl_str))
        
        self.display_rules()
    
    def display_rules(self):
        """Hiển thị luật lên giao diện"""
        self.rules_text.delete(1.0, tk.END)
        for idx, rule in sorted(self.rules.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            self.rules_text.insert(tk.END, f"{idx}\t{rule['left']}->{rule['right']}\n")
        
        if self.GT:
            self.rules_text.insert(tk.END, f"\nGT = {', '.join(sorted(self.GT))}\n")
        if self.KL:
            self.rules_text.insert(tk.END, f"KL = {', '.join(sorted(self.KL))}\n")
        
        self.gt_entry.delete(0, tk.END)
        self.gt_entry.insert(0, ', '.join(sorted(self.GT)))
        
        self.kl_entry.delete(0, tk.END)
        self.kl_entry.insert(0, ', '.join(sorted(self.KL)))
    
    def save_to_file(self):
        """Lưu luật vào file"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            for idx, rule in sorted(self.rules.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                f.write(f"{idx}\t{rule['left']}->{rule['right']}\n")
            if self.GT:
                f.write(f"GT = {', '.join(sorted(self.GT))}\n")
            if self.KL:
                f.write(f"KL = {', '.join(sorted(self.KL))}\n")
    
    def add_rule(self):
        idx = self.rule_id_entry.get().strip()
        left = self.rule_left_entry.get().strip()
        right = self.rule_right_entry.get().strip()
        
        if not idx or not left or not right:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return
        
        self.rules[idx] = {'left': left, 'right': right}
        self.save_to_file()
        self.display_rules()
        messagebox.showinfo("Thành công", f"Đã thêm luật {idx}")
    
    def edit_rule(self):
        idx = self.rule_id_entry.get().strip()
        left = self.rule_left_entry.get().strip()
        right = self.rule_right_entry.get().strip()
        
        if idx not in self.rules:
            messagebox.showwarning("Cảnh báo", f"Không tìm thấy luật {idx}!")
            return
        
        self.rules[idx] = {'left': left, 'right': right}
        self.save_to_file()
        self.display_rules()
        messagebox.showinfo("Thành công", f"Đã sửa luật {idx}")
    
    def delete_rule(self):
        idx = self.rule_id_entry.get().strip()
        
        if idx not in self.rules:
            messagebox.showwarning("Cảnh báo", f"Không tìm thấy luật {idx}!")
            return
        
        # Xóa luật
        del self.rules[idx]
        
        # Tái đánh số thứ tự các luật
        try:
            # Chuyển số thứ tự hiện tại sang dạng số để sắp xếp
            numeric_keys = []
            non_numeric_keys = []
            
            for key in self.rules.keys():
                if key.isdigit():
                    numeric_keys.append(int(key))
                else:
                    non_numeric_keys.append(key)
            
            numeric_keys.sort()
            
            # Tạo dict mới với số thứ tự liên tiếp
            new_rules = {}
            for new_idx, old_idx in enumerate(numeric_keys, 1):
                new_rules[str(new_idx)] = self.rules[str(old_idx)]
            
            # Thêm lại những luật không phải số
            for key in non_numeric_keys:
                new_rules[key] = self.rules[key]
            
            self.rules = new_rules
        except:
            pass
        
        self.save_to_file()
        self.display_rules()
        messagebox.showinfo("Thành công", f"Đã xóa luật {idx} và cập nhật lại số thứ tự")
    
    def update_gt_kl(self):
        gt_str = self.gt_entry.get().strip()
        kl_str = self.kl_entry.get().strip()
        
        self.GT = set(re.findall(r"[a-zA-Z0-9]+", gt_str))
        self.KL = set(re.findall(r"[a-zA-Z0-9]+", kl_str))
        
        self.save_to_file()
        self.display_rules()
        messagebox.showinfo("Thành công", "Đã cập nhật GT và KL")
    
    def open_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filename:
            self.rules_file = filename
            self.load_rules()
    
    def save_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            self.rules_file = filename
            self.save_to_file()
    
    # ============ TAB 2: ĐỒ THỊ FPG ============
    def create_fpg_tab(self):
        control_frame = ttk.Frame(self.tab_fpg)
        control_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Vẽ đồ thị FPG", command=self.draw_fpg).pack(side='left', padx=5)
        
        self.fpg_canvas_frame = ttk.Frame(self.tab_fpg)
        self.fpg_canvas_frame.pack(fill='both', expand=True)
    
    def draw_fpg(self):
        """Vẽ đồ thị FPG (Facts Precedence Graph)"""
        for widget in self.fpg_canvas_frame.winfo_children():
            widget.destroy()
        
        G = nx.DiGraph()
        
        for idx, rule in self.rules.items():
            left_items = re.split(r'\^', rule['left'])
            left_items = [i.strip() for i in left_items if i.strip()]
            right = rule['right']
            
            for item in left_items:
                G.add_edge(item, right, rule=f"r{idx}")
        
        fig, ax = plt.subplots(figsize=(10, 7))
        pos = nx.shell_layout(G)
        
        colors = []
        for node in G.nodes():
            if node in self.GT:
                colors.append("#8da0cb") # Giả thiết
            elif node in self.KL:
                colors.append("#fc8d62") # Kết luận
            else:
                colors.append("#a6d854") # Trung gian
        
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=1500, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
        nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=20, width=2, ax=ax)
        
        edge_labels = {(u, v): d['rule'] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)
        
        ax.set_title("Facts Precedence Graph (FPG)", fontsize=14, fontweight="bold")
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, self.fpg_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    # ============ TAB 3: ĐỒ THỊ RPG ============
    def create_rpg_tab(self):
        control_frame = ttk.Frame(self.tab_rpg)
        control_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Vẽ đồ thị RPG", command=self.draw_rpg).pack(side='left', padx=5)
        
        self.rpg_canvas_frame = ttk.Frame(self.tab_rpg)
        self.rpg_canvas_frame.pack(fill='both', expand=True)
    
    def draw_rpg(self):
        """Vẽ đồ thị RPG (Rules Precedence Graph)"""
        for widget in self.rpg_canvas_frame.winfo_children():
            widget.destroy()
        
        G = nx.DiGraph()
        
        # Xây dựng đồ thị phụ thuộc giữa các luật
        for idx_i, rule_i in self.rules.items():
            for idx_j, rule_j in self.rules.items():
                if idx_i != idx_j:
                    left_j = re.split(r'\^', rule_j['left'])
                    left_j = [i.strip() for i in left_j if i.strip()]
                    if rule_i['right'] in left_j:
                        G.add_edge(f"r{idx_i}", f"r{idx_j}", label=rule_i['right'])
        
        # Phân loại R_GT và R_KL
        R_GT = set()
        R_KL = set()
        
        for idx, rule in self.rules.items():
            left_items = re.split(r'\^', rule['left'])
            left_items = set([i.strip() for i in left_items if i.strip()])
            
            if left_items.issubset(self.GT):
                R_GT.add(f"r{idx}")
            if rule['right'] in self.KL:
                R_KL.add(f"r{idx}")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        pos = nx.shell_layout(G)
        
        colors = []
        for node in G.nodes():
            if node in R_GT:
                colors.append("#FF5722") # Luật xuất phát từ GT
            elif node in R_KL:
                colors.append("#4CAF50") # Luật dẫn đến KL
            else:
                colors.append("#2196F3") # Luật trung gian
        
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=2000, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", font_color='white', ax=ax)
        nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=20, width=2, ax=ax)
        
        edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)
        
        ax.set_title("Rules Precedence Graph (RPG)", fontsize=14, fontweight="bold")
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, self.rpg_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    # ============ FPG/RPG HELPERS ============
    def build_fpg(self, rules):
        """Xây dựng đồ thị FPG (Facts Precedence Graph) từ dict luật.
        rules: dict mapping idx -> (premises_set, conclusion)
        """
        G = nx.DiGraph()
        for idx, (premises, conclusion) in rules.items():
            for p in premises:
                G.add_edge(p, conclusion, rule=f"r{idx}")
        return G

    def build_rpg(self, rules):
        """Xây dựng đồ thị RPG (Rules Precedence Graph) từ dict luật.
        rules: dict mapping idx -> (premises_set, conclusion)
        """
        G = nx.DiGraph()
        for idx1, (prem1, concl1) in rules.items():
            for idx2, (prem2, concl2) in rules.items():
                if idx1 != idx2 and concl1 in prem2:
                    G.add_edge(idx1, idx2)
        return G

    def d_fpg(self, G, start, end):
        try:
            return nx.shortest_path_length(G, start, end)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float('inf')

    def heuristic_fpg(self, G, premises, goal):
        """Tính h(r,GT) = max{d(f, goal) | f in premises} (the smaller the better).
        Nếu mọi d là inf thì trả về inf.
        """
        if not premises or not goal:
            return float('inf')
        vals = []
        for f in premises:
            vals.append(self.d_fpg(G, f, goal))
        return max(vals) if vals else float('inf')

    def heuristic_rpg(self, G, rule_idx):
        """Tính h(r) = số lượng luật phụ thuộc vào r trong RPG.
        Luật càng ít ảnh hưởng đến luật khác thì càng tốt (nhỏ).
        """
        try:
            return len(nx.descendants(G, rule_idx))
        except:
            return 0
    
    # ============ TAB 4: SUY DIỄN TIẾN ============
    def create_forward_tab(self):
        control_frame = ttk.LabelFrame(self.tab_forward, text="Tùy chọn", padding=10)
        control_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Label(control_frame, text="Chiến lược:").grid(row=0, column=0, padx=5)
        self.fwd_strategy_var = tk.StringVar(value="min")
        ttk.Radiobutton(control_frame, text="Min", variable=self.fwd_strategy_var, value="min").grid(row=0, column=1)
        ttk.Radiobutton(control_frame, text="Max", variable=self.fwd_strategy_var, value="max").grid(row=0, column=2)
        ttk.Radiobutton(control_frame, text="FPG", variable=self.fwd_strategy_var, value="fpg").grid(row=0, column=3)
        ttk.Radiobutton(control_frame, text="RPG", variable=self.fwd_strategy_var, value="rpg").grid(row=0, column=4)
        
        ttk.Label(control_frame, text="Tập THOA:").grid(row=1, column=0, padx=5)
        self.fwd_agenda_var = tk.StringVar(value="queue")
        ttk.Radiobutton(control_frame, text="Queue (FIFO)", variable=self.fwd_agenda_var, value="queue").grid(row=1, column=1)
        ttk.Radiobutton(control_frame, text="Stack (LIFO)", variable=self.fwd_agenda_var, value="stack").grid(row=1, column=2)
        
        ttk.Button(control_frame, text="Thực hiện Suy diễn Tiến", command=self.run_forward).grid(row=2, column=0, columnspan=5, pady=10)
        
        self.fwd_result = scrolledtext.ScrolledText(self.tab_forward, height=30)
        self.fwd_result.pack(fill='both', expand=True, padx=5, pady=5)
    
    def run_forward(self):
        """Thực hiện suy diễn tiến"""
        self.fwd_result.delete(1.0, tk.END)
        
        if not self.GT:
            self.fwd_result.insert(tk.END, "❌ Chưa có giả thiết (GT)!\n")
            return
        
        facts = set(self.GT)
        strategy = self.fwd_strategy_var.get()
        agenda_type = self.fwd_agenda_var.get()
        
        # Chuyển đổi rules sang format dict
        rules_dict = {}
        for idx, rule in self.rules.items():
            left_items = re.split(r'\^', rule['left'])
            premises = set([i.strip() for i in left_items if i.strip()])
            rules_dict[idx] = (premises, rule['right'])
        
        # Xây dựng đồ thị FPG/RPG nếu cần
        G_fpg = None
        G_rpg = None
        if strategy == 'fpg':
            G_fpg = self.build_fpg(rules_dict)
        elif strategy == 'rpg':
            G_rpg = self.build_rpg(rules_dict)
        
        self.fwd_result.insert(tk.END, f"=== SUY DIỄN TIẾN ===\n")
        self.fwd_result.insert(tk.END, f"GT ban đầu: {facts}\n")
        self.fwd_result.insert(tk.END, f"Chiến lược: {strategy.upper()}\n")
        self.fwd_result.insert(tk.END, f"Tập THOA: {agenda_type.upper()}\n\n")
        
        # Khởi tạo agenda
        if agenda_type == 'queue':
            container = deque()
            push = container.append
            pop = container.popleft
        else:
            container = []
            push = container.append
            pop = container.pop
        
        # Tìm luật khả dụng ban đầu
        available_rules = []
        for idx, (prem, concl) in rules_dict.items():
            if prem.issubset(facts) and concl not in facts:
                available_rules.append(idx)
        
        for idx in available_rules:
            push(idx)
        
        step = 1
        while container:
            # Chọn luật theo chiến lược
            if strategy == 'min':
                indices = list(container)
                chosen = min(indices, key=lambda x: int(x) if str(x).isdigit() else 0)
                container.remove(chosen)
            elif strategy == 'max':
                indices = list(container)
                chosen = max(indices, key=lambda x: int(x) if str(x).isdigit() else 0)
                container.remove(chosen)
            elif strategy == 'fpg':
                indices = list(container)
                h_values = {}
                for idx in indices:
                    premises, conclusion = rules_dict[idx]
                    h_values[idx] = self.heuristic_fpg(G_fpg, premises, conclusion)
                chosen = min(indices, key=lambda x: h_values.get(x, float('inf')))
                container.remove(chosen)
                self.fwd_result.insert(tk.END, f"  → h values: {h_values}\n")
            elif strategy == 'rpg':
                indices = list(container)
                h_values = {}
                for idx in indices:
                    h_values[idx] = self.heuristic_rpg(G_rpg, idx)
                chosen = min(indices, key=lambda x: h_values.get(x, float('inf')))
                container.remove(chosen)
                self.fwd_result.insert(tk.END, f"  → h(r) values: {h_values}\n")
            else:
                chosen = pop()
            
            premises, conclusion = rules_dict[chosen]
            
            if premises.issubset(facts) and conclusion not in facts:
                facts.add(conclusion)
                self.fwd_result.insert(tk.END, f"Bước {step}: Áp dụng luật r{chosen} ({premises} → {conclusion})\n")
                self.fwd_result.insert(tk.END, f"   Suy ra: {conclusion}\n")
                self.fwd_result.insert(tk.END, f"   Tập facts mới: {facts}\n\n")
                step += 1
                
                # Kiểm tra KL
                if self.KL and conclusion in self.KL:
                    self.fwd_result.insert(tk.END, f"🎯 Đã đạt được kết luận: {conclusion}\n\n")
                
                # Thêm luật mới khả dụng
                for idx, (prem, concl) in rules_dict.items():
                    if prem.issubset(facts) and concl not in facts and idx not in container:
                        push(idx)
        
        self.fwd_result.insert(tk.END, f"\n✅ Tập fact cuối cùng: {facts}\n")
        
        if self.KL:
            achieved = self.KL.intersection(facts)
            if achieved:
                self.fwd_result.insert(tk.END, f"✅ Đã đạt KL: {achieved}\n")
            else:
                self.fwd_result.insert(tk.END, f"❌ Chưa đạt KL: {self.KL}\n")
    
    # ============ TAB 5: SUY DIỄN LÙI ============
    def create_backward_tab(self):
        control_frame = ttk.LabelFrame(self.tab_backward, text="Tùy chọn", padding=10)
        control_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Label(control_frame, text="Chiến lược:").grid(row=0, column=0, padx=5)
        self.bwd_strategy_var = tk.StringVar(value="min")
        ttk.Radiobutton(control_frame, text="Min", variable=self.bwd_strategy_var, value="min").grid(row=0, column=1)
        ttk.Radiobutton(control_frame, text="Max", variable=self.bwd_strategy_var, value="max").grid(row=0, column=2)
        ttk.Radiobutton(control_frame, text="FPG", variable=self.bwd_strategy_var, value="fpg").grid(row=0, column=3)
        
        ttk.Label(control_frame, text="Mục tiêu:").grid(row=1, column=0, padx=5)
        self.bwd_goal_entry = ttk.Entry(control_frame, width=20)
        self.bwd_goal_entry.grid(row=1, column=1, columnspan=2, sticky='w')
        
        ttk.Button(control_frame, text="Thực hiện Suy diễn Lùi", command=self.run_backward).grid(row=2, column=0, columnspan=3, pady=10)
        
        self.bwd_result = scrolledtext.ScrolledText(self.tab_backward, height=30)
        self.bwd_result.pack(fill='both', expand=True, padx=5, pady=5)
    
    def run_backward(self):
        """Thực hiện suy diễn lùi"""
        self.bwd_result.delete(1.0, tk.END)
        
        goal = self.bwd_goal_entry.get().strip()
        if not goal:
            if self.KL:
                goal = next(iter(self.KL))
            else:
                self.bwd_result.insert(tk.END, "❌ Vui lòng nhập mục tiêu hoặc thiết lập KL!\n")
                return
        
        if not self.GT:
            self.bwd_result.insert(tk.END, "❌ Chưa có giả thiết (GT)!\n")
            return
        
        known = set(self.GT)
        strategy = self.bwd_strategy_var.get()
        
        # Chuyển đổi rules
        rules_dict = {}
        for idx, rule in self.rules.items():
            left_items = re.split(r'\^', rule['left'])
            premises = set([i.strip() for i in left_items if i.strip()])
            rules_dict[idx] = (premises, rule['right'])
        
        # Xây dựng đồ thị FPG nếu cần
        G = None
        if strategy == 'fpg':
            G = self.build_fpg(rules_dict)
            self.bwd_result.insert(tk.END, "→ Xây dựng đồ thị FPG...\n")
        
        self.bwd_result.insert(tk.END, f"=== SUY DIỄN LÙI ===\n")
        self.bwd_result.insert(tk.END, f"GT ban đầu: {known}\n")
        self.bwd_result.insert(tk.END, f"Mục tiêu: {goal}\n")
        self.bwd_result.insert(tk.END, f"Chiến lược: {strategy.upper()}\n\n")
        
        result = self.backward_chain(goal, known, rules_dict, strategy, 0, set(), G)
        
        if result:
            self.bwd_result.insert(tk.END, f"\n✅ THÀNH CÔNG: Đã chứng minh được {goal}\n")
        else:
            self.bwd_result.insert(tk.END, f"\n❌ THẤT BẠI: Không thể chứng minh {goal}\n")
    
    def backward_chain(self, goal, known, rules, strategy, depth, used, G=None):
        """Thuật toán suy diễn lùi"""
        indent = "  " * depth
        
        self.bwd_result.insert(tk.END, f"{indent}→ Cần chứng minh: {goal}\n")
        
        if goal in known:
            self.bwd_result.insert(tk.END, f"{indent}  ✓ {goal} đã có trong GT\n")
            return True
        
        # Tìm luật có kết luận là goal
        applicable = [idx for idx, (prem, concl) in rules.items() if concl == goal and idx not in used]
        
        if not applicable:
            self.bwd_result.insert(tk.END, f"{indent}  ✗ Không có luật nào suy ra {goal}\n")
            return False
        
        # Sắp xếp các luật áp dụng được theo chiến lược
        if strategy == 'min':
            sorted_rules = sorted(applicable, key=lambda x: int(x) if str(x).isdigit() else 0)
        elif strategy == 'max':
            sorted_rules = sorted(applicable, key=lambda x: int(x) if str(x).isdigit() else 0, reverse=True)
        elif strategy == 'fpg' and G is not None:
            # Tính h(r,GT) cho từng luật và sắp xếp theo h tăng dần
            h_values = {}
            for r in applicable:
                premises = rules[r][0]
                h_values[r] = self.heuristic_fpg(G, premises, goal)
            
            self.bwd_result.insert(tk.END, f"{indent}→ h(r,GT) values: {h_values}\n")
            sorted_rules = sorted(applicable, key=lambda r: h_values.get(r, float('inf')))
        else:
            sorted_rules = sorted(applicable, key=lambda x: int(x) if str(x).isdigit() else 0)
        
        # Thử từng luật một (Backtracking)
        for r_chosen in sorted_rules:
            premises, conclusion = rules[r_chosen]
            
            self.bwd_result.insert(tk.END, f"{indent}  • Thử luật r{r_chosen}: {premises} → {conclusion}\n")
            
            # Đánh dấu luật đã dùng trong nhánh này
            new_used = used.copy()
            new_used.add(r_chosen)
            
            all_proven = True
            for p in premises:
                if not self.backward_chain(p, known, rules, strategy, depth + 1, new_used, G):
                    all_proven = False
                    self.bwd_result.insert(tk.END, f"{indent}    ✗ Thất bại khi chứng minh tiền đề {p} của r{r_chosen}\n")
                    break
            
            if all_proven:
                self.bwd_result.insert(tk.END, f"{indent}  ✓ Chứng minh thành công {goal} bằng r{r_chosen}\n")
                known.add(goal)
                return True
            else:
                self.bwd_result.insert(tk.END, f"{indent}  ✗ Quay lui từ r{r_chosen}\n")
        
        self.bwd_result.insert(tk.END, f"{indent}✗ Đã thử hết luật, không chứng minh được {goal}\n")
        return False


# ============ CHẠY CHƯƠNG TRÌNH ============
if __name__ == "__main__":
    root = tk.Tk()
    app = InferenceSystem(root)
    root.mainloop()