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

import sys
from reflex.parser.ast import (Reference, Array, ArrayAccess, BuiltinType, FunctionType,
  FunctionDeclaration, FunctionCall, Symbol, Struct)

class SourceWriter:
  def __init__(self, ast, f):
    self.file = sys.stdout if f == '-' else open(f, 'w')

    self.indent = 0
    self.in_import = 0
    self.types = {
      'str': 'char*',
      'any': 'void*',
      'void': 'void',
      'char': 'int8_t',
      'int': 'int32_t',
      'int8': 'int8_t',
      'int16': 'int16_t',
      'int32': 'int32_t',
      'int64': 'int64_t',
      'uint8': 'uint8_t',
      'uint16': 'uint16_t',
      'uint32': 'uint32_t',
      'uint64': 'uint64_t',
      'size': 'size_t',
      'bool': 'uint8_t',
    }

    self.control_structures = {
      'if': 'if',
      'elif': 'else if',
      'else': 'else',
      'while': 'while',
    }

    self.file.write('#include <stddef.h>\n#include <stdint.h>\n')

    for node in ast:
      self.write(node)

    if f != '-':
      self.file.close()

  def write(self, node):
    func = getattr(self, 'write' + type(node).__name__)
    func(node)

  def write_indent(self):
    i = 0
    while i < self.indent:
      self.file.write('    ')
      i += 1

  def write_value(self, node):
    if type(node.decl) is FunctionDeclaration:
      parent = node.parent
      while type(parent) is Reference or type(parent) is Symbol:
        parent = parent.parent
      if type(parent) is not FunctionCall:
        self.file.write('&')
        return
    if node.ref_offset == -1:
      self.file.write('&')
    else:
      i = node.ref_offset
      while i > 0:
        self.file.write('*')
        i -= 1
    if node.cast is not None:
      self.file.write('(')
      self.write(node.cast)
      self.file.write(')')
    if node.is_type and node.is_const:
      self.file.write(' const')

  def writeInclude(self, inc):
    self.write_indent()
    self.file.write('#include <')
    self.write(inc.lib)
    self.file.write('.h>\n')

  def writeImport(self, node):
    self.in_import += 1
    for sym in node.syms:
      self.write(sym)
    self.in_import -= 1

  def writeBuiltinType(self, typ):
    self.file.write(self.types[typ.name])
    if typ.is_const:
      self.file.write(' const')

  def writeReference(self, ref):
    self.write(ref.child)
    if ref.is_type:
      self.file.write('*')
      if ref.is_const:
        self.file.write(' const')

  def writeArray(self, arr):
    self.write(arr.child)
    if arr.length is None:
      self.file.write('*')
    if self.array_needs_parens(arr):
      self.file.write('(')

  def is_dynamic_array(self, node):
    typ = type(node)
    return (typ is Array and node.length is None) or typ is Reference

  def array_needs_parens(self, node):
    if self.is_dynamic_array(node):
      return False
    typ = type(node.parent)
    if typ is not Array and typ is not Reference:
      return False
    return self.is_dynamic_array(node.parent)

  def write_declaration_post(self, node):
    typ = type(node)
    if typ is FunctionType:
      self.file.write(')(')
      i = 0
      while i < len(node.args):
        if i is not 0:
          self.file.write(', ')
        self.write(node.args[i])
        i += 1
      self.file.write(')')
    elif typ is Array or typ is Reference:
      if self.array_needs_parens(node):
        self.file.write(')')
      if typ is Array and node.length is not None:
        self.file.write('[')
        self.write(node.length)
        self.file.write(']')
      self.write_declaration_post(node.child)

  def writeFunctionType(self, node):
    self.write(node.ret)
    self.file.write('(*')

  def write_type_prefix(self, typ):
    while type(typ) is Reference:
      typ = typ.child
    if type(typ) is Symbol:
      typ = typ.decl
    prefix = {
      Struct: 'struct',
    }.get(type(typ))
    if prefix is not None:
      self.file.write(prefix + ' ')

  def writeDeclaration(self, decl):
    self.write_type_prefix(decl.typ)
    self.write(decl.typ)
    if decl.sym is not None:
      self.file.write(' ')
      self.write(decl.sym)
    self.write_declaration_post(decl.typ)

  def writeVariableDeclaration(self, decl):
    self.write(decl.decl)
    if decl.assign is not None:
      self.write(decl.assign)

  def writeArgumentDefinitionList(self, args):
    if len(args) == 0:
      self.file.write('void')
    else:
      i = 0
      count = len(args)
      while i < count:
        self.writeDeclaration(args[i])
        i += 1
        if i < count:
          self.file.write(', ')

  def writeFunctionPrototype(self, proto):
    self.write(proto.typ)
    self.file.write(' ')
    self.write(proto.sym)
    self.file.write('(')
    self.writeArgumentDefinitionList(proto.args)
    self.file.write(")")

  def writeFunctionDeclaration(self, fun):
    self.write_indent()
    self.writeFunctionPrototype(fun)
    self.file.write(';\n')

  def writeFunctionDefinition(self, fun):
    if self.in_import > 0:
      self.writeFunctionDeclaration(fun.proto)
      return

    self.write_indent()
    self.file.write("\n")
    self.writeFunctionPrototype(fun.proto)
    self.file.write("\n{\n")

    self.indent += 1
    for instruction in fun.body:
      self.write(instruction)
    self.indent -= 1

    self.file.write("}\n")

  def writeStatement(self, stmt):
    self.write_indent()
    self.write(stmt.expr)
    self.file.write(';\n')

  def writeExpression(self, expr):
    if expr.is_parenthesised:
      self.file.write('(')
    i = 0
    count = len(expr.contents)
    while i < count:
      self.write(expr.contents[i])
      i += 1
      if i < count:
        self.file.write(' ')
    if expr.is_parenthesised:
      self.file.write(')')

  def writeAssignment(self, assign):
    self.file.write(' ')
    if assign.operator is not None:
      self.write(assign.operator)
    self.file.write('= ')
    self.write(assign.expr)

  def writeVariableAssignment(self, assign):
    self.write(assign.var)
    self.write(assign.assign)

  def writeFunctionCall(self, call):
    if call.is_cast:
      self.file.write('((')
      self.write(call.sym)
      self.file.write(')')
      self.write(call.args[0])
      self.file.write(')')
    else:
      self.write(call.sym)
      self.file.write('(')
      i = 0
      count = len(call.args)
      while i < count:
        self.write(call.args[i])
        i += 1
        if i < count:
          self.file.write(', ')
      self.file.write(')')

  def writeArrayAccess(self, arr):
    self.write_value(arr)
    decl = arr.decl.typ
    sym = arr
    while type(decl) is Array or type(decl) is Reference or BuiltinType('str') == decl:
      if type(sym) is ArrayAccess:
        sym = sym.child
      decl = decl.child
    cur = sym.parent
    decl = decl.parent
    while type(decl) is Array or type(decl) is Reference or BuiltinType('str') == decl:
      if type(decl) is Reference:
        rdecl = decl
        while type(rdecl) is Reference:
          rdecl = rdecl.parent
        if type(rdecl) is Array:
          self.file.write('*')
      elif type(cur) is ArrayAccess:
        if type(decl.parent) is Reference:
          self.file.write('(')
        cur = cur.parent
      decl = decl.parent
    self.write(sym)
    decl = arr.decl.typ
    while type(decl) is Reference:
      decl = decl.child
    while type(arr) is ArrayAccess or type(decl) is Reference:
      if type(decl) is not Reference and type(arr) is ArrayAccess:
        if type(decl.parent) is Reference:
          self.file.write(')')
        self.file.write('[')
        self.write(arr.idx)
        self.file.write(']')
        arr = arr.child
      decl = decl.child

  def writeControlStructure(self, struct):
    self.write_indent()
    self.file.write(self.control_structures[struct.name])
    if struct.cond is not None:
      self.file.write(' (')
      self.write(struct.cond)
      self.file.write(')')
    self.file.write('\n')

    self.write_indent()
    self.file.write('{\n')
    self.indent += 1
    for instruction in struct.body:
      self.write(instruction)
    self.indent -= 1

    self.write_indent()
    self.file.write('}\n')

  def writeCondition(self, cond):
    for branch in cond.branches:
      self.write(branch)

  def writeReturn(self, ret):
    self.file.write('return (')
    self.write(ret.expr)
    self.file.write(')')

  def writeOperator(self, op):
    self.file.write(op.op)

  def writeSymbol(self, node):
    self.write_value(node)
    i = 0
    while i < len(node.elems):
      if i < len(node.elems) - 1:
        ref_offset = node.elems[i].ref_offset
        if ref_offset is 0:
          self.write(node.elems[i])
          self.file.write('.')
        elif ref_offset is 1:
          self.write(node.elems[i])
          self.file.write('->')
        else:
          self.file.write('(')
          while ref_offset > 1:
            self.file.write('*')
            ref_offset -= 1
          self.write(node.elems[i])
          self.file.write(')->')
      else:
        self.write(node.elems[i])
      i += 1

  def writeIdentifier(self, node):
    if node.decl is not None:
      self.file.write(node.decl.name)
    else:
      self.file.write(node.name)

  def writeChar(self, c):
    self.file.write('\'')
    self.file.write(c.char)
    self.file.write('\'')

  def writeString(self, s):
    self.file.write('"')
    self.file.write(s.string)
    self.file.write('"')

  def writeNumber(self, num):
    self.file.write(num.num)

  def writeNullValue(self, stmt):
    self.file.write('NULL')

  def writeBoolValue(self, node):
    self.file.write('0' if node.val is False else '!0')

  def writePrefixOperatorValue(self, val):
    self.file.write(val.op)
    self.write(val.val)

  def writeSuffixOperatorValue(self, val):
    self.write(val.val)
    self.file.write(val.op)

  def writeSizeof(self, node):
    self.file.write('sizeof(')
    self.write(node.sz_typ)
    self.file.write(')')

  def writeAlias(self, node):
    if node.src.is_type:
      self.file.write('typedef ')
      self.write(node.src)
      self.file.write(' ')
      self.write(node.dst)
      self.file.write(';\n')

  def writeStruct(self, node):
    self.file.write('\nstruct ')
    self.write(node.sym)
    self.file.write('\n{\n')
    self.indent += 1
    for f in node.fields:
      self.write_indent()
      self.write(f)
      self.file.write(';\n')
    self.indent -= 1
    self.file.write('};\n')
