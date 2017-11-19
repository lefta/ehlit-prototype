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

class Node:
  def build(self, parent):
    self.parent = parent


class Import(Node):
  def __init__(self, lib):
    self.lib = lib

class BuiltinType(Node):
  def __init__(self, name):
    self.name = name

class Array(Node):
  def __init__(self, typ):
    self.typ = typ

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)

class Type(Node):
  def __init__(self, sym):
    self.sym = sym

  def is_builtin(self):
    return type(self.sym) == BuiltinType

  def build(self, parent):
    super().build(parent)
    self.sym.build(self)

class Operator(Node):
  def __init__(self, op):
    self.op = op

class VariableAssignment(Node):
  def __init__(self, var, assign):
    self.var = var
    self.assign = assign

  def build(self, parent):
    super().build(parent)
    self.var.build(self)
    self.assign.build(self)

class Assignment(Node):
  def __init__(self, expr):
    self.expr = expr

  def build(self, parent):
    super().build(parent)
    self.expr.build(self)

class Declaration(Node):
  def __init__(self, typ, sym):
    self.typ = typ
    self.sym = sym

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)
    self.sym.build(self)

class VariableDeclaration(Node):
  def __init__(self, decl, assign):
    self.decl = decl
    self.assign = assign

  def build(self, parent):
    super().build(parent)
    self.decl.build(self)
    if self.assign is not None:
      self.assign.build(self)

class FunctionDeclaration(Node):
  def __init__(self, typ, sym, args):
    self.typ = typ
    self.sym = sym
    self.args = args

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)
    self.sym.build(self)
    for a in self.args:
      a.build(self)

class FunctionDefinition(Node):
  def __init__(self, proto, body):
    self.proto = proto
    self.body = body

  def build(self, parent):
    super().build(parent)
    self.proto.build(self)
    for s in self.body:
      s.build(self)


class Statement(Node):
  def __init__(self, expr):
    self.expr = expr

  def build(self, parent):
    super().build(parent)
    self.expr.build(self)

class Expression(Node):
  def __init__(self):
    self.contents = []

  def append(self, c):
    self.contents.append(c)

  def build(self, parent):
    super().build(parent)
    for e in self.contents:
      e.build(self)

class FunctionCall(Node):
  def __init__(self, sym, args):
    self.sym = sym
    self.args = args

  def build(self, parent):
    super().build(parent)
    self.sym.build(self)
    for a in self.args:
      a.build(self)

class ControlStructure(Node):
  def __init__(self, name, cond, body):
    self.name = name
    self.cond = cond
    self.body = body

  def build(self, parent):
    super().build(parent)
    if self.cond is not None:
      self.cond.build(self)
    for s in self.body:
      s.build(self)

class Condition(Node):
  def __init__(self, branches):
    self.branches = branches

  def build(self, parent):
    super().build(parent)
    for b in self.branches:
      b.build(self)

class Return(Node):
  def __init__(self, expr):
    self.expr = expr

  def build(self, parent):
    super().build(parent)
    self.expr.build(self)


class Symbol(Node):
  def __init__(self, name):
    self.name = name

class String(Node):
  def __init__(self, string):
    self.string = string

class Number(Node):
  def __init__(self, num):
    self.num = num

class NullValue(Node):
  pass


class AST(Node):
  def __init__(self):
    self.nodes = []

  def append(self, n):
    self.nodes.append(n)

  def __iter__(self):
    return self.nodes.__iter__()

  def __getitem__(self, key):
    return self.nodes[key]

  def __len__(self):
    return len(self.nodes)

  def build(self):
    self.parent = None
    for n in self.nodes:
      n.build(self)
