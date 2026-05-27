from __future__ import annotations

import heapq
from typing import Dict, Iterable, List, Optional, Set, Tuple


State = Tuple[int, int, int, int, int, int, int, int, int]


def neighbors(state: State) -> Iterable[State]:
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
			yield tuple(lst)


def _reconstruct_path(goal: State, parent: Dict[State, Optional[State]]) -> List[State]:
	path: List[State] = [goal]
	node = goal
	while parent[node] is not None:
		node = parent[node]  # type: ignore[assignment]
		path.append(node)
	path.reverse()
	return path


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


def greedy_with_stats(start: State, goal: State) -> tuple[Optional[List[State]], int]:
	"""Greedy Best-First Search (chọn node có h(n) nhỏ nhất).

	Returns:
		(path, visited_count)
	"""
	if start == goal:
		return [start], 1

	frontier: List[tuple[int, int, State]] = []
	tie = 0
	start_h = manhattan_distance(start, goal)
	heapq.heappush(frontier, (start_h, tie, start))
	frontier_set: Set[State] = {start}

	reached: Set[State] = set()
	parent: Dict[State, Optional[State]] = {start: None}

	visited_count = 1

	while frontier:
		_h, _t, node = heapq.heappop(frontier)
		if node not in frontier_set:
			continue
		frontier_set.remove(node)

		if node == goal:
			return _reconstruct_path(node, parent), visited_count

		reached.add(node)

		for child in neighbors(node):
			if child in reached or child in frontier_set:
				continue
			parent[child] = node
			visited_count += 1
			tie += 1
			h = manhattan_distance(child, goal)
			heapq.heappush(frontier, (h, tie, child))
			frontier_set.add(child)

	return None, visited_count
