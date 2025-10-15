import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

DATA_DIR = os.path.dirname(__file__)
RULES_FILE = os.path.join(DATA_DIR, 'rules.json')
EVENTS_FILE = os.path.join(DATA_DIR, 'events.json')


def load_rules():
    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def load_events():
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Hệ cơ sở tri thức - GUI ')
        self.geometry('800x500')

        # Left frame: controls
        left = ttk.Frame(self, padding=10)
        left.pack(side='left', fill='y')

        ttk.Label(left, text='Chức năng :').pack(pady=(0, 10))
        buttons = [
            ('Nhập luật', self.not_impl),
            ('Sửa luật', self.not_impl),
            ('Xóa luật', self.not_impl),
            ('Vẽ đồ thị FPG', self.not_impl),
            ('Vẽ đồ thị RPG', self.not_impl),
            ('Suy diễn TIẾN', self.not_impl),
            ('Suy diễn LÙI', self.not_impl),
        ]
        for (t, cmd) in buttons:
            ttk.Button(left, text=t, width=20, command=cmd).pack(pady=4)

        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=5)

        # Right frame: display rules/events
        right = ttk.Frame(self, padding=10)
        right.pack(side='left', fill='both', expand=True)

        ttk.Label(right, text='Luật ').pack(anchor='w')
        self.rules_box = tk.Text(right, height=12, wrap='none')
        self.rules_box.pack(fill='x', pady=(0, 10))

        ttk.Label(right, text='Sự kiện ').pack(anchor='w')
        self.events_box = tk.Text(right, height=6, wrap='none')
        self.events_box.pack(fill='x', pady=(0, 10))

        ttk.Button(right, text='Làm mới', command=self.refresh).pack(anchor='e')

        self.refresh()

    def not_impl(self):
        messagebox.showinfo('Chưa triển khai', 'Chức năng này chưa được triển khai trong GUI skeleton.')

    def refresh(self):
        rules = load_rules()
        events = load_events()
        self.rules_box.delete('1.0', tk.END)
        for r in rules:
            self.rules_box.insert(tk.END, f"ID {r.get('id')} : {r.get('antecedent')} -> {r.get('consequent')} (min={r.get('min')},max={r.get('max')})\n")
        self.events_box.delete('1.0', tk.END)
        for e in events:
            self.events_box.insert(tk.END, f"- {e}\n")


def run():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    run()
