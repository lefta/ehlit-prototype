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
from arpeggio import ParserPython
from os import path, getcwd, listdir
from typing import Iterator, List, Optional, Tuple, Union, cast
import typing
import ehlit.parser.parse
from ehlit.parser.error import ParseError, Failure
from ehlit.options import OptionsStruct

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

  def __init__(self, pos: int =0) -> None:
    '''! Constructor
    @param pos @b int The position of the node in the source file
    '''
    ## @b int Position of the node in the source file.
    self.pos: int = pos
    ## @b bool Whether this node have already been built or not.
    self.built: bool = False

  def build(self, parent: 'Node') -> 'Node':
    '''! Build a node.
    Depending on the node type, this may mean resolving symbol references, making sanity checks
    and / or building children.
    @param parent @b Node The parent node of this node.
    '''
    ## @b Node The parent node of this node.
    self.parent: Node = parent
    self.built = True
    return self

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

  def is_child_of(self, cls: typing.Type['Node']) -> bool:
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

  def build(self, parent: Node) -> 'GenericExternInclusion':
    '''! Build the node, this actually imports the file
    @param parent @b Node The parent of this node
    '''
    super().build(parent)
    parsed: List[Node] = []
    try:
      parsed = self.parse()
    except ParseError as err:
      for e in err.failures:
        self.fail(e.severity, self.pos, e.msg)
    for s in parsed:
      self.syms.append(s.build(self))
    return self

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
    self._cast: Optional[Symbol] = None

  def build(self, parent: Node) -> 'Value':
    super().build(parent)
    return self

  @property
  def ref_offset(self) -> int:
    return self._ref_offset

  @ref_offset.setter
  def ref_offset(self, v: int) -> None:
    self._ref_offset = v

  @property
  def cast(self) -> Optional['Symbol']:
    return self._cast

  @cast.setter
  def cast(self, v: Optional['Symbol']) -> None:
    self._cast = v

  @property
  @abstractmethod
  def typ(self) -> 'Type':
    raise NotImplementedError

  @property
  def decl(self) -> Optional['DeclarationBase']:
    return None

  def _from_any_aligned(self, target: Union['Symbol', 'Type', 'Value'],
                        source: Union['Symbol', 'Type', 'Value'], is_casting: bool) -> 'Symbol':
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
    res: Symbol = target.from_any() if isinstance(target, Type) else target.typ.from_any()
    if is_casting:
      # We align the result to match the ref offset of the target
      if not isinstance(target, Type):
        target_ref_offset: int = target.ref_offset
        while target_ref_offset > 0:
          assert isinstance(res, ReferenceToType)
          res = res.child
          target_ref_offset -= 1
    else:
      # We reduce the result to the minimal Referencing needed for the conversion.
      if isinstance(res, ReferenceToType):
        while isinstance(res.child, ReferenceToType):
          res = res.child
        if res.any_memory_offset is 0:
          res = res.child
    if target_ref_count is not 0:
      # The developper asked for some referencing
      target_ref_count -= res.ref_offset - res.typ.any_memory_offset
      while target_ref_count > 0:
        res = Reference(res).build(self)
        target_ref_count -= 1
    return res

  def auto_cast(self, target: Union['Symbol', 'Type']) -> None:
    '''! Make this value binary compatible with target.
    @param target @b Node The node that this value shall be made compatible with.
    '''
    src: 'Type' = self.typ
    target_ref_level: int = 0
    self_typ: 'Type' = self.typ
    if isinstance(self_typ, ReferenceType):
      self_typ = self_typ.inner_child
    target_typ: 'Type' = target if isinstance(target, Type) else target.typ
    if isinstance(target_typ, ReferenceType):
      target_typ = target_typ.inner_child
    if self_typ != target_typ:
      if self_typ == BuiltinType('@any'):
        self.cast = self._from_any_aligned(target, self.typ, True)
        src = self.cast.typ
      elif target_typ == BuiltinType('@any'):
        target = self._from_any_aligned(self, target, False)
        parent = self.parent
        if type(parent) is CompoundIdentifier:
          parent = parent.parent
        while type(parent) is ReferenceToValue:
          target_ref_level += 1
          parent = parent.parent
        if target_ref_level is not 0:
          target_ref_level -= target.ref_offset
    if src:
      if (isinstance(target, Symbol) and target.is_type) or isinstance(target, Type):
        target_ref_level += target.ref_offset
      else:
        target_ref_level += target.typ.ref_offset - target.ref_offset
      self.ref_offset = src.ref_offset - target_ref_level


