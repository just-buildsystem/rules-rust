#!/usr/bin/env python3
# Copyright 2024 Huawei Cloud Computing Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from argparse import ArgumentParser
from collections import defaultdict
import glob
from pprint import pprint
import re
import shutil
import sys
import subprocess
import json
import os
from hashlib import sha256
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Tuple, Union, cast

UPSTREAM_RULES_RUST = "https://github.com/just-buildsystem/rules-rust"

JSON = Union[str, int, float, bool, None, Dict[str, 'JSON'], List['JSON']]

# ------- JSON formating ------------
# inlined to have a self-contained binary
def is_simple(entry: JSON) -> bool:
    if isinstance(entry, list):
        return len(entry) == 0
    if isinstance(entry, dict):
        return len(entry) == 0
    return True


def is_short(entry: Any, indent: int) -> bool:
    return (len(json.dumps(entry)) + indent) < 80


def hdumps(entry: JSON, *, _current_indent: int = 0) -> str:
    if is_short(entry, _current_indent):
        return json.dumps(entry)
    if isinstance(entry, list) and entry:
        result: str = "[ " + hdumps(entry[0],
                                    _current_indent=_current_indent + 2)
        for x in entry[1:]:
            result += "\n" + " " * _current_indent + ", "
            result += hdumps(x, _current_indent=_current_indent + 2)
        result += "\n" + " " * _current_indent + "]"
        return result
    if isinstance(entry, dict) and entry:
        result: str = "{ "
        is_first: bool = True
        for k in entry.keys():
            if not is_first:
                result += "\n" + " " * _current_indent + ", "
            result += json.dumps(k) + ":"
            if is_simple(entry[k]):
                result += " " + json.dumps(entry[k])
            elif is_short(entry[k], _current_indent + len(json.dumps(k)) + 4):
                result += " " + json.dumps(entry[k])
            else:
                result += "\n" + " " * _current_indent + "  "
                result += hdumps(entry[k], _current_indent=_current_indent + 2)
            is_first = False
        result += "\n" + " " * _current_indent + "}"
        return result
    return json.dumps(entry)

# ------- end JSON formating ------------

my_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

HOME = os.environ.get("HOME", "/")
CACHE_ROOT = os.path.join(HOME, ".cache", "crate-index-just")

# used to skip from circular dependencies
visited: Dict[str, bool] = {}

# to generate the repos.json file
repos_json: JSON = dict()

recompute_targets = False
recompute_repos = False
recompute_sources = False
compute_index = False
root_id = None
root_name = None
root_version = None
root_rep_name = None
root_dir = None
relative_path = "."
repo_root = "/"
IMPORTED_REPOS = set()


def split_id(id: str):
    try:
        # metadata provided by stable cargo, as of 2024-03-18
        name, version, source = id.split()
        source = source[1:-1]
    except ValueError as e:
        if id.startswith("registry"):
            # "registry+https://github.com/rust-lang/crates.io-index#libc@0.2.153"
            source, name_version = id.split("#")
            name, version = name_version.split("@")

        elif id.startswith("path"):
            # path+file:///home/username/opt/src/commonlibrary_rust_ylong_runtime#ylong_io@1.0.0
            # or
            # path+file:///tmp/hashbrown#0.14.3
            if id.find("@") >= 0:
                source, name_version = id.split("#")
                name, version = name_version.split("@")
            else:
                source, version = id.split("#")
                name = source.split("/")[-1]
        else:
            print(f"while processing {id=}: {e}", file=sys.stderr)
            exit(1)
    except Exception as e:
        print(f"while processing {id=}: {e}", file=sys.stderr)
        exit(1)

    return name, version, source


def abspath(x: str) -> str:
    return os.path.abspath(x)


def cargo_metadata(
    pkg_name: str,
    root_dir: str,
    cache_dir: Optional[str] = None,
    traverse_dev: bool = False,
) -> JSON:
    metadata_path: Optional[str] = None

    x = subprocess.run(
        "cargo metadata --format-version 1".split(),
        cwd=root_dir,
        capture_output=True,
    )

    if x.returncode != 0:
        print(f"Failed to run cargo: {x.returncode}: {x.stderr}",
              file=sys.stderr)
        exit(x.returncode)
    d: JSON = json.loads(x.stdout)
    if metadata_path:
        with open(metadata_path, "w") as f:
            print(hdumps(d), file=f)
            print(f"stored metadata of {pkg_name} to {metadata_path}",
                  file=sys.stderr)
    return d


