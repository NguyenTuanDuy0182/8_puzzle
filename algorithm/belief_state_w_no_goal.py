from __future__ import annotations

import heapq
import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from algorithm.a_star import State, manhattan_distance, neighbors

BeliefNode = Tuple[State, ...]
Action = str

_ACTIONS: tuple[Action, ...] = ("U", "D", "L", "R")
_MOVE_DELTAS: dict[Action, tuple[int, int]] = {
	"U": (-1, 0),
	"D": (1, 0),
	"L": (0, -1),
	"R": (0, 1),
}


@dataclass(frozen=True)
class BeliefStateResult:
	start1: State
	start2: State
	goals: Tuple[State, ...]
	path1: Optional[List[State]]
	path2: Optional[List[State]]
	moves: List[str]
	visited_count: int
	total_cost: int
	cost1: int
	cost2: int
	duration: float


def _canonical_node(states: Sequence[State]) -> BeliefNode:
	return tuple(sorted(set(states)))


def _normalize_goals(goals: Sequence[State]) -> tuple[State, ...]:
	normalized = tuple(sorted(set(goals)))
	if not normalized:
		raise ValueError("Goal set must contain at least one state.")
	return normalized


def _apply_action(state: State, action: Action) -> State:
	zero = state.index(0)
	x, y = divmod(zero, 3)
	dx, dy = _MOVE_DELTAS[action]
	nx, ny = x + dx, y + dy

	if not (0 <= nx < 3 and 0 <= ny < 3):
		return state

	nidx = nx * 3 + ny
	lst = list(state)
	lst[zero], lst[nidx] = lst[nidx], lst[zero]
	return tuple(lst)


def _apply_action_to_node(node: BeliefNode, action: Action) -> BeliefNode:
	return _canonical_node(_apply_action(state, action) for state in node)


def _node_neighbors(node: BeliefNode) -> Iterable[tuple[Action, BeliefNode]]:
	for action in _ACTIONS:
		next_node = _apply_action_to_node(node, action)
		if next_node == node:
			continue
		yield action, next_node


def _goal_satisfied(node: BeliefNode, goals: tuple[State, ...]) -> bool:
	goal_set = set(goals)
	return bool(node) and set(node).issubset(goal_set)


def _node_heuristic(node: BeliefNode, goals: tuple[State, ...]) -> int:
	if not node:
		return 0

	if len(goals) == 1:
		goal = goals[0]
		return sum(manhattan_distance(state, goal) for state in node)

	if len(goals) == 2 and len(node) <= 2:
		if len(node) == 1:
			state = node[0]
			return min(manhattan_distance(state, goals[0]), manhattan_distance(state, goals[1]))
		left, right = node
		g1, g2 = goals
		return min(
			manhattan_distance(left, g1) + manhattan_distance(right, g2),
			manhattan_distance(left, g2) + manhattan_distance(right, g1),
		)

	# Fallback cho trường hợp tổng quát hơn: ghép mỗi state với goal gần nhất.
	return sum(min(manhattan_distance(state, goal) for goal in goals) for state in node)


def _reconstruct_node_path(
	goal_node: BeliefNode,
	parent: Dict[BeliefNode, Optional[BeliefNode]],
	action_parent: Dict[BeliefNode, Optional[Action]],
) -> tuple[List[BeliefNode], List[str]]:
	node_path: List[BeliefNode] = [goal_node]
	moves: List[str] = []
	node = goal_node

	while parent[node] is not None:
		action = action_parent[node]
		if action is not None:
			moves.append(action)
		node = parent[node]  # type: ignore[assignment]
		node_path.append(node)

	node_path.reverse()
	moves.reverse()
	return node_path, moves


def _replay_moves(start: State, moves: Sequence[str]) -> List[State]:
	path: List[State] = [start]
	state = start
	for move in moves:
		state = _apply_action(state, move)
		path.append(state)
	return path


