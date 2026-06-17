def forward_checking_search(csp):
    """
    FORWARD-CHECKING-SEARCH(csp)
        return FORWARD-CHECK({}, csp)
    """
    # Tạo bản sao của domains vì thuật toán sẽ sửa đổi chúng trong quá trình chạy
    csp_copy = {
        'variables': csp['variables'],
        'domains': {k: v[:] for k, v in csp['domains'].items()},
        'neighbors': csp['neighbors']
    }
    return forward_check({}, csp_copy)


def forward_check(assignment, csp):
    """
    FORWARD-CHECK(assignment, csp)
        if assignment is complete then return assignment
        var ← SELECT-UNASSIGNED-VARIABLE(csp)
        for each value in ORDER-DOMAIN-VALUES(var, assignment, csp)
            if value is consistent with assignment then
                add {var = value} to assignment
                removed ← FORWARD-CHECKING(csp, var, value)
                if removed ≠ failure then
                    result ← FORWARD-CHECK(assignment, csp)
                    if result ≠ failure then return result
                restore removed values to domains
                remove {var = value} from assignment
        return failure
    """
    if len(assignment) == len(csp['variables']):
        return assignment

    var = select_unassigned_variable(assignment, csp)

    for value in order_domain_values(var, assignment, csp):
        if is_consistent(var, value, assignment, csp):
            assignment[var] = value

            removed = do_forward_checking(csp, var, value, assignment)

            if removed is not False:  # False represents failure
                result = forward_check(assignment, csp)
                if result is not None:
                    return result
                
                restore_removed_values(csp, removed)
            
            del assignment[var]

    return None


def do_forward_checking(csp, var, value, assignment):
    """
    Thực hiện Forward Checking: 
    Loại bỏ `value` khỏi miền giá trị của các biến kề chưa được gán.
    Nếu có miền nào rỗng, trả về False (thất bại) và khôi phục các giá trị vừa xóa.
    Nếu thành công, trả về danh sách các giá trị đã bị xóa.
    """
    removed = []
    for neighbor in csp['neighbors'][var]:
        if neighbor not in assignment:
            if value in csp['domains'][neighbor]:
                csp['domains'][neighbor].remove(value)
                removed.append((neighbor, value))
                if len(csp['domains'][neighbor]) == 0:
                    # Khôi phục các giá trị đã xóa trước khi báo lỗi
                    restore_removed_values(csp, removed)
                    return False
    return removed


def restore_removed_values(csp, removed):
    for neighbor, value in removed:
        csp['domains'][neighbor].append(value)


def select_unassigned_variable(assignment, csp):
    for var in csp['variables']:
        if var not in assignment:
            return var
    return None


def order_domain_values(var, assignment, csp):
    return list(csp['domains'][var])


def is_consistent(var, value, assignment, csp):
    for neighbor in csp['neighbors'][var]:
        if neighbor in assignment and assignment[neighbor] == value:
            return False
    return True
