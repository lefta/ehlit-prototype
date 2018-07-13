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

from os import path, getcwd, listdir
from reflex.parser import c_compat, parse
from reflex.parser.error import ParseError, Failure

MOD_NONE = 0
MOD_CONST = 1

imported = []

class Node:
  def __init__(self, pos):
    self.pos = pos

  def build(self, parent):
    self.parent = parent

  def is_declaration(self):
    return False

  """
  Find a declaration when coming from downsides. Scoping structures (like functions) would want to
  search symbols in this function.

  The default is to try get_declaration on self, then to try with parent.
  """
  def find_declaration(self, sym):
    decl = self.get_declaration(sym)
    if decl is None:
      return self.parent.find_declaration(sym)
    return decl

  """
  Find a declaration when coming from upsides. Structures exposing symbols to their parent (like
  Import) would want to search symbols in this function.
  """
  def get_declaration(self, sym): return None

  """
  Find a declaration strictly in children. Container types (like structs) would want to search
  symbols in this function.
  """
  def get_inner_declaration(self, sym): return None

  """
  Scoping nodes should call this function when they get a match in their respective
  `get_declaration` to automatically handle scope access (`foo.bar`).
  """
  def declaration_match(self, sym):
    if len(sym) is 1:
      return self
    return self.get_inner_declaration(sym[1:])

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
    self.lib = Identifier(lib.pos, path.join(*[ x.name for x in lib.elems]))
    self.syms = []

  def build(self, parent):
    super().build(parent)
    try:
      self.syms = self.parse()
    except ParseError as err:
      for e in err.failures:
        self.fail(e.severity, self.pos, e.msg)

    for s in self.syms:
      s.build(self)

  def get_declaration(self, sym):
    for s in self.syms:
      decl = s.get_declaration(sym)
      if decl is not None:
        return decl

class Import(GenericExternInclusion):
  def import_dir(self, dir):
    res = []
    for sub in listdir(dir):
      full_path = path.join(dir, sub)
      if full_path in imported:
        continue
      imported.append(full_path)
      if path.isdir(full_path):
        res += self.import_dir(full_path)
      elif path.isfile(full_path):
        res += parse.parse(full_path).nodes
    return res

  def parse(self):
    for p in self.import_paths:
      full_path = path.abspath(path.join(p, self.lib.name))
      if path.isdir(full_path):
        if full_path in imported:
          return []
        imported.append(full_path)
        return self.import_dir(full_path)
      full_path += '.ref'
      if path.isfile(full_path):
        if full_path in imported:
          return []
        imported.append(full_path)
        return parse.parse(full_path).nodes
    self.error(self.pos, '%s: no such file or directory' % self.lib.name)
    return []

class Include(GenericExternInclusion):
  def parse(self): return c_compat.parse_header(self.lib.name)

class Value(Node):
  def __init__(self, pos=0):
    super().__init__(pos)
    self.ref_offset = 0
    self.cast = None

  def from_any_aligned(self, target, source, is_casting):
    target_ref_count = source.ref_offset
    res = target.typ.from_any()
    if is_casting:
      # We align the result to match the ref offset of the target
      if not target.is_declaration() and not target.is_type:
        target_ref_offset = target.ref_offset
        while target_ref_offset > 0:
          res = res.child
          target_ref_offset -= 1
    else:
      # We reduce the result to the minimal Referencing needed for the conversion.
      if type(res) is Reference:
        while type(res.child) is Reference:
          res = res.child
        if res.any_memory_offset is 0:
          res = res.child
    if target_ref_count is not 0:
      # The developper asked for some referencing
      target_ref_count -= res.ref_offset - res.any_memory_offset
      while target_ref_count > 0:
        res = Reference(res)
        target_ref_count -= 1
    return res

  def auto_cast(self, target):
    src = self.typ
    target_ref_level = 0
    self_typ = self.typ.inner_child
    target_typ = target.typ.inner_child
    if self_typ != target_typ:
      if self_typ == BuiltinType('any'):
        src = self.from_any_aligned(target, self.typ, True)
        self.cast = src
      elif target_typ == BuiltinType('any'):
        target = self.from_any_aligned(self, target.typ, False)
        parent = self.parent
        if type(parent) is Symbol:
          parent = parent.parent
        while type(parent) is Reference:
          target_ref_level += 1
          parent = parent.parent
        if target_ref_level is not 0:
          target_ref_level -= target.typ.ref_offset
    if src:
      if target.is_declaration() or target.is_type:
        target_ref_level += target.typ.ref_offset
      else:
        target_ref_level += target.typ.ref_offset - target.ref_offset
      self.ref_offset = src.ref_offset - target_ref_level

class Type(Node):
  def __init__(self, pos=0):
    super().__init__(pos)
    self.mods = MOD_NONE

  def set_modifiers(self, mods):
    self.mods = mods

  @property
  def is_const(self): return self.mods & MOD_CONST

  @property
  def is_type(self): return True

  @property
  def any_memory_offset(self): return 1

  @property
  def inner_child(self): return self

