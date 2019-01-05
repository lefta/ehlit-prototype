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

from arpeggio import ParserPython, ParseTreeNode, visit_parse_tree, NoMatch

from ehlit.parser.ast import AST
from ehlit.parser.grammar import grammar
from ehlit.parser.ast_builder import ASTBuilder
from ehlit.parser.error import handle_parse_error


def parse(source: str) -> AST:
    parser: ParserPython = ParserPython(grammar, autokwd=True, memoization=True)
    try:
        parsed: ParseTreeNode = parser.parse_file(source)
        ast: AST = visit_parse_tree(parsed, ASTBuilder())
        ast.parser = parser
    except NoMatch as err:
        handle_parse_error(err, parser)
    return ast
