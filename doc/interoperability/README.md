# Interoperability

The majority of the modern projects combine different programming
languages. These rules, and of course `justbuild`, have all that is
needed to easily mix different programming languages.

In particular, we propose two simple tutorials to demonstrate how Rust
and C can work together.

## How to call Rust from C

The tutorial [rust-from-c](./rust-from-c/README.md) showcases how a C
binary can link against a Rust library `foo`. It is worth mentioning
that all the details required to let `foo` be consumed by a C target
are confined within the `foo` definition and implementation. The C
consumer doesn't even need to know how the library is implemented, as
long as the interface is kept the same.

## How to call C from Rust

The tutorial [c-from-rust](./c-from-rust/README.md) showcases how to
call a C function from Rust. All the details are Rust-specific, and
must be implemented in the consuming Rust target. From the rules'
viewpoint, nothing special is happening, but we think it is still
worth to have this tutorial for the sake of completeness.