class DeclarationBase(Node):
  def build(self, parent: Node) -> 'Node':
    super().build(parent)
    return self

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


class Type(DeclarationBase):
  def build(self, parent: Node) -> 'Type':
    super().build(parent)
    return self

  @property
  def is_type(self) -> bool:
    return True

  @property
  def any_memory_offset(self) -> int:
    return 1

  @property
  def ref_offset(self) -> int:
    return 0

  @abstractmethod
  def from_any(self) -> 'Symbol':
    raise NotImplementedError

  @abstractmethod
  def dup(self) -> 'Type':
    raise NotImplementedError


class Symbol(Value):
  def __init__(self, pos: int =0) -> None:
    super().__init__(pos)
    self.mods: int = MOD_NONE

  def build(self, parent: Node) -> 'Symbol':
    super().build(parent)
    return self

  def solve(self) -> Optional[DeclarationBase]:
    decl = self.decl
    while decl is not None and isinstance(decl, Symbol):
      decl = decl.decl
    return decl

  def set_modifiers(self, mods: int) -> None:
    self.mods = mods

  @property
  def is_const(self) -> bool:
    return self.mods & MOD_CONST is not 0

  @property
  def is_type(self) -> bool:
    return isinstance(self.decl, Type)

  @property
  @abstractmethod
  def decl(self) -> Optional[DeclarationBase]:
    raise NotImplementedError

  @property
  @abstractmethod
  def repr(self) -> str:
    raise NotImplementedError


class BuiltinType(Type):
  def make(parent: Node, name: str) -> 'CompoundIdentifier':
    res = CompoundIdentifier([Identifier(parent.pos, '@' + name)])
    res.build(parent)
    return res

  def __init__(self, name: str) -> None:
    super().__init__()
    self._name: str = name

  def build(self, parent: Node) -> 'BuiltinType':
    super().build(parent)
    return self

  @property
  def child(self) -> Optional[Type]:
    if self.name == '@str':
      return BuiltinType('@char').build(self)
    return None

  @property
  def decl(self) -> Optional['DeclarationBase']:
    return self.dup().build(self.parent)

  def from_any(self) -> Symbol:
    if self.name == '@str':
      return BuiltinType.make(self, 'str')
    return Reference(BuiltinType.make(self, self.name[1:])).build(self)

  @property
  def any_memory_offset(self) -> int:
    return 0 if self.name == '@str' else 1

  @property
  def name(self) -> str:
    return self._name

  def __eq__(self, rhs: object) -> bool:
    if isinstance(rhs, Symbol):
      rhs = rhs.decl
    if isinstance(rhs, BuiltinType):
      return self.name == rhs.name
    return False

  def dup(self) -> 'BuiltinType':
    return BuiltinType(self.name)


class Container(Node):
  def __init__(self, child: Node) -> None:
    super().__init__(0)
    self.child: Node = child

  def build(self, parent: Node) -> Node:
    super().build(parent)
    self.child = self.child.build(self)
    return self

  @property
  def inner_child(self) -> Node:
    if isinstance(self.child, Container):
      return self.child.inner_child
    return self.child


class SymbolContainer(Symbol, Container):
  def __init__(self, child: Symbol) -> None:
    self.child: Symbol
    self.inner_child: Symbol
    super().__init__()
    Container.__init__(self, child)

  def build(self, parent: Node) -> 'SymbolContainer':
    super().build(parent)
    Container.build(self, parent)
    return self

  @property
  def is_type(self) -> bool:
    return self.child.is_type


