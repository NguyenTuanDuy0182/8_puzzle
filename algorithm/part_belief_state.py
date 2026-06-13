from __future__ import annotations

import heapq
import random
import itertools
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from algorithm.belief_state_w_no_goal import (
    State,
    BeliefNode,
    BeliefStateResult,
    Action,
    _ACTIONS,
    _MOVE_DELTAS,
    _canonical_node,
    _apply_action,
    _apply_action_to_node,
    _node_neighbors,
    _reconstruct_node_path,
    _replay_moves,
    manhattan_distance,
)

def get_matching_states(pattern: Sequence[int]) -> List[State]:
    """Tìm tất cả các trạng thái 8-puzzle hợp lệ khớp với pattern (0 là wildcard)."""
    # Các số đã xuất hiện trong pattern
    filled_numbers = {x for x in pattern if x != 0}
    # Các số chưa xuất hiện (bao gồm cả ô trống 0 nếu chưa được chỉ định)
    remaining_numbers = [x for x in range(9) if x not in filled_numbers]
    # Các chỉ số trống cần điền trong pattern
    empty_indices = [i for i, x in enumerate(pattern) if x == 0]
    
    matching_states = []
    # Thử mọi hoán vị của các số còn lại điền vào các ô trống
    for p in itertools.permutations(remaining_numbers):
        state_list = list(pattern)
        for idx, val in zip(empty_indices, p):
            state_list[idx] = val
        matching_states.append(tuple(state_list))
    return matching_states


def generate_compatible_pairs(
    start_pattern: Sequence[int],
    goal_pattern: Sequence[int],
) -> tuple[State, State, State, State]:
    """Sinh S1, S2 khớp với start_pattern và G1, G2 khớp với goal_pattern sao cho cả 4 có cùng Parity."""
    start_states = get_matching_states(start_pattern)
    goal_states = get_matching_states(goal_pattern)
    
    # Chia nhóm theo inversion parity
    from controller.puzzle_controller import PuzzleController
    start_by_parity = {0: [], 1: []}
    for s in start_states:
        p = PuzzleController.inversion_parity(s)
        start_by_parity[p].append(s)
        
    goal_by_parity = {0: [], 1: []}
    for g in goal_states:
        p = PuzzleController.inversion_parity(g)
        goal_by_parity[p].append(g)
        
    # Tìm parity mà cả hai phía đều có ít nhất 1 trạng thái
    for p in (0, 1):
        s_pool = start_by_parity[p]
        g_pool = goal_by_parity[p]
        if len(s_pool) >= 1 and len(g_pool) >= 1:
            # Chọn s1, s2
            if len(s_pool) >= 2:
                s1 = s_pool[0]
                s2 = None
                idx_zero_s1 = s1.index(0)
                for s in s_pool[1:]:
                    if s.index(0) != idx_zero_s1:
                        s2 = s
                        break
                if s2 is None:
                    s2 = s_pool[1]
            else:
                s1 = s2 = s_pool[0]
                
            # Chọn g1, g2
            if len(g_pool) >= 2:
                g1 = g_pool[0]
                g2 = None
                idx_zero_g1 = g1.index(0)
                for g in g_pool[1:]:
                    if g.index(0) != idx_zero_g1:
                        g2 = g
                        break
                if g2 is None:
                    g2 = g_pool[1]
            else:
                g1 = g2 = g_pool[0]
                
            return s1, s2, g1, g2
            
    raise ValueError("Không thể tìm thấy hai cặp S1, S2 và G1, G2 có cùng tính chẵn lẻ (Bài toán vô nghiệm).")


def _goal_satisfied_part(node: BeliefNode, goals: tuple[State, State]) -> bool:
	g1, g2 = goals
	# Dừng lại khi cả S1 và S2 cùng bằng G1 (node chỉ chứa G1) hoặc cùng bằng G2 (node chỉ chứa G2)
	return node == (g1,) or node == (g2,)


def _node_heuristic_part(node: BeliefNode, goals: tuple[State, State]) -> int:
	if not node:
		return 0
	g1, g2 = goals
	if len(node) == 1:
		s = node[0]
		return 2 * min(manhattan_distance(s, g1), manhattan_distance(s, g2))
	elif len(node) == 2:
		s1, s2 = node
		return min(
			manhattan_distance(s1, g1) + manhattan_distance(s2, g1),
			manhattan_distance(s1, g2) + manhattan_distance(s2, g2),
		)
	return 0


def solve_part_belief_state(
	start_pattern: Sequence[int],
	goal_pattern: Sequence[int],
) -> BeliefStateResult:
	"""Giải bài toán A* cho tập BS={S1,S2} và BG={G1,G2} thỏa mãn các ô đã biết."""
	s1, s2, g1, g2 = generate_compatible_pairs(start_pattern, goal_pattern)
	
	goals = (g1, g2)
	start_node = _canonical_node((s1, s2))

	if _goal_satisfied_part(start_node, goals):
		return BeliefStateResult(
			start1=s1,
			start2=s2,
			goals=goals,
			path1=[s1],
			path2=[s2],
			moves=[],
			visited_count=1,
			total_cost=0,
			cost1=0,
			cost2=0,
			duration=0.0,
		)

	import time
	t0 = time.time()
	open_heap: List[tuple[int, int, BeliefNode]] = []
	tie = 0
	start_g = 0
	start_f = start_g + _node_heuristic_part(start_node, goals)
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
		if f != node_g + _node_heuristic_part(node, goals):
			continue

		if _goal_satisfied_part(node, goals):
			_, moves = _reconstruct_node_path(node, parent, action_parent)
			duration = time.time() - t0
			path1 = _replay_moves(s1, moves)
			path2 = _replay_moves(s2, moves)
			return BeliefStateResult(
				start1=s1,
				start2=s2,
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
				child_f = tentative_g + _node_heuristic_part(child, goals)
				heappush(open_heap, (child_f, tie, child))

	duration = time.time() - t0
	return BeliefStateResult(
		start1=s1,
		start2=s2,
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
