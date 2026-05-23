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



def state_cost(state: State, goal: State, *, include_blank: bool = True) -> int:
	#Cost của một state = số ô khác goal.
	if include_blank:
		return sum(1 for a, b in zip(state, goal) if a != b)
	return sum(1 for a, b in zip(state, goal) if a != 0 and a != b)


def path_cost(path: List[State], goal: State, *, include_blank: bool = True) -> int:
	"""Tính tổng path cost theo quy tắc g(child)=g(parent)+cost(child_state).

	- g(start) = cost(start)
	- g(child) = g(parent) + cost(child)

	=> tổng chi phí của một lời giải = sum(cost(state) for state in path)
	"""

	if not path:
		return 0
	return sum(state_cost(s, goal, include_blank=include_blank) for s in path)


def ucs_with_stats(
	start: State,
	goal: State,
	*,
	include_blank: bool = True,
) -> tuple[Optional[List[State]], int, int]:

	if start == goal:
		return [start], 1, state_cost(start, goal, include_blank=include_blank)

	frontier: List[tuple[int, int, State]] = []
	tie = 0
	start_g = state_cost(start, goal, include_blank=include_blank)
	heapq.heappush(frontier, (start_g, tie, start))

	explored: Set[State] = set()

	frontier_cost: Dict[State, int] = {start: start_g}

	parent: Dict[State, Optional[State]] = {start: None}

	visited_count = 1 

	while frontier:
		g, _t, node = heapq.heappop(frontier)

		if frontier_cost.get(node) != g:
			continue

		frontier_cost.pop(node, None)

		if node == goal:
			return _reconstruct_path(node, parent), visited_count, g

		explored.add(node)

		for child in neighbors(node):
			if child in explored:
				continue

			child_g = g + state_cost(child, goal, include_blank=include_blank)

			if child not in frontier_cost:
				tie += 1
				heapq.heappush(frontier, (child_g, tie, child))
				frontier_cost[child] = child_g
				parent[child] = node
				visited_count += 1
				continue

			if child_g < frontier_cost[child]:
				tie += 1
				heapq.heappush(frontier, (child_g, tie, child))
				frontier_cost[child] = child_g
				parent[child] = node

	return None, visited_count, 0

