# Copyright © 2017-2018 Cedric Legrand
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

from arpeggio import ParserPython, ParseTreeNode, visit_parse_tree, NoMatch, StrMatch
from typing import List, Set

from ehlit.parser.ast import AST, Statement
from ehlit.parser.grammar import grammar, function_body_grammar, Context
from ehlit.parser.ast_builder import ASTBuilder
from ehlit.parser.error import ParseError, Failure


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


def parse(source: str) -> AST:
    parser: ParserPython = ParserPython(grammar, autokwd=True, memoization=True)
    try:
        parsed: ParseTreeNode = parser.parse_file(source)
        ast: AST = visit_parse_tree(parsed, ASTBuilder())
        ast.parser = parser
    except NoMatch as err:
        handle_parse_error(err, parser)
    return ast


def parse_function(source: str, have_return_value: bool) -> List[Statement]:
    Context.return_value = have_return_value
    parser: ParserPython = ParserPython(function_body_grammar, autokwd=True, memoization=True)
    try:
        parsed: ParseTreeNode = parser.parse(source)
        body: List[Statement] = visit_parse_tree(parsed, ASTBuilder())
    except NoMatch as err:
        handle_parse_error(err, parser)
    return body
