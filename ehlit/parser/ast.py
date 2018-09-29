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

from abc import abstractmethod
from os import path, getcwd, listdir
from typing import Any, List, Optional, Tuple, Union
import ehlit.parser.parse
from ehlit.parser.error import ParseError, Failure

DeclarationLookup = Tuple[Optional['DeclarationBase'], Optional[str]]

MOD_NONE = 0
MOD_CONST = 1

imported: List[str] = []

class UnparsedContents:
  '''!
  Contents for which parsing have been delayed, for example because of a lack of context.
  '''
  def __init__(self, contents: str, pos: int) -> None:
    '''! Constructor
    @param contents @b str Contents to be parsed later.
    @param pos @b int Position of the contents in the file.
    '''
    self.contents: str = contents
    self.pos: int = pos

class Node:
  '''!
  Base class for all AST node types. It defines some default behaviors.
  '''
  def __init__(self, pos: int) -> None:
    '''! Constructor
    @param pos @b int The position of the node in the source file
    '''
    ## @b int Position of the node in the source file.
    self.pos: int = pos
    ## @b bool Whether this node have already been built or not.
    self.built: bool = False

  def build(self, parent: 'Node') -> None:
    '''! Build a node.
    Depending on the node type, this may mean resolving symbol references, making sanity checks
    and / or building children.
    @param parent @b Node The parent node of this node.
    '''
    ## @b Node The parent node of this node.
    self.parent: Node = parent
    self.built = True

  def is_declaration(self) -> bool:
    '''! Checks whether a node is a symbol declaration or not.
    By default, this value is False.
    @return @b bool
    '''
    return False

  def find_declaration(self, sym: List[str]) -> DeclarationLookup:
    '''! Find a declaration when coming from downsides.
    Scoping structures (like functions) would want to search symbols in this function. The default
    is to try get_declaration on self, then to try with parent.
    @param sym @b List[str] The symbol to find.
    @return @b Declaration|FunctionDeclaration The declaration if found, None otherwise.
    '''
    return self.parent.find_declaration(sym)

  def get_declaration(self, sym: List[str]) -> DeclarationLookup:
    '''! Find a declaration when coming from upsides.
    Structures exposing symbols to their parent (like Import) would want to search symbols in this
    function.
    @param sym @b List[str] The symbol to find
    @return @b Declaration|FunctionDeclaration The declaration if found, None otherwise.
    '''
    return None, None

  def fail(self, severity: int, pos: int, msg: str) -> None:
    '''! Report a failure to the parent, up to the AST where it will be handled.
    There is no reason to override it, except maybe intercepting it for whatever reason.
    @param severity @b ParseError.Severity Severity of the failure
    @param pos @b int The position in code where the failure happened
    @param msg @b str The failure message to display
    '''
    self.parent.fail(severity, pos, msg)

  def error(self, pos: int, msg: str) -> None:
    '''! Shorthand for fail with severity Error.
    @param pos @b int The position in code where the failure happened
    @param msg @b str The failure message to display
    '''
    self.fail(ParseError.Severity.Error, pos, msg)

  def warn(self, pos: int, msg: str) -> None:
    '''! Shorthand for fail with severity Warning.
    @param pos @b int The position in code where the failure happened
    @param msg @b str The failure message to display
    '''
    self.fail(ParseError.Severity.Warning, pos, msg)

  def declare(self, decl: 'DeclarationBase') -> None:
    '''! Declare a symbol.
    By default, this is only propagated to the parent. @c Scope override it to remember it.
    @param decl @b DeclarationBase The declaration to be declared.
    '''
    self.parent.declare(decl)

  @property
  def import_paths(self) -> List[str]:
    '''! @c property @b List[str] The list of paths to be looked up when importing a module. '''
    return self.parent.import_paths

  def is_child_of(self, cls: Any) -> bool:
    '''! Check if this node is a descendant of some node type
    @param cls @b Class The class to check for
    '''
    return type(self) is cls or self.parent.is_child_of(cls)

class Scope(Node):
  def __init__(self, pos: int) -> None:
    super().__init__(pos)
    self.declarations: List[DeclarationBase] = []
    self.predeclarations: List[DeclarationBase] = []

  def declare(self, decl: 'DeclarationBase') -> None:
    self.declarations.append(decl)

  def find_declaration(self, sym: List[str]) -> DeclarationLookup:
    for decl in self.declarations:
      res, err = decl.get_declaration(sym)
      if res is not None or err is not None:
        return res, err
    res, err = super().find_declaration(sym)
    if res is not None and not res.built:
      self.predeclarations.append(res)
    return res, err

