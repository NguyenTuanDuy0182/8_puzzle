from algorithm.backtracking_search import backtracking_search
from algorithm.forward_checking_search import forward_checking_search
from algorithm.AC_3 import ac3_search
from algorithm.min_conflicts import min_conflicts

class MapColoringCSP:
    def __init__(self):
        self.variables = ['WA', 'NT', 'SA', 'Q', 'NSW', 'V', 'T']
        # Đỏ, Xanh lá, Xanh dương
        self.colors = ['#ff4d4d', '#4dff4d', '#4d4dff'] 
        self.domains = {v: self.colors[:] for v in self.variables}
        self.neighbors = {
            'WA': ['NT', 'SA'],
            'NT': ['WA', 'SA', 'Q'],
            'SA': ['WA', 'NT', 'Q', 'NSW', 'V'],
            'Q':  ['NT', 'SA', 'NSW'],
            'NSW': ['Q', 'SA', 'V'],
            'V':  ['SA', 'NSW'],
            'T':  []
        }

    def get_csp_dict(self):
        return {
            'variables': self.variables,
            'domains': self.domains,
            'neighbors': self.neighbors
        }

class ColoringController:
    def __init__(self):
        self.csp = MapColoringCSP()

    def solve_backtracking(self):
        """Gọi thuật toán Backtracking Search, trả về dictionary gán màu hoặc None."""
        return backtracking_search(self.csp.get_csp_dict())

    def solve_forward_checking(self):
        """Gọi thuật toán Forward Checking Search, trả về dictionary gán màu hoặc None."""
        return forward_checking_search(self.csp.get_csp_dict())

    def solve_ac3(self):
        """Gọi thuật toán AC-3 Search, trả về dictionary gán màu hoặc None."""
        return ac3_search(self.csp.get_csp_dict())

    def solve_min_conflicts(self):
        """Gọi thuật toán Min-Conflicts Search, trả về dictionary gán màu hoặc None."""
        return min_conflicts(self.csp.get_csp_dict(), max_steps=1000)
