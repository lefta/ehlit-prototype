# Copyright © 2017-2019 Cedric Legrand
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
from enum import IntEnum, IntFlag
from os import path, getcwd, listdir
from typing import Any, Iterator, List, Optional, TypeVar, Union, cast
import typing
from ehlit.parser.error import ParseError, Failure
from ehlit.options import OptionsStruct

T = TypeVar('T', bound='Node')

imported: List[str] = []
included: List[str] = []


class DeclarationLookup(list):
    def __init__(self, name: str, decls: Optional[List['Node']] = None) -> None:
        super().__init__()
        self._error: Optional[str] = None
        self._name = name
        if decls is not None:
            self.find_in(decls)

    def get_inner_declaration(self, sym: str) -> 'DeclarationLookup':
        res: DeclarationLookup = DeclarationLookup(sym)
        for decl in self:
            res.merge(decl.get_inner_declaration(sym))
        return res

    @property
    def error(self) -> str:
        if self._error is None:
            return "use of undeclared identifier {}".format(self._name)
        return self._error

    @error.setter
    def error(self, err: str) -> None:
        self._error = err

    def merge(self, other: 'DeclarationLookup') -> None:
        assert self._name == other._name
        self.extend(other)
        if self._error is None:
            self._error = other._error

    def find_in(self, decls: List['Node']) -> None:
        for decl in decls:
            self.merge(decl.get_declaration(self._name))


class Qualifier(IntFlag):
    """!
    Qualifier for a declaration

    This changes the behavior of the declaration. See the description of each value to know in which
    way.
    """
    NONE = 0
    CONST = 1
    RESTRICT = 2
    VOLATILE = 4
    INLINE = 8
    STATIC = 16
    PRIVATE = 32

    @property
    def is_const(self) -> bool:
        """! Whether this declaration is const or not.
        A const declaration is a declaration that may not be modified at run time.
        """
        return bool(self & Qualifier.CONST)

    @property
    def is_restricted(self) -> bool:
        """! Returns whether this declaration is restricted or not.
        A restricted reference is a reference that refers to a unique value in its scope, i.e. two
        restricted references may not refer to the same variable, thus allowing the compiler to
        optimize a function farther.
        @note: This only applies to function argument declarations
        """
        return bool(self & Qualifier.RESTRICT)

    @property
    def is_volatile(self) -> bool:
        """! Returns whether this declaration is volatile or not.
        A volatile declaration is a declaration whose value may change unexpectidely, thus
        preventing the compiler to guess it a build time.
        @note: This only applies to variable declarations
        """
        return bool(self & Qualifier.VOLATILE)

    @property
    def is_inline(self) -> bool:
        """! Returns whether this declaration is inline or not.
        An inline declaration is a declaration whose usage get replaced with its content at build
        time.
        @note: This only applies to function declarations.
        """
        return bool(self & Qualifier.INLINE)

    @property
    def is_static(self) -> bool:
        """! Returns whether this declaration is static or not.
        A static declaration is a declaration whose lifetime storage does not belong to the scope it
        is declared. For example, a static variable in a function will keep its value between each
        function call.
        However, the visibility of a static declaration remains the same.
        """
        return bool(self & Qualifier.STATIC)

    @property
    def is_private(self) -> bool:
        """! Returns whether this declaration is private or not.
        A private declaration is a declaration that is not visible outside the scope it is declared.
        For example, a private global symbol will not be visible outside the file where it is
        declared.
        """
        return bool(self & Qualifier.PRIVATE)

    @property
    def mangled(self) -> str:
        res = ''
        if self.is_const:
            res += 'C'
        if self.is_volatile:
            res += 'W'
        if self.is_restricted:
            res += 'X'
        return res


class DeclarationType(IntEnum):
    """!
    Type of a declaration

    The type of a declaration is the way a declaration gets mangled, stored and used in the
    program.
    """

    ## An Ehlit symbol, this is the default.
    EHLIT = 0
    ## A C symbol, used by symbols imported from a C header.
    C = 1


class UnparsedContents:
    """!
    Contents for which parsing have been delayed, for example because of a lack of context.
    """

    def __init__(self, contents: str, pos: int) -> None:
        """! Constructor
        @param contents @b str Contents to be parsed later.
        @param pos @b int Position of the contents in the file.
        """
        self.contents: str = contents
        self.pos: int = pos


class Node:
    """!
    Base class for all AST node types. It defines some default behaviors.
    """

    def __init__(self, pos: int = 0) -> None:
        """! Constructor
        @param pos @b int The position of the node in the source file
        """
        ## @b int Position of the node in the source file.
        self.pos: int = pos
        ## @b bool Whether this node have already been built or not.
        self.built: bool = False
        ## @b Node The parent node of this node.
        self._parent: Optional[Node] = None

    def build(self) -> 'Node':
        """! Build a node.
        Depending on the node type, this may mean resolving symbol references, making sanity checks
        and / or building children.
        """
        self.built = True
        return self

    def find_declaration(self, sym: str) -> DeclarationLookup:
        """! Find a declaration when coming from downsides.
        Scoping structures (like functions) would want to search symbols in this function. The
        default is to pass the lookup to the parent.
        @param sym @b str The symbol to find.
        @return @b Declaration|FunctionDeclaration The declaration if found, None otherwise.
        """
        return self.parent.find_declaration(sym)

    def get_declaration(self, sym: str) -> DeclarationLookup:
        """! Find a declaration when coming from upsides.
        Structures exposing symbols to their parent (like Import) would want to search symbols in
        this function.
        @param sym @b str The symbol to find
        @return @b Declaration|FunctionDeclaration The declaration if found, None otherwise.
        """
        return DeclarationLookup(sym)

    def fail(self, severity: ParseError.Severity, pos: int, msg: str) -> None:
        """! Report a failure to the parent, up to the AST where it will be handled.
        There is no reason to override it, except maybe intercepting it for whatever reason.
        @param severity @b ParseError.Severity Severity of the failure
        @param pos @b int The position in code where the failure happened
        @param msg @b str The failure message to display
        """
        self.parent.fail(severity, pos, msg)

    def error(self, pos: int, msg: str) -> None:
        """! Shorthand for fail with severity Error.
        @param pos @b int The position in code where the failure happened
        @param msg @b str The failure message to display
        """
        self.fail(ParseError.Severity.Error, pos, msg)

    def warn(self, pos: int, msg: str) -> None:
        """! Shorthand for fail with severity Warning.
        @param pos @b int The position in code where the failure happened
        @param msg @b str The failure message to display
        """
        self.fail(ParseError.Severity.Warning, pos, msg)

    def declare(self, decl: 'DeclarationBase') -> None:
        """! Declare a symbol.
        By default, this is only propagated to the parent. @c Scope override it to remember it.
        @param decl @b DeclarationBase The declaration to be declared.
        """
        self.parent.declare(decl)

    @property
    def import_paths(self) -> List[str]:
        """! @c property @b List[str] The list of paths to be looked up when importing a module. """
        return self.parent.import_paths

    def is_child_of(self, cls: typing.Type['Node']) -> bool:
        """! Check if this node is a descendant of some node type
        @param cls @b Class The class to check for
        """
        return isinstance(self, cls) or self.parent.is_child_of(cls)

    def do_before(self, do: 'Node', before: 'Node') -> None:
        """! Do something before executing the current node
        By default, this call is only propagated to this node's parent. It will get handled by node
        types that are able to handle the requested action.
        @param do @c Node The node representing the action to execute.
        @param before @c Node The node before which the action shall be executed.
        """
        self.parent.do_before(do, self)

    def generate_var_name(self) -> str:
        """! Generate a variable name
        The generated variable name is ensured to be unique in its scope.
        @return @b str The generated variable name
        """
        return self.parent.generate_var_name()

    @property
    def mangled_scope(self) -> str:
        return self.parent.mangled_scope

    def make(self, node: T) -> T:
        node.parent = self
        return cast(T, node.build())

    @property
    def parent(self) -> 'Node':
        assert self._parent is not None
        return self._parent

    @parent.setter
    def parent(self, parent: 'Node') -> None:
        if self._parent is None:
            self._parent = parent


