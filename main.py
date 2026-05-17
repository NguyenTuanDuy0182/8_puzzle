import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys

from controller.puzzle_controller import PuzzleController


# main.py chỉ chứa UI + nối sự kiện.
# Toàn bộ logic không thuộc UI nằm trong controller/ và thuật toán nằm trong algorithm/.


class PuzzleUI:
    def __init__(self, root):
        self.root = root
        self.controller = PuzzleController()
        root.title('8-Puzzle Solver')
        root.configure(bg='#0f1720')

        # Font/kích thước: tự điều chỉnh theo Windows scaling (vd 125% -> tk scaling ~ 1.25)
        try:
            self.ui_scale = float(root.tk.call('tk', 'scaling'))
        except Exception:
            self.ui_scale = 1.0

        def _fs(pt: float) -> int:
            # Tk đã tự scale theo DPI; để tránh “tràn” ở 125%+, ta scale-down cỡ chữ.
            return max(8, int(round(pt / max(1.0, self.ui_scale))))

        self.font_title = ('Helvetica', _fs(18), 'bold')
        self.font_label = ('Helvetica', _fs(11))
        self.font_entry = ('Consolas', _fs(12))
        self.font_button = ('Helvetica', _fs(11), 'bold')
        self.font_tile = ('Helvetica', _fs(20), 'bold')
        self.font_steps = ('Consolas', _fs(12))

        style = ttk.Style(root)
        style.configure('TCombobox', font=self.font_entry)

        self.mainframe = tk.Frame(root, bg='#0f1720')
        # Giảm padding một chút để đỡ tràn khi DPI scaling cao
        self.mainframe.pack(fill='both', expand=True, padx=12, pady=12)

        # Chia layout 3 vùng: trái (điều khiển), giữa (thông tin), phải (lưới)
        self.left = tk.Frame(self.mainframe, bg='#0f1720', width=260)
        self.center = tk.Frame(self.mainframe, bg='#0f1720')
        self.right = tk.Frame(self.mainframe, bg='#0f1720', width=340)

        # Giữ cố định bề rộng vùng trái/phải
        self.left.pack_propagate(False)
        self.right.pack_propagate(False)

        self.left.pack(side='left', fill='y', padx=(0,16))
        self.center.pack(side='left', fill='both', expand=True)
        self.right.pack(side='right', fill='y')

        # Cụm điều khiển bên trái
        tk.Label(self.left, text='Nhập trạng thái ban đầu (0 là ô trống):', fg='white', bg='#0f1720', font=self.font_label).pack(anchor='w')
        self.start_var = tk.StringVar(value='283164705')
        self.start_entry = tk.Entry(self.left, textvariable=self.start_var, width=20, font=self.font_entry)
        self.start_entry.pack(pady=6, fill='x')
        self.start_entry.bind('<Return>', lambda e: self.on_start_enter())

        self.random_btn = tk.Button(self.left, text='Ngẫu nhiên', command=self.on_random_start, bg='#0b1220', fg='white', font=self.font_button)
        self.random_btn.pack(pady=(0, 10), fill='x')

        tk.Label(self.left, text='Nhập trạng thái đích:', fg='white', bg='#0f1720', font=self.font_label).pack(anchor='w')
        self.goal_var = tk.StringVar(value='123804765')
        self.goal_entry = tk.Entry(self.left, textvariable=self.goal_var, width=20, font=self.font_entry)
        self.goal_entry.pack(pady=6, fill='x')
        self.goal_entry.bind('<Return>', lambda e: self.on_goal_enter())

        tk.Label(self.left, text='Chọn thuật toán:', fg='white', bg='#0f1720', font=self.font_label).pack(anchor='w')
        self.algo = ttk.Combobox(self.left, values=['BFS', 'DFS'], state='readonly', width=17, font=self.font_entry)
        self.algo.set('BFS')
        self.algo.pack(pady=6, fill='x')

        self.solve_btn = tk.Button(self.left, text='Giải', command=self.on_solve, bg='#0b1220', fg='white', font=self.font_button)
        self.solve_btn.pack(pady=10, fill='x')

        # Khu vực giữa: thông tin lời giải
        tk.Label(self.center, text='Đáp án', fg='#3dd0ff', bg='#0f1720', font=self.font_title).pack(anchor='w')
        self.info_frame = tk.Frame(self.center, bg='#0f1720')
        self.info_frame.pack(anchor='nw', pady=8)
        self.time_label = tk.Label(self.info_frame, text='Thời gian chạy: -', fg='white', bg='#0f1720', font=self.font_label)
        self.time_label.pack(anchor='w')
        self.steps_label = tk.Label(self.info_frame, text='Số bước: -', fg='white', bg='#0f1720', font=self.font_label)
        self.steps_label.pack(anchor='w')
        self.visited_label = tk.Label(self.info_frame, text='Số trạng thái đã duyệt: -', fg='white', bg='#0f1720', font=self.font_label)
        self.visited_label.pack(anchor='w')

        tk.Label(self.center, text='Các bước:', fg='white', bg='#0f1720', font=self.font_label).pack(anchor='w', pady=(8,0))
        # Đặt width/height nhỏ để widget không “đòi” kích thước quá lớn theo DPI.
        self.steps_text = tk.Text(self.center, height=1, width=1, bg='#071025', fg='white', font=self.font_steps, wrap='word')
        self.steps_text.pack(pady=6, fill='both', expand=True)

        # Bên phải: lưới 9 ô
        self.grid_frame = tk.Frame(self.right, bg='#0f1720')
        self.grid_frame.pack(pady=(0, 8))
        self.tiles = []
        for r in range(3):
            for c in range(3):
                lbl = tk.Label(
                    self.grid_frame,
                    text='',
                    width=6,
                    height=3,
                    bg='#1f2937',
                    fg='white',
                    font=self.font_tile,
                    relief='flat'
                )
                lbl.grid(row=r, column=c, padx=4, pady=4)
                self.tiles.append(lbl)

        self.nav_frame = tk.Frame(self.right, bg='#0f1720')
        self.nav_frame.pack(pady=8)
        self.prev_btn = tk.Button(self.nav_frame, text='Prev', command=self.prev_step, bg='#0b1220', fg='white', font=self.font_button, width=9)
        self.next_btn = tk.Button(self.nav_frame, text='Next', command=self.next_step, bg='#0b1220', fg='white', font=self.font_button, width=9)
        self.prev_btn.grid(row=0, column=0, padx=6)
        self.next_btn.grid(row=0, column=1, padx=6)

        # Trạng thái animation
        self.solution = []
        self.current_index = 0
        self.animating = False
        self.visited_count = None

        self.update_grid(tuple(range(1,9))+ (0,))

    def update_grid(self, state):
        for i, val in enumerate(state):
            b = self.tiles[i]
            if val == 0:
                b.config(text='', bg='#0b1220')
            else:
                b.config(text=str(val), bg='#1287d6')

    def on_solve(self):
        try:
            start = self.controller.parse_state(self.start_var.get())
            goal = self.controller.parse_state(self.goal_var.get())
        except ValueError as e:
            messagebox.showerror('Lỗi', str(e))
            return
        if not self.controller.is_solvable(start, goal):
            messagebox.showerror('Lỗi', 'Trạng thái không có lời giải cho trạng thái đích này (không thể giải được).')
            return

        # Khoá input khi đang solve/animate để tránh lệch giữa goal hiển thị và kết quả tính toán
        self.start_entry.config(state='disabled')
        self.goal_entry.config(state='disabled')
        self.algo.config(state='disabled')
        self.solve_btn.config(state='disabled')

        algo = self.algo.get()
        self.steps_text.delete('1.0', 'end')
        self.visited_count = None
        self.visited_label.config(text='Số trạng thái đã duyệt: -')
        thread = threading.Thread(target=self.run_solver, args=(start, goal, algo), daemon=True)
        thread.start()

    def on_start_enter(self):
        try:
            state = self.controller.parse_state(self.start_var.get())
        except ValueError:
            messagebox.showerror('Lỗi', 'Trạng thái bắt đầu không hợp lệ.')
            return
        # Dừng animation đang chạy và reset lời giải
        self.animating = False
        self.solution = []
        self.current_index = 0
        self.visited_count = None
        self.visited_label.config(text='Số trạng thái đã duyệt: -')
        self.prev_btn.config(state='normal')
        self.next_btn.config(state='normal')
        # Tải state lên lưới ngay
        self.update_grid(state)

    def on_goal_enter(self):
        try:
            _ = self.controller.parse_state(self.goal_var.get())
        except ValueError:
            messagebox.showerror('Lỗi', 'Trạng thái đích không hợp lệ.')
            return
        # Reset lời giải cũ để tránh so sánh step cũ với goal mới
        self.animating = False
        self.solution = []
        self.current_index = 0
        self.steps_text.delete('1.0', 'end')
        self.time_label.config(text='Thời gian chạy: -')
        self.steps_label.config(text='Số bước: -')
        self.visited_label.config(text='Số trạng thái đã duyệt: -')

    def on_random_start(self):
        """Sinh state bắt đầu ngẫu nhiên (đảm bảo solvable theo goal hiện tại)."""
        try:
            goal = self.controller.parse_state(self.goal_var.get())
        except ValueError:
            messagebox.showerror('Lỗi', 'Trạng thái đích không hợp lệ.')
            return

        state = self.controller.random_start(goal, steps=60)

        self.start_var.set(''.join(str(x) for x in state))
        self.on_start_enter()

    def run_solver(self, start, goal, algo):
        try:
            path, duration, visited_count = self.controller.solve(start, goal, algo)
        except Exception:
            path, duration, visited_count = None, 0.0, None
        if path is None:
            self.root.after(0, lambda: messagebox.showinfo('Kết quả', 'Không tìm thấy lời giải.'))
            def _unlock():
                self.solve_btn.config(state='normal')
                self.start_entry.config(state='normal')
                self.goal_entry.config(state='normal')
                self.algo.config(state='readonly')
            self.root.after(0, _unlock)
            return
        self.solution = path
        self.visited_count = visited_count
        self.current_index = 0
        self.root.after(0, lambda: self.on_solution_found(duration))

    def on_solution_found(self, duration):
        self.time_label.config(text=f'Thời gian chạy: {duration:.3f}s')
        self.steps_label.config(text=f'Số bước: {len(self.solution)-1}')
        if self.visited_count is None:
            self.visited_label.config(text='Số trạng thái đã duyệt: -')
        else:
            self.visited_label.config(text=f'Số trạng thái đã duyệt: {self.visited_count}')
        moves = self.controller.path_to_moves(self.solution)
        # Hiển thị bước dạng U/D/L/R
        self.steps_text.insert('end', ' '.join(moves))
        self.update_grid(self.solution[0])
        self.solve_btn.config(state='normal')
        self.start_entry.config(state='normal')
        self.goal_entry.config(state='normal')
        self.algo.config(state='readonly')
        # Tự chạy animation theo lời giải
        self.start_animation(delay=500)

    def prev_step(self):
        if not self.solution: return
        if self.current_index > 0:
            self.current_index -= 1
            self.update_grid(self.solution[self.current_index])

    def next_step(self):
        if not self.solution: return
        if self.current_index < len(self.solution)-1:
            self.current_index += 1
            self.update_grid(self.solution[self.current_index])

    def start_animation(self, delay=500):
        if not self.solution:
            return
        self.animating = True
        # Tắt nút điều hướng thủ công khi đang animate
        self.prev_btn.config(state='disabled')
        self.next_btn.config(state='disabled')
        self.current_index = 0
        # Đảm bảo lưới đang hiển thị state ban đầu
        self.update_grid(self.solution[self.current_index])
        self.root.after(delay, lambda: self.animate_next(delay))

    def animate_next(self, delay):
        if not self.animating:
            return
        if self.current_index < len(self.solution)-1:
            self.current_index += 1
            self.update_grid(self.solution[self.current_index])
            self.root.after(delay, lambda: self.animate_next(delay))
        else:
            # Kết thúc
            self.animating = False
            self.prev_btn.config(state='normal')
            self.next_btn.config(state='normal')


def main():
    root = tk.Tk()
    width, height = 1080, 608
    root.geometry(f'{width}x{height}')
    root.minsize(width, height)
    root.maxsize(width, height)
    root.resizable(False, False)

    if sys.platform == 'win32':
        try:
            import ctypes

            GWL_STYLE = -16
            WS_MAXIMIZEBOX = 0x00010000
            WS_SIZEBOX = 0x00040000

            root.update_idletasks()
            hwnd = root.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style = style & ~WS_MAXIMIZEBOX & ~WS_SIZEBOX
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
            ctypes.windll.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0027)
        except Exception:
            pass

    app = PuzzleUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()