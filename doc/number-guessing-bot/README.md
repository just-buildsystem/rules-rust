# Transitioning an existing Cargo-based Rust project

In this tutorial, we will write a simple c++ "bot" that will play the
`guessing_game` of the [previous tutorial](../number-guessing/README.md). The
focus is not the implementation but how we can automatically generate the
required `repos.json` file.

## Project structure

```sh
$ tree
.
├── bot.cpp
├── etc
│   ├── gen-repos.sh
│   └── repos.template.json
├── play_game.sh
├── README.md
├── ROOT
└── TARGETS

1 directory, 7 files
```

## The repository configuration file (`repos.json`)

This project has two direct dependencies, namely, the `rules-cc` repository,
which brings in the rules for C/C++ files, and the `guessing_game` presented in
the [previous tutorial](../number-guessing/README.md).

So, we start with a `repos.template.json` file that looks

File: etc/repos.template.json
```jsonc
{ "main": "bot"
, "repositories":
  { "bot":
    { "repository": {"type": "file", "path": "."}
    , "bindings": {"rules-cc": "rules-cc", "guessing_game": "guessing_game"}
    }
  }
}
```

The two required dependencies are listed in the `"bindings"` key, and left as
open names.  `"rules-cc"` can be retrieved using the script
[`just-import-git.py`](https://github.com/just-buildsystem/justbuild/blob/master/bin/just-import-git.py),
while `"guessing_game"` with
[`just-import-cargo.py`](../../bin/just-import-cargo.py). In the following we
assume that these two scripts are available in the `PATH` without the suffix
`.py`. It is recommended to generate the final `repos.json` via a script, which,
for this tutorial is provided in the file `etc/gen-repos.sh` and looks as
follows

```sh
set -euo pipefail

readonly ROOT=$(readlink -f $(dirname $0)/..)

just-import-git -C ${ROOT}/etc/repos.template.json \
                --as rules-cc -b master https://github.com/just-buildsystem/rules-cc rules \
    | \
    just-import-cargo --to-git --repo-root ${ROOT} ${ROOT}/../number-guessing > ${ROOT}/etc/repos.json
```

Once we run the `etc/gen-repos.sh` script, the directory tree should look

```sh
$ tree
.
├── bot.cpp
├── etc
│   ├── defaults
│   │   └── rust
│   │       └── TARGETS.cargo_import
│   ├── deps-rust
│   │   ├── TARGETS.byteorder-1.5.0
│   │   ├── TARGETS.cfg-if-1.0.0
│   │   ├── TARGETS.getrandom-0.2.15
│   │   ├── TARGETS.libc-0.2.155
│   │   ├── TARGETS.ppv-lite86-0.2.18
│   │   ├── TARGETS.proc-macro2-1.0.86
│   │   ├── TARGETS.quote-1.0.36
│   │   ├── TARGETS.rand-0.8.5
│   │   ├── TARGETS.rand_chacha-0.3.1
│   │   ├── TARGETS.rand_core-0.6.4
│   │   ├── TARGETS.syn-2.0.72
│   │   ├── TARGETS.unicode-ident-1.0.12
│   │   ├── TARGETS.zerocopy-0.6.6
│   │   └── TARGETS.zerocopy-derive-0.6.6
│   ├── gen-repos.sh
│   ├── repos.json
│   └── repos.template.json
├── play_game.sh
├── README.md
├── ROOT
└── TARGETS

4 directories, 23 files
```

Since we used the option `--to-git` of the `just-import-cargo` script, we need
to `git add` and `git commit` the `etc` folder before compiling.

```sh
$ git add etc
$ git commit -m "Add repositories."
```

## Target descriptions

In order to let our bot play the `guessing_game`, the `TARGETS` file can be as follows:

File: TARGETS
```jsonc
{ "bot":
  { "type": ["@", "rules-cc", "CC", "binary"]
  , "name": ["bot"]
  , "srcs": ["bot.cpp"]
  }
, "bot-test":
  { "type": ["@", "rules-cc", "shell/test", "script"]
  , "name": ["guessing_game"]
  , "test": ["play_game.sh"]
  , "deps": ["bot", ["@", "guessing_game", "", "guessing_game"]]
  }
}
```

## How to compile

To build the test report of the `"bot-test"` target we can run

```sh
$ just-mr build bot-test
INFO: Performing repositories setup
INFO: Found 21 repositories to set up
...
INFO: Processed 34 actions, 0 cache hits.
INFO: Artifacts built, logical paths are:
        pwd [0a2bee0cbe8eed860dffa724e92d99c4be750731:137:f]
        result [7ef22e9a431ad0272713b71fdc8794016c8ef12f:5:f]
        stderr [e69de29bb2d1d6434b8b29ae775ad8c2e48c5391:0:f]
        stdout [47f9933e607fe51c0f24b1d80d5621fd1b9b939c:9:f]
        time-start [2fe8b0b1e52bf12f18ca667d0528492f7c68cb51:11:f]
        time-stop [2fe8b0b1e52bf12f18ca667d0528492f7c68cb51:11:f]
      (1 runfiles omitted.)
INFO: Backing up artifacts of 12 export targets
INFO: Target tainted ["test"].
```

Please refer to the "Let's build" section of the [getting-started
tutorial](../../getting-started/README.md) for more details on how to
find/select the `rustc` compiler.
