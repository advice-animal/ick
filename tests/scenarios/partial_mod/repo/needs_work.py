import sys

# Modify a file,
with open("pyproject.toml", "a") as f:
    f.write("# Add a comment\n")

# and say more needs to be done.
print("This repo needs work!")
sys.exit(99)