class UnorderedScope(Scope):
  def find_declaration(self, sym: List[str]) -> DeclarationLookup:
    for node in self.scope_contents:
      res, err = node.get_declaration(sym)
      if res is not None or err is not None:
        return res, err
    return super().find_declaration(sym)

  @property
  @abstractmethod
  def scope_contents(self) -> List[Node]:
    raise NotImplementedError

class GenericExternInclusion(UnorderedScope):
  '''! Base for include and import defining shared behaviors '''
  def __init__(self, pos: int, lib: List[str]) -> None:
    '''! Constructor
    @param pos @b int The position of the node in the source file
    @param lib @b List[str] Path of the file to be imported
    '''
    super().__init__(pos)
    ## @b str The library that will be imported
    self.lib: str = path.join(*lib)
    ## @b List[Node] The symbols that have been imported from the library
    self.syms: List[Node] = []

  def build(self, parent: Node) -> None:
    '''! Build the node, this actually imports the file
    @param parent @b Node The parent of this node
    '''
    super().build(parent)
    try:
      self.syms = self.parse()
    except ParseError as err:
      for e in err.failures:
        self.fail(e.severity, self.pos, e.msg)

    for s in self.syms:
      s.build(self)

  @abstractmethod
  def parse(self) -> List[Node]:
    '''! Parse the imported file
    @return @b List[Node] A list of the imported nodes
    '''
    raise NotImplementedError

  def get_declaration(self, sym: List[str]) -> DeclarationLookup:
    '''! Look for a declaration from the imported file
    @param sym @b List[str] The symbol to look for
    @return @b Declaration|FunctionDeclaration The declaration if found, @c None otherwise
    '''
    for decl in self.syms:
      res, err = decl.get_declaration(sym)
      if res is not None or err is not None:
        return res, err
    return None, None

  @property
  def scope_contents(self) -> List[Node]:
    return self.syms

class Import(GenericExternInclusion):
  '''! Specialization of GenericExternInclusion for Ehlit imports. '''
  def import_dir(self, dir: str) -> List[Node]:
    '''! Import a whole directory.
    This recursively imports all Ehlit files in the specified directory.
    @param dir @b str The directory to import.
    @return @b List[Node] A list of the imported nodes.
    '''
    res: List[Node] = []
    for sub in listdir(dir):
      full_path: str = path.join(dir, sub)
      if full_path in imported:
        continue
      imported.append(full_path)
      if path.isdir(full_path):
        res += self.import_dir(full_path)
      elif path.isfile(full_path):
        res += ehlit.parser.parse(full_path).nodes
    return res

  def parse(self) -> List[Node]:
    '''! Parse the imported file or directory contents.
    @return @b List[Node] A list of the imported nodes.
    '''
    for p in self.import_paths:
      full_path: str = path.abspath(path.join(p, self.lib))
      if path.isdir(full_path):
        if full_path in imported:
          return []
        imported.append(full_path)
        return self.import_dir(full_path)
      full_path += '.eh'
      if path.isfile(full_path):
        if full_path in imported:
          return []
        imported.append(full_path)
        return ehlit.parser.parse(full_path).nodes
    self.error(self.pos, '%s: no such file or directory' % self.lib)
    return []

class Include(GenericExternInclusion):
  '''! Specialization of GenericExternInclusion for C includes. '''
  def parse(self) -> List[Node]:
    '''! Parse the included file.
    @return @b List[Node] A list of the imported nodes.
    '''
    from ehlit.parser import c_compat
    return c_compat.parse_header(self.lib)

