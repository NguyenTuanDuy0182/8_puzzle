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
        self.start_label = tk.Label(self.left, text='Nhập trạng thái ban đầu (0 là ô trống):', fg='white', bg='#0f1720', font=self.font_label)
        self.start_label.pack(anchor='w')
        self.start_var = tk.StringVar(value='283164705')
        self.start_entry = tk.Entry(self.left, textvariable=self.start_var, width=20, font=self.font_entry)
        self.start_entry.pack(pady=6, fill='x')
        self.start_entry.bind('<Return>', lambda e: self.on_start_enter())

        self.random_btn = tk.Button(self.left, text='Ngẫu nhiên', command=self.on_random_start, bg='#0b1220', fg='white', font=self.font_button)
        self.random_btn.pack(pady=(0, 10), fill='x')

        self.goal_label = tk.Label(self.left, text='Nhập trạng thái đích:', fg='white', bg='#0f1720', font=self.font_label)
        self.goal_label.pack(anchor='w')
        self.goal_var = tk.StringVar(value='123804765')
        self.goal_entry = tk.Entry(self.left, textvariable=self.goal_var, width=20, font=self.font_entry)
        self.goal_entry.pack(pady=6, fill='x')
        self.goal_entry.bind('<Return>', lambda e: self.on_goal_enter())

        tk.Label(self.left, text='Chọn thuật toán:', fg='white', bg='#0f1720', font=self.font_label).pack(anchor='w')
        self.algo = ttk.Combobox(self.left, values=['BFS', 'DFS', 'IDFS', 'Greedy', 'A*', 'Belief State', 'Belief State (2 Goals)', 'Part Belief State', 'AND-OR', 'UCS', 'Simple Hill Climbing', 'Steepest Ascent Hill Climbing', 'Stochastic Hill Climbing', 'Random Restart Hill Climbing', 'Simulated Annealing', 'Local Beam Search'], state='readonly', width=17, font=self.font_entry)
        self.algo.set('BFS')
        self.algo.pack(pady=6, fill='x')
        self.algo.bind('<<ComboboxSelected>>', lambda e: self.on_algo_change())

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
        self.cost_label = tk.Label(self.info_frame, text='Tổng chi phí (g): -', fg='white', bg='#0f1720', font=self.font_label)
        self.cost_label.pack(anchor='w')
        self.visited_label = tk.Label(self.info_frame, text='Số trạng thái đã duyệt: -', fg='white', bg='#0f1720', font=self.font_label)
        self.visited_label.pack(anchor='w')
        self.belief_label = tk.Label(self.center, text='', fg='#ffd166', bg='#0f1720', font=self.font_label, justify='left', anchor='w')
        self.belief_label.pack(anchor='w', pady=(4, 0))

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

        # Thanh chỉnh tốc độ animation (ms / bước)
        self.anim_delay_ms = tk.IntVar(value=500)
        self.speed_frame = tk.Frame(self.right, bg='#0f1720')
        self.speed_frame.pack(pady=(0, 8), fill='x')
        tk.Label(
            self.speed_frame,
            text='Tốc độ animation (ms/bước):',
            fg='white',
            bg='#0f1720',
            font=self.font_label,
        ).pack(anchor='w')
        self.speed_scale = tk.Scale(
            self.speed_frame,
            from_=1000,
            to=50,
            orient='horizontal',
            variable=self.anim_delay_ms,
            resolution=10,
            showvalue=True,
            bg='#0f1720',
            fg='white',
            troughcolor='#0b1220',
            highlightthickness=0,
            bd=0,
            font=self.font_label,
        )
        self.speed_scale.pack(fill='x')

        # Trạng thái animation
        self.solution = []
        self.current_index = 0
        self.animating = False
        self.visited_count = None
        self.belief_mode = False
        self.belief_2_goals_mode = False
        self.part_belief_mode = False

        self.update_grid(tuple(range(1,9))+ (0,))
        self.on_algo_change()

    def update_grid(self, state):
        for i, val in enumerate(state):
            b = self.tiles[i]
            if val == 0:
                b.config(text='', bg='#0b1220')
            else:
                b.config(text=str(val), bg='#1287d6')

    def on_algo_change(self):
        algo = self.algo.get()
        self.belief_mode = algo == 'Belief State'
        self.belief_2_goals_mode = algo == 'Belief State (2 Goals)'
        self.part_belief_mode = algo == 'Part Belief State'

        if self.belief_mode:
            self.start_label.config(text='Trạng thái ban đầu: tự sinh từ goal')
            self.start_entry.config(state='disabled')
            self.random_btn.config(state='disabled')
            self.goal_label.config(text='Nhập trạng thái đích:')
            self.goal_entry.config(state='normal')
            self.belief_label.config(text='Sẽ sinh 2 trạng thái niềm tin và giải cả hai về cùng goal.')
        elif self.belief_2_goals_mode:
            self.start_label.config(text='Trạng thái ban đầu: tự sinh')
            self.start_entry.config(state='disabled')
            self.random_btn.config(state='disabled')
            self.goal_label.config(text='Trạng thái đích: tự sinh')
            self.goal_entry.config(state='disabled')
            self.belief_label.config(text='Sẽ tự sinh S1, S2 (khác nhau) và G1, G2 (khác nhau).')
        elif self.part_belief_mode:
            self.start_label.config(text='Nhập S_pattern (0 là wildcard):')
            self.start_entry.config(state='normal')
            self.random_btn.config(state='disabled')
            self.goal_label.config(text='Nhập G_pattern (0 là wildcard):')
            self.goal_entry.config(state='normal')
            self.belief_label.config(text='Giải đưa S1, S2 khớp với S_pattern về cùng một đích G1 hoặc G2 khớp với G_pattern.')
            # Prefill mẫu để dễ kiểm thử
            if len(self.start_var.get()) != 9 or ',' in self.start_var.get() or self.start_var.get() == '283164705':
                self.start_var.set('860000000')
            if len(self.goal_var.get()) != 9 or ',' in self.goal_var.get() or self.goal_var.get() == '123804765':
                self.goal_var.set('123000000')
        else:
            self.start_label.config(text='Nhập trạng thái ban đầu (0 là ô trống):')
            self.start_entry.config(state='normal')
            self.random_btn.config(state='normal')
            self.goal_label.config(text='Nhập trạng thái đích:')
            self.goal_entry.config(state='normal')
            self.belief_label.config(text='')

    def on_solve(self):
        try:
            if self.belief_2_goals_mode:
                # Lấy base_goal từ goal_var hiện tại làm cơ sở sinh các trạng thái
                try:
                    goal = self.controller.parse_state(self.goal_var.get().split(',')[0].strip())
                except ValueError:
                    goal = (1, 2, 3, 8, 0, 4, 7, 6, 5) # Mặc định
                start = None
            elif self.part_belief_mode:
                def parse_pattern(raw: str) -> tuple[int, ...]:
                    s = raw.strip()
                    if len(s) != 9 or not all(ch.isdigit() for ch in s):
                        raise ValueError("Pattern phải gồm 9 chữ số 0-8, ví dụ: 860000000")
                    state = tuple(int(ch) for ch in s)
                    non_zeros = [x for x in state if x != 0]
                    if len(non_zeros) != len(set(non_zeros)):
                        raise ValueError("Các ô đã biết trong Pattern không được trùng nhau.")
                    return state
                start = parse_pattern(self.start_var.get())
                goal = parse_pattern(self.goal_var.get())
            else:
                goal = self.controller.parse_state(self.goal_var.get())
                if self.belief_mode:
                    start = None
                else:
                    start = self.controller.parse_state(self.start_var.get())
        except ValueError as e:
            messagebox.showerror('Lỗi', str(e))
            return
        if not self.belief_mode and not self.belief_2_goals_mode and not self.part_belief_mode and not self.controller.is_solvable(start, goal):
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
        self.cost_label.config(text='Tổng chi phí (g): -')
        self.visited_label.config(text='Số trạng thái đã duyệt: -')
        thread = threading.Thread(target=self.run_solver, args=(start, goal, algo), daemon=True)
        thread.start()

    def on_start_enter(self):
        if self.belief_mode or self.belief_2_goals_mode or self.part_belief_mode:
            return
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
        self.cost_label.config(text='Tổng chi phí (g): -')
        self.visited_label.config(text='Số trạng thái đã duyệt: -')
        self.prev_btn.config(state='normal')
        self.next_btn.config(state='normal')
        # Tải state lên lưới ngay
        self.update_grid(state)

    def on_goal_enter(self):
        if self.belief_2_goals_mode or self.part_belief_mode:
            self.animating = False
            self.solution = []
            self.current_index = 0
            self.steps_text.delete('1.0', 'end')
            self.time_label.config(text='Thời gian chạy: -')
            self.steps_label.config(text='Số bước: -')
            self.cost_label.config(text='Tổng chi phí (g): -')
            self.visited_label.config(text='Số trạng thái đã duyệt: -')
            self.update_grid(tuple(range(1, 9)) + (0,))
            return
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
        self.cost_label.config(text='Tổng chi phí (g): -')
        self.visited_label.config(text='Số trạng thái đã duyệt: -')
        if self.belief_mode:
            self.start_var.set('')
            self.update_grid(tuple(range(1, 9)) + (0,))

    def on_random_start(self):
        """Sinh state bắt đầu ngẫu nhiên (đảm bảo solvable theo goal hiện tại)."""
        if self.belief_mode or self.belief_2_goals_mode or self.part_belief_mode:
            return
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
            if algo == 'Belief State':
                result = self.controller.solve_belief_state(goal)
                if result.path1 is None or result.path2 is None:
                    raise ValueError('Không tìm thấy lời giải cho một trong hai trạng thái niềm tin.')
                self.root.after(0, lambda: self.on_belief_solution_found(result))
                return
            elif algo == 'Belief State (2 Goals)':
                result = self.controller.solve_belief_state_same_goal_auto(goal)
                if result.path1 is None or result.path2 is None:
                    raise ValueError('Không tìm thấy lời giải để S1 và S2 cùng hội tụ về G1 hoặc G2.')
                self.root.after(0, lambda: self.on_belief_solution_found(result))
                return
            elif algo == 'Part Belief State':
                result = self.controller.solve_part_belief_state(start, goal)
                if result.path1 is None or result.path2 is None:
                    raise ValueError('Không tìm thấy lời giải để S1 và S2 cùng hội tụ về G1 hoặc G2.')
                self.root.after(0, lambda: self.on_belief_solution_found(result))
                return
            path, duration, visited_count, total_cost = self.controller.solve(start, goal, algo)
        except Exception as e:
            import traceback
            traceback.print_exc()
            path, duration, visited_count, total_cost = None, 0.0, None, None
        if path is None:
            self.root.after(0, lambda: messagebox.showinfo('Kết quả', 'Không tìm thấy lời giải.'))
            def _unlock():
                self.solve_btn.config(state='normal')
                if not self.belief_mode and not self.belief_2_goals_mode and not self.part_belief_mode:
                    self.start_entry.config(state='normal')
                self.goal_entry.config(state='normal')
                self.algo.config(state='readonly')
                self.on_algo_change()
            self.root.after(0, _unlock)
            return
        self.solution = path
        self.visited_count = visited_count
        self.current_index = 0
        self.root.after(0, lambda: self.on_solution_found(duration, total_cost))

    def on_belief_solution_found(self, result):
        self.time_label.config(text=f'Thời gian chạy: {result.duration:.3f}s')
        self.steps_label.config(text=f'Số bước đồng bộ: {len(result.moves)}')
        self.cost_label.config(text=f'Tổng chi phí (g): {result.total_cost}')
        self.visited_label.config(text=f'Số trạng thái đã duyệt: {result.visited_count}')
        
        if self.belief_2_goals_mode or self.part_belief_mode:
            self.belief_label.config(
                text=f'S1: {"".join(str(x) for x in result.start1)}  |  S2: {"".join(str(x) for x in result.start2)}\nG1: {"".join(str(x) for x in result.goals[0])}  |  G2: {"".join(str(x) for x in result.goals[1])}'
            )
            self.start_var.set(f'{"".join(str(x) for x in result.start1)}, {"".join(str(x) for x in result.start2)}')
            self.goal_var.set(f'{"".join(str(x) for x in result.goals[0])}, {"".join(str(x) for x in result.goals[1])}')
        else:
            self.belief_label.config(
                text=f'State 1: {"".join(str(x) for x in result.start1)}\nState 2: {"".join(str(x) for x in result.start2)}'
            )
            self.start_var.set(''.join(str(x) for x in result.start1))

        self.update_grid(result.start1)
        self.steps_text.delete('1.0', 'end')
        self.steps_text.insert('end', ' '.join(result.moves))
        self.solve_btn.config(state='normal')
        self.goal_entry.config(state='normal')
        self.algo.config(state='readonly')
        
        if self.belief_mode:
            self.start_label.config(text='Trạng thái ban đầu: tự sinh từ goal')
            self.start_entry.config(state='disabled')
            self.random_btn.config(state='disabled')
            self.goal_entry.config(state='normal')
        elif self.belief_2_goals_mode:
            self.start_label.config(text='Trạng thái ban đầu: tự sinh')
            self.start_entry.config(state='disabled')
            self.random_btn.config(state='disabled')
            self.goal_label.config(text='Trạng thái đích: tự sinh')
            self.goal_entry.config(state='disabled')
        elif self.part_belief_mode:
            self.start_label.config(text='Nhập S_pattern (0 là wildcard):')
            self.start_entry.config(state='normal')
            self.random_btn.config(state='disabled')
            self.goal_label.config(text='Nhập G_pattern (0 là wildcard):')
            self.goal_entry.config(state='normal')
            
        self.solution = result.path1 or []
        self.visited_count = result.visited_count
        self.current_index = 0
        self.start_animation()

    def on_solution_found(self, duration, total_cost):
        self.time_label.config(text=f'Thời gian chạy: {duration:.3f}s')
        self.steps_label.config(text=f'Số bước: {len(self.solution)-1}')
        if total_cost is None:
            self.cost_label.config(text='Tổng chi phí (g): -')
        else:
            self.cost_label.config(text=f'Tổng chi phí (g): {total_cost}')
        if self.visited_count is None:
            self.visited_label.config(text='Số trạng thái đã duyệt: -')
        else:
            self.visited_label.config(text=f'Số trạng thái đã duyệt: {self.visited_count}')
        moves = self.controller.path_to_moves(self.solution)
        # Hiển thị bước dạng U/D/L/R
        self.steps_text.insert('end', ' '.join(moves))
        self.update_grid(self.solution[0])
        self.solve_btn.config(state='normal')
        if not self.belief_mode:
            self.start_entry.config(state='normal')
        self.goal_entry.config(state='normal')
        self.algo.config(state='readonly')
        self.on_algo_change()
        # Tự chạy animation theo lời giải
        self.start_animation()

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

    def start_animation(self):
        if not self.solution:
            return
        self.animating = True
        # Tắt nút điều hướng thủ công khi đang animate
        self.prev_btn.config(state='disabled')
        self.next_btn.config(state='disabled')
        self.current_index = 0
        # Đảm bảo lưới đang hiển thị state ban đầu
        self.update_grid(self.solution[self.current_index])
        delay = max(10, int(self.anim_delay_ms.get()))
        self.root.after(delay, self.animate_next)

    def animate_next(self):
        if not self.animating:
            return
        if self.current_index < len(self.solution)-1:
            self.current_index += 1
            self.update_grid(self.solution[self.current_index])
            delay = max(10, int(self.anim_delay_ms.get()))
            self.root.after(delay, self.animate_next)
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