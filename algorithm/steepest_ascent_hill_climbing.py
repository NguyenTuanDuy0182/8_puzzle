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
	"""Value dùng cho Steepest-Ascent.

	Pseudo-code chọn trạng thái lân cận có Value LỚN NHẤT.
	Trong khi Manhattan h(n) thì CÀNG NHỎ CÀNG TỐT.

	=> Dùng Value = -h để tối đa hoá Value tương đương tối thiểu hoá Manhattan.
	"""
	return -manhattan_distance(state, goal)


def steepest_ascent_hill_climbing(
	start: State, goal: State, *, max_iterations: int = 10_000
) -> State:
	"""Steepest-Ascent Hill Climbing cho 8-puzzle (chọn best trong tất cả lân cận).

	Thuật toán:
	- Sinh tất cả lân cận của Current_State
	- Best_State = lân cận có Value lớn nhất
	- Nếu Value(Best_State) <= Value(Current_State) => dừng (local optimum/plateau)
	- Ngược lại Current_State = Best_State và lặp

	Lưu ý: do Value = -Manhattan và chỉ nhận bước cải thiện nghiêm ngặt,
	thuật toán thường sẽ dừng sớm (Manhattan là số nguyên không âm).
	"""
	current_state = start
	current_value = _value(current_state, goal)

	for _ in range(max_iterations):
		best_state = None
		best_value = current_value

		for next_state in neighbors(current_state):
			next_value = _value(next_state, goal)
			if next_value > best_value:
				best_state = next_state
				best_value = next_value

		if best_state is None or best_value <= current_value:
			return current_state

		current_state = best_state
		current_value = best_value

	return current_state


def steepest_ascent_hill_climbing_with_stats(
	start: State, goal: State, *, max_iterations: int = 10_000
) -> tuple[List[State], int]:
	"""Biến thể trả về path và số lượng state đã đánh giá Value."""
	current_state = start
	current_value = _value(current_state, goal)
	path: List[State] = [start]
	visited_count = 1  # đã tính Value(start)

	for _ in range(max_iterations):
		best_state = None
		best_value = current_value

		for next_state in neighbors(current_state):
			visited_count += 1
			next_value = _value(next_state, goal)
			if next_value > best_value:
				best_state = next_state
				best_value = next_value

		if best_state is None or best_value <= current_value:
			return path, visited_count

		current_state = best_state
		current_value = best_value
		path.append(current_state)

	return path, visited_count