def _solve_belief_node(start1: State, start2: State, goals: Sequence[State]) -> BeliefStateResult:
	goal_tuple = _normalize_goals(goals)
	start_node = _canonical_node((start1, start2))

	if _goal_satisfied(start_node, goal_tuple):
		return BeliefStateResult(
			start1=start1,
			start2=start2,
			goals=goal_tuple,
			path1=[start1],
			path2=[start2],
			moves=[],
			visited_count=1,
			total_cost=0,
			cost1=0,
			cost2=0,
			duration=0.0,
		)

	t0 = time.time()
	open_heap: List[tuple[int, int, BeliefNode]] = []
	tie = 0
	start_g = 0
	start_f = start_g + _node_heuristic(start_node, goal_tuple)
	heappush = heapq.heappush
	heappop = heapq.heappop
	heappush(open_heap, (start_f, tie, start_node))

	open_g: Dict[BeliefNode, int] = {start_node: 0}
	closed_g: Dict[BeliefNode, int] = {}
	parent: Dict[BeliefNode, Optional[BeliefNode]] = {start_node: None}
	action_parent: Dict[BeliefNode, Optional[Action]] = {start_node: None}
	visited_count = 1

	while open_heap:
		f, _t, node = heappop(open_heap)

		if node not in open_g:
			continue

		node_g = open_g[node]
		if f != node_g + _node_heuristic(node, goal_tuple):
			continue

		if _goal_satisfied(node, goal_tuple):
			_, moves = _reconstruct_node_path(node, parent, action_parent)
			duration = time.time() - t0
			path1 = _replay_moves(start1, moves)
			path2 = _replay_moves(start2, moves)
			return BeliefStateResult(
				start1=start1,
				start2=start2,
				goals=goal_tuple,
				path1=path1,
				path2=path2,
				moves=moves,
				visited_count=visited_count,
				total_cost=node_g,
				cost1=len(path1) - 1,
				cost2=len(path2) - 1,
				duration=duration,
			)

		open_g.pop(node, None)
		closed_g[node] = node_g

		for action, child in _node_neighbors(node):
			tentative_g = node_g + 1

			if child in closed_g and tentative_g >= closed_g[child]:
				continue
			if child in closed_g:
				del closed_g[child]

			if child not in open_g or tentative_g < open_g[child]:
				open_g[child] = tentative_g
				parent[child] = node
				action_parent[child] = action
				visited_count += 1
				tie += 1
				child_f = tentative_g + _node_heuristic(child, goal_tuple)
				heappush(open_heap, (child_f, tie, child))

	duration = time.time() - t0
	return BeliefStateResult(
		start1=start1,
		start2=start2,
		goals=goal_tuple,
		path1=None,
		path2=None,
		moves=[],
		visited_count=visited_count,
		total_cost=0,
		cost1=0,
		cost2=0,
		duration=duration,
	)


def solve_belief_state_sets(
	start_states: Sequence[State],
	goal_states: Sequence[State],
) -> BeliefStateResult:
	"""Giải A* trên belief node dạng tập.

	Điều kiện đích: mọi state trong BS đều thuộc BG.
	"""
	if len(start_states) != 2:
		raise ValueError("Belief start set must contain exactly two states.")
	return _solve_belief_node(start_states[0], start_states[1], goal_states)


def solve_belief_state_pair(start1: State, start2: State, goal1: State, goal2: State) -> BeliefStateResult:
	"""Giải A* cho BS={S1,S2} và BG={G1,G2}.

	Node đích đạt khi cả hai state trong belief node đều thuộc {G1, G2}.
	"""
	return _solve_belief_node(start1, start2, (goal1, goal2))


def random_start(goal: State, steps: int = 60, rng: random.Random | None = None) -> State:
	rng = rng or random.Random()
	state: State = goal
	last: Optional[State] = None

	for _ in range(steps):
		nbs = list(neighbors(state))
		if last is not None and len(nbs) > 1:
			nbs2 = [candidate for candidate in nbs if candidate != last]
			nbs = nbs2 or nbs
		nxt = rng.choice(nbs)
		last, state = state, nxt

	return state


def generate_belief_starts(goal: State, steps: int = 60, rng: random.Random | None = None) -> tuple[State, State]:
	rng = rng or random.Random()
	start1 = random_start(goal, steps=steps, rng=rng)
	start2 = random_start(goal, steps=steps + 11, rng=rng)

	for _ in range(12):
		if start1 != start2:
			break
		start2 = random_start(goal, steps=steps + 11, rng=rng)

	return start1, start2


def solve_belief_state(goal: State, steps: int = 60, rng: random.Random | None = None) -> BeliefStateResult:
	"""Giữ tương thích với controller hiện tại: sinh 2 start và giải bằng A*.

	Với biến thể này, BG chỉ có một goal nên cả hai state phải hội tụ về goal đó.
	"""
	rng = rng or random.Random()

	for _ in range(60):
		start1, start2 = generate_belief_starts(goal, steps=steps, rng=rng)
		if start1 == start2:
			continue
		result = _solve_belief_node(start1, start2, (goal,))
		if result.path1 is not None and result.path2 is not None:
			return result

	return _solve_belief_node(goal, goal, (goal,))


def _goal_satisfied_same_goal(node: BeliefNode, goals: tuple[State, State]) -> bool:
	g1, g2 = goals
	# Dừng lại khi cả S1 và S2 cùng bằng G1 (node chỉ chứa G1) hoặc cùng bằng G2 (node chỉ chứa G2)
	return node == (g1,) or node == (g2,)


def _node_heuristic_same_goal(node: BeliefNode, goals: tuple[State, State]) -> int:
	if not node:
		return 0
	g1, g2 = goals
	if len(node) == 1:
		s = node[0]
		return 2 * min(manhattan_distance(s, g1), manhattan_distance(s, g2))
	elif len(node) == 2:
		s1, s2 = node
		# A* tính bằng tổng manhattan của S1 và S2 tới cùng một đích (G1 hoặc G2)
		return min(
			manhattan_distance(s1, g1) + manhattan_distance(s2, g1),
			manhattan_distance(s1, g2) + manhattan_distance(s2, g2),
		)
	return 0


