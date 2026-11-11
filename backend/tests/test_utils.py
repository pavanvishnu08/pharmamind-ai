"""
PharmaMind AI - Test Utilities
Provides synchronous coroutine driver to execute async pipelines deterministically
on Windows without requiring loopback socketpair bindings.
"""

from typing import Coroutine, Any

def run_sync(coro: Coroutine) -> Any:
    """
    Drive a coroutine (and any nested awaited coroutines) to completion synchronously
    without triggering OS-level loopback socketpair creation.
    """
    stack = [coro]
    val = None
    while stack:
        try:
            val = stack[-1].send(val)
            if hasattr(val, "send"):  # Nested coroutine yielded
                stack.append(val)
                val = None
        except StopIteration as e:
            stack.pop()
            val = e.value
    return val