class Array(SymbolContainer):
  def __init__(self, child: Symbol, length: Optional[Node]) -> None:
    super().__init__(child)
    self.length: Optional[Node] = length

  def build(self, parent: Node) -> 'Array':
    super().build(parent)
    return self

  @property
  def typ(self) -> Type:
    return ArrayType(self.child.typ).build(self)

  @property
  def any_memory_offset(self) -> int:
    return 0

  def solve(self) -> DeclarationBase:
    child: Optional[DeclarationBase] = self.child.solve()
    assert isinstance(child, Type)
    return ArrayType(child).build(self)

  @property
  def repr(self) -> str:
    return '{}[]'.format(self.child.repr)

  @property
  def decl(self) -> DeclarationBase:
    child_decl: Optional[DeclarationBase] = self.child.decl
    assert isinstance(child_decl, Type)
    return ArrayType(child_decl).build(self)


class ArrayType(Type, Container):
  def __init__(self, child: Type) -> None:
    self.child: Type
    super().__init__(child)

  def build(self, parent: Node) -> 'ArrayType':
    super().build(parent)
    Container.build(self, parent)
    return self

  @property
  def any_memory_offset(self) -> int:
    return self.child.any_memory_offset

  def from_any(self) -> Symbol:
    if isinstance(self.child, Container):
      return Array(self.child.from_any(), None).build(self)
    return Array(CompoundIdentifier([Identifier(0, self.child.name)]), None).build(self)

  @property
  def name(self) -> str:
    return '@array'

  def dup(self) -> Type:
    return ArrayType(self.child.dup())


class Reference(SymbolContainer):
  def __init__(self, child: Symbol) -> None:
    SymbolContainer.__init__(self, child)
    self.child: Symbol

  def build(self, parent: Node) -> SymbolContainer:
    super().build(parent)
    ref: Reference = (ReferenceToType(self.child, self.mods) if self.child.is_type else
                      ReferenceToValue(self.child))
    ref.child.parent = ref
    ref.parent = parent
    return ref.build(parent)

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return ReferenceType(self.child.typ).build(self)

  @property
  def typ(self) -> Type:
    return ReferenceType(self.child.typ).build(self)

  @property
  def repr(self) -> str:
    return 'ref {}'.format(self.child)

  @property
  def name(self) -> str:
    return '@ref'


class ReferenceToValue(Reference):
  def __init__(self, child: Symbol) -> None:
    super().__init__(child)

  def build(self, parent: Node) -> 'ReferenceToValue':
    self.child.ref_offset -= 1
    return self

  @property
  def typ(self) -> Type:
    if self.child.decl is not None:
      assert isinstance(self.inner_child.decl, Declaration)
      return self.inner_child.decl.typ
    return BuiltinType('@any').build(self)

  @property
  def ref_offset(self) -> int:
    return self.child.ref_offset

  @ref_offset.setter
  def ref_offset(self, val: int) -> None:
    self.child.ref_offset = val - 1

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    self.child.auto_cast(target)


class ReferenceToType(Reference):
  def __init__(self, child: Symbol, mods: int =0) -> None:
    super().__init__(child)
    self.mods: int = mods

  def build(self, parent: Node) -> 'ReferenceToType':
    return self

  @property
  def ref_offset(self) -> int:
    return self.child.ref_offset + 1

  @ref_offset.setter
  def ref_offset(self, val: int) -> None:
    self.child.ref_offset = val

  @property
  def any_memory_offset(self) -> int:
    return self.child.typ.any_memory_offset


