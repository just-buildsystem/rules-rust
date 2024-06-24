import json
import os
from typing import List

def lines(doc:List[str]):
    return '\n'.join(doc)

def gen_doc(dir: str, f):

    with open(os.path.join(dir, "RULES")) as r:
        rules = json.load(r)

    for k, v in sorted(rules.items()):
        print(f"### `[\"{os.path.basename(dir)}\", \"{k}\"]`\n\n {lines(v['doc'])}\n", file=f)
        print("| Field | Description |", file=f)
        print("| ----- | ----------- |", file=f)
        for field, doc in sorted(v["field_doc"].items()):
            print(f"| `\"{field}\"` | {' '.join(doc)} |", file=f)
        print(file=f)


def main():
    with open("README.md", "w") as f:
        print(
            """# Rust rules for the [`just`](https://github.com/just-buildsystem/justbuild) build system

A collection of rules for building Rust libraries, binaries and unit tests.
""",
            file=f,
        )
        gen_doc("rules/rust", f)
        gen_doc("rules/cargo", f)


main()
