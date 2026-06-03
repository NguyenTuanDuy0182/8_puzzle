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
	"""Value(state) cho Random-Restart Hill Climbing.

	Value = Manhattan distance.
	Value càng nhỏ càng tốt.
	"""
	return manhattan_distance(state, goal)


def random_state(goal: State, *, steps: int = 60, rng: random.Random | None = None) -> State:
	"""Sinh một trạng thái ngẫu nhiên bằng random-walk từ goal.

	Cách này đảm bảo state sinh ra luôn solvable đối với goal.
	"""
	rng = rng or random.Random()
	state: State = goal
	last: State | None = None
	for _ in range(steps):
		nbs = list(neighbors(state))
		if last is not None and len(nbs) > 1:
			nbs2 = [s for s in nbs if s != last]
			nbs = nbs2 or nbs
		nxt = rng.choice(nbs)
		last, state = state, nxt
	return state


def random_restart_hill_climbing(
	start: State,
	goal: State,
	*,
	max_restarts: int = 30,
	max_iterations_per_restart: int = 10_000,
	random_walk_steps: int = 60,
	rng: random.Random | None = None,
) -> State | None:
	"""Random-Restart Hill Climbing cho 8-puzzle.

	Theo pseudo-code (đã điều chỉnh cho Value = Manhattan, nhỏ hơn là tốt hơn):
	- Mỗi lần restart: chạy Stochastic Hill Climbing với bước cải thiện nghiêm ngặt
	  (chỉ chọn neighbor có Value < Value(Current)).
	- Nếu kẹt local minimum thì restart từ một trạng thái ngẫu nhiên mới.
	- Nếu đạt goal thì trả về goal; nếu hết restart thì trả về None.
	"""
	rng = rng or random.Random()
	current_start = start

	for _ in range(max_restarts):
		current_state = current_start
		current_value = _value(current_state, goal)

		for _ in range(max_iterations_per_restart):
			if current_state == goal:
				return current_state

			better_neighbors: List[State] = []
			for nb in neighbors(current_state):
				if _value(nb, goal) < current_value:
					better_neighbors.append(nb)

			if not better_neighbors:
				break

			next_state = rng.choice(better_neighbors)
			current_state = next_state
			current_value = _value(current_state, goal)

		current_start = random_state(goal, steps=random_walk_steps, rng=rng)

	return None


def random_restart_hill_climbing_with_stats(
	start: State,
	goal: State,
	*,
	max_restarts: int = 30,
	max_iterations_per_restart: int = 10_000,
	random_walk_steps: int = 60,
	rng: random.Random | None = None,
) -> tuple[List[State], int]:
	"""Biến thể trả về path và số lượng state đã đánh giá Value.

	- Nếu tìm thấy goal: trả về path kết thúc ở goal.
	- Nếu thất bại: trả về path của lần chạy cuối (không tới goal).
	"""
	rng = rng or random.Random()
	visited_count = 0
	current_start = start
	last_path: List[State] = [start]

	for _ in range(max_restarts):
		current_state = current_start
		current_value = _value(current_state, goal)
		visited_count += 1
		path: List[State] = [current_start]

		for _ in range(max_iterations_per_restart):
			if current_state == goal:
				return path, visited_count

			better_neighbors: List[State] = []
			for nb in neighbors(current_state):
				visited_count += 1
				nb_value = _value(nb, goal)
				if nb_value < current_value:
					better_neighbors.append(nb)

			if not better_neighbors:
				break

			next_state = rng.choice(better_neighbors)
			current_state = next_state
			current_value = _value(current_state, goal)
			path.append(current_state)

		last_path = path
		current_start = random_state(goal, steps=random_walk_steps, rng=rng)

	return last_path, visited_count
