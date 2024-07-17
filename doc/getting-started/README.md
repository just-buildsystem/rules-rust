# Getting started

In this example, we will gradually modify the simple "Hello, World!"
Rust program to become familiar with the major features of the Rust
rules for Justbuild. By the end of this tutorial, you will know how to
define Rust binaries, libraries, and tests and configure the project,
for example, using specific compile flags.

## Project structure

Let's start with the following structure.

```sh
$ tree
.
├── etc
│   └── repos.json
├── main.rs
├── README.md
├── ROOT
└── TARGETS

1 directories, 5 files
```

Apart from the `README.md` (this file) and `main.rs`, which should be expected, three additional files are required:
 - `ROOT`, which is just an empty file that sets the workspace root of the given project;
 - `etc/repos.json` contains all the repositories involved - can you guess how many repos we need?
 - `TARGETS`, which contains the target descriptions.

For the sake of completeness, this is how the `main.rs` looks like

```rust
// file: main.rs

fn main() {
   println!("Hello, World!");
}
```

## Multi-repository setup

`Justbuild` is a truly language-agnostic tool tailored to
multi-repository projects. This project requires _two_ repositories:

 - the repository containing all the source files for this example
   (therefore, only the `main.rs`, for now)

 - the repository that instructs `Justbuild` on how to deal with the Rust
   programming language

The `etc/repos.json` file is as follows:
``` jsonc
// file: etc/repos.json

{ "main": "example"
, "repositories":
  { "example":
    { "repository": {"type": "file", "path": "."}
    , "bindings": {"rules": "rules-rust"}
    }
  , "rules-rust":
    { "repository":
      { "type": "git"
      , "repository": "https://github.com/just-buildsystem/rules-rust"
      , "branch": "master"
      , "commit": "ed652442176aea086104479bb31aced501df48a2"
      , "subdir": "rules"
      }
    }
  }
}
```

## Target description

For this example, we can define one `hello` target which will generate
a _binary_ from the `main.rs` source file.
``` jsonc
// file: TARGETS

{ "hello":
  { "type": ["@", "rules", "rust", "binary"]
  , "name": ["hello"]
  , "crate_root": ["main.rs"]
  }
}
```

As you might know, the entry point of a crate must be passed to the
`rustc` compiler. In these rules, the entry point is defined by the
key `"crate_root"`. If the project contained _additional_ files,
they would have been listed under the key `srcs`. For example,

``` jsonc
// file: TARGETS

{ "hello":
  { "type": ["@", "rules", "rust", "binary"]
  , "name": ["hello"]
  , "crate_root": ["main.rs"]
  , "srcs": ["foo.rs", "bar.rs"]
  }
}
```

It is important to stress that _ALL_ of the required inputs must be
explicitly declared because `Justbuild` compiles in isolation, and
only the listed source files are staged where the compile action is
executed. Coming from `cargo`, where everything is discovered
automatically (because everything must be locally available), this
listing of all and only required inputs might sound like an annoying
and pointless burden on the developer's shoulders. This is not true;
it helps to understand the dependencies between crates better and thus
avoid spaghetti code, which typically means a long compilation time.

## Let's build

Finally, we are ready to compile. If you have manually installed Rust
by running

```sh
$ curl ... https://sh.rustup.rs | ...
```

the artifacts are installed under `$RUSTUP_HOME`, which defaults to
`/home/<user_name>/.rustup/`. Since the path contains the username and
the rules don't try to infer this information, we have to provide the
path as well as which CPU architecture we are targeting.

```sh
$ just-mr build -D'{"ARCH":"x86_64","TOOLCHAIN_CONFIG":{"RUST":{"RUSTUP_HOME":"/home/<user_name>/.rustup"}}}' hello
INFO: Performing repositories setup
INFO: Found 2 repositories to set up
...
INFO: Processed 1 actions, 0 cache hits.
INFO: Artifacts built, logical paths are:
        hello [0a747e71e6a525a0d938c704108d2b014f59fdc7:3781216:x]
$
```

Alternatively, the full path to the `rustc` compiler can be provided:
```sh
$ just-mr build -D'{"TOOLCHAIN_CONFIG":{"RUST":{"RUSTC":"/home/<user_name>/.rustup/toolchains/nightly-x86_64-unknown-linux-gnu/bin/rustc"}}}' hello
```

Please note that the `rustc` to be used must not be under the
`$CARGO_HOME/bin` directory, which is a wrapper around the `rustc`
under the `$RUSTUP_HOME` directory.

Typing `-D'{...}'` at every tool invocation can be tedious and
error-prone. We now discuss two possible alternatives to leverage the
command line.

### `~/.just-mrrc`

The first option is to have a `just-mr` configuration file under your
`$HOME` directory that defines the above variables so the user no
longer needs to type them. For example, a minimal `~/.just-mrrc` can
look as follows:

``` jsonc
// file: ~/.just-mrrc

{ "just files":
  {"config": [{"root": "home", "path": ".just_file_rust.json"}]}
}
```
and `~/.just_file_rust.json` can be

``` jsonc
// file: ~/.just_file_rust.json

{ "ARCH": "x86_64"
, "TOOLCHAIN_CONFIG": {"RUST": {"RUSTUP_HOME": "/home/<user_name>/.rustup"}}
}
```
In this way, the example can be compiled by simply typing

```sh
$ just-mr build hello
```

