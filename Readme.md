# Reflex Lang

## Introduction

Reflex is a compiled programmation language designed for performance, simplicity, readability and
typing economy (in this order). It is a global usage language, but excells when performance or
compatibility are required. It is designed to create programs directly but also allows for C code
prototyping.

It is compatible out of the box with any existing C library, and using a Reflex library in a C
program is very easy.

It is distributed under the MIT license. In short, do whatever you want, but keep the original
license text in any distribution and dont point at me if you get problems. See the `Copying` file
for details.

## Hello world example

Note that the language is still a work in progress, this example will likely change in the future.

    include stdio

    int main(int ac, str[] av)
    {
        printf("Hello, world!\n")
        return 0
    }

## Requirements

* Python 3.5+
* arpeggio Python module
* clang with Python 3.5+ bindings (shipped with clang 5.0+)

## Basic usage

All you need is calling `python -m reflex` with the reflex file you wish to build as argument.
Note that for this to work, you must either be at the root of this repository, or the reflex
package must be installed somewhere in your python path.

This will generate a C file at the same place with the same name, just replacing the `.ref`
extension with `.c`. Next, you may build your C file(s) as you would with other programs.

This duplicates build work, but all (good?) compilation system allows you to automate this, so you
do not even have to think about this. For instance, with Makefiles, you could use a rule like:

    out/src/%.c: %.ref
        python -m reflex $<

This way, you may build your program the exact same way you would build it if it was written in pure
C. C source files will be generated dynamically as needed.

## Roadmap

* WIP: Language definition
* TODO: Standard library definition
* WIP: Compiler
* TODO: Language specification
* WIP: Syntax files for major text editors
* TODO: Autocompletion module for Atom
