from __future__ import annotations

from typing import Iterable, List, Optional, Tuple


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


def _depth_limited_search_with_stats(
	start: State,
	goal: State,
	limit: int,
) -> tuple[Optional[List[State]], bool, int]:
	
	if start == goal:
		return [start], False, 1

	frontier: List[tuple[State, int, List[State]]] = [(start, 0, [start])]
	visited_count = 1
	cutoff = False

	while frontier:
		node, depth, path = frontier.pop()

		if node == goal:
			return path, False, visited_count

		if depth == limit:
			cutoff = True
			continue

		# IS-CYCLE(node): tránh lặp lại trạng thái đã xuất hiện trên đường đi hiện tại
		for child in neighbors(node):
			if child in path:
				continue
			frontier.append((child, depth + 1, path + [child]))
			visited_count += 1

	return None, cutoff, visited_count


def idfs_with_stats(start: State, goal: State, max_depth: int = 60) -> tuple[Optional[List[State]], int]:
	visited_total = 0
	for limit in range(max_depth + 1):
		path, cutoff, visited = _depth_limited_search_with_stats(start, goal, limit)
		visited_total += visited

		if path is not None:
			return path, visited_total

		if not cutoff:
			break

	return None, visited_total