class Scope(Node):
    """! Container for declarations.
    A @c Scope handles the declaration of symbols and their resolution.
    It also handles pre-declaration of symbols, i.e. symbols that are declared later, but that
    are used in this @c Scope. Pre-declaration is needed to generate valid C output.
    """

    def __init__(self, pos: int) -> None:
        super().__init__(pos)
        self.declarations: List[DeclarationBase] = []
        self.predeclarations: List[DeclarationBase] = []

    def declare(self, decl: 'DeclarationBase') -> None:
        self.declarations.append(decl)

    def find_declaration(self, sym: str) -> DeclarationLookup:
        # MyPy does not consider List[DeclarationBase] as a List[Node]
        res: DeclarationLookup = DeclarationLookup(sym, cast(List[Node], self.declarations))
        res.merge(super().find_declaration(sym))
        for decl in res:
            if decl is not None and not decl.built:
                self.predeclarations.append(decl)
        return res


class UnorderedScope(Scope):
    """! @c Scope in which declaration order does not matter """

    def find_declaration(self, sym: str) -> DeclarationLookup:
        res: DeclarationLookup = DeclarationLookup(sym, self.scope_contents)
        res.merge(super().find_declaration(sym))
        return res

    @property
    @abstractmethod
    def scope_contents(self) -> List[Node]:
        """! Contents of the scope
        @return @b List[Node] The list of nodes contained in the scope
        """
        raise NotImplementedError


class FlowScope(Scope):
    """! Scope containing a @c Statement flow
    It adds the ability to change the statement flow at build time.
    @see do_before
    """
    def __init__(self, pos: int, body: List['Statement']) -> None:
        super().__init__(pos)
        self.body: List[Statement] = body
        for node in self.body:
            node.parent = self

    def build(self) -> Node:
        super().build()
        self._counter: int = 0
        while self._counter < len(self.body):
            self.body[self._counter] = self.make(self.body[self._counter])
            self._counter += 1
        return self

    def do_before(self, do: Node, before: Node) -> None:
        """! Insert a @c Statement to be executed before @c before
        @param do @b Node The @c Statement to be executed. It must be a @c Statement, otherwise it
                          gets ignored
        @param before @b Node The node before which the statement will be executed
        """
        if not isinstance(do, Statement):
            super().do_before(do, before)
            return
        assert isinstance(before, Statement)
        self.body.insert(self.body.index(before), self.make(do))
        self._counter += 1


class GenericExternInclusion(UnorderedScope):
    """! Base for include and import defining shared behaviors """

    def __init__(self, pos: int, lib: List[str]) -> None:
        """! Constructor
        @param pos @b int The position of the node in the source file
        @param lib @b List[str] Path of the file to be imported
        """
        super().__init__(pos)
        ## @b str The library that will be imported
        self.lib: str = '/'.join(lib)
        ## @b List[Node] The symbols that have been imported from the library
        self.syms: List[Node] = []

    def build(self) -> 'GenericExternInclusion':
        """! Build the node, this actually imports the file
        @param parent @b Node The parent of this node
        """
        super().build()
        parsed: List[Node] = []
        try:
            parsed = self.parse()
        except ParseError as err:
            for e in err.failures:
                self.fail(e.severity, self.pos, e.msg)
        for s in parsed:
            self.syms.append(self.make(s))
        return self

    @abstractmethod
    def parse(self) -> List[Node]:
        """! Parse the imported file
        @return @b List[Node] A list of the imported nodes
        """
        raise NotImplementedError

    def get_declaration(self, sym: str) -> DeclarationLookup:
        """! Look for a declaration from the imported file
        @param sym @b List[str] The symbol to look for
        @return @b Declaration|FunctionDeclaration The declaration if found, @c None otherwise
        """
        return DeclarationLookup(sym, self.syms)

    @property
    def scope_contents(self) -> List[Node]:
        return self.syms


class Import(GenericExternInclusion):
    """! Specialization of GenericExternInclusion for Ehlit imports. """

    def import_dir(self, dir: str) -> List[Node]:
        """! Import a whole directory.
        This recursively imports all Ehlit files in the specified directory.
        @param dir @b str The directory to import.
        @return @b List[Node] A list of the imported nodes.
        """
        res: List[Node] = []
        for sub in listdir(dir):
            full_path: str = path.join(dir, sub)
            if full_path in imported:
                continue
            imported.append(full_path)
            if path.isdir(full_path):
                res += self.import_dir(full_path)
            elif path.isfile(full_path):
                res += source.parse(full_path).nodes
        return res

    def parse(self) -> List[Node]:
        """! Parse the imported file or directory contents.
        @return @b List[Node] A list of the imported nodes.
        """
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
                return source.parse(full_path).nodes
        self.error(self.pos, '%s: no such file or directory' % self.lib)
        return []

    def find_declaration(self, sym: str) -> DeclarationLookup:
        found = super().find_declaration(sym)
        res = DeclarationLookup(sym)
        for decl in found:
            if isinstance(decl, Declaration) and decl._qualifiers.is_private:
                res.error = 'accessing to private symbol `{}`'.format(sym)
            else:
                res.append(decl)
        return res


class Include(GenericExternInclusion):
    """! Specialization of GenericExternInclusion for C includes. """

    def parse(self) -> List[Node]:
        """! Parse the included file.
        @return @b List[Node] A list of the imported nodes.
        """
        if self.lib in included:
            return []
        included.append(self.lib)
        return c_header.parse(self.lib)

    def declare(self, decl: 'DeclarationBase') -> None:
        decl.declaration_type = DeclarationType.C
        self.declarations.append(decl)


class Value(Node):
    """! Base for all nodes representing a value. """

    def __init__(self, pos: int = 0) -> None:
        """! Constructor
        @param pos @b int The position of the node in the source file
        """
        Node.__init__(self, pos)
        ## @b int Referencing offset to be applied when writing this value.
        self._ref_offset: int = 0
        ## @b Type Cast to apply to this value when writing it, if relevant.
        self._cast: Optional[Symbol] = None

    def build(self) -> 'Value':
        super().build()
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
        """! Compute the conversion needed to transform an any into target.
        This function computes the referencing offset and / or the cast to make an @b any, or a
        container of @b any, binary compatible with target. It also takes into account the will of
        the developper if he wants more references than the minimum required.
        @param target @b Node The target of the conversion, with which source will be made
                              compatible.
        @param source @b Type The source type that should be converted. It shall be either an
                              @c any, or any container of it.
        @param is_casting @b bool Whether we are already in a casting context or not.
        @return @b Type The cast needed for a successful conversion.
        """
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
                if res.any_memory_offset == 0:
                    res = res.child
        if target_ref_count != 0:
            # The developper asked for some referencing
            target_ref_count -= res.ref_offset - res.typ.any_memory_offset
            while target_ref_count > 0:
                res = self.make(Reference(res))
                target_ref_count -= 1
        return res

    def auto_cast(self, target: Union['Symbol', 'Type']) -> None:
        """! Make this value binary compatible with target.
        @param target @b Node The node that this value shall be made compatible with.
        """
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
                if target_ref_level != 0:
                    target_ref_level -= target.ref_offset
        if src:
            if (isinstance(target, Symbol) and target.is_type) or isinstance(target, Type):
                target_ref_level += target.ref_offset
            else:
                target_ref_level += target.typ.ref_offset - target.ref_offset
            self.ref_offset = src.ref_offset - target_ref_level


