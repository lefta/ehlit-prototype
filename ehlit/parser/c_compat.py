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

import os
import logging
import subprocess
from argparse import ArgumentParser
from clang.cindex import Index, TranslationUnitLoadError, CursorKind, TypeKind
from ehlit.parser.error import ParseError, Failure
from ehlit.parser import ast
from typing import List, Optional

include_dirs: List[str] = []
gparent: Optional[ast.Node] = None

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
  # - Only differences should be minor / internal enough to not have consequences on ehlit code
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


def cursor_to_ehlit(cursor):
  try:
    return globals()['parse_' + cursor.kind.name](cursor)
  except KeyError:
    logging.debug('c_compat: unimplemented: parse_%s' % cursor.kind.name)
  return None


uint_types = {
  'UCHAR',
  'USHORT',
  'UINT',
  'ULONG',
  'ULONGLONG',
}

int_types = {
  'CHAR_S',
  'SCHAR',
  'SHORT',
  'INT',
  'LONG',
  'LONGLONG',
}

def type_to_ehlit(typ):
  assert gparent is not None
  if typ.kind.name in uint_types:
    return ast.BuiltinType.make(gparent, 'uint' + str(typ.get_size() * 8))
  if typ.kind.name in int_types:
    return ast.BuiltinType.make(gparent, 'int' + str(typ.get_size() * 8))

  try:
    return globals()['type_' + typ.kind.name](typ)
  except KeyError:
    logging.debug('c_compat: unimplemented: type_%s' % typ.kind.name)
  return ast.BuiltinType.make(gparent, 'any')

def value_to_ehlit(val, typ):
  if typ.kind.name in uint_types or typ.kind.name in int_types:
    return ast.Number(val)

  try:
    return globals()['value_' + typ.kind.name](val)
  except KeyError:
    logging.debug('c_compat: unimplemented: value_%s' % typ.kind.name)
  return None

def find_file_in_path(filename):
  for d in include_dirs:
    path = os.path.join(d, filename)
    if os.path.isfile(path):
      return path
  raise ParseError([Failure(ParseError.Severity.Error, 0,
    '%s: no such file or directory' % filename, None)])

def parse_header(filename, parent):
  global gparent
  gparent = parent

  path = find_file_in_path(filename)
  index = Index.create()
  try:
    tu = index.parse(path)
  except TranslationUnitLoadError as err:
    raise ParseError([Failure(ParseError.Severity.Error, 0, '%s: parsing failed' % filename, None)])
  ast = []
  for c in tu.cursor.get_children():
    node = cursor_to_ehlit(c)
    if node is not None:
      ast.append(cursor_to_ehlit(c))
  del tu
  del index
  return ast


def parse_VAR_DECL(cursor):
  assign = cursor.get_definition()
  value = None
  if assign is not None:
    got_eq = False
    for t in assign.get_tokens():
      if value is not None:
        logging.debug(
          'c_compat: error: unhandled token while getting value: {}'.format(t.spelling)
        )
      elif got_eq:
        value = value_to_ehlit(t.spelling, cursor.type)
      elif t.spelling == '=':
        got_eq = True
    if got_eq is False:
      logging.debug('c_compat: error: unhandled assignment')
  return ast.VariableDeclaration(
    type_to_ehlit(cursor.type),
    ast.Identifier(0, cursor.spelling),
    ast.Assignment(value) if value is not None else None
  )

def parse_FUNCTION_DECL(cursor):
  args = []
  for c in cursor.get_children():
    if c.kind == CursorKind.PARM_DECL:
      args.append(ast.VariableDeclaration(type_to_ehlit(c.type), ast.Identifier(0, c.spelling)))

  return ast.FunctionDeclaration(
    ast.FunctionType(
      type_to_ehlit(cursor.type.get_result()),
      args,
      cursor.type.is_function_variadic()
    ),
    ast.Identifier(0, cursor.spelling)
  )

def parse_TYPEDEF_DECL(cursor):
  return ast.Alias(
    type_to_ehlit(cursor.underlying_typedef_type),
    ast.Symbol([ast.Identifier(0, cursor.spelling)])
  )

def parse_STRUCT_DECL(cursor):
  if not cursor.is_definition():
    return ast.Struct(0, ast.Identifier(0, cursor.spelling), None)
  fields = []
  for f in cursor.type.get_fields():
    fields.append(ast.VariableDeclaration(
      type_to_ehlit(f.type),
      ast.Identifier(0, f.spelling),
      None
    ))
  return ast.Struct(0, ast.Identifier(0, cursor.spelling), fields)

def parse_UNION_DECL(cursor):
  if not cursor.is_definition():
    return ast.EhUnion(0, ast.Identifier(0, cursor.spelling), None)
  fields = []
  for f in cursor.type.get_fields():
    fields.append(ast.VariableDeclaration(
      type_to_ehlit(f.type),
      ast.Identifier(0, f.spelling),
      None
    ))
  return ast.EhUnion(0, ast.Identifier(0, cursor.spelling), fields)


def type_VOID(typ):
  assert gparent is not None
  return ast.BuiltinType.make(gparent, 'void')

def type_POINTER(typ):
  assert gparent is not None
  subtype = typ.get_pointee()
  builtin_type = {
    TypeKind.CHAR_S: ast.BuiltinType.make(gparent, 'str'),
    TypeKind.SCHAR: ast.BuiltinType.make(gparent, 'str'),
    TypeKind.VOID: ast.BuiltinType.make(gparent, 'any')
  }.get(subtype.kind)
  if builtin_type is not None:
    return builtin_type
  res = type_to_ehlit(subtype)
  if type(res) == ast.FunctionType:
    return res
  return ast.Reference(res)

def type_TYPEDEF(typ):
  return ast.Symbol([ast.Identifier(0, typ.get_declaration().spelling)])

def type_CONSTANTARRAY(typ):
  if typ.element_count == 1:
    return ast.Array(type_to_ehlit(typ.element_type), None)
  return ast.Array(type_to_ehlit(typ.element_type), ast.Number(str(typ.element_count)))

def type_ELABORATED(typ):
  decl = typ.get_canonical().get_declaration()
  # If the declaration do not have a name, it may not be referenced. In this case, we have to embed
  # the type definition in its usage. Otherwise, we reference it with its identifier.
  if decl.spelling == '':
    res = cursor_to_ehlit(decl)
    if res is None:
      # The underlying type is not handled, so make this elaborated type unhandled too
      raise KeyError
    return res
  return ast.Symbol([ast.Identifier(0, decl.spelling)])

def type_RECORD(typ):
  typ = typ.get_declaration()
  # If the type do not have a name, it may not be referenced. In the case, we have to embed
  # the type definition in its usage. Otherwise, we reference it with its identifier.
  if typ.spelling == '':
    res = cursor_to_ehlit(typ)
    if res is None:
      # The underlying type is not handled, so make this elaborated type unhandled too
      raise KeyError
    return res
  return ast.Symbol([ast.Identifier(0, typ.spelling)])

def type_FUNCTIONPROTO(typ):
  args = []
  for a in typ.argument_types():
    args.append(type_to_ehlit(a))
  return ast.FunctionType(type_to_ehlit(typ.get_result()), args)

def type_UNEXPOSED(typ):
  return type_to_ehlit(typ.get_canonical())
