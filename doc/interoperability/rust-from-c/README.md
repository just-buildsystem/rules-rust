# Call Rust code from a C binary

The purpose of this tutorial is to showcase how to mix different
programming languages using `justbuild`, along with the features that
these Rust rules have to foster the interoperability. For the sake of
simplicity, in this example we are going to write a library in Rust
that is consumed by a C binary. In particular, the program will read a
number from `stdin` and will print the absolute value, which is
computed via the call to a Rust function.

Spoiler: developers should pay attention to the definition of the
target for the `foo` library.

## Project structure

Let's start with the following structure.

```sh
$ tree
.
├── etc
│   └── repos.json
├── foo
│   ├── foo.h
│   ├── foo.rs
│   └── TARGETS
├── main.c
├── README.md
├── ROOT
└── TARGETS

2 directories, 8 files
```

## Required repositories

In the `repos.json` file we need import both the rules for compiling Rust and C code

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

## The `foo` library

This library is made by a simple function that returns the absolute value of a number

```rust
// file: foo/foo.rs

#[no_mangle]
pub extern "C" fn foo(x: i32) -> i32 {
    return x.abs();
}
```

As you may know, in C, before calling a function its signature must be
declared. Typically, this kind of information is written in header
files. The `justbuild` Rust rules allow for the definition of
companion header files, that can be maintained by the Rust library
developers. In this case, `foo.h` looks as follows

```C
/* file: foo/foo.h */

#pragma once
int foo(int);
```

Of course, we are not forced to write the corresponding header file,
and we could, for example, put the declaration of the functions we
want to use in the `main.c` file. However, having the headers make the
usage of the library much easier. Therefore, the Rust rules feature a
dedicated field `"c_hdrs"`, so, the target definition for the library
can be as follows

```jsonc
// file foo/TARGETS

{ "foo":
  { "type": ["@", "rules-rust", "rust", "library"]
  , "name": ["foo"]
  , "crate_root": ["foo.rs"]
  , "native": ["true"]
  , "c_hdrs": ["foo.h"]
  , "stage": ["foo"]
  }
}
```

With respect to the example of the [getting started
tutorial](../../getting-started/README.md), the above target
definition contains two new fields: `"native"` and `"c_hdrs"`. When
the field `"native"` evaluates to `true`, a native library is
generated instead of a Rust one. In the field `"c_hdrs"`, there are
listed the headers required to use the library. Since it makes sense
to set the field `"c_hdrs"` only for a native library, when `"c_hdrs"`
evaluates to a true value, a native library is implied. Therefore, for
this case, we can drop the `"native"` field

```jsonc
// file: foo/TARGETS

{ "foo":
  { "type": ["@", "rules-rust", "rust", "library"]
  , "name": ["foo"]
  , "crate_root": ["foo.rs"]
  , "c_hdrs": ["foo.h"]
  , "stage": ["foo"]
  }
}
```

## The main

From the C consumer, the `foo` library can be seen as a normal C library

```C
/* file: main.c */

#include <stdio.h>
#include <stdlib.h>

#include "foo/foo.h"

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "Please provide one number as argument\n");
    exit(1);
  }
  int x = atoi(argv[1]);
  printf("absolute value of %d is %d\n", x, foo(x));
  return 0;
}
```

and the target definition is as simple as follows:

```jsonc
// file: TARGETS

{ "main":
  { "type": ["@", "rules-cc", "CC", "binary"]
  , "pure C": ["true"]
  , "name": ["main"]
  , "srcs": ["main.c"]
  , "private-deps": [["foo", "foo"]]
  }
}
```

It' worth to highlight that we simply stated that `"main"` depends on
the target `["foo", "foo"]`, and, at this level, we don't care how it
is defined.

## How to compile

The `"main"` target can be built issuing the following command

```sh
$ just-mr build main
```

Please refer to the "Let's build" section of the [getting-started
tutorial](../../getting-started/README.md) for more details on how to
find/select the `rustc` compiler.

## Additional exercises

To get more familiarity with the rules, you may want to:

 - add a `["@", "rules-rust", "rust", "test"]`, which tests the `foo`
   library.

 - add a `["@", "rules-cc", "shell/script", "test"]` to test that the
   main actually works.
