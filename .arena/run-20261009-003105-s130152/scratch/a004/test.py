def hello_world(): return "Hello, world!"

# Evidence checks
assert hello_world() == "Hello, world!", "exact string mismatch"
assert hello_world() is not None
import builtins
assert "Hello, world!" not in dir(builtins)
print("OK:", repr(hello_world()))