def cache_entry_from_hash(hash: str) -> Tuple[str, bool]:
    os.makedirs(CACHE_ROOT, exist_ok=True)
    path = os.path.join(CACHE_ROOT, hash[:2], hash[2:])
    return path, os.path.exists(path)


def repo_name(name: str, version: str = "") -> str:
    return "-".join((name, version))


def bindings(nodes: Any, id: str, keep_dev: bool = True) -> JSON:
    pkg: JSON = {}
    for pkg in nodes:
        if pkg["id"] == id:
            break
    b: JSON = {"rules": "rust-rules"}
    global compute_index
    if compute_index:
        b["index"] = "index"
    for d in pkg["deps"]:
        d_name, d_version, _ = split_id(d["pkg"])
        is_dev = d["dep_kinds"][0]["kind"] == "dev"
        if not is_dev or keep_dev:
            b[d_name] = repo_name(d_name, d_version)
    return b


def bindings_from_tree(key: str, tree_out: JSON) -> JSON:
    b: JSON = {"rules": "rust-rules"}
    global compute_index
    if compute_index:
        b["index"] = "index"
    b.update(tree_out[key]["bindings"])
    return b


def cache_entry(name: str, version: str) -> Tuple[str, bool]:
    key: str = repo_name(name, version)
    hash = sha256(key.encode()).hexdigest()
    return cache_entry_from_hash(hash)  # returns (entry, present)


def fetch_crate_from_crates_io(
    name: str, version: str, rep_name: str, tree_out: JSON
) -> str:
    entry, present = cache_entry(name, version)
    archive = f"{name}.tar.gz"
    archive_path = os.path.join(entry, archive)
    global recompute_repos, repos_json
    if recompute_repos or not present:
        fetch_url = f"https://crates.io/api/v1/crates/{name}/{version}/download"
        tmp_dir = TemporaryDirectory(prefix="cargo-parser-")
        print(f"retrieving: {repo_name(name,version)} from {fetch_url}", end="...",
              file=sys.stderr)
        curl = subprocess.run(
            f"wget {fetch_url} --tries=10 -O {name}.tar.gz".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=tmp_dir.name,
        )
        curl.check_returncode()
        os.makedirs(entry, exist_ok=True)
        shutil.copyfile(os.path.join(tmp_dir.name, archive), archive_path)
        x = subprocess.check_output(
            f"git hash-object {name}.tar.gz".split(), cwd=tmp_dir.name
        )
        repo: JSON = {
            "repository": dict(
                type="archive",
                fetch=fetch_url,
                content=x.decode().split()[0],
                subdir=rep_name,
                distfile=f"{rep_name}.tar.gz",
            )
        }
        repos: JSON = dict()
        repos[rep_name] = repo
        repos[rep_name]["bindings"] = bindings_from_tree(rep_name, tree_out)
        repos[rep_name]["target_root"] = "external-deps"
        repos[rep_name]["target_file_name"] = f"TARGETS.{rep_name}"
        with open(file=os.path.join(entry, "repos.json"), mode="w") as f:
            print(hdumps(repos), file=f)
        repos_json.update(repos)
        print("done", file=sys.stderr)
    else:
        with open(file=os.path.join(entry, "repos.json")) as f:
            d = json.load(f)
        repos_json.update(d)
    return archive_path


def local_repo(
    name: str,
    version: str,
    rep_name: str,
    tree_out: JSON,
    is_main=False,
    path: str = ".",
) -> str:
    global repos_json
    print(f"local: {repo_name(name,version)}", end="...", file=sys.stderr)

    repo: JSON = {
        "repository": dict(
            type="file",
            path=path,
        )
    }
    repos: JSON = dict()
    key = name if is_main else rep_name
    repos[key] = repo
    repos[key]["bindings"] = bindings_from_tree(rep_name, tree_out)

    repos_json.update(repos)
    print("done", file=sys.stderr)

