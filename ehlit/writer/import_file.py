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


class ImportWriter:
  def __init__(self, ast, f):
    self.file = sys.stdout if f == '-' else open(f, 'w')
    self.indent = 0
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

  def writeInclude(self, node):
    pass

  def writeImport(self, node):
    pass

  def write_type_prefix(self, node):
    pass

  def writeFunctionDefinition(self, node):
    self.writeFunctionDeclaration(node)

  def writeFunctionDeclaration(self, node):
    self.write(node.typ.ret)
    self.file.write(' ')
    self.write(node.sym)
    self.file.write('(')
    self.writeArgumentDefinitionList(node.typ.args)
    self.file.write(")")

  def writeDeclaration(self, node):
    self.write(node.typ_src)
    if node.sym is not None:
      self.file.write(' ')
      self.write(node.sym)

  def writeArgumentDefinitionList(self, node):
    if len(node) != 0:
      i = 0
      count = len(node)
      while i < count:
        self.writeDeclaration(node[i])
        i += 1
        if i < count:
          self.file.write(', ')

  def writeExpression(self, node):
    if node.is_parenthesised:
      self.file.write('(')
    i = 0
    count = len(node.contents)
    while i < count:
      self.write(node.contents[i])
      i += 1
      if i < count:
        self.file.write(' ')
    if node.is_parenthesised:
      self.file.write(')')

  def writeArray(self, node):
    self.write(node.child)
    self.file.write('[')
    if node.length is not None:
      self.write(node.length)
    self.file.write(']')

  def writeTypeReference(self, node):
    if node.is_const:
      self.file.write('const ')
    self.file.write('ref ')
    self.write(node.child)

  def writeReferenceToType(self, node):
    self.file.write('ref ')
    self.write(node.child)

  def writeFunctionType(self, node):
    self.write(node.ret)
    self.file.write('(')
    i = 0
    while i < len(node.args):
      if i is not 0:
        self.file.write(', ')
      self.write(node.args[i])
      i += 1
    self.file.write(')')

  def writeAssignment(self, node):
    self.file.write(' ')
    if node.operator is not None:
      self.write(node.operator)
    self.file.write('= ')
    self.write(node.expr)

  def writeCompoundIdentifier(self, node):
    fst = True
    for e in node.elems:
      if not fst:
        self.file.write('.')
      self.write(e)
      fst = False

  def writeIdentifier(self, node):
    self.file.write(node.name)

  def writeTemplatedIdentifier(self, node):
    self.file.write(node.name)
    self.file.write('<')
    for t in node.types:
      self.write(t)
      if t is not node.types[-1]:
        self.file.write(', ')
    self.file.write('>')

  def writeNumber(self, node):
    self.file.write(node.num)

  def writeAlias(self, node):
    self.file.write('alias ')
    self.write(node.src_sym)
    self.file.write(' ')
    self.write(node.dst)
    self.file.write('\n')

  def writeVariableDeclaration(self, node):
    self.writeDeclaration(node)
    if node.assign is not None:
      self.file.write(' = ')
      self.write(node.assign)

  def writeContainerStructure(self, node):
    self.file.write('\n{} '.format(node.display_name))
    self.write(node.sym)
    if node.fields is not None:
      self.file.write(' {\n')
      self.indent += 1
      for f in node.fields:
        self.write_indent()
        self.write(f)
        self.file.write('\n')
      self.indent -= 1
      self.file.write('}\n')

  def writeStruct(self, node):
    self.writeContainerStructure(node)

  def writeEhUnion(self, node):
    self.writeContainerStructure(node)
