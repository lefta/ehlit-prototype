# Ehlit language

This project is in a very early stage and is not safe for production use. The compiler and the
language itself *will* change. You have been warned !

At the moment, focus is put on making the language working. The compiler transpiles to C source
code, this is only because it is easier and faster to develop the language this way. In the future,
it is of course planned to directly generate binary code.

While there is some error and unsafe behavior checking, this is not the main goal at the moment.
Invalid Ehlit code will either result in invalid C code or, in the worst cases, make the compiler
crash (it is known to be the case when accessing an array index on a non-array type, for example).

I (lefta) am developping this project on my free time. Neither the language, this project nor myself
are backed by anyone. This means that you may not expect any ETA for any feature. If you are
interrested in the Ehlit language, please be patient (really patient). If you are **very**
interrested, I am open to any help you are able to provide. See the `how can I help ?` section
below. Unfortunately, I do not have as much time that I want to work on this project.

## Build status

| Build bot | Status |
|-----------|--------|
| Travis CI | [![Build Status](https://travis-ci.org/lefta/ehlit-prototype.svg?branch=master)](https://travis-ci.org/lefta/ehlit-prototype) |

## Introduction

Ehlit is a compiled programmation language designed for performance, simplicity, readability and
typing economy (in this order). It is a global usage language, but excells when performance or
compatibility are required.

It is compatible out of the box with any existing C library, and using an Ehlit library in a C
program is very easy.

It is distributed under the MIT license. In short, do whatever you want, but keep the original
license text in any distribution and don't point at me if you get problems. See the `Copying` file
for details.

## Hello world example

Note that the language is still a work in progress. While the syntax of the language syntax should
be quite stable, no standard library have been started. That's why this example relies on the C
libraries, but it will not stay this way.

```ehlit
include stdio.h

int main(int ac, str[] av)
{
    printf("Hello, world!\n")
    return 0
}
```

## Features

* Strong, static typing system (still a work in progress though)
* Native binaries (fast and lightweight execution, no runtime support required and all other
  strenghts it implies)
* Weaknesses of native execution reduced at a their minimum.
* « If it builds, it won't crash » language. (Well, at least that is what I'm planning and trying)
* Clean syntax (no weird symbols everywhere)
* Out of source builds
* ...

## Requirements

### On Ubuntu

Note that Ubuntu prior to 18.04 LTS is not supported

```bash
sudo apt install python3-pip clang llvm
pip3 -r requirements.txt
```

### On Gentoo

*Before answering yes to the installation, make sure all packages are installed with at least the
python3.6 python target*

```bash
# For usage
emerge --ask dev-python/clang-python dev-python/arpeggio
# Or, for development
emerge --ask dev-python/clang-python dev-python/arpeggio dev-python/mypy dev-python/flake8
```

### On other systems

Make sure you have the following packages installed:

* Python 3.6+
* pip
* LLVM
* Clang

Then run:

```bash
pip3 -r requirements.txt
```

Alternatively to the pip3 command, you may install the following python modules in the way that
suits you:

* arpeggio
* clang
* mypy (for development only)
* flake8 (for development only)


## Basic usage

All you need is calling `python -m ehlit` with the Ehlit file you wish to build as argument.
Note that for this to work, you must either be at the root of this repository, or the Ehlit
package must be installed somewhere in your python path.

This will generate a `out` directory, containing all generated files. This way, it allows to keep
your code base clean: you only have to delete this directory to go back to a « clean » state, and
only have to add `/out/` to your `.gitignore` file to avoid pushing generated files.

The resulting C file is put in a `src` subdirectory with the same name, just replacing the `.eh`
extension with `.c`. Next, you may build your C file(s) as you would with other programs.

This duplicates build work, but all (good?) compilation system allows you to automate this, so you
do not even have to think about this. For instance, with Makefiles, you could use a rule like:

    out/src/%.c: %.eh
        python -m ehlit $<

This way, you may build your program the exact same way you would build it if it was written in pure
C. C source files will be generated dynamically as needed.

Import files are put in an `include` subdirecty. If you are writing a library, you will need to
release this directory as well.

## How can I help ?

There is a very long road ahead, if you want to speed up things, you may:

* Test the language : write some toy programs to help identify problems in the language or the
compiler. Even better if you improve the test suite by the way, and there is a lot to do !
* Write documentation : the language and its features are not yet documented. This would make it
easier to start with.
* Suggest features : I would love to know what you expect from Ehlit (but please, avoid things like
« fast », this is obvious and planned :) ).
* Implement features : If the development of the feature you are waiting for takes too long, you are
welcome to implement it. But if you do, please make sure to talk about it with me before to make
sure we agree on the whys and the hows.
* Anything else I did not think of but that may still be usefull.

## Roadmap

### Ehlit itself

Codenames will be revealed once the development of their corresponding milestone starts.

* C with clean syntax / CWCS
* WIP: Cool, high level features / CHLF
* TODO: SL
* TODO: DRC
* TODO: OPAT

### Documentation

* WIP: Compiler code
* WIP: [Tutorial](https://github.com/lefta/ehlit-tutorial)
* TODO: Language specification
* TODO: Standard library documentation

### Ecosystem

* WIP: Syntax files for major text editors
* TODO: KDevelop plugin
* TODO: Support for GDB