class ReferenceType(Type, Container):
  def __init__(self, child: Type, mods: int =0) -> None:
    self.child: Type
    super().__init__(child)
    self.mods: int = mods

  def build(self, parent: Node) -> 'ReferenceType':
    super().build(parent)
    return self

  @property
  def ref_offset(self) -> int:
    return self.child.ref_offset + 1

  @property
  def any_memory_offset(self) -> int:
    return self.child.any_memory_offset

  def from_any(self) -> Symbol:
    if self.child.any_memory_offset == 1 and not type(self.child) is ReferenceType:
      return self.child.from_any()
    return Reference(self.child.from_any()).build(self)

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.child

  @property
  def inner_child(self) -> Type:
    if isinstance(self.child, ReferenceType):
      return self.child.inner_child
    assert isinstance(self.child, Type)
    return self.child

  @property
  def name(self) -> str:
    return '@ref'

  def dup(self) -> Type:
    return ReferenceType(self.child.dup())

  def get_inner_declaration(self, sym: List['str']) -> DeclarationLookup:
    return self.child.get_inner_declaration(sym)


class FunctionType(Type):
  def __init__(self, ret: Symbol, args: List['VariableDeclaration'],
               is_variadic: bool =False) -> None:
    super().__init__()
    self.args: List['VariableDeclaration'] = args
    self.ret: Symbol = ret
    self.is_variadic: bool = is_variadic

  def build(self, parent: Node) -> 'FunctionType':
    super().build(parent)
    self.ret = self.ret.build(self)
    i: int = 0
    while i < len(self.args):
      self.args[i].build(self)
      i += 1
    return self

  @property
  def name(self) -> str:
    return '@func'

  def dup(self) -> 'FunctionType':
    return FunctionType(self.ret, self.args, self.is_variadic)

  def from_any(self) -> Symbol:
    return TemplatedIdentifier('func', [self])


class Operator(Node):
  def __init__(self, op: str) -> None:
    self.op: str = op

  def auto_cast(self, target: Symbol) -> None:
    pass


class VariableAssignment(Node):
  def __init__(self, var: Symbol, assign: 'Assignment') -> None:
    self.var: Symbol = var
    self.assign: 'Assignment' = assign

  def build(self, parent: Node) -> 'VariableAssignment':
    super().build(parent)
    self.var = self.var.build(self)
    self.assign = self.assign.build(self)
    self.assign.expr.auto_cast(self.var)
    return self


class Assignment(Node):
  def __init__(self, expr: 'Expression') -> None:
    self.expr: 'Expression' = expr
    self.operator: Optional[Operator] = None

  def build(self, parent: Node) -> 'Assignment':
    super().build(parent)
    self.expr = self.expr.build(self)
    return self


class Declaration(DeclarationBase):
  def __init__(self, typ: Symbol, sym: Optional['Identifier']) -> None:
    super().__init__(0)
    self._typ: Optional[Type] = None
    self.typ_src: Symbol = typ
    self.sym: Optional['Identifier'] = sym

  def build(self, parent: Node) -> 'Declaration':
    super().build(parent)
    parent.declare(self)
    self.typ_src = self.typ_src.build(self)
    self._make_type()
    if self.sym is not None:
      self.sym.build(self)
    return self

  def get_inner_declaration(self, sym: List[str]) -> DeclarationLookup:
    return self.typ.get_inner_declaration(sym)

  @property
  def is_type(self) -> bool:
    return False

  @property
  def name(self) -> str:
    return self.sym.name if self.sym is not None else ''

  @property
  def typ(self) -> Type:
    if not self.built:
      self._make_type()
    if self._typ is None:
      return BuiltinType('@any')
    return self._typ

  def _make_type(self) -> None:
    tmp: Optional[DeclarationBase] = self.typ_src.solve()
    if tmp is not None:
      assert isinstance(tmp, Type)
      self._typ = tmp


class VariableDeclaration(Declaration):
  def __init__(self, typ: Symbol, sym: Optional['Identifier'], assign: Optional[Assignment] =None
               ) -> None:
    super().__init__(typ, sym)
    self.assign: Optional[Assignment] = assign

  def build(self, parent: Node) -> 'VariableDeclaration':
    super().build(parent)
    if self.assign is not None:
      self.assign = self.assign.build(self)
      self.assign.expr.auto_cast(self.typ)
    return self


class FunctionDeclaration(Declaration):
  pass


