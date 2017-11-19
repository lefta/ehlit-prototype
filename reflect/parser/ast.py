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

import logging

class Node:
  def build(self, parent):
    self.parent = parent

  def find_declaration(self, sym):
    return self.parent.find_declaration(sym)

  def get_declaration(self, sym):
    return None

  def error(self, msg):
    self.parent.error(msg)

  def warn(self, msg):
    self.parent.warn(msg)


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
    if not self.is_builtin():
      sym = self.find_declaration(self.sym)
      if sym is None:
        self.warn("use of undeclared type %s" % self.sym.name)
      else:
        self.sym = sym

class Operator(Node):
  def __init__(self, op):
    self.op = op

class VariableAssignment(Node):
  def __init__(self, var, assign):
    self.var = var
    self.assign = assign

  def build(self, parent):
    super().build(parent)
    var = self.find_declaration(self.var.name)
    if var is None:
      self.warn("use of undeclared variable %s" % self.var.name)
    else:
      self.var = var
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

  def get_declaration(self, sym):
    if self.sym.name == sym:
      return self
    return None

class VariableDeclaration(Node):
  def __init__(self, decl, assign):
    self.decl = decl
    self.assign = assign

  def build(self, parent):
    super().build(parent)
    self.decl.build(self)
    if self.assign is not None:
      self.assign.build(self)

  def get_declaration(self, sym):
    return self.decl.get_declaration(sym)

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

  def get_declaration(self, sym):
    if self.proto.sym.name == sym:
      return self
    for s in self.body:
      decl = s.get_declaration(sym)
      if decl is not None:
        return decl


class Statement(Node):
  def __init__(self, expr):
    self.expr = expr

  def build(self, parent):
    super().build(parent)
    self.expr.build(self)

  def get_declaration(self, sym):
    return self.expr.get_declaration(sym)

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
    sym = self.find_declaration(self.sym)
    if sym is None:
      self.warn("use of undeclared function %s" % self.sym.name)
    else:
      self.sym = sym
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
    self.errors = 0
    self.warnings = 0

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
    if self.errors != 0:
      raise ParseError("build failed with %d errors and %d warnings" % self.errors, self.warnings)
    elif self.warnings != 0:
      logging.info("build finished with %d warnings" % self.warnings)

  def error(self, msg):
    logging.error(msg)
    self.errors += 1

  def warn(self, msg):
    logging.warning(msg)
    self.warnings += 1

  def find_declaration(self, sym):
    for n in self.nodes:
      res = n.get_declaration(sym)
      if res is not None:
        return res
