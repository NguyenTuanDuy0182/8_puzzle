"""Controller + phần glue logic cho UI Tkinter của bài 8-puzzle.

- UI giữ trong main.py
- Thuật toán tìm kiếm (BFS/DFS) giữ trong algorithm/

Module này phụ trách:
- Parse/validate state nhập vào
- Kiểm tra solvable với goal bất kỳ
- Đổi path -> chuỗi bước U/D/L/R
- Sinh state bắt đầu ngẫu nhiên
- Chọn solver và đo thời gian chạy
"""

from __future__ import annotations

import random
import time
from typing import List, Optional, Sequence, Tuple

from algorithm import bfs as bfs_module
from algorithm import dfs as dfs_module
from algorithm import a_star as a_star_module
from algorithm import greedy as greedy_module
from algorithm import idfs as idfs_module
from algorithm import ucs as ucs_module
from algorithm.bfs import neighbors as _neighbors

State = Tuple[int, int, int, int, int, int, int, int, int]


class PuzzleController:
    @staticmethod
    def parse_state(raw: str) -> State:
        s = raw.strip()
        if len(s) != 9 or not all(ch.isdigit() for ch in s):
            raise ValueError("Trạng thái phải gồm 9 chữ số 0-8, ví dụ: 012345678")
        state: State = tuple(int(ch) for ch in s)  # type: ignore[assignment]
        if set(state) != set(range(9)):
            raise ValueError("Trạng thái phải là hoán vị của 0..8 (không trùng, không thiếu).")
        return state

    @staticmethod
    def inversion_parity(state: Sequence[int]) -> int:
        arr = [x for x in state if x != 0]
        inv = 0
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] > arr[j]:
                    inv += 1
        return inv % 2

    @classmethod
    def is_solvable(cls, start: Sequence[int], goal: Sequence[int]) -> bool:
        """Với puzzle 3x3: solvable khi parity nghịch thế (inversion) của start == goal."""
        return cls.inversion_parity(start) == cls.inversion_parity(goal)

    @staticmethod
    def path_to_moves(path: Sequence[Sequence[int]]) -> List[str]:
        """Đổi path (các state liên tiếp) thành bước di chuyển của ô trống: U/D/L/R."""
        if not path or len(path) < 2:
            return []
        moves: List[str] = []
        for a, b in zip(path, path[1:]):
            ia = a.index(0)
            ib = b.index(0)
            d = ib - ia
            if d == -3:
                moves.append("U")
            elif d == 3:
                moves.append("D")
            elif d == -1:
                moves.append("L")
            elif d == 1:
                moves.append("R")
            else:
                moves.append("?")
        return moves

    @staticmethod
    def random_start(goal: State, steps: int = 60, rng: random.Random | None = None) -> State:
        """Sinh state bắt đầu ngẫu nhiên bằng random-walk từ goal."""
        rng = rng or random.Random()
        state: State = goal
        last: Optional[State] = None
        for _ in range(steps):
            nbs = list(_neighbors(state))
            if last is not None and len(nbs) > 1:
                nbs2 = [s for s in nbs if s != last]
                nbs = nbs2 or nbs
            nxt = rng.choice(nbs)
            last, state = state, nxt
        return state

    @staticmethod
    def solve(start: State, goal: State, algo_name: str) -> tuple[Optional[List[State]], float, int, int]:
        """Chạy solver theo lựa chọn.

        Returns:
            (path, thời_gian_giây, visited_count, total_path_cost)

        Ghi chú path cost (g(n)) đang dùng trong project này:
            cost(state) = số ô khác goal (mặc định không tính ô trống 0)
            g(start) = 0
            g(child) = g(parent) + cost(child_state)
        """
        t0 = time.time()
        if algo_name == "BFS":
            path, visited_count = bfs_module.bfs_with_stats(start, goal)
            total_cost = ucs_module.path_cost(path, goal, include_blank=True) if path else 0
        elif algo_name == "DFS":
            path, visited_count = dfs_module.dfs_with_stats(start, goal)
            total_cost = ucs_module.path_cost(path, goal, include_blank=True) if path else 0
        elif algo_name == "IDFS":
            path, visited_count = idfs_module.idfs_with_stats(start, goal)
            total_cost = ucs_module.path_cost(path, goal, include_blank=True) if path else 0
        elif algo_name == "Greedy":
            path, visited_count = greedy_module.greedy_with_stats(start, goal)
            total_cost = ucs_module.path_cost(path, goal, include_blank=True) if path else 0
        elif algo_name in ("A*", "AStar"):
            path, visited_count, g_goal = a_star_module.a_star_with_stats(start, goal)
            total_cost = g_goal if path else 0
        elif algo_name == "UCS":
            path, visited_count, total_cost = ucs_module.ucs_with_stats(start, goal, include_blank=True)
        else:
            raise ValueError("Thuật toán không hợp lệ. Chỉ hỗ trợ BFS/DFS/IDFS/Greedy/A*/UCS.")
        t1 = time.time()
        return path, (t1 - t0), visited_count, total_cost