class DeclarationBase(Node):
    def __init__(self, pos: int = 0) -> None:
        Node.__init__(self, pos)
        self.declaration_type: DeclarationType = DeclarationType.EHLIT

    def get_declaration(self, sym: str) -> DeclarationLookup:
        res = DeclarationLookup(sym)
        if self.name == sym:
            res.append(self)
        return res

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        """! Find a declaration strictly in children.
        Container types (like structs) would want to search symbols in this function.
        @param sym @b List[str] The symbol to find.
        @return @b Declaration|FunctionDeclaration The inner declaration if found, None otherwise.
        """
        return DeclarationLookup(sym)

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def mangled_name(self) -> str:
        if self.declaration_type == DeclarationType.C:
            return self.name
        return '{}{}'.format(self.parent.mangled_scope, self.mangled)

    @property
    @abstractmethod
    def mangled(self) -> str:
        raise NotImplementedError


class Type(DeclarationBase):
    def build(self) -> 'Type':
        super().build()
        return self

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
    def __init__(self, pos: int = 0) -> None:
        super().__init__(pos)
        self.qualifiers: Qualifier = Qualifier.NONE
        self._canonical: Optional[DeclarationBase] = None

    def build(self) -> 'Symbol':
        super().build()
        self._canonical = self.solve()
        return self

    def solve(self) -> Optional[DeclarationBase]:
        decl = self.decl
        while decl is not None and isinstance(decl, Symbol):
            decl = decl.decl
        if decl is None or decl.built:
            return decl
        res = decl.build()
        assert res is None or isinstance(res, DeclarationBase)
        return res

    def set_qualifiers(self, qualifiers: Qualifier) -> None:
        self.qualifiers = qualifiers

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

    @property
    def canonical(self) -> Optional[DeclarationBase]:
        if not self.built and self._canonical is None:
            self._canonical = self.solve()
        return self._canonical

    @property
    @abstractmethod
    def mangled(self) -> str:
        raise NotImplementedError


class BuiltinType(Type):
    @staticmethod
    def make_symbol(parent: Node, name: str) -> 'CompoundIdentifier':
        return parent.make(CompoundIdentifier([Identifier(parent.pos, '@' + name)]))

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name: str = name

    def build(self) -> 'BuiltinType':
        super().build()
        return self

    @property
    def child(self) -> Optional[Type]:
        if self.name == '@str':
            return self.make(BuiltinType('@char'))
        return None

    @property
    def as_symbol(self) -> 'CompoundIdentifier':
        return CompoundIdentifier([Identifier(self.pos, self.name)])

    def from_any(self) -> Symbol:
        if self.name == '@str':
            return BuiltinType.make_symbol(self, 'str')
        return self.make(Reference(self.as_symbol))

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

    @property
    def mangled(self) -> str:
        return 'B{}{}'.format(len(self.name) - 1, self.name[1:])


class Container(Node):
    def __init__(self, child: Node) -> None:
        super().__init__(0)
        self.child: Node = child
        self.child.parent = self

    def build(self) -> Node:
        super().build()
        self.child = self.child.build()
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

    def build(self) -> 'SymbolContainer':
        super().build()
        Container.build(self)
        return self

    @property
    def is_type(self) -> bool:
        return self.child.is_type


class Array(SymbolContainer):
    def __init__(self, child: Symbol, length: Optional[Node]) -> None:
        super().__init__(child)
        self.length: Optional[Node] = length
        if self.length is not None:
            self.length.parent = self

    def build(self) -> 'Array':
        super().build()
        return self

    @property
    def typ(self) -> Type:
        return self.make(ArrayType(self.child.typ))

    @property
    def any_memory_offset(self) -> int:
        return 0

    def solve(self) -> DeclarationBase:
        child: Optional[DeclarationBase] = self.child.canonical
        assert isinstance(child, Type)
        return self.make(ArrayType(child))

    @property
    def repr(self) -> str:
        return '{}[]'.format(self.child.repr)

    @property
    def decl(self) -> DeclarationBase:
        child_decl: Optional[DeclarationBase] = self.child.decl
        assert isinstance(child_decl, Type)
        return self.make(ArrayType(child_decl))

    @property
    def mangled(self) -> str:
        return '{}A{}'.format(self.qualifiers.mangled, self.child.mangled)


class ArrayType(Type, Container):
    def __init__(self, child: Type) -> None:
        self.child: Type
        Type.__init__(self)
        Container.__init__(self, child)
        child._parent = self

    def build(self) -> 'ArrayType':
        super().build()
        Container.build(self)
        return self

    @property
    def any_memory_offset(self) -> int:
        return self.child.any_memory_offset

    def from_any(self) -> Symbol:
        if isinstance(self.child, Container):
            return self.make(Array(self.child.from_any(), None))
        return self.make(Array(CompoundIdentifier([Identifier(0, self.child.name)]), None))

    @property
    def name(self) -> str:
        return '@array'

    def dup(self) -> Type:
        return ArrayType(self.child.dup())

    @property
    def mangled(self) -> str:
        return 'A{}'.format(self.child.mangled)


class Reference(SymbolContainer):
    def __init__(self, child: Symbol) -> None:
        super().__init__(child)
        self.child: Symbol

    def build(self) -> SymbolContainer:
        self.child.build()
        res: SymbolContainer = self.parent.make(ReferenceToType(self.child, self.qualifiers)
                                                if self.child.is_type
                                                else ReferenceToValue(self.child))
        res.child._parent = res
        return res

    @property
    def decl(self) -> Optional[DeclarationBase]:
        return self.typ

    @property
    def typ(self) -> Type:
        return self.make(ReferenceType(self.child.typ))

    @property
    def repr(self) -> str:
        return 'ref {}'.format(self.child)

    @property
    def name(self) -> str:
        return '@ref'

    @property
    def mangled(self) -> str:
        return '{}R{}'.format(self.qualifiers.mangled, self.child.mangled)


class ReferenceToValue(Reference):
    def __init__(self, child: Symbol) -> None:
        super().__init__(child)

    def build(self) -> 'ReferenceToValue':
        SymbolContainer.build(self)
        self.child.ref_offset -= 1
        return self

    @property
    def typ(self) -> Type:
        if self.child.decl is not None:
            assert isinstance(self.inner_child.decl, Declaration)
            return self.inner_child.decl.typ
        return self.make(BuiltinType('@any'))

    @property
    def ref_offset(self) -> int:
        return self.child.ref_offset

    @ref_offset.setter
    def ref_offset(self, val: int) -> None:
        self.child.ref_offset = val

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        self.child.auto_cast(target)


class ReferenceToType(Reference):
    def __init__(self, child: Symbol, qualifiers: Qualifier = Qualifier.NONE) -> None:
        super().__init__(child)
        self.qualifiers: Qualifier = qualifiers

    def build(self) -> 'ReferenceToType':
        SymbolContainer.build(self)
        return self

    @property
    def ref_offset(self) -> int:
        return self.child.ref_offset + 1

    @ref_offset.setter
    def ref_offset(self, val: int) -> None:
        self.child.ref_offset = val - 1

    @property
    def any_memory_offset(self) -> int:
        return self.child.typ.any_memory_offset


