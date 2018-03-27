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

from os import path, getcwd
from reflect.parser import c_compat, parse
from reflect.parser.error import ParseError, Failure

MOD_NONE = 0
MOD_CONST = 1

class Node:
  def __init__(self, pos):
    self.pos = pos

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
  Report a failure to the parent, up to the root where it will be handled. There is no reason to
  override it, except intercepting it for whatever reason.
  """
  def fail(self, severity, pos, msg): self.parent.fail(severity, pos, msg)

  """
  Shorthand for fail with severity Error.
  """
  def error(self, pos, msg): self.parent.fail(ParseError.Severity.Error, pos, msg)

  """
  Shorthand for fail with severity Warning.
  """
  def warn(self, pos, msg): self.parent.fail(ParseError.Severity.Warning, pos, msg)

  @property
  def import_paths(self): return self.parent.import_paths


class GenericExternInclusion(Node):
  def __init__(self, pos, lib):
    super().__init__(pos)
    self.lib = lib

  def build(self, parent):
    super().build(parent)
    try:
      self.syms = self.parse()
    except ParseError as err:
      for e in err.failures:
        self.fail(e.severity, self.pos, e.message)
        self.syms = []

    for s in self.syms:
      s.build(self)

  def get_declaration(self, sym):
    for s in self.syms:
      decl = s.get_declaration(sym)
      if decl is not None:
        return decl

class Import(GenericExternInclusion):
  def parse(self):
    for p in self.import_paths:
      try: return parse.parse(path.join(p, self.lib.name + '.ref')).nodes
      except FileNotFoundError: pass
    self.error(self.pos, '%s: no such file or directory' % self.lib.name)

class Include(GenericExternInclusion):
  def parse(self): return c_compat.parse_header(self.lib.name)

class Value(Node):
  def __init__(self, pos=0):
    super().__init__(pos)
    self.ref_offset = 0
    self.cast = None

  def auto_cast(self, target):
    invert_ref_level = False
    if self.typ != target.typ:
      if self.typ == BuiltinType('any'):
        self.cast = target.typ.from_any()
        target = self.cast
      elif target.typ == BuiltinType('any'):
        target = self.typ.from_any()
        invert_ref_level = True

    if self.typ:
      if target.is_declaration():
        target_ref_level = target.typ.ref_offset
      else:
        target_ref_level = target.typ.ref_offset - target.ref_offset

      if invert_ref_level:
        target_ref_level *= -1
      self.ref_offset = self.typ.ref_offset - target_ref_level

class BuiltinType(Node):
  def __init__(self, name):
    self.name = name
    self.mods = MOD_NONE

  def set_modifiers(self, mods):
    self.mods = mods

  @property
  def sym(self): return self

  @property
  def subtype(self): return BuiltinType('char') if self.name == 'str' else None

  @property
  def is_reference(self): return False

  @property
  def ref_offset(self): return 1 if self.is_reference else 0

  @property
  def is_type(self): return True

  @property
  def typ(self): return self

  @property
  def is_const(self): return self.mods & MOD_CONST

  def from_any(self): return self if self.name == 'str' else Reference(self)

  def __eq__(self, rhs):
    if type(rhs) != BuiltinType:
      return False
    return self.name == rhs.name

class Array(Node):
  def __init__(self, subtype):
    self.subtype = subtype

  def build(self, parent):
    super().build(parent)
    self.subtype.build(self)

  @property
  def typ(self): return self

  @property
  def sym(self): return self

  @property
  def ref_offset(self): return 0

  @property
  def is_type(self): return True

  def from_any(self): return self

class Reference(Node):
  def __init__(self, typ):
    self.typ = typ
    self.mods = MOD_NONE

  def set_modifiers(self, mods): self.mods = mods

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)
    if not self.typ.is_type:
      self.typ.ref_offset -= 1

  @property
  def is_reference(self): return True

  @property
  def is_type(self): return self.typ.is_type

  @property
  def is_const(self): return self.mods & MOD_CONST

  @property
  def decl(self): return self.typ.decl

  @property
  def ref_offset(self):
    if self.typ.is_type:
      return self.typ.sym.ref_offset + 1
    return self.typ.ref_offset - 1

  def auto_cast(self, target): return self.typ.auto_cast(target)

class Operator(Node):
  def __init__(self, op):
    self.op = op

  def auto_cast(self, target_type): pass

class VariableAssignment(Node):
  def __init__(self, var, assign):
    self.var = var
    self.assign = assign

  def build(self, parent):
    super().build(parent)
    self.var.build(self)
    self.assign.build(self)
    self.assign.expr.auto_cast(self.var)

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

  @property
  def is_type(self): return False

class VariableDeclaration(Node):
  def __init__(self, decl, assign):
    self.decl = decl
    self.assign = assign

  def build(self, parent):
    super().build(parent)
    self.decl.build(self)
    if self.assign is not None:
      self.assign.build(self)
      self.assign.expr.auto_cast(self.decl)

  def get_declaration(self, sym):
    return self.decl.get_declaration(sym)

  def is_declaration(self):
    return True

class FunctionDeclaration(Node):
  def __init__(self, typ, sym, args, variadic=False):
    self.typ = typ
    self.sym = sym
    self.args = args
    self.name = sym.name
    self.variadic = variadic

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

  @property
  def is_variadic(self): return self.variadic

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

  def is_declaration(self): return True

class Statement(Node):
  def __init__(self, expr):
    self.expr = expr

  def build(self, parent):
    super().build(parent)
    self.expr.build(self)

  def get_declaration(self, sym):
    return self.expr.get_declaration(sym)

class Expression(Node):
  def __init__(self, contents, parenthesised):
    self.contents = contents
    self.parenthesised = parenthesised

  def build(self, parent):
    super().build(parent)
    for e in self.contents:
      e.build(self)

  def auto_cast(self, target_type):
    for e in self.contents:
      e.auto_cast(target_type)

  @property
  def is_parenthesised(self): return self.parenthesised

class FunctionCall(Node):
  def __init__(self, pos, sym, args):
    self.pos = pos
    self.sym = sym
    self.args = args

  def build(self, parent):
    super().build(parent)
    self.sym.build(self)

    if self.is_cast:
      if len(self.args) < 1:
        self.error(self.pos, 'cast requires a value')
      elif len(self.args) > 1:
        self.error(self.pos, 'too many values for cast expression')
    elif self.sym.decl is not None:
      diff = len(self.args) - len(self.sym.decl.args)
      err = None
      if diff < 0:
        err = 'not enough'
      elif diff > 0 and not self.sym.decl.is_variadic:
        err = 'too many'
      if err is not None:
        self.warn(self.pos, '{} arguments for call to {}: expected {}, got {}'.format(err,
          self.sym.name, len(self.sym.decl.args), len(self.args)))

    i = 0
    while i < len(self.args):
      self.args[i].build(self)
      if not self.is_cast and self.sym.decl is not None and i < len(self.sym.decl.args):
        self.args[i].auto_cast(self.sym.decl.args[i])
      i += 1

  @property
  def ref_offset(self): return self.sym.ref_offset

  @ref_offset.setter
  def ref_offset(self, val): self.sym.ref_offset = val

  @property
  def is_cast(self): return self.sym.is_type

  @property
  def typ(self): return self.sym if self.is_cast else self.sym.typ

  def auto_cast(self, target_type):
    if not self.is_cast:
      self.sym.auto_cast(target_type)

class ArrayAccess(Value):
  def __init__(self, child, idx):
    super().__init__()
    self.child = child
    self.idx = idx

  def build(self, parent):
    super().build(parent)
    self.child.build(self)
    self.idx.build(self)

  @property
  def typ(self): return self.child.typ.subtype

  def from_any(self): return self.child.typ.subtype.from_any()

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

  def find_declaration(self, name):
    for s in self.body:
      decl = s.get_declaration(name)
      if decl is not None:
        return decl
    return super().find_declaration(name)

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

    decl = self.parent
    while type(decl) is not FunctionDefinition:
      decl = decl.parent
    self.expr.auto_cast(decl)


class Symbol(Value):
  def __init__(self, pos, name):
    super().__init__(pos)
    self.name = name
    self.decl = None
    self.mods = MOD_NONE

  def set_modifiers(self, mods): self.mods = mods

  @property
  def is_const(self): return self.mods & MOD_CONST

  def build(self, parent):
    super().build(parent)
    if not parent.is_declaration():
      self.decl = self.find_declaration(self.name)
      if self.decl is None:
        self.error(self.pos, "use of undeclared identifier %s" % self.name)
      else:
        self.ref_offset = self.decl.typ.ref_offset

  @property
  def is_type(self): return False if self.decl is None else self.decl.is_type

  @property
  def typ(self): return self.decl.typ if self.decl is not None else BuiltinType('any')

class String(Value):
  def __init__(self, string):
    super().__init__()
    self.string = string

  @property
  def typ(self): return BuiltinType('str')

  def auto_cast(self, target_type): pass

class Char(Value):
  def __init__(self, char):
    super().__init__()
    self.char = char

  @property
  def typ(self): return BuiltinType('char')

  def auto_cast(self, target_type): pass

class Number(Value):
  def __init__(self, num):
    super().__init__()
    self.num = num

  @property
  def typ(self): return BuiltinType('int')

  def auto_cast(self, target_type): pass

class NullValue(Value):
  def __init__(self):
    super().__init__()

  @property
  def typ(self): return BuiltinType('any')

  def auto_cast(self, target_type): pass

class UnaryOperatorValue(Node):
  def __init__(self, op, val):
    self.op = op
    self.val = val

  def build(self, parent):
    super().build(parent)
    self.val.build(self)

  @property
  def typ(self): return self.val.typ

class PrefixOperatorValue(UnaryOperatorValue): pass
class SuffixOperatorValue(UnaryOperatorValue): pass

class AST(Node):
  def __init__(self, nodes):
    self.nodes = nodes
    self.failures = []

  def __iter__(self):
    return self.nodes.__iter__()

  def __getitem__(self, key):
    return self.nodes[key]

  def __len__(self):
    return len(self.nodes)

  def build(self, args):
    self._import_paths = [
      path.dirname(args.source),
      getcwd(),
      path.dirname(args.output_import_file)]

    self.parent = None
    for n in self.nodes:
      n.build(self)
    if len(self.failures) != 0:
      raise ParseError(self.failures, self.parser)

  def fail(self, severity, pos, msg):
    self.failures.append(Failure(severity, pos, msg))

  def find_declaration(self, sym):
    for n in self.nodes:
      res = n.get_declaration(sym)
      if res is not None:
        return res

  @property
  def import_paths(self): return self._import_paths
