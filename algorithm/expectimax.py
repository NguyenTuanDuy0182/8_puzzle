from typing import Tuple, List, Optional
import random

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

def expectimax_with_stats(start: Tuple[int, ...], goal: Tuple[int, ...], max_depth: int = 4) -> Tuple[Optional[List[Tuple[int, ...]]], int]:
    visited_count = 0

    def expectimax(state: Tuple[int, ...], depth: int, nodeType: str, prev_state: Optional[Tuple[int, ...]] = None) -> Tuple[float, List[Tuple[int, ...]]]:
        nonlocal visited_count
        visited_count += 1
        
        if depth == 0 or state == goal:
            return float(get_heuristic(state, goal)), []
            
        valid_children = [c for c in neighbors(state) if c != prev_state]
        if not valid_children:
            return float(get_heuristic(state, goal)), []

        if nodeType == "MAX":
            bestValue = -float('inf')
            bestPath = []
            for child in valid_children:
                value, path = expectimax(child, depth - 1, "CHANCE", state)
                if value > bestValue:
                    bestValue = value
                    bestPath = [child] + path
            return bestValue, bestPath
            
        elif nodeType == "CHANCE":
            expectedValue = 0.0
            probability = 1.0 / len(valid_children)
            
            # Chọn ngẫu nhiên một path đại diện (phục vụ type signature),
            # thực tế MAX chỉ dùng giá trị expectedValue.
            random_child = random.choice(valid_children)
            bestPath = []
            
            for child in valid_children:
                value, path = expectimax(child, depth - 1, "MAX", state)
                expectedValue += probability * value
                
                if child == random_child:
                    bestPath = [child] + path
                    
            return expectedValue, bestPath

        return 0.0, []

    # Mô phỏng quá trình chơi: MAX đi 1 bước tối ưu (Expectimax), sau đó môi trường (CHANCE) đi ngẫu nhiên
    path = [start]
    current = start
    nodeType = "MAX"
    prev = None
    
    # Mô phỏng tối đa 50 bước
    for _ in range(50):
        if current == goal:
            break
            
        if nodeType == "MAX":
            val, best_path = expectimax(current, max_depth, "MAX", prev)
            if not best_path:
                break
            nxt = best_path[0]
        else: # CHANCE
            valid_children = [c for c in neighbors(current) if c != prev]
            if not valid_children:
                break
            nxt = random.choice(valid_children)
            
        path.append(nxt)
        prev = current
        current = nxt
        nodeType = "CHANCE" if nodeType == "MAX" else "MAX"

    return path, visited_count
