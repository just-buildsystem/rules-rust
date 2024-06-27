# Rust rules for the [`just`](https://github.com/just-buildsystem/justbuild) build system

A collection of rules for building Rust libraries, binaries and unit tests.

### `["rust", "binary"]`

 A Rust binary.

| Field | Description |
| ----- | ----------- |
| `"build_script"` | The "build_script" target required to be built and run before compiling this binary. |
| `"cargo_features"` | List of cargo features this binary requires to be enabled. |
| `"crate_root"` | The crate to be fed to the Rust compiler. It must evaluate to a single artifact/file. |
| `"defaults"` | The Rust toolchain to use. |
| `"deps"` | Any other libraries this binary depends upon. |
| `"edition"` | The edition of the compiler to use during compilation. If unset, 2015 is used. |
| `"name"` | The name of the crate being built. |
| `"pkg_name"` | The name of the package the crate belongs to. It is exported to the CARGO_PKG_NAME environment variable. |
| `"srcs"` | The source files of the binary. |
| `"stage"` | The logical location of the resulting artifact. Elements are joined with "/". |
| `"version"` | The crate version. Elements are joined with "." and the first three elements are used for the major, minor, and patch number respectively. |

### `["rust", "defaults"]`

 A rule to provide defaults.
All rust targets take their defaults for RUSTC, TARGET, compile
flags etc.

| Field | Description |
| ----- | ----------- |
| `"ADD_RUSTC_FLAGS"` | Additional flags for rustc. The values are appended to the ones from "base". |
| `"CARGO_CFG_TARGET_ARCH"` | The CPU target architecture. It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_ENDIAN"` | The CPU target endianness. It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_ENV"` | The target environment ABI. It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_FAMILY"` | The target family. It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_FEATURE"` | List of CPU target features enabled. Elements are joined with ",". It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_HAS_ATOMIC"` | List of atomics types (in bits) supported by the target CPU. Elements are joined with ",". It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_OS"` | The target operating system. It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_POINTER_WIDTH"` | The CPU pointer width. It overwrites the value from "base". |
| `"CARGO_CFG_TARGET_VENDOR"` | The target vendor. It overwrites the value from "base". |
| `"CARGO_CFG_UNIX"` | To be set on unix-like platforms. It overwrites the value from "base". |
| `"CARGO_CFG_WINDOWS"` | To be set on windows-like platforms. It overwrites the value from "base". |
| `"HOST"` | The host triple of the Rust compiler (e.g., "x86_64-unknown-linux-gnu"). It overwrites the value from "base". |
| `"LINKER"` | The value to pass to the "--linker" rustc flag. It overwrites the value from "base". |
| `"PATH"` | Environment variable for looking up compilers and linkers. Elements are joined with ":". The values are put in front of the ones from "base". |
| `"RUSTC"` | The Rust compiler to use. It overwrites the value from "base". |
| `"RUSTC_FLAGS"` | The rustc flags to use. It overwrites the value from "base". |
| `"TARGET"` | The target triple for which the code is compiled (e.g., "x86_64-unknown-linux-gnu"). It overwrites the value from "base". |
| `"base"` | Other targets of the very same type to inherit values from. If the same field is defined both targets, depending on the field, the value from "base" is extended or overwritten. |

### `["rust", "library"]`

 A Rust library. Depending on the value of the fields "shared"
and "native", the `--crate-type` is inferred as follows:

|shared|native|crate-type|
|------|------|----------|
| null | null | rlib     |
| null |"true"| staticlib|
|"true"| null | dylib    |
|"true"|"true"| cdylib   |

| Field | Description |
| ----- | ----------- |
| `"build_script"` | The "build_script" target required to be built and run before compiling this library. |
| `"c_hdrs"` | C headers that define the interface to this library. This field is ignored when this library is consumed by another Rust target.  If non empty, a native library will be produced. |
| `"cargo_features"` | List of cargo features this library requires to be enabled. |
| `"crate_root"` | The crate to be fed to the Rust compiler. It must evaluate to a single artifact/file. |
| `"defaults"` | The Rust toolchain to use. |
| `"deps"` | Any other libraries this library depends upon. |
| `"edition"` | The edition of the compiler to use during compilation. If unset, 2015 is used. |
| `"name"` | The name of the crate being built. |
| `"native"` | If not null, a native library will be produced.  Note that, when this target is consumed by another Rust target, it will be compiled to a Rust static library (.rlib). |
| `"pkg_name"` | The name of the package the crate belongs to. It is exported to the CARGO_PKG_NAME environment variable. |
| `"shared"` | If not null, a shared library will be produced. |
| `"srcs"` | The source files of the library. |
| `"stage"` | The logical location of the resulting artifact. Elements are joined with "/". |
| `"version"` | The crate version. Elements are joined with "." and the first three elements are used for the major, minor, and patch number respectively. |