def compute_srcs(root_dir: str, name: str, version: str) -> List[Any]:
    entry, exists = cache_entry(name, version)
    if not exists:
        os.makedirs(entry)
    srcs_file = os.path.join(entry, "srcs.json")
    global recompute_sources
    if not recompute_sources and os.path.exists(srcs_file):
        with open(srcs_file) as f:
            return json.load(f)

    srcs: List[Any] = list()

    for f in glob.glob(f"{root_dir}/**/*.rs", recursive=True):
        f = os.path.relpath(f, root_dir)
        if (
            not f.startswith("example")
            and not f.startswith("test")
            and not f.startswith("bench")
        ):
            srcs.append(f)

    with open(srcs_file, "w") as f:
        print(json.dumps(srcs), file=f)
    return sorted(srcs)


def to_underscore(x: str):
    return x.replace("-", "_")


def active_deps(
    nodes: Any, pkg: JSON, tree_out: JSON, keep_dev: bool
) -> Tuple[List[Any], JSON]:
    p: JSON = {}
    for p in nodes:
        if p["id"] == pkg["id"]:
            break

    b: List[Any] = list()
    for d in p["deps"]:
        d_name, _, _ = split_id(d["pkg"])

        is_dev: bool = d["dep_kinds"][0]["kind"] == "dev"
        if not is_dev or keep_dev:
            b.append(["@", d_name, "", d_name])
    return b, p["features"]


def active_deps_from_tree(
    key: str, tree_out: JSON, root_name: str = None, is_dev: bool = False
) -> Tuple[List[Any], JSON]:
    dep_names = tree_out[key]["bindings"].keys()
    deps = [["@", x, "", to_underscore(x)] for x in dep_names]
    if is_dev:
        deps.append(root_name)
    return deps, tree_out[key]["features"]


def compute_targets(
    metadata: JSON, pkg: JSON, tree_out: JSON, dev: bool = False, is_main: bool = False
) -> JSON:
    name, version, _ = split_id(pkg["id"])
    entry, _ = cache_entry(name, version)
    targets_file = os.path.join(entry, f"TARGETS.{repo_name(name,version)}")
    if os.path.exists(targets_file) and not recompute_targets:
        with open(targets_file) as f:
            return json.load(f)
    root_dir: str = os.path.dirname(pkg["manifest_path"])
    targets: JSON = dict()
    has_build_script = False
    for t in pkg["targets"]:
        t_kind = t["kind"][0]
        if t_kind == "custom-build":
            has_build_script = True
            break

    config = ["ARCH", "HOST_ARCH", "TARGET_ARCH", "ENV", "TOOLCHAIN_CONFIG"]
    t: JSON = {}
    for t in pkg["targets"]:
        t_kind = t["kind"][0]
        is_dev_target = t_kind in ["test", "bench", "example"]
        unsupported_target = t_kind in ["bench"]
        d_build_script: Optional[JSON] = None
        rep_name = repo_name_from_id(pkg["id"])
        version_lst = version.split(".")
        if not dev and is_dev_target:
            continue
        if unsupported_target:
            print(f"{t['name']}: rust {t_kind} target type not yet supported",
                  file=sys.stderr)
            continue

        if t_kind == "custom-build":
            # we will use foreign cargo rules to build
            d_build_script = dict()
            d_build_script["type"] = "@ rules cargo build_script".split()
            d_build_script["name"] = ["build_script"]
            crate_root = os.path.relpath(t["src_path"], root_dir)
            d_build_script["crate_root"] = [crate_root]
            d_build_script["arguments_config"] = config
            d_build_script["edition"] = [t["edition"]]
            d_build_script["stage"] = [rep_name]
            d_build_script["deps"], d_build_script["cargo_features"] = (
                active_deps_from_tree(rep_name, tree_out)
            )
            d_build_script["version"] = version_lst
            d_build_script["pkg_name"] = [name]
            targets["build_script"] = d_build_script
            has_build_script = True
            continue

        crate_root = os.path.relpath(t["src_path"], root_dir)
        d: JSON = dict()
        d["type"] = just_type(t, False)
        d["name"] = [to_underscore(t["name"])]
        d["crate_root"] = [crate_root]
        if not is_dev_target:
            d["srcs"] = compute_srcs(root_dir, name, version)
        d["edition"] = [t["edition"]]
        d["arguments_config"] = config
        d["deps"], d["cargo_features"] = active_deps_from_tree(
            rep_name, tree_out, to_underscore(name), is_dev_target
        )
        d["stage"] = [rep_name]
        d["version"] = version_lst
        d["pkg_name"] = [name]
        if not is_main and t["name"] == pkg["name"]:
            internal_name = f"{to_underscore(t['name'])}-internal"
            d["arguments_config"] = config
            targets[to_underscore(t["name"])] = {
                "type": "export",
                "target": internal_name,
                "flexible_config": config,
            }
            targets[internal_name] = d
            if has_build_script:
                targets[internal_name]["build_script"] = ["build_script"]
                global compute_index
                if compute_index:
                    targets["tree"] = {
                        "type": "install",
                        "dirs": [[["TREE", None, "."], rep_name]],
                    }
                    targets["cargo-srcs"] = {
                        "type": "generic",
                        "cmds": [f"mv index {rep_name}"],
                        "deps": ["tree", ["@", "index", "", "index"]],
                        "out_dirs": [rep_name],
                    }
                    targets["config.toml"] = {
                        "type": "generic",
                        "cmds": [
                            f'echo "[source.crates-io]\\nreplace-with = \\"vendored-sources\\"\\n\\n[source.vendored-sources]\\ndirectory = \\"index\\"\\n" > config.toml'
                        ],
                        "outs": ["config.toml"],
                    }
                    targets["cargo-srcs"]["cmds"].append(
                        f"mkdir -p {rep_name}/.cargo && mv config.toml {rep_name}/.cargo"
                    )
                    targets["cargo-srcs"]["deps"].append("config.toml")
            continue
        targets[t["name"]] = d

    for f, _ in pkg["features"].items():
        d = defaultdict(list)
        d["type"] = ["@", "rules", "cargo", "feature"]
        d["name"] = [f]
        targets[f] = dict(d)
    with open(targets_file, "w") as f:
        print(hdumps(targets), file=f)
    return targets


