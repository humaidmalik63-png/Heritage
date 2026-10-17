from a002 import hello

result = hello()
expected = "Hello, world!"
if result == expected:
    print("PASS: " + result)
else:
    print("FAIL: got " + repr(result) + ", expected " + repr(expected))