class BuiltinType(Type):
  def __init__(self, name):
    super().__init__()
    self.name = name

  @property
  def sym(self): return self

  @property
  def child(self):
    if self.name == 'str':
      ch = BuiltinType('char')
      ch.parent = self
      return ch
    return None

  @property
  def ref_offset(self): return 0

  @property
  def typ(self): return self

  def from_any(self): return self if self.name == 'str' else Reference(self)

  @property
  def any_memory_offset(self): return 0 if self.name == 'str' else 1

  def __eq__(self, rhs):
    if type(rhs) != BuiltinType:
      return False
    return self.name == rhs.name

class Array(Type):
  def __init__(self, child, length):
    super().__init__()
    self.child = child
    self.length = length

  def build(self, parent):
    super().build(parent)
    self.child.build(self)

  @property
  def typ(self): return self

  @property
  def ref_offset(self): return 0

  def from_any(self): return self

  @property
  def any_memory_offset(self): return 0

class Reference(Value, Type):
  def __init__(self, child):
    self.child = child
    super().__init__()

  def build(self, parent):
    super().build(parent)
    self.child.build(self)
    if not self.child.is_type:
      self.child.ref_offset -= 1

  @property
  def is_type(self): return self.child.is_type

  @property
  def decl(self): return self.child.decl

  @property
  def ref_offset(self):
    if self.child.is_type:
      return self.child.ref_offset + 1
    return self.child.ref_offset

  @ref_offset.setter
  def ref_offset(self, val):
    if not self.is_type:
      self.child.ref_offset = val

  @property
  def typ(self): return self if self.is_type else self.decl.typ

  @property
  def inner_child(self): return self.child.inner_child

  @property
  def name(self): return self.child.name

  def auto_cast(self, target): return self.child.auto_cast(target)
  def from_any(self): return self

  @property
  def any_memory_offset(self): return self.child.any_memory_offset

class FunctionType(Type):
  def __init__(self, ret, args):
    super().__init__()
    self.ret = ret
    self.args = args

  def build(self, parent):
    super().build(parent)
    self.ret.build(self)
    i = 0
    while i < len(self.args):
      self.args[i].build(self)
      i += 1

  @property
  def ref_offset(self): return self.ret.ref_offset

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
    self.name = sym.name if sym is not None else None
    self.sym = sym
    self.assign = None

  def build(self, parent):
    super().build(parent)
    self.typ.build(self)
    if self.sym is not None:
      self.sym.build(self)

  def get_declaration(self, sym):
    if self.name == sym[0]:
      return self.declaration_match(sym)
    return None

  def get_inner_declaration(self, sym):
    return None if self.typ.decl is None else self.typ.decl.get_inner_declaration(sym)

  def is_declaration(self):
    return True

  @property
  def is_type(self): return False

  @property
  def args(self): return self.typ.args if type(self.typ) is FunctionType else None

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

  @property
  def typ(self): return self.decl.typ

  @property
  def sym(self): return self.decl.sym

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
    if self.sym.name == sym[0]:
      return self.declaration_match(sym)
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
  def __init__(self, proto, body_str):
    self.proto = proto
    self.name = proto.sym.name
    self.typ = proto.typ
    self.body = []
    self.body_str = body_str

  def build(self, parent):
    from reflex.parser.parse import parse_function
    super().build(parent)
    self.proto.build(self)
    try:
      typ = self.typ
      if (type(typ) is Symbol):
        typ = typ.decl
      have_return_value = not ((type(typ) is Alias and typ.src == BuiltinType('void')) or
        typ == BuiltinType('void'))
      self.body = parse_function(self.body_str.contents, have_return_value)
      for s in self.body:
        s.build(self)
    except ParseError as err:
      for f in err.failures:
        self.fail(f.severity, f.pos + self.body_str.pos, f.msg)

  def get_declaration(self, sym):
    decl = self.proto.get_declaration(sym)
    if decl is not None:
      return decl

    for s in self.body:
      decl = s.get_declaration(sym)
      if decl is not None:
        return decl

  def is_declaration(self): return True

  def fail(self, severity, pos, msg): super().fail(severity, pos + self.body_str.pos, msg)

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
    if not self.is_cast:
      self.ref_offset = 0

    if self.is_cast:
      if len(self.args) < 1:
        self.error(self.pos, 'cast requires a value')
      elif len(self.args) > 1:
        self.error(self.pos, 'too many values for cast expression')
    elif self.sym.decl is not None:
      diff = len(self.args) - len(self.sym.decl.args)
      i = 0
      while i < len(self.sym.decl.args):
        if i >= len(self.args):
          if self.sym.decl.args[i].assign is not None:
            self.args.append(self.sym.decl.args[i].assign.expr)
            diff += 1
          else:
            break
        i += 1
      if diff < 0 or (diff > 0 and not self.sym.decl.is_variadic):
        self.warn(self.pos, '{} arguments for call to {}: expected {}, got {}'.format(
          'not enough' if diff < 0 else 'too many', self.sym.name, len(self.sym.decl.args),
          len(self.args)))

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

  @property
  def decl(self): return self.sym if self.is_cast else self.sym.decl

  @property
  def is_type(self): return False

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
  def typ(self): return self.child.typ.child

  @property
  def is_type(self): return False

  @property
  def decl(self): return self.child.decl

  def from_any(self): return self.child.typ.from_any()

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
  def __init__(self, expr=None):
    self.expr = expr

  def build(self, parent):
    super().build(parent)
    if self.expr is not None:
      self.expr.build(self)
      decl = self.parent
      while type(decl) is not FunctionDefinition:
        decl = decl.parent
      self.expr.auto_cast(decl)


