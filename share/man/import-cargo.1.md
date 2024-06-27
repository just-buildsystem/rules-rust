% JUST-IMPORT-CARGO(1) | General Commands Manual

NAME
====

just-import-cargo - import the cargo dependencies of one crate

SYNOPSIS
========

**`just-import-cargo`** \[*`OPTION`*]... *`relative-crate-location`*

DESCRIPTION
===========

Given a physical repository where one subdirectory has the file
layout of a crate and a **`just-mr-repository-config`**(5) on
standard input,
 - extend the repository configuration by a logical repository for
   that crate, as well as logical repositories for all the transitive
   dependencies as reported by **`cargo`**(1) when asked for the
   development dependencies of the given crate,
 - generate the needed target files in the directory *`etc/deps-rust`*
   of the physical repository, and
 - add appropriate rust default targets in the directory *`etc/defaults`*
   of the physical repository.

OPTIONS
=======

**`-h`**, **`--help`**  
Output a usage message and exit.

**`--rules`** *`name`*  
Assume the rust rules are the logical repository *`name`* in the
configuration provided on standard input. Typically, the rust rules would
be imported first via **`just-import-git`**(1). If this option is not
given, the latest commit of `https://github.com/just-buildsystem/rules-rust`
is taken.

**`--repo-root`** *`root`*  
Specify the root of the physical directory the configuration read from
standard input refers to. If not given, it is assumed that the current
working directory is the root of the physical repository.

**`--local-crate-cache`** *`cache-root`*  
Specify the location where to cache the information about non-local crates.
If not given, `~/.cache/crate-index-just` is used.

**`-g`**, **`--to-git`**  
Add the `"to_git"` pragma to the generated repositories that are non
content-fixed anyway.

**`-t`**, **`--recompute-targets`**  
Recompute all target files, even if cached.

**`-r`**, **`--recompute-repos`**  
Recompute all repositories, even if cached.

**`-s`**, **`--recompute-sources`**  
Recompute all source descriptions, even if cached.

**`-I`**, **`--compute-index`**  
Add an index repository.

See also
========

**`cargo`**(1),
**`just-deduplicate-repos`**(1),
**`just-import-git`**(1),
**`just-mr-repository-config`**(5),
**`just-mr`**(1)
