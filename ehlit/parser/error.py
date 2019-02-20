# Copyright © 2017-2019 Cedric Legrand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from arpeggio import ParserPython, NoMatch, StrMatch
from enum import IntEnum
from typing import List, Optional, Set, Tuple


excluded_tokens: Set[str] = {
    # These are not relevant to display
    "'['",
    "'.'",
    # Builtin types are identifiers
    'bool',
    'int',
    'int8',
    'int16',
    'int32',
    'int64',
    'uint',
    'uint8',
    'uint16',
    'uint32',
    'uint64',
    'size',
    'float',
    'double',
    'decimal',
    'char',
    'str',
    'void',
    'any',
    'func',
    # Part of a type, so they belong to an identifier too
    'ref',
    'const',
    'volatile',
    'restrict',
}


def handle_parse_error(err: NoMatch, parser: ParserPython) -> None:
    exp: List[str] = []
    for r in err.rules:
        repr: str = "'%s'" % str(r) if type(r) is StrMatch else str(r)
        if repr not in excluded_tokens and repr not in exp:
            exp.append(repr)
    raise ParseError([Failure(ParseError.Severity.Fatal, err.position,
                              'expected %s' % (' or '.join(exp)), parser.file_name)], parser)


class Failure(Exception):
    def __init__(self, severity: 'ParseError.Severity', pos: int, msg: str, file: Optional[str]
                 ) -> None:
        self.severity: ParseError.Severity = severity
        self.pos: int = pos
        self.msg: str = msg
        self.file: Optional[str] = file
        self.linecol: Optional[Tuple[int, int]] = None

    def __str__(self) -> str:
        assert self.linecol is not None and self.file is not None
        return self.file + ':' + str(self.linecol[0]) + ':' + str(self.linecol[1]) + ': ' + self.msg


class ParseError(Exception):
    class Severity(IntEnum):
        Unset = -1
        Warning = 1
        Error = 2
        Fatal = 3

    def __init__(self, failures: List[Failure], parser: Optional[ParserPython] = None) -> None:
        self.failures: List[Failure] = failures
        self.max_level: ParseError.Severity = ParseError.Severity.Unset
        self.errors: int = 0
        self.warnings: int = 0
        if parser is not None:
            for f in failures:
                if f.severity > self.max_level:
                    self.max_level = f.severity
                if f.severity is ParseError.Severity.Warning:
                    self.warnings += 1
                else:
                    self.errors += 1
                f.linecol = parser.pos_to_linecol(f.pos)

    @property
    def summary(self) -> str:
        if self.warnings == 0:
            return 'build finished with %d errors' % self.errors
        elif self.errors == 0:
            return 'build finished with %d warnings' % self.warnings
        else:
            return 'build finished with %d errors and %d warnings' % (self.errors, self.warnings)

    def __str__(self) -> str:
        res: List[str] = []
        for f in self.failures:
            res.append(str(f))
        return '\n'.join(res) + '\n'
