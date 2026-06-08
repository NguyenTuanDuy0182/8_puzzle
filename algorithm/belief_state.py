from __future__ import annotations

import heapq
import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from algorithm.a_star import State, a_star_with_stats, manhattan_distance, neighbors

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


def _apply_action_to_node(node: BeliefNode, action: Action) -> BeliefNode:
    return _canonical_node(_apply_action(state, action) for state in node)


def _node_heuristic(node: BeliefNode, goal: State) -> int:
    if not node:
        return 0
    return sum(manhattan_distance(state, goal) for state in node)


def _node_neighbors(node: BeliefNode) -> Iterable[tuple[Action, BeliefNode]]:
    for action in _ACTIONS:
        next_node = _apply_action_to_node(node, action)
        if next_node == node:
            continue
        yield action, next_node


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


def _solve_belief_node(start1: State, start2: State, goal: State) -> BeliefStateResult:
    start_node = _canonical_node((start1, start2))
    goal_node: BeliefNode = (goal,)

    if start_node == goal_node:
        return BeliefStateResult(
            start1=start1,
            start2=start2,
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
    start_f = start_g + _node_heuristic(start_node, goal)
    heapq.heappush(open_heap, (start_f, tie, start_node))

    open_g: Dict[BeliefNode, int] = {start_node: 0}
    closed_g: Dict[BeliefNode, int] = {}
    parent: Dict[BeliefNode, Optional[BeliefNode]] = {start_node: None}
    action_parent: Dict[BeliefNode, Optional[Action]] = {start_node: None}
    visited_count = 1

    while open_heap:
        f, _t, node = heapq.heappop(open_heap)

        if node not in open_g:
            continue

        node_g = open_g[node]
        if f != node_g + _node_heuristic(node, goal):
            continue

        if node == goal_node:
            node_path, moves = _reconstruct_node_path(node, parent, action_parent)
            duration = time.time() - t0
            path1 = _replay_moves(start1, moves)
            path2 = _replay_moves(start2, moves)
            return BeliefStateResult(
                start1=start1,
                start2=start2,
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
                child_f = tentative_g + _node_heuristic(child, goal)
                heapq.heappush(open_heap, (child_f, tie, child))

    duration = time.time() - t0
    return BeliefStateResult(
        start1=start1,
        start2=start2,
        path1=None,
        path2=None,
        moves=[],
        visited_count=visited_count,
        total_cost=0,
        cost1=0,
        cost2=0,
        duration=duration,
    )


def solve_belief_state(goal: State, steps: int = 60, rng: random.Random | None = None) -> BeliefStateResult:
    """Sinh 2 trạng thái niềm tin khác nhau và giải trên belief node dạng tập.

    Node belief là một tập không thứ tự: {S1, S2}. Vì vậy (S1, S2) và (S2, S1)
    là cùng một node. Khi hai trạng thái trùng nhau thì node co lại thành {Goal}.
    """
    rng = rng or random.Random()

    for _ in range(60):
        start1, start2 = generate_belief_starts(goal, steps=steps, rng=rng)
        if start1 == start2:
            continue
        result = _solve_belief_node(start1, start2, goal)
        if result.path1 is not None and result.path2 is not None:
            return result

    return _solve_belief_node(goal, goal, goal)


def belief_state_with_stats(start: State, goal: State) -> tuple[Optional[List[State]], int, int]:
    """Belief State solver cho 8-puzzle.

    Trong project hiện tại 8-puzzle vẫn là bài toán trạng thái xác định, nên
    lựa chọn này được tách riêng như một chế độ riêng nhưng vẫn dùng A* để giải.

    Trả về cùng format với A* để controller/UI dùng thống nhất:
    (path, visited_count, g_goal)
    """
    return a_star_with_stats(start, goal)