class ReferenceType(Type, Container):
    def __init__(self, child: Type, qualifiers: Qualifier = Qualifier.NONE) -> None:
        self.child: Type
        Container.__init__(self, child)
        Type.__init__(self)
        self.qualifiers: Qualifier = qualifiers
        self.child._parent = self

    def build(self) -> 'ReferenceType':
        super().build()
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
        return self.make(Reference(self.child.from_any()))

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

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        return self.child.get_inner_declaration(sym)

    @property
    def mangled(self) -> str:
        if self.declaration_type == DeclarationType.C:
            return self.child.mangled
        return 'R{}'.format(self.child.mangled)


class FunctionType(Type):
    def __init__(self, ret: Symbol, args: List['VariableDeclaration'],
                 is_variadic: bool = False, variadic_type: Optional[Symbol] = None) -> None:
        super().__init__()
        self.args: List['VariableDeclaration'] = args
        self.ret: Symbol = ret
        self.is_variadic: bool = is_variadic
        self.variadic_type: Optional[Symbol] = variadic_type
        for arg in self.args:
            arg.parent = self
        self.ret.parent = self
        if self.variadic_type is not None:
            self.variadic_type.parent = self

    def build(self) -> 'FunctionType':
        super().build()
        self.ret = self.ret.build()
        self.args = [arg.build() for arg in self.args]
        if self.variadic_type is not None:
            self.variadic_type = self.variadic_type.build()
        return self

    @property
    def name(self) -> str:
        return '@func'

    def dup(self) -> 'FunctionType':
        return FunctionType(self.ret, self.args, self.is_variadic)

    def from_any(self) -> Symbol:
        return TemplatedIdentifier('func', [self])

    @property
    def mangled(self) -> str:
        name = 'B4func'
        for a in self.args:
            name = '{}{}'.format(name, a.typ_src.mangled)
        if self.is_variadic:
            assert self.variadic_type is not None
            name = '{}v{}'.format(name, self.variadic_type.mangled)
        return name


class Operator(Node):
    def __init__(self, op: str) -> None:
        super().__init__()
        self.op: str = op

    def auto_cast(self, target: Symbol) -> None:
        pass


class VariableAssignment(Node):
    def __init__(self, var: Symbol, assign: 'Assignment') -> None:
        super().__init__()
        self.var: Symbol = var
        self.assign: Assignment = assign
        self.var.parent = self
        self.assign.parent = self

    def build(self) -> 'VariableAssignment':
        super().build()
        self.var = self.var.build()
        self.assign = self.assign.build()
        self.assign.expr.auto_cast(self.var)
        return self


class Assignment(Node):
    def __init__(self, expr: 'Expression') -> None:
        super().__init__()
        self.expr: Expression = expr
        self.expr.parent = self
        self.operator: Optional[Operator] = None

    def build(self) -> 'Assignment':
        super().build()
        self.expr = self.expr.build()
        return self


class Declaration(DeclarationBase):
    def __init__(self, pos: int, typ: Symbol, sym: Optional['Identifier'], qualifiers: Qualifier
                 ) -> None:
        super().__init__(pos)
        self._typ: Optional[Type] = None
        self.typ_src: Symbol = typ
        self.sym: Optional['Identifier'] = sym
        self._qualifiers: Qualifier = qualifiers
        self.typ_src.parent = self
        if self.sym is not None:
            self.sym.parent = self

    def build(self) -> 'Declaration':
        super().build()
        self.parent.declare(self)
        self.typ_src = self.typ_src.build()
        self._make_type()
        if self.sym is not None:
            self.sym.build()
        return self

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        return self.typ.get_inner_declaration(sym)

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
        tmp: Optional[DeclarationBase] = self.typ_src.canonical
        if tmp is not None:
            assert isinstance(tmp, Type)
            self._typ = tmp


class VariableDeclaration(Declaration):
    def __init__(self, typ: Symbol, sym: Optional['Identifier'], assign: Optional[Assignment] = None
                 ) -> None:
        super().__init__(0, typ, sym, Qualifier.NONE)
        self.assign = assign

    def build(self) -> 'VariableDeclaration':
        super().build()
        if self.assign is not None:
            self.assign = self.assign.build()
            self.assign.expr.auto_cast(self.typ)
        return self

    @property
    def private(self) -> bool:
        return self._qualifiers.is_private

    @private.setter
    def private(self, value: bool) -> None:
        if value:
            self._qualifiers |= Qualifier.PRIVATE
        else:
            self._qualifiers &= ~Qualifier.PRIVATE

    @property
    def static(self) -> bool:
        return self._qualifiers.is_static

    @static.setter
    def static(self, value: bool) -> None:
        if value:
            self._qualifiers |= Qualifier.STATIC
        else:
            self._qualifiers &= ~Qualifier.STATIC

    @property
    def mangled_name(self) -> str:
        if self.sym is None:
            return ''
        if self._is_mangled:
            return super().mangled_name
        return self.sym.name

    @property
    def mangled(self) -> str:
        if self.sym is None:
            return ''
        if self._is_mangled:
            return '{}V{}'.format(self.typ_src.qualifiers.mangled, self.sym.mangled)
        return self.sym.name

    @property
    def _is_mangled(self) -> bool:
        return not (self.declaration_type == DeclarationType.C or
                    self.is_child_of(FunctionDeclaration) or self.is_child_of(Struct) or
                    self.is_child_of(EhUnion) or self.is_child_of(EhClass))

    @property
    def assign(self) -> Optional[Assignment]:
        return self._assign

    @assign.setter
    def assign(self, assign: Optional[Assignment]) -> None:
        self._assign = assign
        if self._assign is not None:
            self._assign.parent = self


class FunctionDeclaration(Declaration):
    def __init__(self, pos: int, qualifiers: Qualifier, typ: 'TemplatedIdentifier',
                 sym: 'Identifier') -> None:
        super().__init__(0, typ, sym, qualifiers)
        self.this_cls: Optional[EhClass] = None

    @property
    def qualifiers(self) -> Qualifier:
        return self._qualifiers

    @property
    def mangled_name(self) -> str:
        if self.sym is None:
            return ''
        if self.sym.name == 'main':
            return self.sym.name
        return super().mangled_name

    @property
    def mangled(self) -> str:
        if self.sym is None:
            return ''
        if self.sym.name == 'main':
            return self.sym.name
        assert isinstance(self.typ, FunctionType)
        name: str = '{}F{}'.format(self.qualifiers.mangled, self.sym.mangled)
        for a in self.typ.args:
            name = '{}{}'.format(name, a.typ_src.mangled)
        if self.typ.is_variadic:
            assert self.typ.variadic_type is not None
            name = '{}v{}'.format(name, self.typ.variadic_type.mangled)
        return name


