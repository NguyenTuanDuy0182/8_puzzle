from __future__ import annotations

import random
from typing import Iterable, List, Tuple


State = Tuple[int, int, int, int, int, int, int, int, int]


def neighbors(state: State) -> Iterable[State]:
	"""Sinh các trạng thái lân cận bằng cách di chuyển ô trống (0).

	Thứ tự sinh giống các module khác trong repo: U, D, L, R.
	"""
	zero = state.index(0)
	x, y = divmod(zero, 3)

	deltas = [
		(-1, 0),
		(1, 0),
		(0, -1),
		(0, 1),
	]

	for dx, dy in deltas:
		nx, ny = x + dx, y + dy
		if 0 <= nx < 3 and 0 <= ny < 3:
			nidx = nx * 3 + ny
			lst = list(state)
			lst[zero], lst[nidx] = lst[nidx], lst[zero]
			yield tuple(lst)  # type: ignore[return-value]


def manhattan_distance(state: State, goal: State, *, include_blank: bool = False) -> int:
	"""Heuristic Manhattan cho 8-puzzle.

	Mặc định không tính ô trống (0).
	"""
	goal_pos = {value: divmod(i, 3) for i, value in enumerate(goal)}
	dist = 0
	for i, value in enumerate(state):
		if value == 0 and not include_blank:
			continue
		x, y = divmod(i, 3)
		gx, gy = goal_pos[value]
		dist += abs(x - gx) + abs(y - gy)
	return dist


def _value(state: State, goal: State) -> int:
	"""Value(STATE) dùng trong Stochastic Hill Climbing.

	Value ở đây đúng bằng Manhattan distance.
	Value càng nhỏ càng tốt.
	"""
	return manhattan_distance(state, goal)


def stochastic_hill_climbing(
	start: State,
	goal: State,
	*,
	max_iterations: int = 50_000,
	rng: random.Random | None = None,
) -> State:
	"""Stochastic Hill Climbing cho 8-puzzle.

	Theo pseudo-code:
	- Sinh tất cả trạng thái lân cận của Current_State
	- Better_Neighbors = các lân cận có Value >= Value(Current_State)
	- Chọn ngẫu nhiên một trạng thái trong Better_Neighbors
	- Nếu Better_Neighbors rỗng => dừng tại local optimum/plateau

	Ghi chú: Do cho phép bước "không xấu hơn" (>=), thuật toán có thể lặp trên plateau.
	`max_iterations` dùng để chặn an toàn.
	"""
	rng = rng or random.Random()
	current_state = start
	current_value = _value(current_state, goal)

	for _ in range(max_iterations):
		if current_state == goal:
			return current_state

		better_neighbors: List[State] = []
		for nb in neighbors(current_state):
			nb_value = _value(nb, goal)
			if nb_value <= current_value:
				better_neighbors.append(nb)

		if not better_neighbors:
			return current_state

		next_state = rng.choice(better_neighbors)
		current_state = next_state
		current_value = _value(current_state, goal)

	return current_state


def stochastic_hill_climbing_with_stats(
	start: State,
	goal: State,
	*,
	max_iterations: int = 50_000,
	rng: random.Random | None = None,
) -> tuple[List[State], int]:
	"""Biến thể trả về path và số lượng state đã đánh giá Value."""
	rng = rng or random.Random()
	current_state = start
	current_value = _value(current_state, goal)
	path: List[State] = [start]
	visited_count = 1  # đã tính Value(start)

	for _ in range(max_iterations):
		if current_state == goal:
			return path, visited_count

		better_neighbors: List[State] = []
		for nb in neighbors(current_state):
			visited_count += 1
			nb_value = _value(nb, goal)
			if nb_value <= current_value:
				better_neighbors.append(nb)

		if not better_neighbors:
			return path, visited_count

		next_state = rng.choice(better_neighbors)
		current_state = next_state
		current_value = _value(current_state, goal)
		path.append(current_state)

	return path, visited_count
