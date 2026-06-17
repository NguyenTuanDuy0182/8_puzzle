import random

def min_conflicts(csp, max_steps=1000):
    """
    FUNCTION MIN-CONFLICTS(csp, max_steps)
        current ← INITIAL-COMPLETE-ASSIGNMENT(csp)
        FOR i ← 1 TO max_steps DO
            IF current là nghiệm THEN
                RETURN current
            var ← RANDOM-CONFLICTED-VARIABLE(current)
            value ← argminv CONFLICTS(var, v, current, csp)
            current[var] ← value
        RETURN failure
    """
    current = initial_complete_assignment(csp)

    for i in range(max_steps):
        if is_solution(current, csp):
            return current

        var = random_conflicted_variable(current, csp)
        
        if var is None: # An toàn nếu không tìm thấy biến xung đột (dù is_solution sẽ bắt trước)
            return current

        # Tìm giá trị tối thiểu hóa conflicts.
        min_c = float('inf')
        best_values = []
        for v in csp['domains'][var]:
            c = conflicts(var, v, current, csp)
            if c < min_c:
                min_c = c
                best_values = [v]
            elif c == min_c:
                best_values.append(v)
                
        value = random.choice(best_values)
        current[var] = value

    return None # failure

def initial_complete_assignment(csp):
    """Gán ngẫu nhiên cho mọi biến trong csp"""
    assignment = {}
    for var in csp['variables']:
        assignment[var] = random.choice(csp['domains'][var])
    return assignment

def is_solution(current, csp):
    for var in csp['variables']:
        if conflicts(var, current[var], current, csp) > 0:
            return False
    return True

def random_conflicted_variable(current, csp):
    """Chọn ngẫu nhiên 1 biến đang bị xung đột với các biến khác."""
    conflicted_vars = []
    for var in csp['variables']:
        if conflicts(var, current[var], current, csp) > 0:
            conflicted_vars.append(var)
            
    if not conflicted_vars:
        return None
    return random.choice(conflicted_vars)

def conflicts(var, value, current, csp):
    """
    FUNCTION CONFLICTS(var, value, current, csp)
        count ← 0
        FOR EACH constraint liên quan đến var DO
            IF constraint bị vi phạm khi gán var = value THEN
                count ← count + 1
        RETURN count
    """
    count = 0
    for neighbor in csp['neighbors'][var]:
        # Ràng buộc tô màu: Các vùng kề nhau phải khác màu
        if neighbor in current and current[neighbor] == value:
            count += 1
    return count
