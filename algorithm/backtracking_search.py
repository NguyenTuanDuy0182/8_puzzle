def backtracking_search(csp):
    """
    BACKTRACKING-SEARCH(csp)
        return RECURSIVE-BACKTRACKING({}, csp)
    """
    return recursive_backtracking({}, csp)


def recursive_backtracking(assignment, csp):
    """
    RECURSIVE-BACKTRACKING(assignment, csp)
        if assignment is complete then return assignment
        var ← SELECT-UNASSIGNED-VARIABLE(csp)
        for each value in ORDER-DOMAIN-VALUES(var, assignment, csp) do
            if value is consistent with assignment then
                add {var = value} to assignment
                result ← RECURSIVE-BACKTRACKING(assignment, csp)
                if result ≠ failure then return result
                remove {var = value} from assignment
        return failure
    """
    # if assignment is complete then return assignment
    if len(assignment) == len(csp['variables']):
        return assignment
    
    # var ← SELECT-UNASSIGNED-VARIABLE(csp)
    var = select_unassigned_variable(assignment, csp)
    
    # for each value in ORDER-DOMAIN-VALUES(var, assignment, csp) do
    for value in order_domain_values(var, assignment, csp):
        # if value is consistent with assignment then
        if is_consistent(var, value, assignment, csp):
            # add {var = value} to assignment
            assignment[var] = value
            
            # result ← RECURSIVE-BACKTRACKING(assignment, csp)
            result = recursive_backtracking(assignment, csp)
            
            # if result ≠ failure then return result
            if result is not None:
                return result
            
            # remove {var = value} from assignment
            del assignment[var]
            
    # return failure
    return None


def select_unassigned_variable(assignment, csp):
    """Chọn biến chưa được gán giá trị."""
    for var in csp['variables']:
        if var not in assignment:
            return var
    return None


def order_domain_values(var, assignment, csp):
    """Trả về danh sách các giá trị khả dĩ cho biến."""
    return csp['domains'][var]


def is_consistent(var, value, assignment, csp):
    """Kiểm tra xem việc gán value cho var có vi phạm ràng buộc nào không."""
    for neighbor in csp['neighbors'][var]:
        # Nếu hàng xóm đã được tô màu và màu đó trùng với value -> Không hợp lệ
        if neighbor in assignment and assignment[neighbor] == value:
            return False
    return True
