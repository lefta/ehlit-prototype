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

class Import:
  def __init__(self, lib):
    self.lib = lib

class BuiltinType:
  def __init__(self, name):
    self.name = name

class Array:
  def __init__(self, typ):
    self.typ = typ

class Type:
  def __init__(self, sym):
    self.sym = sym

  def is_builtin(self):
    return type(self.sym) == BuiltinType

class Operator:
  def __init__(self, op):
    self.op = op

class VariableAssignment:
  def __init__(self, var, assign):
    self.var = var
    self.assign = assign

class Assignment:
  def __init__(self, expr):
    self.expr = expr

class Declaration:
  def __init__(self, typ, sym):
    self.typ = typ
    self.sym = sym

class VariableDeclaration:
  def __init__(self, decl, assign):
    self.decl = decl
    self.assign = assign

class FunctionDeclaration:
  def __init__(self, typ, sym, args):
    self.typ = typ
    self.sym = sym
    self.args = args

class FunctionDefinition:
  def __init__(self, proto, body):
    self.proto = proto
    self.body = body


class Statement:
  def __init__(self, expr):
    self.expr = expr

class Expression:
  def __init__(self):
    self.contents = []

  def append(self, c):
    self.contents.append(c)

class FunctionCall:
  def __init__(self, sym, args):
    self.sym = sym
    self.args = args

class ControlStructure:
  def __init__(self, name, cond, body):
    self.name = name
    self.cond = cond
    self.body = body

class Condition:
  def __init__(self, branches):
    self.branches = branches

class Return:
  def __init__(self, expr):
    self.expr = expr


class Symbol:
  def __init__(self, name):
    self.name = name

class String:
  def __init__(self, string):
    self.string = string

class Number:
  def __init__(self, num):
    self.num = num

class NullValue:
  pass


class AST:
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
