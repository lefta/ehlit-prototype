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
from typing import cast, Dict, Optional, Sequence, TextIO
import typing
from ehlit.parser.ast import (
    Alias, Array, ArrayType, ArrayAccess, Assignment, AST, BoolValue, BuiltinType, Cast, Char,
    CompoundIdentifier, Condition, ContainerStructure, ControlStructure, Container, Declaration,
    DeclarationBase, EhUnion, Expression, FunctionCall, FunctionDeclaration, FunctionDefinition,
    FunctionType, Identifier, Import, Include, Node, NullValue, Number, Operator,
    PrefixOperatorValue, ReferenceToType, ReferenceToValue, ReferenceType, Return, Sizeof,
    Statement, String, Struct, SuffixOperatorValue, SwitchCase, SwitchCaseBody, SwitchCaseTest,
    Symbol, TemplatedIdentifier, Type, VariableAssignment, VariableDeclaration, Value
)


class SourceWriter:
    def __init__(self, ast: AST, f: str) -> None:
        self.file: TextIO = sys.stdout if f == '-' else open(f, 'w')

        self.indent: int = 0
        self.in_import: int = 0
        self.types: Dict[str, str] = {
            '@str': 'char*',
            '@any': 'void*',
            '@void': 'void',
            '@char': 'int8_t',
            '@int': 'int32_t',
            '@int8': 'int8_t',
            '@int16': 'int16_t',
            '@int32': 'int32_t',
            '@int64': 'int64_t',
            '@uint8': 'uint8_t',
            '@uint16': 'uint16_t',
            '@uint32': 'uint32_t',
            '@uint64': 'uint64_t',
            '@size': 'size_t',
            '@bool': 'uint8_t',
        }

        self.control_structures: Dict[str, str] = {
            'if': 'if',
            'elif': 'else if',
            'else': 'else',
            'while': 'while',
            'switch': 'switch',
        }

        self.file.write('#include <stddef.h>\n#include <stdint.h>\n')

        for node in ast:
            self.write(node)

        if f != '-':
            self.file.close()

    def write(self, node: Node) -> None:
        func = getattr(self, 'write' + type(node).__name__)
        func(node)

    def write_indent(self) -> None:
        i: int = 0
        while i < self.indent:
            self.file.write('    ')
            i += 1

    def write_value(self, node: Value) -> None:
        decl: Optional[DeclarationBase] = node.decl
        if isinstance(decl, Alias):
            decl = decl.canonical
        if isinstance(decl, FunctionDeclaration) and not isinstance(node, FunctionCall):
            parent: Node = node.parent
            while (type(parent) is ReferenceToValue or type(parent) is CompoundIdentifier):
                parent = parent.parent
            if type(parent) is not FunctionCall:
                self.file.write('&')
                return
        if node.ref_offset == -1:
            self.file.write('&')
        else:
            i: int = node.ref_offset
            while i > 0:
                self.file.write('*')
                i -= 1
        if node.cast is not None:
            self.file.write('(')
            self.write_type_prefix(node.cast)
            self.write(node.cast)
            self.file.write(')')

    def writeInclude(self, inc: Include) -> None:
        self.write_indent()
        self.file.write('#include <')
        self.file.write(inc.lib)
        self.file.write('>\n')

    def writeImport(self, node: Import) -> None:
        self.in_import += 1
        for sym in node.syms:
            self.write(sym)
        self.in_import -= 1

    def writeReferenceToType(self, ref: ReferenceToType) -> None:
        self.write(ref.child)
        self.file.write('*')
        if ref.is_const:
            self.file.write(' const')

    def writeReferenceToValue(self, ref: ReferenceToValue) -> None:
        self.write(ref.child)

    def writeArray(self, arr: Array) -> None:
        self.write(arr.child)
        if arr.length is None:
            self.file.write('*')
        if self.array_needs_parens(arr):
            self.file.write('(')

    def is_dynamic_array(self, node: Node) -> bool:
        return ((isinstance(node, Array) and node.length is None) or
                isinstance(node, ReferenceToType))

    def array_needs_parens(self, node: Node) -> bool:
        if self.is_dynamic_array(node):
            return False
        if not isinstance(node.parent, Container):
            return False
        return self.is_dynamic_array(node.parent)

    def write_declaration_post(self, node: Symbol) -> None:
        if isinstance(node, TemplatedIdentifier) and node.name == '@func':
            self.file.write(')(')
            i: int = 0
            assert isinstance(node.typ, FunctionType)
            while i < len(node.typ.args):
                if i is not 0:
                    self.file.write(', ')
                self.write(node.typ.args[i])
                i += 1
            self.file.write(')')
        elif isinstance(node, Container):
            if self.array_needs_parens(node):
                self.file.write(')')
            if isinstance(node, Array) and node.length is not None:
                self.file.write('[')
                self.write(node.length)
                self.file.write(']')
            self.write_declaration_post(node.child)

    def writeFunctionType(self, node: FunctionType) -> None:
        self.write_type_prefix(node.ret)
        self.write(node.ret)
        self.file.write('(*')

    def write_type_prefix(self, node: Symbol) -> None:
        if isinstance(node, Container):
            node = node.inner_child
        typ: Type = node.typ
        prefix_mapping: Dict[typing.Type[Type], str] = {
            Struct: 'struct',
            EhUnion: 'union',
        }
        prefix = prefix_mapping.get(type(typ))
        if prefix is not None:
            self.file.write(prefix + ' ')

    def write_type_suffix(self, node: Symbol) -> None:
        if node.is_const:
            self.file.write(' const')

    def writeDeclaration(self, decl: Declaration) -> None:
        self.write_type_prefix(decl.typ_src)
        self.write(decl.typ_src)
        if decl.sym is not None:
            self.file.write(' ')
            self.write(decl.sym)
        self.write_declaration_post(decl.typ_src)

    def writeVariableDeclaration(self, decl: VariableDeclaration) -> None:
        self.writeDeclaration(decl)
        if decl.assign is not None:
            self.write(decl.assign)

    def writeArgumentDefinitionList(self, args: Sequence[VariableDeclaration]) -> None:
        if len(args) == 0:
            self.file.write('void')
        else:
            i: int = 0
            count: int = len(args)
            while i < count:
                self.writeDeclaration(args[i])
                i += 1
                if i < count:
                    self.file.write(', ')

    def writeFunctionPrototype(self, proto: FunctionDeclaration) -> None:
        assert isinstance(proto.typ, FunctionType)
        self.write_type_prefix(proto.typ.ret)
        self.write(proto.typ.ret)
        self.file.write(' ')
        if proto.sym is not None:
            self.write(proto.sym)
        self.file.write('(')
        self.writeArgumentDefinitionList(proto.typ.args)
        self.file.write(")")

    def writeFunctionDeclaration(self, fun: FunctionDeclaration) -> None:
        self.write_indent()
        self.writeFunctionPrototype(fun)
        self.file.write(';\n')

    def writeFunctionDefinition(self, fun: FunctionDefinition) -> None:
        if self.in_import > 0:
            self.writeFunctionDeclaration(fun)
            return

        if len(fun.predeclarations) is not 0:
            self.file.write('\n')
        for decl in fun.predeclarations:
            # It is possible that we get the definition of the function, but we only want to write
            # its prototype. For all other declaration types, we can write it as is.
            if isinstance(decl, FunctionDefinition):
                self.writeFunctionDeclaration(decl)
            else:
                self.write(decl)

        self.write_indent()
        self.file.write("\n")
        self.writeFunctionPrototype(fun)
        self.file.write("\n{\n")

        self.indent += 1
        for instruction in fun.body:
            self.write(instruction)
        self.indent -= 1

        self.file.write("}\n")

    def writeStatement(self, stmt: Statement) -> None:
        self.write_indent()
        self.write(stmt.expr)
        self.file.write(';\n')

    def writeExpression(self, expr: Expression) -> None:
        if expr.is_parenthesised:
            self.file.write('(')
        i: int = 0
        count: int = len(expr.contents)
        while i < count:
            self.write(expr.contents[i])
            i += 1
            if i < count:
                self.file.write(' ')
        if expr.is_parenthesised:
            self.file.write(')')

    def writeAssignment(self, assign: Assignment) -> None:
        self.file.write(' ')
        if assign.operator is not None:
            self.write(assign.operator)
        self.file.write('= ')
        self.write(assign.expr)

    def writeVariableAssignment(self, assign: VariableAssignment) -> None:
        self.write(assign.var)
        self.write(assign.assign)

    def writeCast(self, node: Cast) -> None:
        self.file.write('((')
        self.write_type_prefix(node.sym)
        self.write(node.sym)
        self.file.write(')')
        self.write(node.args[0])
        self.file.write(')')

    def writeFunctionCall(self, call: FunctionCall) -> None:
        self.write_value(call)
        self.write(call.sym)
        self.file.write('(')
        i: int = 0
        count: int = len(call.args)
        while i < count:
            self.write(call.args[i])
            i += 1
            if i < count:
                self.file.write(', ')
        self.file.write(')')

    def writeArrayAccess(self, arr: ArrayAccess) -> None:
        self.write_value(arr)
        assert isinstance(arr.decl, Type) or isinstance(arr.decl, Declaration)
        decl: Node = arr.decl if isinstance(arr.decl, Type) else arr.decl.typ
        sym: Symbol = arr
        while type(decl) is ArrayType or type(decl) is ReferenceType or BuiltinType('@str') == decl:
            if isinstance(sym, ArrayAccess):
                sym = sym.child
            decl = cast(Type, cast(Container, decl).child)
        cur = sym.parent
        assert isinstance(decl.parent, Type)
        decl = decl.parent
        while type(decl) is ArrayType or type(decl) is ReferenceType or BuiltinType('@str') == decl:
            if type(decl) is ReferenceType:
                rdecl: Node = decl
                while type(rdecl) is ReferenceType:
                    rdecl = rdecl.parent
                if type(rdecl) is ArrayType:
                    self.file.write('*')
            elif type(cur) is ArrayAccess:
                if type(decl.parent) is ReferenceType:
                    self.file.write('(')
                cur = cur.parent
            decl = decl.parent
        self.write(sym)
        decl = arr.decl if isinstance(arr.decl, Type) else arr.decl.typ
        while isinstance(decl, ReferenceType):
            decl = decl.child
        sym = arr
        while isinstance(sym, ArrayAccess) or isinstance(decl, ReferenceType):
            if type(decl) is not ReferenceType and isinstance(sym, ArrayAccess):
                if type(decl.parent) is ReferenceType:
                    self.file.write(')')
                self.file.write('[')
                self.write(sym.idx)
                self.file.write(']')
                sym = sym.child
            decl = cast(Container, decl).child

    def writeControlStructure(self, struct: ControlStructure) -> None:
        self.write_indent()
        self.file.write(self.control_structures[struct.name])
        if struct.cond is not None:
            self.file.write(' (')
            self.write(struct.cond)
            self.file.write(')')
        self.file.write('\n')

        self.write_indent()
        self.file.write('{\n')
        self.indent += 1
        for instruction in struct.body:
            self.write(instruction)
        self.indent -= 1

        self.write_indent()
        self.file.write('}\n')

    def writeCondition(self, cond: Condition) -> None:
        for branch in cond.branches:
            self.write(branch)

    def writeSwitchCase(self, node: SwitchCase) -> None:
        self.indent -= 1
        for c in node.cases:
            self.write(c)
        self.write(node.body)
        self.indent += 1

    def writeSwitchCaseTest(self, node: SwitchCaseTest) -> None:
        self.write_indent()
        if node.test is None:
            self.file.write('default:\n')
        else:
            self.file.write('case ')
            self.write(node.test)
            self.file.write(':\n')

    def writeSwitchCaseBody(self, node: SwitchCaseBody) -> None:
        if node.block:
            self.write_indent()
            self.file.write('{\n')
        self.indent += 1
        for i in node.contents:
            self.write(i)
        if not node.fallthrough:
            self.write_indent()
            self.file.write('break;\n')
        self.indent -= 1
        if node.block:
            self.write_indent()
            self.file.write('}\n')

    def writeReturn(self, ret: Return) -> None:
        self.file.write('return')
        if ret.expr is not None:
            self.file.write(' (')
            self.write(ret.expr)
            self.file.write(')')

    def writeOperator(self, op: Operator) -> None:
        self.file.write(op.op)

    def writeCompoundIdentifier(self, node: CompoundIdentifier) -> None:
        self.write_value(node)
        i: int = 0
        while i < len(node.elems):
            if i < len(node.elems) - 1:
                ref_offset: int = node.elems[i].ref_offset
                if ref_offset is 0:
                    self.write(node.elems[i])
                    self.file.write('.')
                elif ref_offset is 1:
                    self.write(node.elems[i])
                    self.file.write('->')
                else:
                    self.file.write('(')
                    while ref_offset > 1:
                        self.file.write('*')
                        ref_offset -= 1
                    self.write(node.elems[i])
                    self.file.write(')->')
            else:
                self.write(node.elems[i])
            i += 1
        if node.is_type:
            self.write_type_suffix(node)

    def writeIdentifier(self, node: Identifier) -> None:
        if isinstance(node.decl, Alias) and node.decl.is_type:
            self.file.write(node.decl.dst.name)
            return

        decl: Optional[DeclarationBase] = node.decl
        if isinstance(decl, Symbol):
            decl = decl.canonical
        if decl is not None:
            if isinstance(decl, BuiltinType):
                self.file.write(self.types[decl.name])
            else:
                self.file.write(decl.name)
        else:
            self.file.write(node.name)

    def writeTemplatedIdentifier(self, node: TemplatedIdentifier) -> None:
        self.write(node.typ)

    def writeChar(self, c: Char) -> None:
        self.file.write('\'')
        self.file.write(c.char)
        self.file.write('\'')

    def writeString(self, s: String) -> None:
        self.file.write('"')
        self.file.write(s.string)
        self.file.write('"')

    def writeNumber(self, num: Number) -> None:
        self.file.write(num.num)

    def writeNullValue(self, stmt: NullValue) -> None:
        self.file.write('NULL')

    def writeBoolValue(self, node: BoolValue) -> None:
        self.file.write('0' if node.val is False else '!0')

    def writePrefixOperatorValue(self, val: PrefixOperatorValue) -> None:
        self.file.write(val.op)
        self.write(val.val)

    def writeSuffixOperatorValue(self, val: SuffixOperatorValue) -> None:
        if val.val.ref_offset is not 0:
            self.file.write('(')
        self.write(val.val)
        if val.val.ref_offset is not 0:
            self.file.write(')')
        self.file.write(val.op)

    def writeSizeof(self, node: Sizeof) -> None:
        self.file.write('sizeof(')
        self.write_type_prefix(node.sz_typ)
        self.write(node.sz_typ)
        self.file.write(')')

    def writeAlias(self, node: Alias) -> None:
        if isinstance(node.src, Type):
            self.file.write('typedef ')
            self.write(node.src_sym)
            self.file.write(' ')
            self.write(node.dst)
            if isinstance(node.src_sym, Symbol):
                self.write_declaration_post(node.src_sym)
            self.file.write(';\n')

    def writeContainerStructure(self, node: ContainerStructure) -> None:
        self.write(node.sym)
        if node.fields is not None:
            self.file.write('\n{\n')
            self.indent += 1
            for f in node.fields:
                self.write_indent()
                self.write(f)
                self.file.write(';\n')
            self.indent -= 1
            self.file.write('}')
        self.file.write(';\n')

    def writeStruct(self, node: Struct) -> None:
        self.file.write('\nstruct ')
        self.writeContainerStructure(node)

    def writeEhUnion(self, node: EhUnion) -> None:
        self.file.write('\nunion ')
        self.writeContainerStructure(node)