kinds: Dict[str, str] = dict(bin="binary", lib="library", example="binary")


def just_type(target: JSON, use_foreign_cargo: bool) -> List[str]:
    if use_foreign_cargo:
        return "@ rules cargo library".split()
    t: List[str] = ["@", "rules", "rust"]
    k: str = target["kind"][0]
    return t + [kinds.get(k, k)]


def parse_metadata(metadata: JSON, tree_out: JSON) -> None:
    nodes = metadata["resolve"]["nodes"]
    global root_id, root_name, root_version, root_rep_name
    root_id = metadata["resolve"]["root"]
    if root_id:
        root_name, root_version, _ = split_id(root_id)
        root_rep_name = repo_name(root_name, root_version)

    # generate repos.json
    for p in nodes:
        name, version, source = split_id(p["id"])
        rep_name = repo_name(name, version)
        if rep_name in tree_out:
            if rep_name == root_rep_name:
                local_repo(name, version, rep_name, tree_out, is_main=True, path=relative_path)
                continue

            if source == "registry+https://github.com/rust-lang/crates.io-index":
                fetch_crate_from_crates_io(name, version, rep_name, tree_out)
            elif source.startswith("path+file"):
                path = source.split("#")[0][12:]
                local_repo(
                    name,
                    version,
                    rep_name,
                    tree_out,
                    path=os.path.relpath(path, repo_root),
                    is_main=True,
                )


def repo_name_from_id(id: str):
    name, version, _ = split_id(id)
    return repo_name(name, version)


def parse_tree_entry(x: str) -> Tuple[int, str, str, List[Any]]:
    match = re.match(r"^\d+", x)
    if not match:
        print(f"failed to parse tree entry: {x}", file=sys.stderr)
        exit(1)
    depth = int(match.group())
    rest = x[match.span()[-1] :].replace('"', "").split()
    rest = [x for x in rest if not x.startswith("(")]
    name, version, features = split_tree_entry(rest)
    return depth, name, version, features


def split_tree_entry(x: List[str]) -> Tuple[str, str, List[Any]]:
    if len(x) < 2:
        print(f"malformed tree entry: {x}", file=sys.stderr)
        exit(1)
    name: str = x[0]
    version: str = x[1][1:]  # drop the leading "v"
    features: List[Any] = []
    if len(x) == 3:
        features = x[2].split(",")
    return name, version, features


