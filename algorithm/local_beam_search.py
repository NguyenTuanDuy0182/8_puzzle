from __future__ import annotations

import random
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


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


def _reconstruct_path(goal: State, parent: Dict[State, Optional[State]]) -> List[State]:
	path: List[State] = [goal]
	node = goal
	while parent.get(node) is not None:
		node = parent[node]  # type: ignore[assignment]
		path.append(node)
	path.reverse()
	return path


def _random_states_from_start(
	start: State,
	*,
	count: int,
	random_walk_steps: int,
	rng: random.Random,
) -> List[State]:
	"""Sinh thêm các state khởi tạo bằng random-walk từ start.

	Giữ cùng parity với start, nên nếu start solvable với goal thì các state này cũng solvable.
	"""
	states: List[State] = [start]
	seen: Set[State] = {start}

	while len(states) < count:
		state: State = start
		last: State | None = None
		for _ in range(random_walk_steps):
			nbs = list(neighbors(state))
			if last is not None and len(nbs) > 1:
				nbs2 = [s for s in nbs if s != last]
				nbs = nbs2 or nbs
			nxt = rng.choice(nbs)
			last, state = state, nxt

		if state not in seen:
			seen.add(state)
			states.append(state)

	return states


def local_beam_search_with_stats(
	start: State,
	goal: State,
	*,
	k: int = 3,
	random_walk_steps: int = 30,
	max_iterations: int = 50_000,
	rng: random.Random | None = None,
) -> tuple[Optional[List[State]], int]:
	"""Local Beam Search (k-beam) theo pseudo-code.

	- Current_State_Set: k trạng thái khởi tạo (start + các state random-walk từ start)
	- Visited: tập state đã gặp
	- Mỗi vòng: thu thập tất cả neighbor chưa visited từ mọi state trong beam
	- Sắp xếp theo h (Manhattan) tăng dần và chọn k trạng thái tốt nhất

	Returns:
		(path|None, visited_count)
	"""
	if k <= 0:
		raise ValueError("k phải > 0")

	rng = rng or random.Random()

	current_set = _random_states_from_start(
		start, count=k, random_walk_steps=random_walk_steps, rng=rng
	)
	visited: Set[State] = set(current_set)
	parent: Dict[State, Optional[State]] = {s: None for s in current_set}

	visited_count = len(current_set)

	# Nếu start/seed đã là goal.
	for s in current_set:
		if s == goal:
			return [s], visited_count

	for _ in range(max_iterations):
		neighbor_states: List[State] = []

		for state in current_set:
			for nb in neighbors(state):
				if nb == goal:
					if nb not in parent:
						parent[nb] = state
						visited_count += 1
					return _reconstruct_path(nb, parent), visited_count
				if nb in visited:
					continue
				visited.add(nb)
				parent[nb] = state
				neighbor_states.append(nb)
				visited_count += 1

		if not neighbor_states:
			return None, visited_count

		neighbor_states.sort(key=lambda s: manhattan_distance(s, goal))
		current_set = neighbor_states[:k]

	return None, visited_count


def local_beam_search(
	start: State,
	goal: State,
	*,
	k: int = 5,
	random_walk_steps: int = 30,
	max_iterations: int = 50_000,
	rng: random.Random | None = None,
) -> Optional[List[State]]:
	path, _visited = local_beam_search_with_stats(
		start,
		goal,
		k=k,
		random_walk_steps=random_walk_steps,
		max_iterations=max_iterations,
		rng=rng,
	)
	return path