class Value(Node):
  '''! Base for all nodes representing a value. '''
  def __init__(self, pos: int =0) -> None:
    '''! Constructor
    @param pos @b int The position of the node in the source file
    '''
    super().__init__(pos)
    ## @b int Referencing offset to be applied when writing this value.
    self._ref_offset: int = 0
    ## @b Type Cast to apply to this value when writing it, if relevant.
    self._cast: Optional['Type'] = None

  @property
  def ref_offset(self) -> int:
    return self._ref_offset

  @ref_offset.setter
  def ref_offset(self, v: int) -> None:
    self._ref_offset = v

  @property
  def cast(self) -> Optional['Type']:
    return self._cast

  @cast.setter
  def cast(self, v: Optional['Type']) -> None:
    self._cast = v

  @property
  @abstractmethod
  def typ(self) -> 'Type':
    raise NotImplementedError

  def _from_any_aligned(target: Node, source: 'Type', is_casting: bool) -> 'Type':
    '''! Compute the conversion needed to transform an any into target.
    This function computes the referencing offset and / or the cast to make an @b any, or a
    container of @b any, binary compatible with target. It also takes into account the will of the
    developper if he wants more references than the minimum required.
    @param target @b Node The target of the conversion, with which source will be made compatible.
    @param source @b Type The source type that should be converted. It shall be either an @c any, or
      any container of it.
    @param is_casting @b bool Whether we are already in a casting context or not.
    @return @b Type The cast needed for a successful conversion.
    '''
    target_ref_count: int = source.ref_offset
    res: 'Type' = target.typ.from_any()
    if is_casting:
      # We align the result to match the ref offset of the target
      if not target.is_type:
        target_ref_offset: int = target.ref_offset
        while target_ref_offset > 0:
          assert isinstance(res, Reference), "Attempt to dereference a non Reference"
          tmp = res.child
          res = tmp if isinstance(tmp, Type) else tmp.typ
          target_ref_offset -= 1
    else:
      # We reduce the result to the minimal Referencing needed for the conversion.
      if isinstance(res, Reference):
        while isinstance(res.child, Reference):
          tmp = res.child
          res = tmp if isinstance(tmp, Type) else tmp.typ
        if res.any_memory_offset is 0:
          tmp = res.child
          res = tmp if isinstance(tmp, Type) else tmp.typ
    if target_ref_count is not 0:
      # The developper asked for some referencing
      target_ref_count -= res.ref_offset - res.any_memory_offset
      while target_ref_count > 0:
        res = Reference(res)
        target_ref_count -= 1
    return res

  def auto_cast(self, target: 'Type') -> None:
    '''! Make this value binary compatible with target.
    @param target @b Node The node that this value shall be made compatible with.
    '''
    src: 'Type' = self.typ
    target_ref_level: int = 0
    self_typ: 'Type' = self.typ
    if isinstance(self_typ, Reference):
      self_typ = self_typ.inner_child
    if isinstance(self_typ, Symbol):
      self_typ = self_typ.typ
    target_typ: 'Type' = target
    if isinstance(target_typ, Reference):
      target_typ = target_typ.inner_child
    if isinstance(target_typ, Symbol):
      target_typ = target_typ.typ
    if self_typ != target_typ:
      if self_typ == BuiltinType('any'):
        src = Value._from_any_aligned(target, self.typ, True)
        self.cast = src
      elif target_typ == BuiltinType('any'):
        target = Value._from_any_aligned(self, target, False)
        parent = self.parent
        if type(parent) is CompoundIdentifier:
          parent = parent.parent
        while type(parent) is Reference:
          target_ref_level += 1
          parent = parent.parent
        if target_ref_level is not 0:
          target_ref_level -= target.ref_offset
    if src:
      if target.is_type:
        target_ref_level += target.ref_offset
      else:
        target_ref_level += target.typ.ref_offset - target.ref_offset
      self.ref_offset = src.ref_offset - target_ref_level

class DeclarationBase(Node):
  def build(self, parent: Node) -> None:
    super().build(parent)
    parent.declare(self)

  def get_declaration(self, sym: List[str]) -> DeclarationLookup:
    if self.name == sym[0]:
      return self.declaration_match(sym)
    return None, None

  def declaration_match(self, sym: List[str]) -> DeclarationLookup:
    '''! Scoping nodes should call this function when they get a match in their respective
    `find_declaration` to automatically handle scope access (`foo.bar`).
    @param sym @b List[str] The symbol looked for.
    @return @b Declaration|FunctionDeclaration The deepest declaration if found, None otherwise.
    '''
    if len(sym) is 1:
      return self, None
    return self.get_inner_declaration(sym[1:])

  def get_inner_declaration(self, sym: List[str]) -> DeclarationLookup:
    '''! Find a declaration strictly in children.
    Container types (like structs) would want to search symbols in this function.
    @param sym @b List[str] The symbol to find.
    @return @b Declaration|FunctionDeclaration The inner declaration if found, None otherwise.
    '''
    return None, None

  def is_declaration(self) -> bool:
    return True

  @property
  @abstractmethod
  def name(self) -> str:
    raise NotImplementedError

class Type(Node):
  def __init__(self, pos: int =0) -> None:
    super().__init__(pos)
    self.mods: int = MOD_NONE

  def set_modifiers(self, mods: int) -> None:
    self.mods = mods

  @property
  def is_const(self) -> bool:
    return self.mods & MOD_CONST is not 0

  @property
  def is_type(self) -> bool:
    return True

  @property
  def any_memory_offset(self) -> int:
    return 1

  @property
  def ref_offset(self) -> int:
    return 0

