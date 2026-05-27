from __future__ import annotations

import heapq
from typing import Dict, Iterable, List, Optional, Tuple


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


def a_star_with_stats(start: State, goal: State) -> tuple[Optional[List[State]], int, int]:
	"""A* Search.

	- g(n): số bước đã đi từ start đến n (unit cost)
	- h(n): Manhattan distance
	- f(n) = g(n) + h(n)

	Returns:
		(path, visited_count, g_goal)
	"""
	if start == goal:
		return [start], 1, 0

	open_heap: List[tuple[int, int, State]] = []
	tie = 0
	start_g = 0
	start_f = start_g + manhattan_distance(start, goal)
	heapq.heappush(open_heap, (start_f, tie, start))

	open_g: Dict[State, int] = {start: 0}
	closed_g: Dict[State, int] = {}
	parent: Dict[State, Optional[State]] = {start: None}

	visited_count = 1

	while open_heap:
		f, _t, node = heapq.heappop(open_heap)

		# Skip stale entries
		if node not in open_g:
			continue
		node_g = open_g[node]
		if f != node_g + manhattan_distance(node, goal):
			continue

		# Goal test after selecting min f
		if node == goal:
			return _reconstruct_path(node, parent), visited_count, node_g

		# Move node from OPEN to CLOSED
		open_g.pop(node, None)
		closed_g[node] = node_g

		for child in neighbors(node):
			tentative_g = node_g + 1

			if child in closed_g:
				if tentative_g >= closed_g[child]:
					continue
				# Better path found: reopen
				del closed_g[child]

			if child not in open_g or tentative_g < open_g[child]:
				open_g[child] = tentative_g
				parent[child] = node
				visited_count += 1
				tie += 1
				child_f = tentative_g + manhattan_distance(child, goal)
				heapq.heappush(open_heap, (child_f, tie, child))

	return None, visited_count, 0
