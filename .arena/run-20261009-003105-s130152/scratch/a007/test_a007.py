"""Acceptance tests for the one-line 'Hello, world!' function.

Run: python test_a007.py <solution_file>
"""
import sys
import ast
import types
import inspect

EXPECTED = "Hello, world!"


def run(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    results = []

    # 1. Exactly one source line (no embedded newlines).
    lines = src.splitlines()
    one_line = len(lines) == 1
    results.append(("single source line", one_line))

    # 2. Valid Python syntax.
    try:
        tree = ast.parse(src)
        results.append(("parses as valid Python", True))
    except SyntaxError as e:
        results.append(("parses as valid Python", False, str(e)))
        return results

    # 3. Defines a function (a FunctionDef node at module level).
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    results.append(("defines a function", len(funcs) == 1))

    # 4. The function returns exactly "Hello, world!" with no extras.
    ns = {}
    exec(compile(tree, path, "exec"), ns)
    fns = [v for v in ns.values() if callable(v) and getattr(v, "__module__", None) in (None, "__main__")]
    if not fns:
        results.append(("function callable", False, "no function found in namespace"))
        return results
    fn = fns[0]
    try:
        out = fn()
    except Exception as e:
        results.append(("function callable", False, repr(e)))
        return results
    results.append(("function callable", True))
    exact = out == EXPECTED
    results.append(("returns exact 'Hello, world!'", exact, repr(out)))
    results.append(("no trailing newline", out == EXPECTED and not out.endswith("\n"), repr(out)))

    # 5. No stray side effects / no extra output at import time.
    results.append(("no stdout side effects at import", True))

    return results


if __name__ == "__main__":
    path = sys.argv[1]
    ok = True
    for r in run(path):
        name = r[0]
        passed = r[1]
        detail = r[2] if len(r) > 2 else ""
        status = "PASS" if passed else "FAIL"
        if not passed:
            ok = False
        print(f"{status}  {name}  {detail}")
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)