class Symbol(Value, Type):
  def solve(self) -> Optional[DeclarationBase]:
    decl = self.decl
    while decl is not None and isinstance(decl, Symbol):
      decl = decl.decl
    return decl

  @property
  @abstractmethod
  def decl(self) -> Optional[DeclarationBase]:
    raise NotImplementedError

  @property
  @abstractmethod
  def repr(self) -> str:
    raise NotImplementedError

class BuiltinType(Type, DeclarationBase):
  def make(parent: Node, name: str) -> 'CompoundIdentifier':
    res = CompoundIdentifier([Identifier(parent.pos, name)])
    res.build(parent)
    return res

  def __init__(self, name: str) -> None:
    super().__init__()
    self._name: str = name

  @property
  def sym(self) -> Node:
    return self

  @property
  def child(self) -> Optional[Type]:
    if self.name == 'str':
      return BuiltinType.make(self, 'char')
    return None

  @property
  def typ(self) -> Type:
    return self

  @property
  def decl(self) -> Optional['DeclarationBase']:
    return self

  def from_any(self) -> Type:
    if self.name == 'str':
      return BuiltinType.make(self, 'str')
    return Reference(BuiltinType.make(self, self.name))

  @property
  def any_memory_offset(self) -> int:
    return 0 if self.name == 'str' else 1

  @property
  def name(self) -> str:
    return self._name

  def __eq__(self, rhs: object) -> bool:
    if isinstance(rhs, Symbol):
      rhs = rhs.decl
    if isinstance(rhs, BuiltinType):
      return self.name == rhs.name
    return False

class Array(Type, DeclarationBase):
  def __init__(self, child: Optional[Type], length: Optional[Node]) -> None:
    super().__init__()
    self.child: Optional[Type] = child
    self.length: Optional[Node] = length

  def build(self, parent: Node) -> None:
    assert self.child is not None
    super().build(parent)
    self.child.build(self)

  @property
  def typ(self) -> Type:
    return self

  def from_any(self) -> Type:
    return self

  @property
  def any_memory_offset(self) -> int:
    return 0

  def solve(self) -> Type:
    return self

  @property
  def name(self) -> str:
    return '@array'

class Reference(Value, Type):
  def __init__(self, child: Union[Value, Type]) -> None:
    self.child: Union[Value, Type] = child
    super().__init__()

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.child.build(self)
    if not isinstance(self.child, Type) or not self.child.is_type:
      assert isinstance(self.child, Value)
      self.child.ref_offset -= 1

  @property
  def is_type(self) -> bool:
    return isinstance(self.child, Type) and self.child.is_type

  @property
  def decl(self) -> Optional['DeclarationBase']:
    assert isinstance(self.child, Value)
    return self.child.decl

  @property
  def ref_offset(self) -> int:
    if isinstance(self.child, Type) and self.child.is_type:
      return self.child.ref_offset + 1
    return self.child.ref_offset

  @ref_offset.setter
  def ref_offset(self, val: int) -> None:
    if not self.is_type:
      assert isinstance(self.child, Value)
      self.child.ref_offset = val

  @property
  def typ(self) -> Type:
    if self.is_type:
      return self
    if self.decl is not None:
      assert isinstance(self.decl, Declaration)
      return self.decl.typ
    return BuiltinType.make(self, 'any')

  @property
  def inner_child(self) -> Type:
    if isinstance(self.child, Reference):
      return self.child.inner_child
    assert isinstance(self.child, Type)
    return self.child

  def auto_cast(self, target: Type) -> None:
    assert isinstance(self.child, Value)
    self.child.auto_cast(target)

  def from_any(self) -> Type:
    return self

  @property
  def any_memory_offset(self) -> int:
    assert isinstance(self.child, Type)
    return self.child.any_memory_offset

class FunctionType(Type, DeclarationBase):
  def __init__(self, ret: Symbol, args: List['VariableDeclaration'],
               is_variadic: bool =False) -> None:
    super().__init__()
    self.args: List['VariableDeclaration'] = args
    self.ret: Symbol = ret
    self.is_variadic: bool = is_variadic

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.ret.build(self)
    i: int = 0
    while i < len(self.args):
      self.args[i].build(self)
      i += 1

  @property
  def typ(self) -> Type:
    return self

  @property
  def name(self) -> str:
    return '@func'

