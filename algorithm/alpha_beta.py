from typing import Tuple, List, Optional

def neighbors(state: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    """Trả về các trạng thái kề hợp lệ."""
    idx = state.index(0)
    r, c = divmod(idx, 3)
    moves = []
    if r > 0: moves.append(idx - 3) # Up
    if r < 2: moves.append(idx + 3) # Down
    if c > 0: moves.append(idx - 1) # Left
    if c < 2: moves.append(idx + 1) # Right
    
    res = []
    for m in moves:
        lst = list(state)
        lst[idx], lst[m] = lst[m], lst[idx]
        res.append(tuple(lst))
    return res

def get_heuristic(state: Tuple[int, ...], goal: Tuple[int, ...]) -> int:
    """Sử dụng Manhattan distance (negative, vì MAX muốn distance = 0)"""
    dist = 0
    for i in range(9):
        if state[i] != 0:
            g_idx = goal.index(state[i])
            r1, c1 = divmod(i, 3)
            r2, c2 = divmod(g_idx, 3)
            dist += abs(r1 - r2) + abs(c1 - c2)
    return -dist

def alpha_beta_with_stats(start: Tuple[int, ...], goal: Tuple[int, ...], max_depth: int = 4) -> Tuple[Optional[List[Tuple[int, ...]]], int]:
    visited_count = 0

    def alpha_beta(state: Tuple[int, ...], depth: int, alpha: float, beta: float, maximizingPlayer: bool, prev_state: Optional[Tuple[int, ...]] = None) -> Tuple[float, List[Tuple[int, ...]]]:
        nonlocal visited_count
        visited_count += 1
        
        if depth == 0 or state == goal:
            return get_heuristic(state, goal), []
            
        valid_children = [c for c in neighbors(state) if c != prev_state]
        if not valid_children:
            return get_heuristic(state, goal), []

        if maximizingPlayer:
            value = -float('inf')
            bestPath = []
            for child in valid_children:
                child_val, path = alpha_beta(child, depth - 1, alpha, beta, False, state)
                if child_val > value:
                    value = child_val
                    bestPath = [child] + path
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, bestPath
        else:
            value = float('inf')
            bestPath = []
            for child in valid_children:
                child_val, path = alpha_beta(child, depth - 1, alpha, beta, True, state)
                if child_val < value:
                    value = child_val
                    bestPath = [child] + path
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value, bestPath

    # Mô phỏng quá trình chơi giữa MAX và MIN trên cùng bàn cờ 8-puzzle.
    # MAX cố gắng về đích (tối đa hóa heuristic), MIN cố gắng ngăn cản (tối thiểu hóa).
    path = [start]
    current = start
    maximizing = True
    prev = None
    
    # Mô phỏng tối đa 50 bước để tránh vòng lặp vô tận
    for _ in range(50):
        if current == goal:
            break
            
        val, best_path = alpha_beta(current, max_depth, -float('inf'), float('inf'), maximizing, prev)
        if not best_path:
            break
            
        nxt = best_path[0]
        path.append(nxt)
        prev = current
        current = nxt
        maximizing = not maximizing

    return path, visited_count