class FunctionDefinition(FunctionDeclaration, FlowScope):
    def __init__(self, pos: int, qualifiers: Qualifier, typ: 'TemplatedIdentifier',
                 sym: 'Identifier', body_str: UnparsedContents) -> None:
        super().__init__(pos, qualifiers, typ, sym)
        FlowScope.__init__(self, pos, [])
        self.body_str: UnparsedContents = body_str
        self.gen_var_count: int = 0

    def build(self) -> 'FunctionDefinition':
        super().build()
        if self.is_child_of(Import):
            return self
        try:
            assert isinstance(self.typ, FunctionType)
            typ: Optional[DeclarationBase] = self.typ.ret.canonical
            self.body = function.parse(self.body_str.contents, not typ == BuiltinType('@void'))
            for stmt in self.body:
                stmt.parent = self
            super().build()
        except ParseError as err:
            for f in err.failures:
                self.fail(f.severity, f.pos, f.msg)
        return self

    def fail(self, severity: ParseError.Severity, pos: int, msg: str) -> None:
        super().fail(severity, pos + self.body_str.pos, msg)

    def find_declaration(self, sym: str) -> DeclarationLookup:
        if sym != 'vargs':
            return super().find_declaration(sym)
        assert isinstance(self.typ, FunctionType)
        res = DeclarationLookup(sym)
        if self.typ.is_variadic:
            assert self.typ.variadic_type is not None
            res.append(self.make(VArgs(self.typ.variadic_type)))
        else:
            res.error = "use of vargs in a non variadic function"
        return res

    def generate_var_name(self) -> str:
        self.gen_var_count += 1
        return '__gen_fun_{}'.format(self.gen_var_count)


class VArgs(VariableDeclaration):
    def __init__(self, typ: Symbol) -> None:
        super().__init__(Array(typ, None), Identifier(0, 'vargs'))

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        res = DeclarationLookup(sym)
        if sym == 'length':
            res.append(self.make(VArgsLength()))
        else:
            res.error = "`vargs` have no property {}".format(sym)
        return res

    @property
    def mangled_name(self) -> str:
        return '_EB5vargs'

    @property
    def mangled(self) -> str:
        return 'B5vargs'


class VArgsLength(VariableDeclaration):
    def __init__(self) -> None:
        super().__init__(CompoundIdentifier([Identifier(0, '@int')]), Identifier(0, 'vargs_len'))

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@int'))

    @property
    def mangled_name(self) -> str:
        return '_EB9vargs_len'

    @property
    def mangled(self) -> str:
        return 'B9vargs_len'


class Statement(Node):
    def __init__(self, expr: Node) -> None:
        super().__init__()
        self.expr: Node = expr
        self.expr.parent = self

    def build(self) -> 'Statement':
        super().build()
        self.expr = self.expr.build()
        return self

    def get_declaration(self, sym: str) -> DeclarationLookup:
        return self.expr.get_declaration(sym)


class Expression(Value):
    def __init__(self, contents: List[Value], parenthesised: bool) -> None:
        super().__init__()
        self.contents: List[Value] = contents
        self.parenthesised: bool = parenthesised
        for node in self.contents:
            node.parent = self

    def build(self) -> 'Expression':
        super().build()
        self.contents = [e.build() for e in self.contents]
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


class InitializationList(Value):
    def __init__(self, contents: List[Expression]) -> None:
        super().__init__()
        self.contents: List[Expression] = contents
        for node in self.contents:
            node.parent = self

    def build(self) -> 'InitializationList':
        super().build()
        self.contents = [x.build() for x in self.contents]
        return self

    def auto_cast(self, target: Union['Symbol', 'Type']) -> None:
        assert isinstance(target, ArrayType)
        tgt: Type = target.child
        for n in self.contents:
            n.auto_cast(tgt)

    def typ(self) -> Type:
        return BuiltinType('@any')


class Cast(Value):
    def __init__(self, pos: int, sym: Symbol, args: List[Expression]) -> None:
        super().__init__(pos)
        self.sym: Symbol = sym
        self.args: List[Expression] = args
        self.sym.parent = self
        for node in self.args:
            node.parent = self
        assert isinstance(sym.canonical, Type)
        self._typ: Type = sym.canonical

    def build(self) -> 'Cast':
        super().build()
        if len(self.args) < 1:
            self.error(self.pos, 'cast requires a value')
        elif len(self.args) > 1:
            self.error(self.pos, 'too many values for cast expression')
        else:
            self.args[0].build()
        return self

    @property
    def typ(self) -> Type:
        return self._typ

    @property
    def decl(self) -> Type:
        return self._typ

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        sym_ref_offset: int = self.sym.ref_offset
        self.sym.auto_cast(target)
        self.ref_offset = self.sym.ref_offset
        self.sym.ref_offset = sym_ref_offset


class FunctionCall(Value):
    def __init__(self, pos: int, sym: Symbol, args: List[Expression]) -> None:
        super().__init__(pos)
        self.sym: Symbol = sym
        self.args: List[Expression] = args
        self._this_ptr: Optional[CompoundIdentifier] = None
        self.sym.parent = self
        for arg in self.args:
            arg.parent = self

    def build(self) -> Value:
        super().build()
        self.sym = self.sym.build()
        if self.this_ptr is not None:
            self.this_ptr = self.this_ptr.build()
        if self.sym.is_type:
            return self.parent.make(Cast(self.pos, self.sym, self.args))
        self.args = [a.build() for a in self.args]
        res = self._reorder()
        if self.sym.canonical is None:
            return res
        assert isinstance(self.sym.canonical, Declaration)
        typ: Type = self.sym.canonical.typ
        if not isinstance(typ, FunctionType):
            self.error(self.pos, "calling non function type {}".format(self.sym.repr))
            return res
        self._check_args(typ)
        self._auto_cast_args(typ)
        return res

    def _check_args(self, typ: FunctionType) -> None:
        diff = self.arg_count - len(typ.args)
        i = 0
        while i < len(typ.args):
            if i >= self.arg_count:
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
                self.arg_count))

    def _auto_cast_args(self, typ: FunctionType) -> None:
        fun_decl_type: DeclarationType = DeclarationType.EHLIT
        if self.sym.decl is not None:
            fun_decl_type = self.sym.decl.declaration_type
        i = 0
        arg_offset = 0
        if self.this_ptr is not None:
            self.this_ptr.auto_cast(typ.args[0].typ)
            arg_offset = 1
        while i < len(self.args) and i < len(typ.args):
            self.args[i].auto_cast(typ.args[i + arg_offset].typ)
            i += 1
        if typ.is_variadic and fun_decl_type is DeclarationType.EHLIT:
            vargs: List[Expression] = self.args[i:]
            self.args = self.args[:i]
            assert typ.variadic_type is not None
            vargs_name: str = self.generate_var_name()
            stmt: Statement = self.make(Statement(VariableDeclaration(
                Array(typ.variadic_type, Number(str(len(vargs)))),
                Identifier(0, vargs_name),
                Assignment(Expression([InitializationList(vargs)], False))
            )))
            self.do_before(stmt, self)
            self.args.append(self.make(Expression([Number(str(len(vargs)))], False)))
            self.args.append(self.make(
                Expression([CompoundIdentifier([Identifier(0, vargs_name)])], False)
            ))

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
            return self.make(BuiltinType('@any'))
        assert isinstance(self.sym.decl, Declaration)
        if not isinstance(self.sym.decl.typ, FunctionType):
            return self.sym.decl.typ
        return self.sym.decl.typ.ret.typ

    @property
    def decl(self) -> Optional[DeclarationBase]:
        return self.sym.decl

    @property
    def arg_count(self) -> int:
        if self.this_ptr is None:
            return len(self.args)
        return len(self.args) + 1

    @property
    def this_ptr(self) -> Optional['CompoundIdentifier']:
        return self._this_ptr

    @this_ptr.setter
    def this_ptr(self, value: 'CompoundIdentifier') -> None:
        self._this_ptr = self.make(value)


class ArrayAccess(SymbolContainer):
    def __init__(self, child: Symbol, idx: Expression) -> None:
        super().__init__(child)
        self.idx: Expression = idx
        self.idx.parent = self

    def build(self) -> 'ArrayAccess':
        super().build()
        self.idx = self.idx.build()
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

    @property
    def mangled(self) -> str:
        return self.child.mangled


