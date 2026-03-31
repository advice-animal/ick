import json
import os
import sys

output_dir = os.environ["ICK_OUTPUT_DIR"]
findings = []
for filename in sys.argv[1:]:
    findings.append({"file": filename, "line": 1, "message": f"test metadata for {filename}"})

with open(os.path.join(output_dir, "metadata.json"), "w") as f:
    json.dump({"findings": findings}, f)

sys.exit(99)
