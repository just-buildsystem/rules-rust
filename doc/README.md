# Prerequisites

The tutorials aim to explain the rules' usage and not learn Rust or
the `Justbuild` tool. Therefore, the user is assumed to know the Rust
programming language and `Justbuild`.

A `rustc` compiler must be installed and accessible in your
environment.

- [Getting started](./getting-started/README.md) tutorial teaches you
  how to define Rust binaries, libraries, and tests and configure the
  project, for example, using specific compile flags.

- [Interoperability](./interoperability/README.md) proposes two
  tutorials on how to mix Rust and C. On the one hand, a Rust library
  is consumed by a C binary, on the other hand, a C library is
  consumed by a Rust binary.

- [Number guessing](./number-guessing/README.md), it showcases how to
  *transition* a Rust-only Cargo-based project to `Justbuild` using
  the script [`just-import-cargo.py`](../bin/just-import-cargo.py).

- [Number guessing bot](./number-guessing-bot/README.md) demonstrates
  how to *import* a Cargo-based repository in another project, written
  in C++ in this example.