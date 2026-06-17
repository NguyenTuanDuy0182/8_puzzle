def ac3(csp):
    """
    FUNCTION AC-3(csp)
        queue ← tất cả các cung (Xi, Xj) trong CSP
        WHILE queue không rỗng DO
            (Xi, Xj) ← REMOVE-FIRST(queue)
            IF REMOVE-INCONSISTENT-VALUES(Xi, Xj) THEN
                IF DOMAIN[Xi] rỗng THEN
                    RETURN FAILURE
                FOR EACH Xk ∈ NEIGHBORS(Xi) DO
                    IF Xk ≠ Xj THEN
                        ADD (Xk, Xi) vào queue
        RETURN SUCCESS
    """
    # Khởi tạo queue với tất cả các cung (Xi, Xj)
    queue = []
    for var in csp['variables']:
        for neighbor in csp['neighbors'][var]:
            queue.append((var, neighbor))
            
    while queue:
        xi, xj = queue.pop(0) # REMOVE-FIRST
        
        if remove_inconsistent_values(xi, xj, csp):
            if len(csp['domains'][xi]) == 0:
                return False # FAILURE
            
            for xk in csp['neighbors'][xi]:
                if xk != xj:
                    # ADD (Xk, Xi) vào queue
                    if (xk, xi) not in queue:
                        queue.append((xk, xi))
                        
    return True # SUCCESS

def remove_inconsistent_values(xi, xj, csp):
    """
    FUNCTION REMOVE-INCONSISTENT-VALUES(Xi, Xj)
        removed ← FALSE
        FOR EACH x ∈ DOMAIN[Xi] DO
            satisfiable ← FALSE
            FOR EACH y ∈ DOMAIN[Xj] DO
                IF constraint(Xi,Xj) được thỏa mãn bởi (x,y) THEN
                    satisfiable ← TRUE
                    BREAK
            IF satisfiable = FALSE THEN
                DELETE x khỏi DOMAIN[Xi]
                removed ← TRUE
        RETURN removed
    """
    removed = False
    
    # Duyệt qua bản sao vì ta sẽ xóa phần tử trong list gốc
    for x in list(csp['domains'][xi]):
        satisfiable = False
        for y in csp['domains'][xj]:
            if x != y: # Ràng buộc: Hai vùng kề nhau khác màu
                satisfiable = True
                break
                
        if not satisfiable:
            csp['domains'][xi].remove(x)
            removed = True
            
    return removed


def ac3_search(csp):
    """
    Hàm kết hợp Backtracking và AC-3 (MAC - Maintaining Arc Consistency)
    để tìm ra lời giải cho bài toán.
    """
    csp_copy = {
        'variables': csp['variables'],
        'domains': {k: v[:] for k, v in csp['domains'].items()},
        'neighbors': csp['neighbors']
    }
    return backtrack_with_ac3({}, csp_copy)


def backtrack_with_ac3(assignment, csp):
    if len(assignment) == len(csp['variables']):
        return assignment

    var = None
    for v in csp['variables']:
        if v not in assignment:
            var = v
            break

    for value in csp['domains'][var]:
        # Lưu lại domains hiện tại trước khi gán
        old_domains = {k: v[:] for k, v in csp['domains'].items()}
        
        # Gán var = value bằng cách thu hẹp domain của var thành 1 phần tử
        csp['domains'][var] = [value]
        
        # Chạy AC-3 để lan truyền ràng buộc từ thay đổi này
        if ac3(csp):
            assignment[var] = value
            result = backtrack_with_ac3(assignment, csp)
            if result is not None:
                return result
            del assignment[var]
            
        # Nếu thất bại hoặc không tìm ra lời giải, khôi phục lại domain
        csp['domains'] = old_domains

    return None
