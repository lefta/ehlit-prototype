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

import sys

class SourceWriter:
  def __init__(self, ast, f):
    self.file = sys.stdout if f == '-' else open(f, 'w')

    self.indent = 0
    self.types = {
      'str': 'char*',
      'any': 'void*',
      'void': 'void',
      'int': 'int',
      'size': 'size_t',
    }

    self.control_structures = {
      'if': 'if',
      'elif': 'else if',
      'else': 'else',
      'while': 'while',
    }

    for node in ast:
      self.write(node)

  def write(self, node):
    func = getattr(self, 'write' + type(node).__name__)
    func(node)

  def write_indent(self):
    i = 0
    while i < self.indent:
      self.file.write('    ')
      i += 1

  def writeImport(self, imp):
    self.write_indent()
    self.file.write('#include <')
    self.write(imp.lib)
    self.file.write('.h>\n')

  def writeType(self, typ):
    if typ.is_builtin():
      self.file.write(self.types[typ.sym.name])
    else:
      self.write(typ.sym)

  def writeArray(self, arr):
    self.write(arr.typ)
    self.file.write('*')

  def writeDeclaration(self, decl):
    self.write(decl.typ)
    self.file.write(' ')
    self.write(decl.sym)

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
    self.file.write(")\n")

  def writeFunctionDefinition(self, fun):
    self.write_indent()
    self.file.write("\n")
    self.writeFunctionPrototype(fun.proto)
    self.file.write("{\n")

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
    i = 0
    count = len(expr.contents)
    while i < count:
      self.write(expr.contents[i])
      i += 1
      if i < count:
        self.file.write(' ')

  def writeAssignment(self, assign):
    self.file.write(' = ')
    self.write(assign.expr)

  def writeVariableAssignment(self, assign):
    self.write(assign.var)
    self.write(assign.assign)

  def writeFunctionCall(self, call):
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

  def writeVariableUsage(self, use):
    self.write(use.var)

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

  def writeSymbol(self, sym):
    self.file.write(sym.name)

  def writeString(self, s):
    self.file.write('"')
    self.file.write(s.string)
    self.file.write('"')

  def writeNumber(self, num):
    self.file.write(num.num)

  def writeNullValue(self, stmt):
    self.file.write('NULL')