Please refer to the [man page of
just-mrrc(5)](https://github.com/just-buildsystem/justbuild/blob/master/share/man/just-mrrc.5.md)
for more details on the `just-mr` configuration file.

### Providing defaults

Specific project configurations, like compile flags, can also be
provided by defining a `defaults` target, which the rules will pick
up. The user can completely overwrite the default `defaults`, which is
defined [here](../../rules/rust/TARGETS), or amend a few entries. It
is worth mentioning that the handling of the variable
`TOOLCHAIN_CONFIG` is defined in the `defaults` target; if needed, it
can also be changed.

For this example, let's change the default compile flags while leaving
the rest untouched. To do so, the `defaults` we write must "inherit"
the values from the upstream `defaults` target.

First of all, create the directory where we have to put the `TARGETS`
file containing the `defaults` target:

```sh
$ mkdir -p etc/defaults/rust
```

and add there the following `TARGETS` file

``` jsonc
// file: etc/defaults/rust/TARGETS

{ "defaults":
  { "type": "defaults"
  , "base": [["@", "upstream-rules", "rust", "defaults"]]
  , "RUSTC_FLAGS": ["--color=always", "-Copt-level=3"]
  }
}
```

Finally, amend the `repos.json` file to take into account the new `defaults`:
``` jsonc
//file: etc/repos.json

{ "main": "example"
, "repositories":
  { "example":
    { "repository": {"type": "file", "path": "."}
    , "bindings": {"rules": "rules-rust"}
    }
  , "rules-rust-defaults":
    {"repository": {"type": "file", "path": "etc/defaults"}}
  , "rules-rust-root":
    { "repository":
      { "type": "git"
      , "repository": "https://github.com/just-buildsystem/rules-rust"
      , "branch": "master"
      , "commit": "ed652442176aea086104479bb31aced501df48a2"
      , "subdir": "rules"
      }
    }
  , "rules-rust":
    { "repository": "rules-rust-root"
    , "target_root": "rules-rust-defaults"
    , "rule_root": "rules-rust-root"
    , "bindings": {"upstream-rules": "rules-rust-root"}
    }
  }
}
```

Now, to double-check that new flags are actually used we can compile
with a higher verbosity level

```sh
$ just-mr build --log-limit 5 hello
...
DEBUG (action:8c992667005bb014e548936f12a9ed77f643f649):
     ["sh","-c","'/home/.../rustc' 'main.rs' ... '--color=always' '-Copt-level=3' ...] in environment {...}
...
INFO: Artifacts built, logical paths are:
        hello [0a747e71e6a525a0d938c704108d2b014f59fdc7:3781216:x]
...
```

## Adding libraries and tests

Now, let's introduce a library `foo`, with only one public function,
that implements the Heaviside function.

Let's keep the source files of the library in the directory `foo`

```sh
$ mkdir foo
```

and write `foo/foo.rs` as follows

```rust
// file: foo/foo.rs

pub fn heaviside(x: i32) -> i32 {
    if x < 0 {
       return 0;
    }
    return 1;
}

```
The `foo/TARGETS` file can be as simple as

``` jsonc
// file: foo/TARGETS

{ "foo":
  { "type": ["@", "rules", "rust", "library"]
  , "name": ["foo"]
  , "crate_root": ["foo.rs"]
  , "stage": ["foo"]
  }
}
```

As for the `"binary"` type, if the `"library"` requires additional
modules that are not meant to be compiled in dedicated libraries, they
can be listed with the key `"srcs"`.

Let's implement a simple unit test for `heaviside` function.

```sh
$ mkdir test
```

```rust
// file: test/foo_test.rs

extern crate foo;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_foo(){
       assert_eq!(foo::heaviside(-7),0);
       assert_eq!(foo::heaviside(0),1);
       assert_eq!(foo::heaviside(7),1);
    }
}
```

and add a dedicated target in the `test/TARGETS` file

``` jsonc
// file: test/TARGETS

{ "foo_test":
  { "type": ["@", "rules", "rust", "test"]
  , "name": ["foo_test"]
  , "crate_root": ["foo_test.rs"]
  , "stage": ["foo"]
  , "deps": [["foo", "foo"]]
  }
}
```

We can check that the function works as expected by building the test report for `"foo_test"`

```sh
$ just-mr build test foo_test
```

Once we are confident with the implementation, let's use it in the `main`:

```rust
// file: main.rs

extern crate foo;

fn main() {
   println!("Hello, World!");
   println!("H(-5) == {}", foo::heaviside(-5));
}
```

``` jsonc
// file: TARGETS

{ "hello":
  { "type": ["@", "rules", "rust", "binary"]
  , "name": ["hello"]
  , "crate_root": ["main.rs"]
  , "deps": [["foo", "foo"]]
  }
}
```

For the sake of completeness, the project tree now looks as follows:

```sh
$ tree
.
├── etc
│   ├── defaults
│   │   └── rust
│   │       └── TARGETS
│   └── repos.json
├── foo
│   ├── foo.rs
│   └── TARGETS
├── main.rs
├── README.md
├── ROOT
├── TARGETS
└── test
    ├── foo_test.rs
    └── TARGETS

5 directories, 10 files
```

## Conclusions and additional exercises

Congratulations! You have learned how to define a Rust binary and a
library, link against it, test, and tune/configure the current project
with the `defaults` target.

It is important to note that these rules do not force users to agree
to the Cargo requirements (e.g., one library per package, source files
only under the `src` directory, etc.).

To become more acquainted with the Rust rules, you may want to:

 - reorganize the project layout, for example, moving all source files
   under a directory called `src`;

 - let `foo` be a module instead of a separate library (hint:
   `foo/foo.rs` must be added to the `"srcs"` field of the `"hello"`
   target);

 - set the `rustc` edition for all the crates within this project.