class FunctionDefinition(FunctionDeclaration, Scope):
  def __init__(self, typ: 'TemplatedIdentifier', sym: 'Identifier', body_str: UnparsedContents
               ) -> None:
    super().__init__(typ, sym)
    self.body: List[Statement] = []
    self.body_str: UnparsedContents = body_str

  def build(self, parent: Node) -> 'FunctionDefinition':
    from ehlit.parser.parse import parse_function
    super().build(parent)
    if self.is_child_of(Import):
      return self
    try:
      assert isinstance(self.typ, FunctionType)
      typ: Optional[DeclarationBase] = self.typ.ret.solve()
      self.body = parse_function(self.body_str.contents, not typ == BuiltinType('@void'))
      for s in self.body:
        s.build(self)
    except ParseError as err:
      for f in err.failures:
        self.fail(f.severity, f.pos + self.body_str.pos, f.msg)
    return self

  def fail(self, severity: int, pos: int, msg: str) -> None:
    super().fail(severity, pos + self.body_str.pos, msg)


class Statement(Node):
  def __init__(self, expr: Node) -> None:
    self.expr: Node = expr

  def build(self, parent: Node) -> 'Statement':
    super().build(parent)
    self.expr = self.expr.build(self)
    return self


class Expression(Value):
  def __init__(self, contents: List[Value], parenthesised: bool) -> None:
    self.contents: List[Value] = contents
    self.parenthesised: bool = parenthesised

  def build(self, parent: Node) -> 'Expression':
    super().build(parent)
    self.contents = [e.build(self) for e in self.contents]
    return self

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    for e in self.contents:
      e.auto_cast(target)

  @property
  def is_parenthesised(self) -> bool:
    return self.parenthesised

  @property
  def typ(self) -> Type:
    return self.contents[0].typ


class Cast(Value):
  def __init__(self, pos: int, sym: Symbol, args: List[Expression]) -> None:
    super().__init__(pos)
    self.sym: Symbol = sym
    tmp: Optional[DeclarationBase] = sym.solve()
    assert isinstance(tmp, Type)
    self._typ: Type = tmp
    self.args: List[Expression] = args

  def build(self, parent: Node) -> 'Cast':
    super().build(parent)
    if len(self.args) < 1:
      self.error(self.pos, 'cast requires a value')
    elif len(self.args) > 1:
      self.error(self.pos, 'too many values for cast expression')
    else:
      self.args[0].build(self)
    return self

  @property
  def typ(self) -> Type:
    return self._typ

  @property
  def decl(self) -> Type:
    return self._typ


class FunctionCall(Value):
  def __init__(self, pos: int, sym: Symbol, args: List[Expression]) -> None:
    super().__init__(pos)
    self.sym: Symbol = sym
    self.args: List[Expression] = args

  def build(self, parent: Node) -> Value:
    super().build(parent)
    self.sym = self.sym.build(self)
    if self.sym.is_type:
      cast: Cast = Cast(self.pos, self.sym, self.args)
      cast = cast.build(parent)
      return cast
    self.args = [a.build(self) for a in self.args]
    res = self._reorder()
    self._check()
    return res

  def _check(self) -> None:
    sym_decl: Optional[DeclarationBase] = self.sym.solve()
    if sym_decl is None:
      return
    assert isinstance(sym_decl, Declaration)
    typ: Type = sym_decl.typ
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

  def _reorder(self) -> 'Value':
    parent: Optional[Value] = None
    while isinstance(self.sym, Container):
      if parent is None:
        parent = self.sym
      sym = self.sym
      self.sym = sym.child
      self.sym.parent = self
      sym.child = self
      sym.parent = self.parent
      self.parent = sym
    if parent is None:
      return self
    # Avoid symbol to write ref offsets, this will conflict with ours.
    self.sym.ref_offset = 0
    return parent

  @property
  def typ(self) -> Type:
    if self.sym.decl is None:
      return BuiltinType('@any').build(self)
    assert isinstance(self.sym.decl, Declaration)
    if not isinstance(self.sym.decl.typ, FunctionType):
      return self.sym.decl.typ
    return self.sym.decl.typ.ret.typ

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.sym.decl