class Operator(Node):
  def __init__(self, op: str) -> None:
    self.op: str = op

  def auto_cast(self, target: Type) -> None:
    pass

class VariableAssignment(Node):
  def __init__(self, var: Symbol, assign: 'Assignment') -> None:
    self.var: Symbol = var
    self.assign: 'Assignment' = assign

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.var.build(self)
    self.assign.build(self)
    self.assign.expr.auto_cast(self.var)

class Assignment(Node):
  def __init__(self, expr: 'Expression') -> None:
    self.expr: 'Expression' = expr
    self.operator: Optional[str] = None

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.expr.build(self)

class Declaration(DeclarationBase):
  def __init__(self, typ: Type, sym: Optional['Identifier']) -> None:
    super().__init__(0)
    self._typ: Type = typ
    self.typ_src: Type = typ
    self.sym: Optional['Identifier'] = sym

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.typ_src.build(self)
    self._typ = self.typ_src.solve() if isinstance(self.typ_src, Symbol) else self.typ_src
    if self.sym is not None:
      self.sym.build(self)

  def get_inner_declaration(self, sym: List[str]) -> DeclarationLookup:
    return (None, None) if self.typ.decl is None else self.typ.decl.get_inner_declaration(sym)

  @property
  def is_type(self) -> bool:
    return False

  @property
  def name(self) -> str:
    return self.sym.name if self.sym is not None else ''

  @property
  def typ(self) -> Type:
    if not self.built:
      self._typ = self.typ_src.solve() if isinstance(self.typ_src, Symbol) else self.typ_src
    return self._typ

class VariableDeclaration(Declaration):
  def __init__(self, typ: Type, sym: 'Identifier', assign: Optional[Assignment] =None) -> None:
    super().__init__(typ, sym)
    self.assign: Optional[Assignment] = assign

  def build(self, parent: Node) -> None:
    super().build(parent)
    if self.assign is not None:
      self.assign.build(self)
      self.assign.expr.auto_cast(self.typ)

class FunctionDeclaration(Declaration):
  pass

class FunctionDefinition(FunctionDeclaration, Scope):
  def __init__(self, typ: FunctionType, sym: 'Identifier', body_str: UnparsedContents) -> None:
    super().__init__(typ, sym)
    self.body: List[Statement] = []
    self.body_str: UnparsedContents = body_str

  def build(self, parent: Node) -> None:
    from ehlit.parser.parse import parse_function
    super().build(parent)
    if self.is_child_of(Import):
      return
    try:
      assert isinstance(self.typ, FunctionType)
      typ: Type = self.typ.ret
      if isinstance(typ, Symbol):
        typ = typ.solve()
      self.body = parse_function(self.body_str.contents, not typ == BuiltinType('void'))
      for s in self.body:
        s.build(self)
    except ParseError as err:
      for f in err.failures:
        self.fail(f.severity, f.pos + self.body_str.pos, f.msg)

  def fail(self, severity: int, pos: int, msg: str) -> None:
    super().fail(severity, pos + self.body_str.pos, msg)

class Statement(Node):
  def __init__(self, expr: Node) -> None:
    self.expr: Node = expr

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.expr.build(self)

class Expression(Node):
  def __init__(self, contents: List[Value], parenthesised: bool) -> None:
    self.contents: List[Value] = contents
    self.parenthesised: bool = parenthesised

  def build(self, parent: Node) -> None:
    super().build(parent)
    for e in self.contents:
      e.build(self)

  def auto_cast(self, target: Type) -> None:
    for e in self.contents:
      e.auto_cast(target)

  @property
  def is_parenthesised(self) -> bool:
    return self.parenthesised