class ControlStructure(FlowScope):
    def __init__(self, pos: int, name: str, cond: Optional[Expression], body: List[Statement]
                 ) -> None:
        super().__init__(pos, body)
        assert cond is not None or name == 'else'
        self.name: str = name
        self.cond: Optional[Expression] = cond
        if self.cond is not None:
            self.cond.parent = self

    def build(self) -> 'ControlStructure':
        super().build()
        if self.cond is not None:
            self.cond = self.cond.build()
        return self


class DoWhileLoop(ControlStructure):
    def __init__(self, pos: int, cond: Expression, body: List[Statement]) -> None:
        super().__init__(pos, 'do while', cond, body)
        self.cond: Expression


class ForDoLoop(ControlStructure):
    def __init__(self, pos: int, initializers: List[Union[VariableDeclaration, VariableAssignment]],
                 actions: List[Union[Expression, VariableAssignment]], cond: Expression,
                 body: List[Statement]) -> None:
        super().__init__(pos, 'for do', cond, body)
        self.cond: Expression
        self.initializers: List[Union[VariableDeclaration, VariableAssignment]] = initializers
        self.actions: List[Union[Expression, VariableAssignment]] = actions
        for node in self.initializers:
            node.parent = self
        for act in self.actions:
            act.parent = self

    def build(self) -> 'ForDoLoop':
        # The condition may use a symbol declared in initializers. In this case, we need to have
        # the declaration actually declared before building the condition.
        self.initializers = [init.build() for init in self.initializers]
        super().build()
        self.actions = [act.build() for act in self.actions]
        for init in self.initializers:
            if isinstance(init, VariableDeclaration) and init.assign is None:
                self.error(init.pos, "uninitialised variable declaration in for do loop")
        return self


class Condition(Node):
    def __init__(self, branches: List[ControlStructure]) -> None:
        super().__init__(0)
        self.branches: List[ControlStructure] = branches
        for branch in self.branches:
            branch.parent = self

    def build(self) -> 'Condition':
        super().build()
        self.branches = [b.build() for b in self.branches]
        return self


class SwitchCase(Node):
    def __init__(self, cases: List['SwitchCaseTest'], body: 'SwitchCaseBody') -> None:
        super().__init__()
        self.cases: List[SwitchCaseTest] = cases
        self.body: SwitchCaseBody = body
        for case in self.cases:
            case.parent = self
        self.body.parent = self

    def build(self) -> 'SwitchCase':
        super().build()
        self.cases = [c.build() for c in self.cases]
        self.body = self.body.build()
        return self


class SwitchCaseTest(Node):
    def __init__(self, test: Optional[Value]) -> None:
        super().__init__()
        self.test: Optional[Value] = test
        if self.test is not None:
            self.test.parent = self

    def build(self) -> 'SwitchCaseTest':
        super().build()
        if self.test is not None:
            self.test = self.test.build()
        return self


class SwitchCaseBody(FlowScope):
    def __init__(self, body: List[Statement], fallthrough: bool) -> None:
        super().__init__(0, body)
        self.fallthrough: bool = fallthrough

    def build(self) -> 'SwitchCaseBody':
        super().build()
        return self


class Return(Node):
    def __init__(self, expr: Optional[Expression] = None) -> None:
        super().__init__()
        self.expr: Optional[Expression] = expr
        if self.expr is not None:
            self.expr.parent = self

    def build(self) -> 'Return':
        super().build()
        if self.expr is not None:
            self.expr = self.expr.build()
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

    def build(self) -> 'Identifier':
        super().build()
        self.ref_offset = self.typ.ref_offset
        return self

    @property
    def typ(self) -> Type:
        if self.decl is None:
            return self.make(BuiltinType('@any'))
        if isinstance(self.decl, Type):
            return self.make(self.decl.dup())
        if isinstance(self.decl, (Declaration, Alias)):
            return self.decl.typ
        return BuiltinType('@any')

    @property
    def decl(self) -> Optional[DeclarationBase]:
        return self._decl

    @decl.setter
    def decl(self, value: Optional[DeclarationBase]) -> None:
        self._decl = value

    @property
    def mangled_name(self) -> str:
        assert isinstance(self.parent, DeclarationBase)
        return self.parent.mangled_name

    @property
    def mangled(self) -> str:
        return '{}{}'.format(len(self.name), self.name)


class CompoundIdentifier(Symbol):
    def __init__(self, elems: List[Identifier]) -> None:
        self.elems: List[Identifier] = elems
        for elem in self.elems:
            elem.parent = self
        super().__init__()

    def build(self) -> 'CompoundIdentifier':
        self._find_children_declarations()
        super().build()
        if isinstance(self.elems[0].decl, ClassProperty):
            self.elems.insert(0, Identifier(0, 'this'))
            decl = self.find_declaration('this')
            if len(decl) == 0:
                self.error(0, decl.error)
            else:
                self.elems[0].decl = decl[0]
        elif isinstance(self.elems[-1].decl, ClassMethod) and isinstance(self.parent, FunctionCall):
            self.parent.this_ptr = CompoundIdentifier(self.elems[:-1])
            self.elems = self.elems[-1:]
        self.elems = [e.build() for e in self.elems]
        return self

    def _find_children_declarations(self) -> None:
        cur_decl: Optional[DeclarationLookup] = None
        for e in self.elems:
            if cur_decl is None:
                cur_decl = self.find_declaration(e.name)
            else:
                cur_decl = cur_decl.get_inner_declaration(e.name)
            if len(cur_decl) == 0:
                self.error(e.pos, cur_decl.error)
                return
            e.decl = cur_decl[0]
        if len(self.elems) >= 2 and isinstance(self.elems[1].decl, VArgsLength):
            self.elems = self.elems[1:]
            self.elems[0].name = '@vargs_len'

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

    @property
    def mangled(self) -> str:
        if self.decl is None:
            return self.elems[-1].name
        return '{}{}'.format(self.qualifiers.mangled, self.decl.mangled)


class TemplatedIdentifier(Symbol):
    def __init__(self, name: str, types: List[Union[Symbol, Type]]) -> None:
        super().__init__()
        self._name: str = name
        self.types: List[Union[Symbol, Type]] = types
        for t in self.types:
            t.parent = self

    def build(self) -> 'TemplatedIdentifier':
        super().build()
        self.types = [t.build() for t in self.types]
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

    @property
    def mangled(self) -> str:
        assert isinstance(self.types[0], Type)
        return 't{}'.format(self.types[0].mangled)


class String(Value):
    def __init__(self, string: str) -> None:
        super().__init__()
        self.string: str = string

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@str'))

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        pass


class Char(Value):
    def __init__(self, char: str) -> None:
        super().__init__()
        self.char: str = char

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@char'))

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        pass


class Number(Value):
    def __init__(self, num: str) -> None:
        super().__init__()
        self.num: str = num

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@int'))

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        pass


class DecimalNumber(Value):
    def __init__(self, num: str) -> None:
        super().__init__()
        self.num: str = num

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@float'))

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        pass


class NullValue(Value):
    def __init__(self) -> None:
        super().__init__()

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@any'))

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        pass


class BoolValue(Value):
    def __init__(self, val: bool) -> None:
        super().__init__()
        self.val: bool = val

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@bool'))

    def auto_cast(self, target: Union[Symbol, Type]) -> None:
        pass