class Identifier(Value, Type):
  def __init__(self, pos, name):
    super().__init__(pos)
    self.name = name
    self.decl = None

  def build(self, parent):
    super().build(parent)
    if not parent.is_declaration():
      # Only declarations use an identifier directly, all other node types shall use Symbol
      self.decl = parent.find_declaration(self)
      if self.decl is None:
        self.error(self.pos, "use of undeclared identifier %s" % self.name)
      else:
        self.ref_offset = self.decl.typ.ref_offset

  @property
  def is_type(self): return False if self.decl is None else self.decl.is_type

  @property
  def typ(self): return self.decl.typ if self.decl is not None else BuiltinType('any')

  def from_any(self): return self.decl.from_any() if self.decl is not None else self

class Symbol(Value, Type):
  def __init__(self, elems):
    self.elems = elems
    super().__init__()

  def build(self, parent):
    super().build(parent)
    for e in self.elems:
      e.build(self)

  @property
  def ref_offset(self): return self.elems[-1].ref_offset

  @ref_offset.setter
  def ref_offset(self, v): self.elems[-1].ref_offset = v

  @property
  def typ(self): return self.elems[-1].typ

  @property
  def is_type(self): return self.elems[-1].is_type

  @property
  def decl(self): return self.elems[-1].decl

  @property
  def name(self): return self.elems[-1].name

  @property
  def cast(self): return self.elems[-1].cast

  @cast.setter
  def cast(self, value): self.elems[-1].cast = value

  def auto_cast(self, tgt): return self.elems[-1].auto_cast(tgt)
  def from_any(self): return self.elems[-1].from_any()

  def find_declaration(self, identifier):
    i = 0
    while i < len(self.elems):
      if identifier is self.elems[i]:
        return self.parent.find_declaration([x.name for x in self.elems[:i+1]])
      i += 1
    return None

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

class BoolValue(Value):
  def __init__(self, val):
    super().__init__()
    self.val = val

  @property
  def typ(self): return BuiltinType('bool')

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

  @property
  def decl(self): return self.val.decl

  def auto_cast(self, tgt): return self.val.auto_cast(tgt)

class PrefixOperatorValue(UnaryOperatorValue): pass
class SuffixOperatorValue(UnaryOperatorValue): pass

class Sizeof(Value):
  def __init__(self, sz_typ):
    super().__init__()
    self.sz_typ = sz_typ

  def build(self, parent):
    super().build(parent)
    self.sz_typ.build(self)

  @property
  def typ(self): return BuiltinType('size')

class Alias(Node):
  def __init__(self, src, dst):
    self.src = src
    self.dst = dst

  def build(self, parent):
    super().build(parent)
    self.src.build(self)

  def get_declaration(self, sym):
    if self.dst.name == sym[0]:
      if type(self.src) is BuiltinType:
        return self.declaration_match(sym)
      if self.src.decl is not None:
        return self.src.decl.declaration_match(sym)
    return None

  @property
  def typ(self): return self.src.typ

  @property
  def name(self): return self.dst.name

  @property
  def is_type(self): return self.dst.is_type

  @property
  def ref_offset(self): return self.dst.ref_offset

  @ref_offset.setter
  def ref_offset(self, offset): self.dst.ref_offset = offset

  @property
  def inner_child(self): return self.dst

class Struct(Node):
  def __init__(self, pos, sym, fields):
    super().__init__(pos)
    self.sym = sym
    self.fields = fields

  def build(self, parent):
    super().build(parent)
    self.sym.build(self)
    for f in self.fields:
      f.build(self)
      if f.assign is not None:
        self.error(self.pos, "struct fields may not have a value yet")

  def is_declaration(self): return True

  def get_declaration(self, sym):
    if self.sym.name == sym[0]:
      return self.declaration_match(sym)
    return None

  @property
  def typ(self): return self

  @property
  def ref_offset(self): return 0

  @property
  def is_type(self): return True

  @property
  def name(self): return self.sym.name

  def get_inner_declaration(self, sym):
    for f in self.fields:
      decl = f.get_declaration(sym)
      if decl is not None:
        return decl.declaration_match(sym)
    return None

  def from_any(self):
    res = Reference(Symbol([Identifier(0, self.sym.name)]))
    res.build(self)  # Needs to be built to get the declaration
    return res

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
    self.failures.append(Failure(severity, pos, msg, self.parser.file_name))

  def find_declaration(self, sym):
    for n in self.nodes:
      res = n.get_declaration(sym)
      if res is not None:
        return res
    return None

  @property
  def import_paths(self): return self._import_paths