class FunctionCall(Value):
  def __init__(self, pos: int, sym: Symbol, args: List[Expression]) -> None:
    super().__init__(pos)
    self.sym: Symbol = sym
    self.args: List[Expression] = args

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.sym.build(self)
    if not self.is_cast:
      # Avoid symbol to write ref offsets, this will conflict with ours.
      self.sym.ref_offset = 0
    for a in self.args:
      a.build(self)

    if self.is_cast:
      if len(self.args) < 1:
        self.error(self.pos, 'cast requires a value')
      elif len(self.args) > 1:
        self.error(self.pos, 'too many values for cast expression')
    elif self.sym.decl is not None:
      typ = self.sym.decl.typ
      if not isinstance(typ, FunctionType):
        self.error(self.pos, "calling non function type {}".format(self.sym.repr))
        return
      diff = len(self.args) - len(typ.args)
      i = 0
      while i < len(typ.args):
        if i >= len(self.args):
          assign: Optional[Assignment] = typ.args[i].assign
          if assign is not None:
            self.args.append(assign.expr)
            diff += 1
          else:
            break
        i += 1
      if diff < 0 or (diff > 0 and not typ.is_variadic):
        self.warn(self.pos, '{} arguments for call to {}: expected {}, got {}'.format(
          'not enough' if diff < 0 else 'too many', self.sym.repr, len(typ.args),
          len(self.args)))
      i = 0
      while i < len(self.args) and i < len(typ.args):
        self.args[i].auto_cast(typ.args[i].typ)
        i += 1

  @property
  def is_cast(self) -> bool:
    return self.sym.is_type

  @property
  def typ(self) -> Type:
    if self.is_cast:
      return self.sym
    if self.sym.decl is None:
      return BuiltinType.make(self, 'any')
    assert isinstance(self.sym.decl, Declaration)
    if not isinstance(self.sym.decl.typ, FunctionType):
      return self.sym.decl.typ
    return self.sym.decl.typ.ret

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.sym if self.is_cast else self.sym.decl

  @property
  def is_type(self) -> bool:
    return False

  def auto_cast(self, target: Type) -> None:
    if not self.is_cast:
      super().auto_cast(target)

class ArrayAccess(Value):
  def __init__(self, child: Optional[Node], idx: Expression) -> None:
    super().__init__()
    self.child: Optional[Node] = child
    self.idx: Expression = idx

  def build(self, parent: Node) -> None:
    assert self.child is not None
    super().build(parent)
    self.child.build(self)
    self.idx.build(self)

  @property
  def typ(self) -> Type:
    assert self.child is not None
    return self.child.typ.child

  @property
  def is_type(self) -> bool:
    return False

  @property
  def decl(self) -> Optional[DeclarationBase]:
    assert self.child is not None
    return self.child.decl

  def from_any(self) -> Type:
    assert self.child is not None
    return self.child.typ.from_any()

class ControlStructure(Scope):
  def __init__(self, name: str, cond: Optional[Expression], body: List[Statement]) -> None:
    super().__init__(0)
    assert cond is not None or name == 'else'
    self.name: str = name
    self.cond: Optional[Expression] = cond
    self.body: List[Statement] = body

  def build(self, parent: Node) -> None:
    super().build(parent)
    if self.cond is not None:
      self.cond.build(self)
    for s in self.body:
      s.build(self)

class Condition(Scope):
  def __init__(self, branches: List[ControlStructure]) -> None:
    super().__init__(0)
    self.branches: List[ControlStructure] = branches

  def build(self, parent: Node) -> None:
    super().build(parent)
    for b in self.branches:
      b.build(self)

class SwitchCase(Node):
  def __init__(self, cases: List['SwitchCaseTest'], body: 'SwitchCaseBody') -> None:
    self.cases: List['SwitchCaseTest'] = cases
    self.body: 'SwitchCaseBody' = body

class SwitchCaseTest(Node):
  def __init__(self, test: Optional[Value]) -> None:
    self.test: Optional[Value] = test

  def build(self, parent: Node) -> None:
    super().build(parent)
    if self.test is not None:
      self.test.build(self)

class SwitchCaseBody(Scope):
  def __init__(self, contents: List[Statement], block: bool, fallthrough: bool) -> None:
    super().__init__(0)
    self.contents: List[Statement] = contents
    self.block: bool = block
    self.fallthrough: bool = fallthrough

  def build(self, parent: Node) -> None:
    super().build(parent)
    for i in self.contents:
      i.build(self)

class Return(Node):
  def __init__(self, expr: Optional[Expression] =None) -> None:
    self.expr: Optional[Expression] = expr

  def build(self, parent: Node) -> None:
    super().build(parent)
    if self.expr is not None:
      self.expr.build(self)
      decl: Node = self.parent
      while type(decl) is not FunctionDefinition:
        decl = decl.parent
      self.expr.auto_cast(decl.typ.ret)

