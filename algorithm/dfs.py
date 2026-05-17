def neighbors(state):
    zero = state.index(0)
    x, y = divmod(zero, 3)

    deltas = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    for dx, dy in deltas:
        nx, ny = x + dx, y + dy

        if 0 <= nx < 3 and 0 <= ny < 3:
            nidx = nx * 3 + ny

            lst = list(state)
            lst[zero], lst[nidx] = lst[nidx], lst[zero]

            yield tuple(lst)


def solution(node, parent):
    path = [node]

    while parent[node] is not None:
        node = parent[node]
        path.append(node)

    return list(reversed(path))


def dfs_with_stats(start, goal):

    node = start

    if node == goal:
        return [node], 1

    frontier = []
    frontier.append(node)

    explored = set()

    parent = {
        start: None
    }

    visited_count = 1

    while frontier:

        node = frontier.pop()

        explored.add(node)

        for child in neighbors(node):

            if child not in explored and child not in frontier:

                parent[child] = node
                visited_count += 1

                if child == goal:
                    return solution(child, parent), visited_count

                frontier.append(child)

    return None, visited_count