def parse_cargo_tree(root_dir: str) -> JSON:
    tree = subprocess.run(
        ["cargo", "tree", "--prefix", "depth", "-f", '"{p} {f}"'],
        cwd=root_dir,
        capture_output=True,
    )

    if tree.returncode != 0:
        print(f"Failed to run cargo: {tree.returncode}: {tree.stderr}",
              file=sys.stderr)
        exit(tree.returncode)
    tree = tree.stdout.decode().split("\n")
    deps: JSON = defaultdict(lambda: cast(JSON, dict(bindings={})))
    depth_package = {}
    for l in tree:
        # skip empty lines
        if not l:
            continue
        depth, name, version, features = parse_tree_entry(l)
        pkg = repo_name(name, version)
        deps[pkg]["features"] = features
        deps[pkg]["name"] = name
        depth_package[depth] = pkg
        if depth > 0:
            parent = depth_package[depth - 1]
            deps[parent]["bindings"].update({name: pkg})

    return dict(deps)

def merge_repos(base_config, new_repos, entry_point_name):
    old_names = set(base_config["repositories"].keys())
    entry_name = entry_point_name
    if entry_name in old_names:
        count = 0
        entry_name = "%s (%d)" % (entry_point_name, count)
        while entry_name in old_names:
            count += 1
            entry_name = "%s (%d)" % (entry_point_name, count)
    print("Adding to repository config the new rust repository %r with dependencies"
          % (entry_name,), file=sys.stderr)

    name_mapping = {entry_point_name: entry_name}
    for k in new_repos.keys():
        if k == entry_point_name:
            continue
        preferred_name = "%s/%s" % (entry_name, k)
        if not preferred_name in old_names:
            name_mapping[k] = preferred_name
            old_names.add(preferred_name)
            continue
        count = 0
        new_name = "%s (%d)" % (preferred_name, count)
        while new_name in old_names:
            count += 1
            new_name = "%s (%d)" % (preferred_name, count)
        name_mapping[k] = new_name
        old_names.add(new_name)
    renamed_repos = {}
    for k, v in new_repos.items():
        if k in IMPORTED_REPOS:
            # no renaming done within the definition this repository definition
            renamed_repos[name_mapping[k]] = v
        else:
            if isinstance(v, str):
                if v in name_mapping:
                    renamed_repos[name_mapping[k]] = name_mapping[v]
                else:
                    renamed_repos[name_mapping[k]] = v
            else:
                # has to be a dict; rename bindings, and roots, if given
                new_v = v
                ws_root = new_v["repository"]
                if isinstance(ws_root, str):
                    if ws_root in name_mapping:
                        new_v = dict(new_v, **{"repository": name_mapping[ws_root]})
                bindings = v.get("bindings", {})
                new_bindings = {}
                for n, m in bindings.items():
                    if m in name_mapping:
                        new_bindings[n] = name_mapping[m]
                    else:
                        new_bindings[n] = m
                if new_bindings:
                    new_v = dict(new_v, **{"bindings": new_bindings})
                for root in ["target_root", "rule_root", "expression_root"]:
                    if root in new_v:
                        r_name = new_v[root]
                        if r_name in name_mapping:
                            new_v = dict(new_v, **{root: name_mapping[r_name]})
                renamed_repos[name_mapping[k]] = new_v
    all_repos = dict(base_config["repositories"], **renamed_repos)
    return dict(base_config, **{"repositories": all_repos})

