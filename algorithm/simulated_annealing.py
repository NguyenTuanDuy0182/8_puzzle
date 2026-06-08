from __future__ import annotations

import math
import random
from typing import Iterable, List, Tuple


State = Tuple[int, int, int, int, int, int, int, int, int]


def neighbors(state: State) -> Iterable[State]:
	"""Sinh các trạng thái lân cận bằng cách di chuyển ô trống (0)."""
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
	"""Value dùng cho Simulated Annealing.

	Giá trị dùng trực tiếp là Manhattan distance: càng nhỏ càng tốt.
	"""
	return manhattan_distance(state, goal)


def simulated_annealing(
	start: State,
	goal: State,
	*,
	t0: float = 100.0,
	tmin: float = 0.1,
	alpha: float = 0.95,
	max_iterations: int = 100_000,
	rng: random.Random | None = None,
) -> State:
	"""Simulated Annealing cho 8-puzzle.

	Pseudo-code tương ứng:
	- Current <- Start
	- T <- T0
	- Lặp khi T > Tmin:
	  - Sinh ngẫu nhiên một láng giềng Next
	  - Nếu Next tốt hơn (Manhattan nhỏ hơn) thì nhận Next
	  - Ngược lại nhận Next với xác suất e^(Delta / T)
	  - Giảm nhiệt độ: T <- alpha * T
	- Trả về Current
	"""
	rng = rng or random.Random()
	current_state = start
	current_value = _value(current_state, goal)
	temperature = t0

	for _ in range(max_iterations):
		if current_state == goal:
			return current_state
		if temperature <= tmin:
			return current_state

		next_state = rng.choice(list(neighbors(current_state)))
		next_value = _value(next_state, goal)
		delta = current_value - next_value

		if delta > 0:
			current_state = next_state
			current_value = next_value
		else:
			if rng.random() < math.exp(delta / temperature):
				current_state = next_state
				current_value = next_value

		temperature *= alpha

	return current_state


def simulated_annealing_with_stats(
	start: State,
	goal: State,
	*,
	t0: float = 100.0,
	tmin: float = 0.1,
	alpha: float = 0.95,
	max_iterations: int = 100_000,
	rng: random.Random | None = None,
) -> tuple[List[State], int]:
	"""Biến thể trả về path và số lượng state đã đánh giá Value."""
	rng = rng or random.Random()
	current_state = start
	current_value = _value(current_state, goal)
	temperature = t0
	path: List[State] = [start]
	visited_count = 1

	for _ in range(max_iterations):
		if current_state == goal:
			return path, visited_count
		if temperature <= tmin:
			return path, visited_count

		neighbors_list = list(neighbors(current_state))
		next_state = rng.choice(neighbors_list)
		visited_count += len(neighbors_list)
		next_value = _value(next_state, goal)
		delta = current_value - next_value

		if delta > 0:
			current_state = next_state
			current_value = next_value
			path.append(current_state)
		else:
			if rng.random() < math.exp(delta / temperature):
				current_state = next_state
				current_value = next_value
				path.append(current_state)

		temperature *= alpha

	return path, visited_count