class UnaryOperatorValue(Value):
    def __init__(self, op: str, val: Value) -> None:
        super().__init__()
        self.op: str = op
        self.val: Value = val
        self.val.parent = self

    def build(self) -> 'UnaryOperatorValue':
        super().build()
        self.val = self.val.build()
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


class AnonymousArray(Value):
    def __init__(self, pos: int, contents: List[Value]) -> None:
        super().__init__(pos)
        self.contents = contents
        for node in self.contents:
            node.parent = self

    def build(self) -> Value:
        if self.built:
            return self
        super().build()
        tmp_name = self.generate_var_name()
        self.do_before(Statement(VariableDeclaration(
            Array(CompoundIdentifier([Identifier(0, self.contents[0].typ.name)]), Number('')),
            Identifier(0, tmp_name),
            Assignment(Expression([self], False))
        )), self)
        return self.make(CompoundIdentifier([Identifier(0, tmp_name)]))

    @property
    def typ(self) -> Type:
        if len(self.contents) == 0:
            return ArrayType(BuiltinType('@any'))
        return ArrayType(self.contents[0].typ.dup())


class Sizeof(Value):
    def __init__(self, sz_typ: Symbol) -> None:
        super().__init__()
        self.sz_typ: Symbol = sz_typ
        self.sz_typ.parent = self

    def build(self) -> 'Sizeof':
        super().build()
        self.sz_typ = self.sz_typ.build()
        return self

    @property
    def typ(self) -> Type:
        return self.make(BuiltinType('@size'))


class Alias(Symbol, DeclarationBase):
    def __init__(self, src: Union[Type, Symbol], dst: Identifier) -> None:
        super().__init__()
        DeclarationBase.__init__(self)
        self.src_sym: Union[Type, Symbol] = src
        self.src: Optional[DeclarationBase] = None
        self.dst: Identifier = dst
        self.src_sym.parent = self
        self.dst.parent = self

    def build(self) -> 'Alias':
        self.parent.declare(self)
        self.src_sym = self.src_sym.build()
        if isinstance(self.src_sym, Symbol):
            self.src = self.src_sym.canonical
        else:
            self.src = self.src_sym
        super().build()
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

    @property
    def mangled(self) -> str:
        return 'T{}'.format(self.dst.mangled)


class ContainerStructure(Type, Scope):
    def __init__(self, pos: int, sym: Identifier,
                 fields: Optional[List[VariableDeclaration]]) -> None:
        super().__init__(pos)
        Scope.__init__(self, pos)
        self.sym: Identifier = sym
        self.fields: Optional[List[VariableDeclaration]] = fields
        self.display_name = ''
        self.sym.parent = self
        if self.fields is not None:
            for f in self.fields:
                f.parent = self

    def build(self) -> 'ContainerStructure':
        if self.built:
            return self
        super().build()
        self.parent.declare(self)
        self.sym.build()
        if self.fields is not None:
            self.fields = [f.build() for f in self.fields]
        return self

    @property
    def name(self) -> str:
        return self.sym.name

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        res = DeclarationLookup(sym)
        if self.fields is None:
            res.error = 'accessing incomplete {} {}'.format(self.display_name, self.sym.name)
        else:
            res.find_in(cast(List[Node], self.fields))
        return res

    def from_any(self) -> Symbol:
        return self.make(Reference(CompoundIdentifier([Identifier(0, self.sym.name)])))

    @property
    def mangled(self) -> str:
        if self.declaration_type == DeclarationType.C:
            return self.sym.name
        return '{}{}'.format(self.display_name[0].upper(), self.sym.mangled)

    @property
    def mangled_scope(self) -> str:
        return '{}{}'.format(self.parent.mangled_scope, self.mangled)


class Struct(ContainerStructure):
    def __init__(self, pos: int, sym: Identifier,
                 fields: Optional[List[VariableDeclaration]]) -> None:
        super().__init__(pos, sym, fields)
        self.display_name = 'struct'

    def dup(self) -> Type:
        return self.make(StructType(self))


class EhUnion(ContainerStructure):
    def __init__(self, pos: int, sym: Identifier,
                 fields: Optional[List[VariableDeclaration]]) -> None:
        super().__init__(pos, sym, fields)
        self.display_name = 'union'

    def dup(self) -> Type:
        return self.make(UnionType(self))


class ClassMethod(FunctionDefinition):
    def __init__(self, obj: FunctionDefinition) -> None:
        self.obj: FunctionDefinition = obj

    def build(self) -> 'ClassMethod':
        self.obj.parent = self.parent
        assert isinstance(self.parent, EhClass)
        assert isinstance(self.typ, FunctionType)
        self.typ.args.insert(0, VariableDeclaration(
            Reference(CompoundIdentifier([Identifier(0, self.parent.name)])),
            Identifier(0, 'this'),
            None
        ))
        self.typ.args[0].parent = self
        self.obj = self.obj.build()
        if self.obj.sym is not None:
            self.obj.sym._parent = self
        return self

    def __getattr__(self, attr: Any) -> Any:
        return getattr(self.obj, attr)

    @property
    def mangled(self) -> str:
        if self.sym is None:
            return ''
        if self.sym.name == 'main':
            return self.sym.name
        assert isinstance(self.typ, FunctionType)
        name: str = '{}F{}'.format(self.qualifiers.mangled, self.sym.mangled)
        for a in self.typ.args[1:]:
            name = '{}{}'.format(name, a.typ_src.mangled)
        if self.typ.is_variadic:
            assert self.typ.variadic_type is not None
            name = '{}v{}'.format(name, self.typ.variadic_type.mangled)
        return name


class ClassProperty(VariableDeclaration):
    def __init__(self, obj: VariableDeclaration) -> None:
        self.obj: VariableDeclaration = obj

    def build(self) -> 'ClassProperty':
        self.obj.parent = self.parent
        self.obj = self.obj.build()
        return self

    def __getattr__(self, attr: Any) -> Any:
        return getattr(self.obj, attr)


class EhClass(Type, UnorderedScope):
    FieldList = List[Union[ClassMethod, ClassProperty]]

    def __init__(self, pos: int, sym: Identifier, contents: Optional['EhClass.FieldList']) -> None:
        super(Type, self).__init__(pos)
        super(UnorderedScope, self).__init__(pos)
        self.sym: Identifier = sym
        self.contents: Optional[EhClass.FieldList] = contents
        self.sym.parent = self
        if self.contents is not None:
            for node in self.contents:
                node.parent = self
        self._properties: List[ClassProperty] = []
        self._methods: List[ClassMethod] = []

    def build(self) -> 'EhClass':
        if self.built:
            return self
        super().build()
        self.parent.declare(self)
        self.sym.build()
        if self.contents is not None:
            self.contents = [f.build() for f in self.contents]
            for node in self.contents:
                if isinstance(node, ClassProperty):
                    self._properties.append(node)
                else:
                    self._methods.append(node)
        return self

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        res = DeclarationLookup(sym)
        if self.contents is None:
            res.error = 'accessing incomplete class `{}`'.format(self.sym.name)
        else:
            res.find_in(cast(List[Node], self.contents))
        return res

    def from_any(self) -> Symbol:
        return self.make(Reference(CompoundIdentifier([Identifier(0, self.sym.name)])))

    def dup(self) -> Type:
        return ClassType(self)

    @property
    def scope_contents(self) -> List[Node]:
        return cast(List[Node], self.contents)

    @property
    def name(self) -> str:
        return self.sym.name

    @property
    def mangled(self) -> str:
        return 'C{}'.format(self.sym.mangled)

    @property
    def mangled_scope(self) -> str:
        return '{}{}'.format(self.parent.mangled_scope, self.mangled)

    @property
    def properties(self) -> List[ClassProperty]:
        return self._properties

    @property
    def methods(self) -> List[ClassMethod]:
        return self._methods


