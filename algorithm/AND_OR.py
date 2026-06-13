from __future__ import annotations

import time
from typing import Dict, List, Optional, Sequence, Tuple, Set
from algorithm.a_star import State, manhattan_distance

# Di chuyển ô trống (0)
_MOVE_DELTAS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}

def _apply_action(state: State, action: str) -> State:
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


def get_actions(state: State) -> List[str]:
    zero = state.index(0)
    x, y = divmod(zero, 3)
    actions = []
    if x > 0:
        actions.append("U")
    if x < 2:
        actions.append("D")
    if y > 0:
        actions.append("L")
    if y < 2:
        actions.append("R")
    return actions


def results(state: State, action: str) -> List[State]:
    return [_apply_action(state, action)]


def step_cost(state: State, action: str, goal: State) -> int:
    next_state = _apply_action(state, action)
    return manhattan_distance(next_state, goal)


class AndOrProblem:
    def __init__(self, start: State, goal: State):
        self.initial_state = start
        self.goal = goal

    def goal_test(self, state: State) -> bool:
        return state == self.goal


def and_or_graph_search_with_stats(start: State, goal: State) -> Tuple[Optional[List[State]], int, int]:
    """Tìm kiếm đồ thị AND-OR (AND-OR Graph Search) cho 8-puzzle.

    Chi phí được tính bằng khoảng cách Manhattan từ trạng thái mới đến đích.
    """
    problem = AndOrProblem(start, goal)
    visited_count = [0]  # Dùng list để pass by reference trong đệ quy

    def or_search(state: State, path: Set[State], cost: int, depth: int) -> Tuple[Optional[list | dict], int]:
        visited_count[0] += 1

        # Tránh đệ quy quá sâu gây tràn stack
        if depth > 100:
            return None, float('inf')

        if problem.goal_test(state):
            return [], cost

        if state in path:
            return None, float('inf')

        best_plan = None
        best_cost = float('inf')

        # Sắp xếp các hành động theo khoảng cách Manhattan tăng dần (Greedy/Informed DFS)
        actions = get_actions(state)
        actions = sorted(actions, key=lambda a: manhattan_distance(_apply_action(state, a), goal))

        for action in actions:
            result_states = results(state, action)
            new_path = path.copy()
            new_path.add(state)
            
            plan, total_cost = and_search(
                result_states,
                new_path,
                cost + step_cost(state, action, goal),
                depth + 1
            )

            if plan is not None and total_cost < best_cost:
                best_cost = total_cost
                best_plan = [action, plan]

        if best_plan is None:
            return None, float('inf')

        return best_plan, best_cost

    def and_search(states: List[State], path: Set[State], cost: int, depth: int) -> Tuple[Optional[dict], int]:
        plans = {}
        max_cost = cost

        for s in states:
            plan_s, cost_s = or_search(s, path, cost, depth)
            if plan_s is None:
                return None, float('inf')
            plans[s] = plan_s
            max_cost = max(max_cost, cost_s)

        return plans, max_cost

    # Thực hiện tìm kiếm
    plan, total_cost = or_search(start, set(), 0, 0)

    if plan is None or total_cost == float('inf'):
        return None, visited_count[0], 0

    # Chuyển đổi plan từ dạng cây AND-OR sang path (danh sách State) để tương thích với UI hiện tại
    path = [start]
    curr = start
    curr_plan = plan
    while curr_plan and isinstance(curr_plan, list) and len(curr_plan) == 2:
        action, next_plans = curr_plan
        curr = _apply_action(curr, action)
        path.append(curr)
        if isinstance(next_plans, dict) and curr in next_plans:
            curr_plan = next_plans[curr]
        else:
            break

    return path, visited_count[0], int(total_cost)