### `["rust", "proc-macro"]`

 A Rust procedural macro. As it is executed on the host system
during the compilation, it is always compiled according to the
host configuration.

| Field | Description |
| ----- | ----------- |
| `"build_script"` | The "build_script" target required to be built and run before compiling this macro. |
| `"cargo_features"` | List of cargo features this macro requires to be enabled. |
| `"crate_root"` | The crate to be fed to the Rust compiler. It must evaluate to a single artifact/file. |
| `"defaults"` | The Rust toolchain to use. |
| `"deps"` | Any other libraries this macro depends upon. |
| `"edition"` | The edition of the compiler to use during compilation. If unset, 2015 is used. |
| `"name"` | The name of the crate being built. |
| `"pkg_name"` | The name of the package the crate belongs to. It is exported to the CARGO_PKG_NAME environment variable. |
| `"srcs"` | The source files of the procedural macro. |
| `"stage"` | The logical location of the resulting artifact. Elements are joined with "/". |
| `"version"` | The crate version. Elements are joined with "." and the first three elements are used for the major, minor, and patch number respectively. |

### `["rust", "test"]`

 A Rust test.

| Field | Description |
| ----- | ----------- |
| `"args"` | Additional arguments to be passed when running the test. |
| `"cargo_features"` | List of cargo features this test requires to be enabled. |
| `"crate_root"` | The crate to be fed to the Rust compiler. It must evaluate to a single artifact/file. |
| `"data"` | Any files and directories the test binary needs when running. |
| `"defaults"` | The Rust toolchain to use. |
| `"deps"` | Any other libraries this test depends upon. |
| `"edition"` | The edition of the compiler to use during compilation. If unset, 2015 is used. |
| `"name"` | The name of the test being built. Note that during execution, the test binary will be restaged to "test". |
| `"pkg_name"` | The name of the package the crate belongs to. It is exported to the CARGO_PKG_NAME environment variable. |
| `"runner"` | The test runner to use, i.e., the binary that will launch the test binary and collect the output. |
| `"srcs"` | The source files of the test. |
| `"stage"` | The logical location of the resulting artifact. Elements are joined with "/". |
| `"version"` | The crate version. Elements are joined with "." and the first three elements are used for the major, minor, and patch number respectively. |

### `["cargo", "build_script"]`

 The custom build script supported by cargo. This binary is
executed before compiling the other crates. Currently, only its
output is processed to augment the rustc flags. During a cross
compilation, since the build script must be run on the host
system, it is always compiled according to the configuration
provided by the "defaults" for the "HOST_ARCH".

| Field | Description |
| ----- | ----------- |
| `"cargo_features"` | List of cargo features this binary requires to be enabled. |
| `"crate_root"` | The crate to be fed to the Rust compiler. It must evaluate to a single artifact/file. |
| `"defaults"` | The Rust toolchain to use. |
| `"deps"` | Any other libraries this binary depends upon. |
| `"edition"` | The edition of the compiler to use during compilation. If unset, 2015 is used. |
| `"name"` | The name of the crate being built. |
| `"pkg_name"` | The name of the package the crate belongs to. It is exported to the CARGO_PKG_NAME environment variable. |
| `"srcs"` | The source files of the binary. |
| `"stage"` | The logical location of the resulting artifact. Elements are joined with "/". |
| `"version"` | The crate version. Elements are joined with "." and the first three elements are used for the major, minor, and patch number respectively. |

### `["cargo", "feature"]`

 A cargo feature.

| Field | Description |
| ----- | ----------- |
| `"deps"` | Any other features or "[rust, library]" this feature depends on. |
| `"name"` | The feature name. The flag `--cfg feature=<name>` is passed to the Rust compiler. |