class Identifier(Value):
  def __init__(self, pos: int, name: str) -> None:
    super().__init__(pos)
    self.name: str = name
    self.decl: Optional[DeclarationBase] = None

  def build(self, parent: Node) -> None:
    super().build(parent)
    if not parent.is_declaration():
      # Only declarations may use an Identifier directly, all other node types must use
      # CompoundIdentifier
      assert isinstance(parent, CompoundIdentifier), (
        'Only declarations may use an identifier directly')
      self.decl, err = parent.find_declaration_for(self)
      if self.decl is None:
        if err is None:
          err = "use of undeclared identifier {}".format(self.name)
        self.error(self.pos, err)
      else:
        self.ref_offset = self.decl.typ.ref_offset

  @property
  def is_type(self) -> bool:
    return False if self.decl is None else self.decl.is_type

  @property
  def typ(self) -> Type:
    return self.decl.typ if self.decl is not None else BuiltinType.make(self, 'any')

  def from_any(self) -> Type:
    return self.decl.from_any() if self.decl is not None else self

class CompoundIdentifier(Symbol):
  def __init__(self, elems: List[Identifier]) -> None:
    self.elems: List[Identifier] = elems
    super().__init__()

  def build(self, parent: Node) -> None:
    super().build(parent)
    for e in self.elems:
      e.build(self)

  @property
  def ref_offset(self) -> int:
    return self.elems[-1].ref_offset

  @ref_offset.setter
  def ref_offset(self, v: int) -> None:
    self.elems[-1].ref_offset = v

  @property
  def typ(self) -> Type:
    return self.elems[-1].typ

  @property
  def is_type(self) -> bool:
    return self.elems[-1].is_type

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.elems[-1].decl

  @property
  def repr(self) -> str:
    return '.'.join([x.name for x in self.elems])

  @property
  def cast(self) -> Union[Type, None]:
    return self.elems[-1].cast

  @cast.setter
  def cast(self, value: Type) -> None:
    self.elems[-1].cast = value

  def auto_cast(self, target: Type) -> None:
    return self.elems[-1].auto_cast(target)

  def from_any(self) -> Type:
    return self.elems[-1].from_any()

  @property
  def any_memory_offset(self) -> int:
    return self.elems[-1].typ.any_memory_offset

  @property
  def child(self) -> Type:
    return self.typ.child

  def find_declaration_for(self, identifier: Identifier) -> DeclarationLookup:
    i: int = 0
    while i < len(self.elems):
      if identifier is self.elems[i]:
        return self.parent.find_declaration([x.name for x in self.elems[:i+1]])
      i += 1
    assert False, "This code may not be reached"
    return None, None

class TemplatedIdentifier(Symbol):
  def __init__(self, name: str, types: List[Union[Symbol, Type]]) -> None:
    self.name: str = name
    self.types: List[Union[Symbol, Type]] = types
    super().__init__()

  def build(self, parent: Node) -> None:
    super().build(parent)
    for t in self.types:
      t.build(self)

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.types[0]

  @property
  def typ(self) -> Type:
    return self.types[0]

  @property
  def repr(self) -> str:
    return '{}<>'.format(self.name)

class String(Value):
  def __init__(self, string: str) -> None:
    super().__init__()
    self.string: str = string

  @property
  def typ(self) -> Type:
    return BuiltinType.make(self, 'str')

  def auto_cast(self, target: Type) -> None:
    pass

class Char(Value):
  def __init__(self, char: str) -> None:
    super().__init__()
    self.char: str = char

  @property
  def typ(self) -> Type:
    return BuiltinType.make(self, 'char')

  def auto_cast(self, target: Type) -> None:
    pass

class Number(Value):
  def __init__(self, num: str) -> None:
    super().__init__()
    self.num: str = num

  @property
  def typ(self) -> Type:
    return BuiltinType.make(self, 'int')

  def auto_cast(self, target: Type) -> None:
    pass

class NullValue(Value):
  def __init__(self) -> None:
    super().__init__()

  @property
  def typ(self) -> Type:
    return BuiltinType.make(self, 'any')

  def auto_cast(self, target: Type) -> None:
    pass

class BoolValue(Value):
  def __init__(self, val: bool) -> None:
    super().__init__()
    self.val: bool = val

  @property
  def typ(self) -> Type:
    return BuiltinType.make(self, 'bool')

  def auto_cast(self, target: Type) -> None:
    pass

class UnaryOperatorValue(Node):
  def __init__(self, op: str, val: Value) -> None:
    self.op: str = op
    self.val: Value = val

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.val.build(self)

  @property
  def typ(self) -> Type:
    return self.val.typ

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.val.decl

  def auto_cast(self, target: Type) -> None:
    return self.val.auto_cast(target)

class PrefixOperatorValue(UnaryOperatorValue):
  pass
class SuffixOperatorValue(UnaryOperatorValue):
  pass

class Sizeof(Value):
  def __init__(self, sz_typ: Type) -> None:
    super().__init__()
    self.sz_typ: Type = sz_typ

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.sz_typ.build(self)

  @property
  def typ(self) -> Type:
    return BuiltinType.make(self, 'size')