class ArrayAccess(SymbolContainer):
  def __init__(self, child: Symbol, idx: Expression) -> None:
    super().__init__(child)
    self.idx: Expression = idx

  def build(self, parent: Node) -> 'ArrayAccess':
    super().build(parent)
    self.idx = self.idx.build(self)
    return self

  @property
  def typ(self) -> Type:
    child_typ = cast(ArrayType, self.child.typ)
    return child_typ.child

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.child.decl

  def from_any(self) -> Symbol:
    return self.child.typ.from_any()

  @property
  def repr(self) -> str:
    return "{}[]".format(self.child.repr)


class ControlStructure(Scope):
  def __init__(self, name: str, cond: Optional[Expression], body: List[Statement]) -> None:
    super().__init__(0)
    assert cond is not None or name == 'else'
    self.name: str = name
    self.cond: Optional[Expression] = cond
    self.body: List[Statement] = body

  def build(self, parent: Node) -> 'ControlStructure':
    super().build(parent)
    if self.cond is not None:
      self.cond = self.cond.build(self)
    self.body = [s.build(self) for s in self.body]
    return self


class Condition(Scope):
  def __init__(self, branches: List[ControlStructure]) -> None:
    super().__init__(0)
    self.branches: List[ControlStructure] = branches

  def build(self, parent: Node) -> 'Condition':
    super().build(parent)
    self.branches = [b.build(self) for b in self.branches]
    return self


class SwitchCase(Node):
  def __init__(self, cases: List['SwitchCaseTest'], body: 'SwitchCaseBody') -> None:
    self.cases: List['SwitchCaseTest'] = cases
    self.body: 'SwitchCaseBody' = body


class SwitchCaseTest(Node):
  def __init__(self, test: Optional[Value]) -> None:
    self.test: Optional[Value] = test

  def build(self, parent: Node) -> 'SwitchCaseTest':
    super().build(parent)
    if self.test is not None:
      self.test = self.test.build(self)
    return self


class SwitchCaseBody(Scope):
  def __init__(self, contents: List[Statement], block: bool, fallthrough: bool) -> None:
    super().__init__(0)
    self.contents: List[Statement] = contents
    self.block: bool = block
    self.fallthrough: bool = fallthrough

  def build(self, parent: Node) -> 'SwitchCaseBody':
    super().build(parent)
    self.contents = [i.build(self) for i in self.contents]
    return self


class Return(Node):
  def __init__(self, expr: Optional[Expression] =None) -> None:
    self.expr: Optional[Expression] = expr

  def build(self, parent: Node) -> 'Return':
    super().build(parent)
    if self.expr is not None:
      self.expr = self.expr.build(self)
      decl: Node = self.parent
      while not isinstance(decl, FunctionDefinition):
        decl = decl.parent
      assert isinstance(decl.typ, FunctionType)
      self.expr.auto_cast(decl.typ.ret)
    return self


class Identifier(Value):
  def __init__(self, pos: int, name: str) -> None:
    super().__init__(pos)
    self.name: str = name
    self._decl: Optional[DeclarationBase] = None

  def build(self, parent: Node) -> 'Identifier':
    super().build(parent)
    if not parent.is_declaration():
      # Only declarations may use an Identifier directly, all other node types must use
      # CompoundIdentifier
      assert isinstance(parent, CompoundIdentifier), (
        'Only declarations may use an identifier directly')
      self._decl, err = parent.find_declaration_for(self)
      if self.decl is None:
        if err is None:
          err = "use of undeclared identifier {}".format(self.name)
        self.error(self.pos, err)
      else:
        self.ref_offset = self.typ.ref_offset
    return self

  @property
  def typ(self) -> Type:
    if self.decl is None:
      return BuiltinType('@any').build(self)
    if isinstance(self.decl, Type):
      return self.decl.dup().build(self)
    assert isinstance(self.decl, Declaration) or isinstance(self.decl, Alias)
    return self.decl.typ

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self._decl