def solve_belief_state_same_goal(
	start1: State,
	start2: State,
	goal1: State,
	goal2: State,
) -> BeliefStateResult:
	"""Giải bài toán A* tìm chuỗi nước đi đồng bộ để cả S1 và S2 cùng hội tụ về G1 HOẶC cùng hội tụ về G2."""
	goals = (goal1, goal2)
	start_node = _canonical_node((start1, start2))

	if _goal_satisfied_same_goal(start_node, goals):
		return BeliefStateResult(
			start1=start1,
			start2=start2,
			goals=goals,
			path1=[start1],
			path2=[start2],
			moves=[],
			visited_count=1,
			total_cost=0,
			cost1=0,
			cost2=0,
			duration=0.0,
		)

	t0 = time.time()
	open_heap: List[tuple[int, int, BeliefNode]] = []
	tie = 0
	start_g = 0
	start_f = start_g + _node_heuristic_same_goal(start_node, goals)
	heappush = heapq.heappush
	heappop = heapq.heappop
	heappush(open_heap, (start_f, tie, start_node))

	open_g: Dict[BeliefNode, int] = {start_node: 0}
	closed_g: Dict[BeliefNode, int] = {}
	parent: Dict[BeliefNode, Optional[BeliefNode]] = {start_node: None}
	action_parent: Dict[BeliefNode, Optional[Action]] = {start_node: None}
	visited_count = 1

	while open_heap:
		f, _t, node = heappop(open_heap)

		if node not in open_g:
			continue

		node_g = open_g[node]
		if f != node_g + _node_heuristic_same_goal(node, goals):
			continue

		if _goal_satisfied_same_goal(node, goals):
			_, moves = _reconstruct_node_path(node, parent, action_parent)
			duration = time.time() - t0
			path1 = _replay_moves(start1, moves)
			path2 = _replay_moves(start2, moves)
			return BeliefStateResult(
				start1=start1,
				start2=start2,
				goals=goals,
				path1=path1,
				path2=path2,
				moves=moves,
				visited_count=visited_count,
				total_cost=node_g,
				cost1=len(path1) - 1,
				cost2=len(path2) - 1,
				duration=duration,
			)

		open_g.pop(node, None)
		closed_g[node] = node_g

		for action, child in _node_neighbors(node):
			tentative_g = node_g + 1

			if child in closed_g and tentative_g >= closed_g[child]:
				continue
			if child in closed_g:
				del closed_g[child]

			if child not in open_g or tentative_g < open_g[child]:
				open_g[child] = tentative_g
				parent[child] = node
				action_parent[child] = action
				visited_count += 1
				tie += 1
				child_f = tentative_g + _node_heuristic_same_goal(child, goals)
				heappush(open_heap, (child_f, tie, child))

	duration = time.time() - t0
	return BeliefStateResult(
		start1=start1,
		start2=start2,
		goals=goals,
		path1=None,
		path2=None,
		moves=[],
		visited_count=visited_count,
		total_cost=0,
		cost1=0,
		cost2=0,
		duration=duration,
	)


def generate_belief_starts_and_goals(
	base_goal: State,
	steps: int = 25,
	rng: random.Random | None = None,
) -> tuple[State, State, State, State]:
	rng = rng or random.Random()
	
	# Sinh G1, G2 khác nhau từ base_goal
	g1 = random_start(base_goal, steps=steps, rng=rng)
	g2 = random_start(base_goal, steps=steps + 5, rng=rng)
	for _ in range(30):
		if g1 != g2:
			break
		g2 = random_start(base_goal, steps=steps + 5, rng=rng)
	else:
		# Fallback nếu ngẫu nhiên trùng
		g2 = list(neighbors(g1))[0]

	# Sinh S1, S2 khác nhau
	s1 = random_start(g1, steps=steps, rng=rng)
	s2 = random_start(g1, steps=steps + 7, rng=rng)
	for _ in range(30):
		if s1 != s2:
			break
		s2 = random_start(g1, steps=steps + 7, rng=rng)
	else:
		s2 = list(neighbors(s1))[0]

	return s1, s2, g1, g2


def solve_belief_state_same_goal_auto(
	base_goal: State,
	steps: int = 25,
	rng: random.Random | None = None,
) -> BeliefStateResult:
	"""Tự sinh ngẫu nhiên S1, S2 khác nhau và G1, G2 khác nhau từ base_goal, rồi giải A*."""
	rng = rng or random.Random()
	for _ in range(60):
		s1, s2, g1, g2 = generate_belief_starts_and_goals(base_goal, steps=steps, rng=rng)
		if s1 == s2 or g1 == g2:
			continue
		result = solve_belief_state_same_goal(s1, s2, g1, g2)
		if result.path1 is not None and result.path2 is not None:
			return result
	
	# Fallback nếu không giải được
	g1 = base_goal
	g2 = list(neighbors(base_goal))[0]
	s1 = list(neighbors(g1))[0]
	s2 = list(neighbors(g2))[0]
	if s1 == s2:
		s2 = g2
	return solve_belief_state_same_goal(s1, s2, g1, g2)

