# Copyright © 2017 Cedric Legrand
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

from modgrammar import ParseError as mgParseError

from reflect.parser.grammar import ReflectGrammar
from reflect.parser.ast import AST

class ParseError(Exception):
  def __init__(self, error):
    self.col = error.col
    self.line = error.line
    self.msg = error.message

  def __str__(self):
    return "%d:%d: %s" % (self.line, self.col, self.msg)


def parse(source):
  parser = ReflectGrammar.parser()

  try:
    ast_generator = parser.parse_file(source)
    ast = AST()
    for node in ast_generator:
      ast_node = node.parse()
      if ast_node is not None:
        ast.append(ast_node)
  except mgParseError as err:
    raise ParseError(err)
  return ast