class CompoundIdentifier(Symbol):
  def __init__(self, elems: List[Identifier]) -> None:
    self.elems: List[Identifier] = elems
    super().__init__()

  def build(self, parent: Node) -> 'CompoundIdentifier':
    super().build(parent)
    self.elems = [e.build(self) for e in self.elems]
    return self

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
  def decl(self) -> Optional[DeclarationBase]:
    return self.elems[-1].decl

  @property
  def repr(self) -> str:
    return '.'.join([x.name for x in self.elems])

  @property
  def cast(self) -> Optional[Symbol]:
    return self.elems[-1].cast

  @cast.setter
  def cast(self, value: Symbol) -> None:
    self.elems[-1].cast = value

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    return self.elems[-1].auto_cast(target)

  @property
  def any_memory_offset(self) -> int:
    return self.elems[-1].typ.any_memory_offset

  def find_declaration_for(self, identifier: Identifier) -> DeclarationLookup:
    i: int = 0
    while i < len(self.elems):
      if identifier is self.elems[i]:
        return self.parent.find_declaration([x.name for x in self.elems[:i + 1]])
      i += 1
    assert False, "This code may not be reached"
    return None, None


class TemplatedIdentifier(Symbol):
  def __init__(self, name: str, types: List[Union[Symbol, Type]]) -> None:
    self._name: str = name
    self.types: List[Union[Symbol, Type]] = types
    super().__init__()

  def build(self, parent: Node) -> 'TemplatedIdentifier':
    super().build(parent)
    self.types = [t.build(self) for t in self.types]
    return self

  @property
  def decl(self) -> Optional[DeclarationBase]:
    assert isinstance(self.types[0], Type)
    return self.types[0]

  @property
  def typ(self) -> Type:
    assert isinstance(self.types[0], Type)
    return self.types[0]

  @property
  def repr(self) -> str:
    return '{}<>'.format(self.name)

  @property
  def name(self) -> str:
    return self._name


class String(Value):
  def __init__(self, string: str) -> None:
    super().__init__()
    self.string: str = string

  @property
  def typ(self) -> Type:
    return BuiltinType('@str').build(self)

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    pass


class Char(Value):
  def __init__(self, char: str) -> None:
    super().__init__()
    self.char: str = char

  @property
  def typ(self) -> Type:
    return BuiltinType('@char').build(self)

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    pass


class Number(Value):
  def __init__(self, num: str) -> None:
    super().__init__()
    self.num: str = num

  @property
  def typ(self) -> Type:
    return BuiltinType('@int').build(self)

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    pass


class NullValue(Value):
  def __init__(self) -> None:
    super().__init__()

  @property
  def typ(self) -> Type:
    return BuiltinType('@any').build(self)

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    pass


class BoolValue(Value):
  def __init__(self, val: bool) -> None:
    super().__init__()
    self.val: bool = val

  @property
  def typ(self) -> Type:
    return BuiltinType('@bool').build(self)

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    pass


class UnaryOperatorValue(Value):
  def __init__(self, op: str, val: Value) -> None:
    self.op: str = op
    self.val: Value = val

  def build(self, parent: Node) -> 'UnaryOperatorValue':
    super().build(parent)
    self.val = self.val.build(self)
    return self

  @property
  def typ(self) -> Type:
    return self.val.typ

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.val.decl

  def auto_cast(self, target: Union[Symbol, Type]) -> None:
    return self.val.auto_cast(target)


class PrefixOperatorValue(UnaryOperatorValue):
  pass


class SuffixOperatorValue(UnaryOperatorValue):
  pass


class Sizeof(Value):
  def __init__(self, sz_typ: Symbol) -> None:
    super().__init__()
    self.sz_typ: Symbol = sz_typ

  def build(self, parent: Node) -> 'Sizeof':
    super().build(parent)
    self.sz_typ = self.sz_typ.build(self)
    return self

  @property
  def typ(self) -> Type:
    return BuiltinType('@size').build(self)


