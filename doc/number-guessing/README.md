# Transitioning an existing Cargo-based Rust project

In this tutorial, we will transition to `justubuild` the [Guessing Game proposed
in the Rust
documentation](https://doc.rust-lang.org/book/ch02-00-guessing-game-tutorial.html),
which consists of two files

```sh
$ tree
.
├── Cargo.toml
└── src
    └── main.rs

1 directory, 2 files
```

The `Cargo.toml` file is as follows

File: Cargo.toml
```toml
[package]
name = "guessing_game"
version = "0.1.0"
edition = "2021"

# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html

[dependencies]
rand = "0.8.5"
```

The novelty in this tutorial is the presence of the external dependencies. In
fact, the manifest, only the direct dependency `rand` is listed, while the
computation and the retrieval of the required transitive dependencies are
leveraged by `cargo`. If we run, for example, `cargo tree` we can see the tree
of the dependencies.

```sh
$ cargo tree
guessing_game v0.1.0 (/.../number_guessing)
└── rand v0.8.5
    ├── libc v0.2.155
    ├── rand_chacha v0.3.1
    │   ├── ppv-lite86 v0.2.18
    │   │   └── zerocopy v0.6.6
    │   │       ├── byteorder v1.5.0
    │   │       └── zerocopy-derive v0.6.6 (proc-macro)
    │   │           ├── proc-macro2 v1.0.86
    │   │           │   └── unicode-ident v1.0.12
    │   │           ├── quote v1.0.36
    │   │           │   └── proc-macro2 v1.0.86 (*)
    │   │           └── syn v2.0.72
    │   │               ├── proc-macro2 v1.0.86 (*)
    │   │               ├── quote v1.0.36 (*)
    │   │               └── unicode-ident v1.0.12
    │   └── rand_core v0.6.4
    │       └── getrandom v0.2.15
    │           ├── cfg-if v1.0.0
    │           └── libc v0.2.155
    └── rand_core v0.6.4 (*)
```

Note that the version number and or the actual list of dependency might change
over time.

To compile the `guessing_game` with `justbuild` all the listed dependencies must
be transitioned as well. Of course, doing it by hand is error prone and time
consuming. Therefore, in this repository, we provide the script
[`just-import-cargo.py`](../../bin/just-import-cargo.py) that can automatize
the transition of a Cargo-based project to `justbuild`. Let's see how to
do it.

## `just-import-cargo.py`

Before showing *how* to use it, let's explain *why* to use it. `justbuild` is a
generic build tool for multi-language projects. The `justbuild`
equivalent of a `Cargo.lock` file is a repository configuration file named
`repos.json`, which contains the list of all the repositories involved in a
given project. The script `just-import-cargo.py` is meant to amend a given
`repos.json` importing all the Rust repositories required for the Cargo project of
concern.

However, the same script can be used to transition a self contained Cargo-based
Rust only project with a simple catch: let's start with a `repos.template.json`
with no listed repositories. For convenience, let's create a directory `etc`
where we store the files related to the external repositories

```sh
$ mkdir etc
```

```sh
$ echo '{}' > etc/repos.template.json
```

The final `etc/repos.json` can be easily be obtained running the following command

```sh
$ cat etc/repos.template.json | /path/to/just-import-cargo.py . > etc/repos.json
```

The full documentation of the command line arguments supported by
`just-import-cargo.py` can be found in the [man
page](../../share/man/import-cargo.1.md).

Before exploring the generated files and their content, let's signal
that this directory is the root of a `justbuild` project.

```sh
$ touch ROOT
```

The directory should have now the following structure

```sh
$ tree
.
├── Cargo.lock
├── Cargo.toml
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
│   └── repos.json
├── README.md
├── src
│   └── main.rs
└── TARGETS

5 directories, 21 files
```

Please note that the tool calls `cargo` under the hood, and a `Cargo.lock` file
is generated. If you want to update the Rust dependencies, run `cargo update`
before invoking the script again.

## The generated `repos.json`

The generated `repos.json` has the following structure:

File: etc/repos.json
```json
{
  "main": "guessing_game",
  "repositories": {
    "guessing_game/byteorder-1.5.0": {},
    "guessing_game/cfg-if-1.0.0": {},
    "guessing_game/getrandom-0.2.15": {},
    "guessing_game": {},
    "guessing_game/libc-0.2.155": {},
    "guessing_game/ppv-lite86-0.2.18": {},
    "guessing_game/proc-macro2-1.0.86": {},
    "guessing_game/quote-1.0.36": {},
    "guessing_game/rand-0.8.5": {},
    "guessing_game/rand_chacha-0.3.1": {},
    "guessing_game/rand_core-0.6.4": {},
    "guessing_game/syn-2.0.72": {},
    "guessing_game/unicode-ident-1.0.12": {},
    "guessing_game/zerocopy-0.6.6": {},
    "guessing_game/zerocopy-derive-0.6.6": {},
    "guessing_game/external-deps": {},
    "guessing_game/rust-rules-root": {},
    "guessing_game/rust-rules-defaults": {},
    "guessing_game/rust-rules": {}
  }
}
```

Under the key `"repositories"` we can recognize `"guessing_game"`, which is the
current project (the name is taken from the `Cargo.toml` manifest), and all the
dependencies reported by `cargo tree`, along with the Rust rules, required by
`justbuild`. Since the `repos.template.json` didn't contain a `"main"`
repository, the tool automatically elected the current project as the `"main"`
repository.

If the project evolves and requires dependencies not managed by Cargo, they
should be listed in the `etc/repos.template.json`, such that the
`just-import-cargo.py` script can be run regularly (maybe just after `cargo
update`) to keep the repositories up to date.

More information on the
format of the repository configuration file can be found
[here](https://github.com/just-buildsystem/justbuild/blob/master/share/man/just-mr-repository-config.5.md).



## Build descriptions of the external repositories in `etc/deps-rust`

The the build descriptions for the external repositories are put in the
`etc/deps-rust` directory. Ideally, the generated `TARGETS` files should not
required to be amended, but the tool is at a relatively early stage, so any
contributions is welcome :) If you find yourself in the need to patch the
*generated* build descriptions, remember that the files are, well, generated and
could be overwritten when the `just-import-cargo.py` script is run again.

Let's have a look at one generated file, for example

File: etc/deps-rust/TARGETS.rand_chacha-0.3.1
```jsonc
{ "rand_chacha":
  { "type": "export"
  , "target": "rand_chacha-internal"
  , "flexible_config":
    ["ARCH", "HOST_ARCH", "TARGET_ARCH", "ENV", "TOOLCHAIN_CONFIG"]
  }
, "rand_chacha-internal":
  { "type": ["@", "rules", "rust", "library"]
  , "name": ["rand_chacha"]
  , "crate_root": ["src/lib.rs"]
  , "srcs": [["TREE", null, "."]]
  , "edition": ["2018"]
  , "arguments_config":
    ["ARCH", "HOST_ARCH", "TARGET_ARCH", "ENV", "TOOLCHAIN_CONFIG"]
  , "deps":
    [ ["@", "ppv-lite86", "", "ppv_lite86"]
    , ["@", "rand_core", "", "rand_core"]
    ]
  , "cargo_features": ["std"]
  , "stage": ["rand_chacha-0.3.1"]
  , "version": ["0", "3", "1"]
  , "pkg_name": ["rand_chacha"]
  }
, "default": {"type": ["@", "rules", "cargo", "feature"], "name": ["default"]}
, "serde": {"type": ["@", "rules", "cargo", "feature"], "name": ["serde"]}
, "serde1": {"type": ["@", "rules", "cargo", "feature"], "name": ["serde1"]}
, "simd": {"type": ["@", "rules", "cargo", "feature"], "name": ["simd"]}
, "std": {"type": ["@", "rules", "cargo", "feature"], "name": ["std"]}
}
```

It is worth to highlight that the target named like the library of concern is of
type `"export"`, meaning that it is eligible for high-level target caching,
which allows to skip the analysis and traversal of entire subgraphs in the
action graph. More details on the export targets and the target-level caching
can be found in the [third-party software
tutorial](https://github.com/just-buildsystem/justbuild/blob/master/doc/tutorial/third-party-software.md).

## Project specific configuration

The directory `etc/defaults` sets the configuration for this project, which by
default, is the one given by these rules with the target
["defaults"](../../rules/rust/TARGETS).

## Build description of the current crate

The build description of the current crate is dumped in the file `TARGETS` next
to when the `Cargo.toml` manifest is.

For this example, it looks

File: TARGETS
```jsonc
{ "guessing_game":
  { "type": ["@", "rules", "rust", "binary"]
  , "name": ["guessing_game"]
  , "crate_root": ["src/main.rs"]
  , "srcs": [["TREE", null, "."]]
  , "edition": ["2021"]
  , "arguments_config":
    ["ARCH", "HOST_ARCH", "TARGET_ARCH", "ENV", "TOOLCHAIN_CONFIG"]
  , "deps": [["@", "rand", "", "rand"]]
  , "cargo_features": []
  , "stage": ["guessing_game-0.1.0"]
  , "version": ["0", "1", "0"]
  , "pkg_name": ["guessing_game"]
  }
}
```

## How to compile

The compilation is done as usual

```sh
$ just-mr build
INFO: Performing repositories setup
INFO: Found 19 repositories to set up
...
INFO: Export targets found: 0 cached, 0 uncached, 12 not eligible for caching
INFO: Discovered 32 actions, 0 trees, 0 blobs
...
INFO: Artifacts built, logical paths are:
        guessing_game-0.1.0/guessing_game [d0133fc676de0044034622c74c44029e50f7a025:3820528:x]
```

Please refer to the "Let's build" section of the [getting-started
tutorial](../../getting-started/README.md) for more details on how to
find/select the `rustc` compiler.

## Enabling target-level caching

In order to enable the target-level caching, we need to mark as content fixed
the imported repositories that are not thought so (e.g., the `etc/defaults`
repository). The `just-import-git.py` script can do this if the flag `--to-git`
(or `-g`) is given.

```sh
$ cat etc/repos.template.json | /path/to/just-import-cargo.py -g . > etc/repos.json
```

If we look at the `etc/repos.json` file we will see that a JSON object
`"pragma":{"to_git":true}` is added to several repositories. For example,

```jsonc
...
  , "guessing_game/rust-rules-defaults":
    { "repository":
      {"type": "file", "path": "etc/defaults", "pragma": {"to_git": true}}
    }
...
```

Now that `etc/defaults` and `etc/rust-deps` are marked as content fixed, we need
to add them to the current git directory,

```sh
$ git add etc
$ git commit -m "Add repositories."
```

If we now compile the project again we will see that the export targets that
were not eligible for caching, now they will be uncached

```sh
$ just-mr build
INFO: Performing repositories setup
INFO: Found 19 repositories to set up
...
INFO: Export targets found: 0 cached, 12 uncached, 0 not eligible for caching
INFO: Discovered 32 actions, 0 trees, 0 blobs
...
INFO: Artifacts built, logical paths are:
        guessing_game-0.1.0/guessing_game [d0133fc676de0044034622c74c44029e50f7a025:3820528:x]
INFO: Backing up artifacts of 12 export targets
```

And if we compile it again

```sh
$ just-mr build
INFO: Performing repositories setup
INFO: Found 19 repositories to set up
...
INFO: Export targets found: 1 cached, 0 uncached, 0 not eligible for caching
INFO: Discovered 1 actions, 0 trees, 0 blobs
...
INFO: Processed 1 actions, 0 cache hits.
INFO: Artifacts built, logical paths are:
        guessing_game-0.1.0/guessing_game [d0133fc676de0044034622c74c44029e50f7a025:3820528:x]
```

To allow for reproducibility of the builds, we also highly recommend to include
in the git tree the generated files (as `Cargo.lock` and `etc/repos.json`).
