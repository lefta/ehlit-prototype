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
import subprocess
from argparse import ArgumentParser
from clang.cindex import Index, TranslationUnitLoadError, CursorKind, TypeKind
from reflect.parser.error import ParseError, Failure
from reflect.parser import ast

include_dirs = []

# Add CFLAGS environment variable include dirs
parser = ArgumentParser()
parser.add_argument('-I', dest='dirs', default=[], action='append')
try:
  args, unknown = parser.parse_known_args(os.environ['CFLAGS'].split())
  for d in args.dirs:
    include_dirs += d
except KeyError:
  # Silently continue if there is no CFLAGS environment variable
  pass


try:
  # Run clang without input in verbose mode just to get its default include directories to have an
  # environment as close to upcoming build as possible. There will be differences do it like this,
  # but:
  # - We know we have clang as we rely on its library for parsing. At least it becomes a minor
  #   dependency.
  # - It is ways easier and more reliable than supporting each and every system / (cross) compiler
  #   combo out there
  # - They should be quite the same than the ones actually used
  # - Only differences should be minor / internal enough to not have consequences on reflect code
  proc = subprocess.run(['clang', '-E', '-v', '-'], stdin=subprocess.PIPE,
    stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')

  if proc.returncode != 0:
    # Just to stop the execution of the try block
    raise Exception('')

  i1 = i2 = None
  lines = proc.stderr.split('\n')
  for i, l in enumerate(lines):
    if l == '#include "..." search starts here:':
      i1 = i
    elif l == 'End of search list.':
      i2 = i

  # Should not happen unless clang changes its output, which is very unlikely
  assert i1 is not None and i2 is not None and i1 < i2
  lines = lines[i1+1:i2]
  lines.remove('#include <...> search starts here:')
  include_dirs += [l.strip() for l in lines]

except Exception:
  logging.warning('failed to get default include directories')


# Yups, mixing multiple languages in the same directory would be very disapointing, but who knows...
include_dirs.append('.')


def cursor_to_reflect(cursor):
  ast = []
  for c in cursor.get_children():
    try:
      ast.append(globals()['parse_' + c.kind.name](c))
    except KeyError:
      logging.debug('c_compat: unimplemented: parse_%s' % c.kind.name)
  return ast


uint_types = {
  'UCHAR',
  'USHORT',
  'UINT',
  'ULONG',
}

int_types = {
  'CHAR',
  'SHORT',
  'INT',
  'LONG',
}

def type_to_reflect(typ):
  if typ.kind.name in uint_types:
    return ast.BuiltinType('uint' + str(typ.get_size() * 8))
  if typ.kind.name in int_types:
    return ast.BuiltinType('int' + str(typ.get_size() * 8))

  try:
    return globals()['type_' + typ.kind.name](typ)
  except KeyError:
    logging.debug('c_compat: unimplemented: type_%s' % typ.kind.name)
  return ast.BuiltinType('any')

def find_file_in_path(filename):
  for d in include_dirs:
    path = os.path.join(d, filename)
    if os.path.isfile(path):
      return path
  raise ParseError([Failure(ParseError.Severity.Error, 0,
    '%s: no such file or directory' % filename)])

def parse_header(filename):
  path = find_file_in_path(filename + '.h')
  index = Index.create()
  try:
    tu = index.parse(path)
  except TranslationUnitLoadError as err:
    raise ParseError([Failure(ParseError.Severity.Error, 0, '%s: parsing failed' % filename)])
  ast = cursor_to_reflect(tu.cursor)
  del tu
  del index
  return ast


def parse_FUNCTION_DECL(cursor):
  args = []
  for c in cursor.get_children():
    if c.kind == CursorKind.PARM_DECL:
      args.append(ast.Declaration(type_to_reflect(c.type), ast.Symbol(0, c.spelling)))

  return ast.FunctionDeclaration(
    type_to_reflect(cursor.type.get_result()),
    ast.Symbol(0, cursor.spelling),
    args,
    cursor.type.is_function_variadic())

def parse_TYPEDEF_DECL(cursor):
  return ast.Alias(type_to_reflect(cursor.underlying_typedef_type), ast.Symbol(0, cursor.spelling))


def type_VOID(typ): return ast.BuiltinType('void')
def type_POINTER(typ):
  subtype = typ.get_pointee()
  builtin_type = {
    TypeKind.CHAR_S: ast.BuiltinType('str'),
    TypeKind.VOID: ast.BuiltinType('any')
  }.get(subtype.kind)
  if builtin_type is not None:
    return builtin_type
  return ast.Reference(type_to_reflect(subtype))

def type_TYPEDEF(typ):
  return ast.Alias(type_to_reflect(typ.get_canonical()), ast.Symbol(0, typ.spelling))