def main():
    parser = ArgumentParser()
    parser.add_argument(
        "root_dir", help="directory where the Cargo.toml file is located; relative to repo_root"
    )
    parser.add_argument("-t", "--recompute-targets", action="store_true")
    parser.add_argument("-r", "--recompute-repos", action="store_true")
    parser.add_argument("-s", "--recompute-sources", action="store_true")
    parser.add_argument("-I", "--compute-index", action="store_true")
    parser.add_argument(
        "-g",
        "--to-git",
        action="store_true",
    )
    parser.add_argument(
        "--rules", dest="rules",
        help="Rust-rules repository name in the base configuration",
        metavar="name")
    parser.add_argument("--local-crate-cache", dest="cache_root")
    parser.add_argument("--repo-root", dest="repo_root")
    args = parser.parse_args()
    global repo_root, root_dir, relative_path
    repo_root = args.repo_root or "."
    repo_root = os.path.abspath(repo_root)
    root_dir = os.path.join(repo_root, args.root_dir)
    relative_path = os.path.relpath(root_dir, repo_root)
    global CACHE_ROOT
    if args.cache_root:
        CACHE_ROOT = args.cache_root

    tree_out: JSON = parse_cargo_tree(root_dir)
    global recompute_targets, recompute_repos, recompute_sources, compute_index, root_name, root_version
    recompute_repos = args.recompute_repos
    recompute_targets = args.recompute_targets
    recompute_sources = args.recompute_sources
    compute_index = args.compute_index
    pprint(args, stream=sys.stderr)

    base_config = json.load(sys.stdin)
    metadata = cargo_metadata(
        os.path.basename(os.path.abspath(root_dir)), root_dir, cache_dir=root_dir
    )
    parse_metadata(metadata, tree_out)

    # if the provided repos.template.json does not contain a "main" let's assume it is the current project
    # this should be useful only when transitioning a Rust-only Cargo-based project
    if "main" not in base_config:
        base_config["main"] = root_name
    if "repositories" not in base_config:
        base_config["repositories"] = {}

    # let's sort to have "main" at the beginning of repos.json
    base_config = {k: v for k, v in sorted(base_config.items())}

    if compute_index:
        index = sorted(repos_json.keys())
        repos_json["index"] = {
            "repository": {"type": "distdir", "repositories": index},
            "target_file_name": "TARGETS.index",
            "target_root": "external-deps",
        }

    repos_json["external-deps"] = {
        "repository": {"type": "file",
                       "path": "etc/deps-rust"}
    }

    if args.rules:
        repos_json["rust-rules-root"] = base_config["repositories"][args.rules]
        global IMPORTED_REPOS
        IMPORTED_REPOS.add("rust-rules-root")
    else:
        # Use git to find out the head commit of the upstream rules-rust
        head_commit=subprocess.run(
            ["git", "ls-remote", UPSTREAM_RULES_RUST, "master"],
            stdout=subprocess.PIPE).stdout.decode('utf-8').split('\t')[0]
        repos_json["rust-rules-root"] = {
            "repository":
            {"type": "git",
             "repository": UPSTREAM_RULES_RUST,
             "branch": "master",
             "commit": head_commit,
             "subdir": "rules"
             }
        }

    repos_json["rust-rules-defaults"] = {
        "repository": {"type": "file",
                       "path": "etc/defaults"}
    }

    if args.to_git:
        for k in ["external-deps", "rust-rules-root", "rust-rules-defaults"]:
            repos_json[k]["repository"]["pragma"] = {"to_git": True}

    repos_json["rust-rules"] = {
        "repository": "rust-rules-root",
        "target_root": "rust-rules-defaults",
        "rule_root": "rust-rules-root",
        "bindings": {"orig-rules": "rust-rules-root"},
        "target_file_name": "TARGETS.cargo_import"
    }

    main_rep = repo_name(root_name, root_version)
    print(hdumps(merge_repos(base_config, repos_json, root_name)))

    ext = os.path.join(repo_root, "etc", "deps-rust")
    os.makedirs(ext, exist_ok=True)

    defaults_dict = {
        "defaults": {
            "type": "defaults",
            "base": [["@", "orig-rules", "rust", "defaults"]],
        }
    }

    defaults_dir = os.path.join(repo_root, "etc", "defaults", "rust")
    os.makedirs(defaults_dir, exist_ok=True)
    with open(os.path.join(defaults_dir, "TARGETS.cargo_import"), "w") as f:
        print(hdumps(defaults_dict), file=f)

    for pkg in metadata["packages"]:
        rep_name = repo_name_from_id(pkg["id"])
        if rep_name in tree_out:
            if rep_name == main_rep:
                with open(os.path.join(root_dir, "TARGETS"), "w") as f:
                    print(
                        hdumps(
                            compute_targets(
                                metadata, pkg, tree_out, is_main=True, dev=True
                            )
                        ),
                        file=f,
                    )
                continue

            if pkg["id"].startswith("path+file"):
                path = pkg["id"].split("#")[0][12:]
                with open(os.path.join(path, "TARGETS"), "w") as f:
                    print(
                        hdumps(
                            compute_targets(
                                metadata, pkg, tree_out, is_main=True, dev=True
                            )
                        ),
                        file=f,
                    )

            with open(os.path.join(ext, f"TARGETS.{rep_name}"), "w") as f:
                print(hdumps(compute_targets(metadata, pkg, tree_out)), file=f)


main()
