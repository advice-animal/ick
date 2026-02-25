"""Test rule that imports from a helper module in the same repo."""

from .helper_module import get_greeting

if __name__ == "__main__":
    print(get_greeting())
