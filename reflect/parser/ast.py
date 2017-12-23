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
from reflect.parser import c_compat
from reflect.parser.error import ParseError

MOD_NONE = 0
MOD_CONST = 1

class Node:
  def build(self, parent):
    self.parent = parent

  def is_declaration(self):
    return False

  """
  Find a declaration when coming from downsides. Scoping structures would want to search symbols
  in this function rather than in get_declaration.

  The default is to try get_declaration on self, then to try with parent.
  """
  def find_declaration(self, sym):
    decl = self.get_declaration(sym)
    if decl is None:
      return self.parent.find_declaration(sym)
    return decl

  """
  Find a declaration when coming from upsides. Structures exposing symbols to their parent (
  like Import) would want to search symbols in this function rather than in find_declaration.
  """
  def get_declaration(self, sym): return None

  """
  Report an error to the parent, up to the root where it will be handled. There is no reason to
  override it, except intercepting it for whatever reason.
  """
  def error(self, msg): self.parent.error(msg)

  """
  Report a warning to the parent, up to the root where it will be handled. There is no reason to
  override it, except intercepting it for whatever reason.
  """
  def warn(self, msg): self.parent.warn(msg)


class Import(Node):
  def __init__(self, lib):
    self.lib = lib

  def build(self, parent):
    super().build(parent)
    try:
      self.syms = c_compat.parse_header(self.lib.name)
    except ParseError as err:
      self.error(err)
      self.syms = []

    for s in self.syms:
      s.build(self)

  def get_declaration(self, sym):
    for s in self.syms:
      decl = s.get_declaration(sym)
      if decl is not None:
        return decl

class BuiltinType(Node):
  def __init__(self, name):
    self.name = name

  @property
  def sym(self): return self

  @property
  def is_reference(self): return self.name == 'str' or self.name == 'any'

  @property
  def ref_offset(self): return 1 if self.is_reference else 0

  @property
  def is_type(self): return True

class Array(Node):
  def __init__(self, typ):
    self.typ = typ

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)

  @property
  def sym(self): return self

  @property
  def ref_offset(self): return 0

class Reference(Node):
  def __init__(self, typ):
    self.typ = typ

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)

  @property
  def is_reference(self): return True

  @property
  def ref_offset(self): return self.typ.sym.ref_offset + 1

class Type(Node):
  def __init__(self, sym, mods):
    self.sym = sym
    self._mods = mods

  def is_builtin(self):
    typ = type(self.sym)
    return typ == BuiltinType or typ == Reference

  @property
  def is_const(self): return self._mods & MOD_CONST

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
    self.operator = None

  def build(self, parent):
    super().build(parent)
    self.expr.build(self)

class Declaration(Node):
  def __init__(self, typ, sym):
    self.typ = typ
    self.name = sym.name
    self.sym = sym

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)
    self.sym.build(self)

  def get_declaration(self, sym):
    if self.name == sym:
      return self
    return None

  def is_declaration(self):
    return True

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

  def is_declaration(self):
    return True

class FunctionDeclaration(Node):
  def __init__(self, typ, sym, args):
    self.typ = typ
    self.sym = sym
    self.args = args
    self.name = sym.name

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)
    self.sym.build(self)
    for a in self.args:
      a.build(self)

  def get_declaration(self, sym):
    if self.sym.name == sym:
      return self
    for a in self.args:
      decl = a.get_declaration(sym)
      if decl is not None:
        return decl
    return None

  def is_declaration(self): return True

  @property
  def is_type(self): return False

class FunctionDefinition(Node):
  def __init__(self, proto, body):
    self.proto = proto
    self.name = proto.sym.name
    self.typ = proto.typ
    self.body = body

  def build(self, parent):
    super().build(parent)
    self.proto.build(self)
    for s in self.body:
      s.build(self)

  def get_declaration(self, sym):
    decl = self.proto.get_declaration(sym)
    if decl is not None:
      return decl

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
  def __init__(self, contents):
    self.contents = contents

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

  @property
  def ref_offset(self): return self.sym.ref_offset

  @ref_offset.setter
  def ref_offset(self, val): self.sym.ref_offset = val

  @property
  def is_cast(self): return self.sym.is_type

class ArrayAccess(Node):
  def __init__(self, child, idx):
    self.child = child
    self.idx = idx

  def build(self, parent):
    super().build(parent)
    self.child.build(self)
    self.idx.build(self)

  @property
  def ref_offset(self): return self.child.ref_offset

  @ref_offset.setter
  def ref_offset(self, val): self.child.ref_offset = val

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
    self.decl = None
    self.ref_offset = 0

  def build(self, parent):
    super().build(parent)
    if not parent.is_declaration():
      self.decl = self.find_declaration(self.name)
      if self.decl is None:
        self.error("use of undeclared identifier %s" % self.name)
      else:
        self.ref_offset = self.decl.typ.sym.ref_offset

  @property
  def is_type(self): return false if self.decl is None else self.decl.is_type

class String(Node):
  def __init__(self, string):
    self.string = string

class Number(Node):
  def __init__(self, num):
    self.num = num

class NullValue(Node):
  pass

class ReferencedValue(Node):
  def __init__(self, val):
    self.val = val

  def build(self, parent):
    super().build(parent)
    self.val.build(self)
    self.val.ref_offset -= 1

class UnaryOperatorValue(Node):
  def __init__(self, op, val):
    self.op = op
    self.val = val

  def build(self, parent):
    super().build(parent)
    self.val.build(self)


class PrefixOperatorValue(UnaryOperatorValue): pass
class SuffixOperatorValue(UnaryOperatorValue): pass

class AST(Node):
  def __init__(self, nodes):
    self.nodes = nodes
    self.errors = 0
    self.warnings = 0

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
      raise ParseError("build failed with %d errors and %d warnings" % (self.errors, self.warnings))
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