class Alias(Symbol, DeclarationBase):
  def __init__(self, src: Union[Type, Symbol], dst: Identifier) -> None:
    self.src_sym: Union[Type, Symbol] = src
    self.src: Optional[DeclarationBase] = None
    self.dst: Identifier = dst

  def build(self, parent: Node) -> 'Alias':
    super().build(parent)
    parent.declare(self)
    self.src_sym = self.src_sym.build(self)
    if isinstance(self.src_sym, Symbol):
      self.src = self.src_sym.solve()
    else:
      self.src = self.src_sym
    return self

  @property
  def typ(self) -> Type:
    if self.src is None:
      return BuiltinType('@any')
    if isinstance(self.src, Type):
      return self.src
    assert isinstance(self.src, Declaration)
    return self.src.typ

  @property
  def repr(self) -> str:
    if isinstance(self.src_sym, DeclarationBase):
      return self.src_sym.name
    return self.src_sym.repr

  @property
  def name(self) -> str:
    if self.src is None:
      return ''
    return self.dst.name

  @property
  def is_type(self) -> bool:
    return isinstance(self.src, Type)

  @property
  def ref_offset(self) -> int:
    return self.dst.ref_offset

  @ref_offset.setter
  def ref_offset(self, offset: int) -> None:
    self.dst.ref_offset = offset

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self.src


class ContainerStructure(Type, Scope):
  def __init__(self, pos: int, sym: Identifier,
               fields: Optional[List[VariableDeclaration]]) -> None:
    super().__init__(pos)
    self.sym: Identifier = sym
    self.fields: Optional[List[VariableDeclaration]] = fields
    self.display_name = ''

  def build(self, parent: Node) -> 'ContainerStructure':
    if self.built:
      return self
    super().build(parent)
    parent.declare(self)
    self.sym.build(self)
    if self.fields is not None:
      self.fields = [f.build(self) for f in self.fields]
    return self

  @property
  def decl(self) -> Optional[DeclarationBase]:
    return self

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

  def from_any(self) -> Symbol:
    return Reference(CompoundIdentifier([Identifier(0, self.sym.name)])).build(self)

  def dup(self) -> Type:
    return self


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
    self.parser: Optional[ParserPython] = None

  def __iter__(self) -> Iterator[Node]:
    return self.nodes.__iter__()

  def __getitem__(self, key: int) -> Node:
    return self.nodes[key]

  def __len__(self) -> int:
    return len(self.nodes)

  def build(self, parent: Node) -> 'Node':
    raise Exception('AST.build may not be called')

  def build_ast(self, args: OptionsStruct) -> None:
    super().build(Node(0))
    self.builtins: List[Type] = [
      FunctionType(CompoundIdentifier([Identifier(0, '@any')]), []),
      BuiltinType('@int'), BuiltinType('@int8'), BuiltinType('@int16'), BuiltinType('@int32'),
      BuiltinType('@int64'), BuiltinType('@uint'), BuiltinType('@uint8'), BuiltinType('@uint16'),
      BuiltinType('@uint32'), BuiltinType('@uint64'), BuiltinType('@void'), BuiltinType('@bool'),
      BuiltinType('@char'), BuiltinType('@size'), BuiltinType('@str'), BuiltinType('@any'),
    ]
    self.builtins = [decl.build(self) for decl in self.builtins]
    self._import_paths = [
      path.dirname(args.source),
      getcwd(),
      path.dirname(args.output_import_file)]

    for n in self.nodes:
      n.build(self)
    if len(self.failures) != 0:
      raise ParseError(self.failures, self.parser)

  def fail(self, severity: int, pos: int, msg: str) -> None:
    assert self.parser is not None
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
      if res is not None:
        return cast(Type, res).dup().build(self), err
      if err is not None:
        return res, err
    return None, None

  @property
  def import_paths(self) -> List[str]:
    return self._import_paths

  def is_child_of(self, cls: typing.Type[Node]) -> bool:
    return False
