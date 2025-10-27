import sys
import argparse
from collections import deque
from typing import List

EPS = 1e-9

def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="assignment_problem.py",
        description="Solve the assignment problem via the Hungarian method (course-specific)."
    )
    p.add_argument("-v", "--verbose", action="store_true", help="print algorithm progress verbosely")
    p.add_argument("--check", action="store_true",
                   help="validate the solution (no extra stdout on success; errors to stderr)")
    p.add_argument("costs_file", help="path to CSV file with the cost matrix")
    return p.parse_args(argv)

def _fail(msg: str, exit_code: int = 1):
    import sys as _sys
    _sys.stderr.write(msg.strip() + "\n")
    _sys.exit(exit_code)

def read_cost_matrix(path: str) -> List[List[float]]:
    M: List[List[float]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                s = line.strip()
                if not s:
                    continue
                parts = [t.strip() for t in s.split(",")]
                if parts == [""]:
                    continue
                try:
                    row = [float(x) for x in parts]
                except ValueError as e:
                    raise ValueError(f"Non-numeric value at line {lineno}: {line.strip()}") from e
                for x in row:
                    if x != x or x in (float('inf'), float('-inf')):
                        raise ValueError(f"Invalid numeric (NaN/Inf) at line {lineno}: {line.strip()}")
                M.append(row)
    except FileNotFoundError as e:
        raise ValueError(f"Input file not found: {path}") from e
    except OSError as e:
        raise ValueError(f"Cannot read file: {path}") from e

    if not M:
        raise ValueError("Empty cost matrix (no numeric rows found).")

    m = len(M[0])
    for r_i, r in enumerate(M, start=1):
        if len(r) != m:
            raise ValueError(f"Inconsistent row length at row {r_i}: expected {m} columns, got {len(r)}.")

    if len(M) != m:
        raise ValueError(f"Matrix must be square (rows={len(M)} != cols={m}).")

    return M

MSG_TITLE = "=== Assignment Problem ==="
MSG_SIZE  = "{n}x{n} cost matrix:"
MSG_MATCHING_SIZE = "--- Matching size {k}, start from free row r={r} ---"
MSG_SET_S = "Set S: {content}"
MSG_SET_T = "Set T: {content}"
MSG_TIGHT_FREE = "Tight edge discovered: ({r}, {c}). Column {c} is free: AUGMENT MATCHING"
MSG_TIGHT_MATCHED = "Tight edge discovered: ({r}, {c}). Column {c} is matched to row {r2}: EXTEND TREE"
MSG_NO_TIGHT = "No tight edge outside T. Update potentials by delta={delta}"
MSG_INIT = "Initial potentials:"
MSG_U = "U: {arr}"
MSG_V = "V: {arr}"
MSG_AUG_PATH = "Augmenting path: {path}"
MSG_MATCHING = "Matching:{space}{list}"
MSG_REMOVE = "Removing edge R{r}->C{c}"
MSG_ADD = "Adding edge R{r}->C{c}"
MSG_FINAL = "=== Final Result ==="
MSG_ROW = "row {r} -> col {c} cost={w:.1f}"
MSG_TOTAL = "Total cost: {total:.1f}"

def fmt_row(row: List[float]) -> str:
    return " ".join(f"{x:.2f}" for x in row)
def fmt_arr(arr: List[float]) -> str:
    return "[ " + " ".join(f"{x:.2f}" for x in arr) + " ]"

def print_intro(cost: List[List[float]]) -> None:
    n = len(cost)
    print(MSG_TITLE)
    print(MSG_SIZE.format(n=n))
    for row in cost:
        print(fmt_row(row))
    print()

def print_initial_potentials(U: List[float], V: List[float]) -> None:
    print(MSG_INIT)
    print(MSG_U.format(arr=fmt_arr(U)))
    print(MSG_V.format(arr=fmt_arr(V)))
    print()

def match_str(match_row: List[int]) -> str:
    parts = []
    for i, j in enumerate(match_row):
        if j != -1:
            parts.append(f"R{i}->C{j}")
    return ", ".join(parts)

def print_sets(S, T) -> None:
    print(MSG_SET_S.format(content="{" + ", ".join(str(x) for x in sorted(S)) + "}"))
    print(MSG_SET_T.format(content="{" + ", ".join(str(x) for x in sorted(T)) + "}"))

def build_augment_info(parent_col, match_row, match_col, r0, free_c):
    steps = []
    to_remove = []
    to_add = []
    j = free_c
    while True:
        i = parent_col[j]
        steps.append((i, j))
        j_prev = match_row[i]
        to_add.append((i, j))
        if j_prev != -1:
            to_remove.append((i, j_prev))
            j = j_prev
        if i == r0:
            break
    steps.reverse()
    tokens = []
    for idx, (i, j) in enumerate(steps):
        token = f"R{i}->C{j}"
        tokens.append(token if idx == 0 else "=>" + token)
    return "".join(tokens), to_remove[::-1], to_add[::-1]

def hungarian_verbose(cost: List[List[float]], verbose: bool = False):
    n = len(cost)
    U = [min(row) for row in cost]
    V = [0.0]*n

    if verbose:
        print_intro(cost)
        print_initial_potentials(U, V)

    match_row = [-1]*n
    match_col = [-1]*n

    def is_tight(i: int, j: int) -> bool:
        return abs((U[i] + V[j]) - cost[i][j]) <= EPS

    matched = 0
    while matched < n:
        r0 = next(i for i in range(n) if match_row[i] == -1)

        if verbose:
            print(MSG_MATCHING_SIZE.format(k=matched, r=r0))

        S = {r0}
        T = set()
        parent_row = [-1]*n
        parent_col = [-1]*n

        if verbose:
            print_sets(S, T)

        queue = deque([r0])
        augmented = False

        while not augmented:
            progressed_this_round = False
            next_queue = deque()

            while queue and not augmented:
                r = queue.popleft()
                for c in range(n):
                    if c in T:
                        continue
                    if not is_tight(r, c):
                        continue

                    parent_col[c] = r
                    if match_col[c] == -1:
                        progressed_this_round = True
                        if verbose:
                            print(MSG_TIGHT_FREE.format(r=r, c=c))
                            path_str, to_remove, to_add = build_augment_info(parent_col, match_row, match_col, r0, c)
                            print(MSG_AUG_PATH.format(path=path_str))
                            prev = match_str(match_row)
                            print(MSG_MATCHING.format(space=(" " if prev else ""), list=prev))
                            for (ri, cj) in to_remove:
                                print(MSG_REMOVE.format(r=ri, c=cj))
                            for (ri, cj) in to_add:
                                print(MSG_ADD.format(r=ri, c=cj))

                        matched_before = matched  
                        j = c
                        while True:
                            i = parent_col[j]
                            j_prev = match_row[i]
                            match_row[i] = j
                            match_col[j] = i
                            j = j_prev
                            if i == r0:
                                break
                        matched += 1
                        assert matched == matched_before + 1
                        augmented = True

                        if verbose:
                            now = match_str(match_row)
                            print(MSG_MATCHING.format(space=(" " if now else ""), list=now))

                        break
                    else:
                        r2 = match_col[c]
                        if r2 not in S:
                            parent_row[r2] = c
                            S.add(r2)
                            T.add(c)
                            next_queue.append(r2)
                            progressed_this_round = True
                            if verbose:
                                print(MSG_TIGHT_MATCHED.format(r=r, c=c, r2=r2))
                                print_sets(S, T)
            if augmented:
                break
            if not progressed_this_round:
                delta = float("inf")
                for r in S:
                    for c in range(n):
                        if c in T:
                            continue
                        slack = cost[r][c] - U[r] - V[c]
                        if slack < delta:
                            delta = slack

                for r in S:
                    U[r] += delta
                for c in T:
                    V[c] -= delta
                if verbose:
                    dprint = int(delta) if abs(delta - round(delta)) < EPS else delta
                    print(MSG_NO_TIGHT.format(delta=dprint))
                    print(MSG_U.format(arr=fmt_arr(U)))
                    print(MSG_V.format(arr=fmt_arr(V)))
                queue = deque(sorted(S))
            else:
                queue = next_queue

    assignment = [(i, match_row[i], cost[i][match_row[i]]) for i in range(n)]
    cols = [c for _, c, _ in assignment]
    if len(set(cols)) != n:
        raise RuntimeError("invalid assignment: duplicate columns in final matching")
    total = sum(w for _,_,w in assignment)
    return assignment, total

def print_final(assignment, total):
    for r, c, w in assignment:
        print(MSG_ROW.format(r=r, c=c, w=w))
    print(MSG_TOTAL.format(total=total)) 

def _check_solution(cost, assignment, total):
    n = len(cost)
    used_cols = set()
    recomputed = 0.0
    for r, c, w in assignment:
        if not (0 <= r < n and 0 <= c < n):
            _fail("Error: assignment contains out-of-range indices.", exit_code=2)
        if c in used_cols:
            _fail("Error: duplicate column in assignment.", exit_code=2)
        used_cols.add(c)
        if abs(w - cost[r][c]) > EPS:
            _fail("Error: reported cost does not match matrix entry.", exit_code=2)
        recomputed += w
    if abs(recomputed - total) > EPS:
        _fail("Error: Total cost does not equal sum of row costs.", exit_code=2)
    if len(used_cols) != n:
        _fail("Error: not a perfect matching (some columns unused).", exit_code=2)

def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        cost = read_cost_matrix(args.costs_file)
        assignment, total = hungarian_verbose(cost, verbose=args.verbose)
        if args.check:
            _check_solution(cost, assignment, total)
        if args.verbose:
            print(MSG_FINAL)
        print_final(assignment, total)
    except (ValueError, RuntimeError) as e:
        _fail(f"Error: {e}", exit_code=1)

if __name__ == "__main__":
    main()
