# Call C code from Rust

This tutorial demonstrates how C code can be called from a Rust
binary. We will write a program that reads a number from `stdin` and
prints its absolute value, which is computed via a call to a function
implemented in C.

## Project structure

```sh
$ tree
.
├── etc
│   └── repos.json
├── foo
│   ├── foo.c
│   ├── foo.h
│   └── TARGETS
├── main.rs
├── README.md
├── ROOT
└── TARGETS

2 directories, 8 files
```

## Required repositories

In the `repos.json` file we need to import both the rules for
compiling Rust and C code

```jsonc
// file: etc/repos.json

{ "main": "example"
, "repositories":
  { "example":
    { "repository": {"type": "file", "path": "."}
    , "bindings": {"rules-rust": "rules-rust", "rules-cc": "rules-cc"}
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
  , "rules-cc":
    { "repository":
      { "type": "git"
      , "repository": "https://github.com/just-buildsystem/rules-cc"
      , "branch": "master"
      , "commit": "fac7e7680e00dfc63eec41a33dff86d31571eb4b"
      , "subdir": "rules"
      }
    }
  }
}
```

## Target definition

No special attention should be given in the target definition --
differently from the [rust-from-c tutorial](../rust-from-c/README.md)
-- therefore the C library is defined as a normal C library

``` jsonc
// file: foo/TARGETS

{ "foo":
  { "type": ["@", "rules-cc", "CC", "library"]
  , "pure C": ["true"]
  , "name": ["foo"]
  , "srcs": ["foo.c"]
  , "hdrs": ["foo.h"]
  , "stage": ["foo"]
  , "ldflags": ["-lm"]
  }
}
```

and the `"main"` is defined as a simple Rust binary that depends on a
library

``` jsonc
//file: TARGETS

{ "main":
  { "type": ["@", "rules-rust", "rust", "binary"]
  , "name": ["main"]
  , "crate_root": ["main.rs"]
  , "deps": [["foo", "foo"]]
  }
}
```

## The `main`

For the sake of completeness, this is how the `main.rs` crate looks

```rust
// file: main.rs

use std::env;

// declaration of the function implemented in the C library
extern "C" {
    fn c_func(input: i32) -> i32;
}

// wrapper to call the C function
fn c_call(i: i32) -> i32 {
    unsafe {
        return c_func(i);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args[1].parse::<i32>() {
        Ok(i) => println!("Absolute value of {} is {}", i, c_call(i)),
        Err(..) => println!("Wrong argument {}", args[1]),
    };
}
```

## How to compile

The `"main"` target can be built with the following command

```sh
$ just-mr build main
```

Please refer to the "Let's build" section of the [getting-started
tutorial](../../getting-started/README.md) for more details on how to
find/select the `rustc` compiler.

## Additional exercises

To get more familiarity with the rules, you may want to:

 - write a Rust library that wraps the C library, and add a
   `["@","rules-rust", "rust", "test"]` to test the library. Of course,
   the main will only have the new Rust library as a dependency.

 - add a `["@", "rules-cc", "shell/script", "test"]` to test that the
   main actually works.
