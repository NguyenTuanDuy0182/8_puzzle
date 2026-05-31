from __future__ import annotations

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
	"""Value(state) dùng trong Hill Climbing.

	Ở đây Value chính là h(n) = Manhattan.
	Value càng nhỏ càng tốt.
	"""
	return manhattan_distance(state, goal)


def simple_hill_climbing(start: State, goal: State, *, max_iterations: int = 10_000) -> State:
	"""Simple Hill Climbing (first-improvement) cho 8-puzzle.

	Thuật toán:
	- Ở mỗi vòng lặp, sinh các trạng thái lân cận của Current_State
	- Duyệt theo thứ tự sinh; gặp trạng thái ĐẦU TIÊN có Value tốt hơn thì nhảy sang nó
	- Nếu không có lân cận nào tốt hơn => dừng, trả về Current_State (có thể là local optimum)

	Args:
		start: trạng thái bắt đầu
		goal: trạng thái đích (dùng để tính Manhattan)
		max_iterations: chặn an toàn (thực tế thường dừng sớm vì Value giảm nghiêm ngặt)
	"""
	current_state = start
	current_value = _value(current_state, goal)

	for _ in range(max_iterations):
		improved = False

		for next_state in neighbors(current_state):
			next_value = _value(next_state, goal)
			if next_value < current_value:
				current_state = next_state
				current_value = next_value
				improved = True
				break

		if not improved:
			return current_state

	return current_state


def simple_hill_climbing_with_stats(
	start: State, goal: State, *, max_iterations: int = 10_000
) -> tuple[List[State], int]:
	"""Biến thể trả về path và số lượng state đã đánh giá heuristic.

	Returns:
		(path, visited_count)
	"""
	current_state = start
	current_value = _value(current_state, goal)
	path: List[State] = [start]
	visited_count = 1  # đã tính Value(start)

	for _ in range(max_iterations):
		improved = False

		for next_state in neighbors(current_state):
			visited_count += 1
			next_value = _value(next_state, goal)
			if next_value < current_value:
				current_state = next_state
				current_value = next_value
				path.append(next_state)
				improved = True
				break

		if not improved:
			return path, visited_count

	return path, visited_count