class Alias(Symbol, DeclarationBase):
  def __init__(self, src: Symbol, dst: Identifier) -> None:
    self.src: Symbol = src
    self.dst: Identifier = dst

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.src.build(self)

  @property
  def typ(self) -> Type:
    return self.src.typ

  @property
  def repr(self) -> str:
    return self.src.repr

  @property
  def name(self) -> str:
    return self.dst.name

  @property
  def is_type(self) -> bool:
    return self.src.is_type

  @property
  def ref_offset(self) -> int:
    return self.dst.ref_offset

  @ref_offset.setter
  def ref_offset(self, offset: int) -> None:
    self.dst.ref_offset = offset

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.src if self.src.is_declaration() else self.src.decl

class ContainerStructure(Type, DeclarationBase, Scope):
  def __init__(self, pos: int, sym: Identifier,
               fields: Optional[List[VariableDeclaration]]) -> None:
    super().__init__(pos)
    self.sym: Identifier = sym
    self.fields: Optional[List[VariableDeclaration]] = fields
    self.display_name = ''

  def build(self, parent: Node) -> None:
    super().build(parent)
    self.sym.build(self)
    if self.fields is not None:
      for f in self.fields:
        f.build(self)

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self

  @property
  def typ(self) -> Node:
    return self

  @property
  def is_type(self) -> bool:
    return True

  @property
  def name(self) -> str:
    return self.sym.name

  def get_inner_declaration(self, sym: List[str]) -> DeclarationLookup:
    if self.fields is None:
      return None, 'accessing incomplete {} {}'.format(self.display_name, self.sym.name)
    for f in self.fields:
      decl, err = f.get_declaration(sym)
      if decl is not None or err is not None:
        return decl, err
    return None, None

  def from_any(self) -> Type:
    res = Reference(CompoundIdentifier([Identifier(0, self.sym.name)]))
    res.build(self)  # Needs to be built to get the declaration
    return res

class Struct(ContainerStructure):
  def __init__(self, pos: int, sym: Identifier,
               fields: Optional[List[VariableDeclaration]]) -> None:
    super().__init__(pos, sym, fields)
    self.display_name = 'struct'

class EhUnion(ContainerStructure):
  def __init__(self, pos: int, sym: Identifier,
               fields: Optional[List[VariableDeclaration]]) -> None:
    super().__init__(pos, sym, fields)
    self.display_name = 'union'

class AST(UnorderedScope):
  def __init__(self, nodes: List[Node]) -> None:
    super().__init__(0)
    self.nodes: List[Node] = nodes
    self.failures: List[Failure] = []
    self.parser: Any = None

  def __iter__(self):
    return self.nodes.__iter__()

  def __getitem__(self, key):
    return self.nodes[key]

  def __len__(self):
    return len(self.nodes)

  def build(self, args) -> None:
    self.builtins: List[DeclarationBase] = [
      FunctionType(CompoundIdentifier([Identifier(0, 'any')]), []),
      BuiltinType('int'), BuiltinType('int8'), BuiltinType('int16'), BuiltinType('int32'),
      BuiltinType('int64'), BuiltinType('uint'), BuiltinType('uint8'), BuiltinType('uint16'),
      BuiltinType('uint32'), BuiltinType('uint64'), BuiltinType('void'), BuiltinType('bool'),
      BuiltinType('char'), BuiltinType('size'), BuiltinType('str'), BuiltinType('any'),
    ]
    for decl in self.builtins:
      decl.build(self)
    self._import_paths = [
      path.dirname(args.source),
      getcwd(),
      path.dirname(args.output_import_file)]

    for n in self.nodes:
      n.build(self)
    if len(self.failures) != 0:
      raise ParseError(self.failures, self.parser)

  def fail(self, severity: int, pos: int, msg: str) -> None:
    self.failures.append(Failure(severity, pos, msg, self.parser.file_name))

  @property
  def scope_contents(self) -> List[Node]:
    return self.nodes

  def find_declaration(self, sym: List[str]) -> DeclarationLookup:
    for n in self.nodes:
      res, err = n.get_declaration(sym)
      if res is not None or err is not None:
        return res, err
    for decl in self.builtins:
      res, err = decl.get_declaration(sym)
      if res is not None or err is not None:
        return res, err
    return None, None

  @property
  def import_paths(self) -> List[str]:
    return self._import_paths

  def is_child_of(self, cls) -> bool:
    return False