class ContainerStructureType(Type):
    def __init__(self, decl: Union[ContainerStructure, EhClass]) -> None:
        super().__init__()
        self._decl: Union[ContainerStructure, EhClass] = decl

    def from_any(self) -> Symbol:
        return self._decl.from_any()

    @property
    def decl(self) -> Optional[DeclarationBase]:
        return self._decl

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        return self._decl.get_inner_declaration(sym)

    def dup(self) -> Type:
        return self._decl.dup()

    @property
    def mangled(self) -> str:
        return self._decl.mangled

    @property
    def name(self) -> str:
        return self._decl.name


class StructType(ContainerStructureType):
    pass


class UnionType(ContainerStructureType):
    pass


class ClassType(ContainerStructureType):
    pass


class EhEnum(Type, Scope):
    def __init__(self, pos: int, sym: Identifier, fields: Optional[List[Identifier]]) -> None:
        super().__init__(pos)
        Scope.__init__(self, pos)
        self.sym: Identifier = sym
        self.sym.parent = self
        self.fields: Optional[List[EnumField]] = None
        if fields is not None:
            self.fields = [EnumField(f, self) for f in fields]

    def build(self) -> 'EhEnum':
        super().build()
        self.sym = self.sym.build()
        if self.fields is not None:
            self.fields = [f.build() for f in self.fields]
        return self

    @property
    def mangled(self) -> str:
        if self.declaration_type == DeclarationType.C:
            return self.sym.name
        return 'N{}'.format(self.sym.mangled)

    @property
    def mangled_scope(self) -> str:
        return '{}{}'.format(self.parent.mangled_scope, self.mangled)

    def from_any(self) -> Symbol:
        return self.make(Reference(CompoundIdentifier([Identifier(0, self.sym.name)])))

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        res = DeclarationLookup(sym)
        if self.fields is None:
            res.error = 'accessing incomplete enum {}'.format(self.sym.name)
        else:
            for f in self.fields:
                if f.name == sym:
                    res.append(f)
        return res

    @property
    def name(self) -> str:
        return self.sym.name

    def dup(self) -> Type:
        return EhEnum(self.pos, self.sym, None)

    def find_declaration(self, sym: str) -> DeclarationLookup:
        res = DeclarationLookup(sym)
        if sym == self.name:
            res.append(self)
        res.merge(super().find_declaration(sym))
        return res


class EnumField(Declaration):
    def __init__(self, sym: Identifier, parent: EhEnum) -> None:
        super().__init__(sym.pos, CompoundIdentifier([Identifier(0, parent.name)]), sym,
                         Qualifier.NONE)
        self.parent = parent

    def build(self) -> 'EnumField':
        super().build()
        return self

    def _make_type(self) -> None:
        assert isinstance(self.parent, EhEnum)
        self._typ = self.parent

    @property
    def mangled(self) -> str:
        if self.sym is None:
            return ''
        if self.declaration_type == DeclarationType.C:
            return self.sym.name
        return self.sym.mangled


class Namespace(DeclarationBase, UnorderedScope):
    def __init__(self, pos: int, sym: Identifier) -> None:
        super().__init__(pos)
        super(UnorderedScope, self).__init__(pos)
        self.sym: Identifier = sym
        self.sym.parent = self
        self._contents: List[Node] = []

    def build(self) -> 'Namespace':
        super().build()
        self._contents = [stmt.build() for stmt in self._contents]
        return self

    @property
    def scope_contents(self) -> List[Node]:
        return self._contents

    def find_declaration(self, sym: str) -> DeclarationLookup:
        res: DeclarationLookup = DeclarationLookup(sym)
        ns: DeclarationLookup = super().find_declaration(self.name)
        res.merge(ns.get_inner_declaration(sym))
        res.merge(super().find_declaration(sym))
        return res

    def get_inner_declaration(self, sym: str) -> DeclarationLookup:
        return DeclarationLookup(sym, self._contents)

    @property
    def name(self) -> str:
        return self.sym.name

    @property
    def mangled(self) -> str:
        return 'N{}'.format(self.sym.mangled)

    @property
    def mangled_scope(self) -> str:
        return '{}N{}'.format(self.parent.mangled_scope, self.sym.mangled)

    @property
    def contents(self) -> List[Node]:
        return self._contents

    @contents.setter
    def contents(self, contents: List[Node]) -> None:
        self._contents = contents
        for node in self._contents:
            node.parent = self


class AST(UnorderedScope):
    def __init__(self, nodes: List[Node]) -> None:
        super().__init__(0)
        self.nodes: List[Node] = nodes
        for node in self.nodes:
            node.parent = self
        self.failures: List[Failure] = []
        self.parser: Optional[ParserPython] = None
        self.gen_var_count: int = 0

    def __iter__(self) -> Iterator[Node]:
        return self.nodes.__iter__()

    def __getitem__(self, key: int) -> Node:
        return self.nodes[key]

    def __len__(self) -> int:
        return len(self.nodes)

    def build(self) -> Node:
        raise Exception('AST.build may not be called')

    def build_ast(self, args: OptionsStruct) -> None:
        global imported
        global included
        imported = included = []
        super().build()
        self.declarations: List[DeclarationBase] = [
            FunctionType(CompoundIdentifier([Identifier(0, '@any')]), []),
            BuiltinType('@int'), BuiltinType('@int8'), BuiltinType('@int16'), BuiltinType('@int32'),
            BuiltinType('@int64'), BuiltinType('@uint'), BuiltinType('@uint8'),
            BuiltinType('@uint16'), BuiltinType('@uint32'), BuiltinType('@uint64'),
            BuiltinType('@float'), BuiltinType('@double'), BuiltinType('@decimal'),
            BuiltinType('@void'), BuiltinType('@bool'), BuiltinType('@char'), BuiltinType('@size'),
            BuiltinType('@str'), BuiltinType('@any'),
        ]
        self.declarations = [self.make(decl) for decl in self.declarations]
        self._import_paths = [
            path.dirname(args.source),
            getcwd(),
            path.dirname(args.output_import_file)]

        self.nodes = [n.build() for n in self.nodes]
        if len(self.failures) != 0:
            raise ParseError(self.failures, self.parser)

    def fail(self, severity: ParseError.Severity, pos: int, msg: str) -> None:
        assert self.parser is not None
        self.failures.append(Failure(severity, pos, msg, self.parser.file_name))

    @property
    def scope_contents(self) -> List[Node]:
        return self.nodes

    def find_declaration(self, sym: str) -> DeclarationLookup:
        res: DeclarationLookup = DeclarationLookup(sym, self.nodes)
        for decl in self.declarations:
            found = decl.get_declaration(sym)
            if len(found) > 0:
                for f in found:
                    if isinstance(f, Type):
                        res.append(self.make(f.dup()))
                    else:
                        res.append(f)
            else:
                res.merge(found)
        return res

    @property
    def import_paths(self) -> List[str]:
        return self._import_paths

    def is_child_of(self, cls: typing.Type[Node]) -> bool:
        return False

    def generate_var_name(self) -> str:
        self.gen_var_count += 1
        return '__gen_ast_{}'.format(self.gen_var_count)

    @property
    def mangled_scope(self) -> str:
        return '_E'


from ehlit.parser import source
from ehlit.parser import function
from ehlit.parser import c_header
