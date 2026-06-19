import ast
import os
import subprocess
import sys
import json
MAX_LINES = 100
repo = os.nviron["REPO"]
pr_number = os.environ["PR_NUMBER"]
token = os.environ["GITHUB_TOKEN"]

def post_comment(message):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    payload = {"body": message}

    subprocess.run([
        "curl",
        "-X", "POST",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json",
        url,
        "-d", json.dumps(payload)
    ])

python_files = []
for root, dirs, files in os.walk("."):
    if ".git" in root:
        continue

    for file in files:
        if file.endswith(".py"):
            python_files.append(os.path.join(root, file))

failed = False

result = subprocess.run(
    ["pycodestyle"] + python_files,
    capture_output=True,
    text=True
)

if result.stdout:
    post_comment(
        "## Pycodestyle Violations\n```text\n"
        + result.stdout +
        "\n```"
    )
    failed = True

for file in python_files:
    with open(file) as f:
        lines = len(f.readlines())

    if lines > MAX_LINES:
        post_comment(
            f" `{file}` has {lines} lines. "
            f"Maximum allowed is {MAX_LINES}."
        )
        failed = True
for file in python_files:
    with open(file, "r") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if ast.get_docstring(node) is None:
                post_comment(
                    f" Function `{node.name}` in "
                    f"`{file}` is missing a docstring."
                )
                failed = True
if failed:
    sys.exit(1)

print("All checks passed!")
