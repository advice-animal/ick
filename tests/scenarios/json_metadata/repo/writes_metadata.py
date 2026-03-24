import json
import os
import sys

output_dir = os.environ["ICK_OUTPUT_DIR"]
with open(os.path.join(output_dir, "metadata.json"), "w") as f:
    json.dump({"findings": [{"line": 1, "message": "test metadata yay"}]}, f)
print("found issues")
sys.exit(99)
