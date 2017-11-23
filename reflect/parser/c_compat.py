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

import os
import logging
from clang.cindex import Index, TranslationUnitLoadError
from reflect.parser.error import ParseError
from reflect.parser import ast

include_dirs = []

def cursor_to_reflect(cursor):
  ast = []
  for c in cursor.get_children():
    try:
      ast.append(globals()['parse_' + c.kind.name](c))
    except KeyError:
      logging.debug('c_compat: unimplemented: %s' % c.kind.name)
  return ast

def find_file_in_path(filename):
  for d in include_dirs:
    path = os.path.join(d, filename)
    if os.path.isfile(path):
      return path
  raise ParseError('%s: no such file or directory' % filename)

def parse_header(filename):
  path = find_file_in_path(filename + '.h')
  index = Index.create()
  try:
    tu = index.parse(path)
  except TranslationUnitLoadError as err:
    raise ParseError('%s: parsing failed' % filename)
  ast = cursor_to_reflect(tu.cursor)
  del tu
  del index
  return ast


def parse_FUNCTION_DECL(cursor):
  typ = ast.Type(ast.BuiltinType('any'))
  sym = ast.Symbol(cursor.spelling)
  args = []
  logging.debug('c_compat: declaring: %s with type any and no argument' % sym.name)
  return ast.FunctionDeclaration(typ, sym, args)
