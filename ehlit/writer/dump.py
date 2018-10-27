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

import logging
from typing import Callable, cast, Sequence, Union
from ehlit.parser.ast import (
    Alias, Array, ArrayAccess, Assignment, AST, BoolValue, Cast, Char, CompoundIdentifier,
    Condition, ControlStructure, DecimalNumber, Declaration, EhUnion, Expression, FunctionCall,
    FunctionDeclaration, FunctionDefinition, FunctionType, Identifier, Include, Import, Node,
    NullValue, Number, Operator, PrefixOperatorValue, ReferenceToType, ReferenceToValue, Return,
    Sizeof, Statement, String, Struct, SuffixOperatorValue, SwitchCase, SwitchCaseBody,
    SwitchCaseTest, TemplatedIdentifier, VariableAssignment, VariableDeclaration
)

IndentedFnType = Callable[['DumpWriter', Union[Node, str]], None]


def indent(fn: IndentedFnType) -> Callable[..., None]:
    def fn_wrapper(cls: 'DumpWriter', node: Union[Node, str], is_next: bool = True) -> None:
        cls.increment_prefix(is_next)
        fn(cls, node)
        cls.decrement_prefix()
    return fn_wrapper


class DumpWriter:
    def __init__(self, ast: AST) -> None:
        self.prefix: str = ''
        logging.debug('')
        logging.debug('--- AST ---')
        i: int = 0
        count: int = len(ast)
        self.prev_have_next: bool = count > 1
        self.upd_prefix: bool = False
        while i < count:
            self.print_node(ast[i], i < count - 1)
            i += 1

    def dump(self, string: str) -> None:
        logging.debug('%s%s', self.prefix, string)

    def decrement_prefix(self) -> None:
        self.prefix = self.prefix[:-3]
        self.upd_prefix = False

    def increment_prefix(self, is_next: bool) -> None:
        if self.upd_prefix:
            self.prefix = self.prefix[:-3]
            if self.prev_have_next:
                self.prefix += '\u2502  '
            else:
                self.prefix += '   '
            self.upd_prefix = False

        self.prev_have_next = is_next
        if is_next:
            self.prefix += '\u251c' + '\u2500 '
        else:
            self.prefix += '\u2514' + '\u2500 '
        self.upd_prefix = True

    def print_node(self, node: Node, is_next: bool = True) -> None:
        func = getattr(self, 'dump' + type(node).__name__)
        func(node, is_next)

    def print_node_list(self, string: str, lst: Sequence[Node], is_next: bool = True) -> None:
        self.increment_prefix(is_next)
        self.dump(string)
        i: int = 0
        cnt: int = len(lst)
        while i < cnt:
            self.print_node(lst[i], i < cnt - 1)
            i += 1
        self.decrement_prefix()

    @indent
    def print_str(self, s: Union[Node, str]) -> None:
        s = cast(str, s)
        self.dump(s)

    @indent
    def dumpInclude(self, inc: Union[Node, str]) -> None:
        inc = cast(Include, inc)
        self.dump('Include')
        self.print_str('Path: {}'.format(inc.lib))
        self.print_node_list('Symbols found', inc.syms, False)

    @indent
    def dumpImport(self, node: Union[Node, str]) -> None:
        node = cast(Import, node)
        self.dump('Import')
        self.print_str('Path: {}'.format(node.lib))
        self.print_node_list('Symbols found', node.syms, False)

    @indent
    def dumpDeclaration(self, decl: Union[Node, str]) -> None:
        decl = cast(Declaration, decl)
        self.dump('Declaration')
        self.print_node(decl.typ_src, decl.sym is not None)
        if decl.sym is not None:
            self.print_node(decl.sym, False)

    @indent
    def dumpVariableDeclaration(self, decl: Union[Node, str]) -> None:
        decl = cast(VariableDeclaration, decl)
        self.dump('VariableDeclaration')
        if decl.assign is not None:
            self.dumpDeclaration(decl)
            self.print_node(decl.assign, False)
        else:
            self.dumpDeclaration(decl, False)

    @indent
    def dumpFunctionDeclaration(self, fun: Union[Node, str]) -> None:
        fun = cast(FunctionDeclaration, fun)
        self.dump('FunctionDeclaration')
        if fun.sym is not None:
            self.print_node(fun.sym)
        self.print_node(fun.typ, False)

    @indent
    def dumpFunctionDefinition(self, fun: Union[Node, str]) -> None:
        fun = cast(FunctionDefinition, fun)
        self.dump('FunctionDefinition')
        self.dumpFunctionDeclaration(fun)
        self.print_node_list('FunctionBody', fun.body, False)

    @indent
    def dumpStatement(self, stmt: Union[Node, str]) -> None:
        stmt = cast(Statement, stmt)
        self.dump('Statement')
        self.print_node(stmt.expr, False)

    def dumpExpression(self, expr: Union[Node, str], is_next: bool) -> None:
        expr = cast(Expression, expr)
        self.print_node_list('Expression', expr.contents, is_next)

    @indent
    def dumpCast(self, node: Union[Node, str]) -> None:
        node = cast(Cast, node)
        self.dump('Cast')
        self.print_node(node.sym)
        self.print_node(node.args[0], False)

    @indent
    def dumpFunctionCall(self, call: Union[Node, str]) -> None:
        call = cast(FunctionCall, call)
        self.dump('FunctionCall')
        self.print_node(call.sym)
        if call.cast:
            self.increment_prefix(True)
            self.dump('Automatic cast')
            self.print_node(call.cast, False)
            self.decrement_prefix()
        self.print_node_list('Arguments', call.args, False)

    @indent
    def dumpArrayAccess(self, arr: Union[Node, str]) -> None:
        arr = cast(ArrayAccess, arr)
        self.dump('ArrayAccess')
        self.print_node(arr.idx)
        self.print_node(arr.child, False)

    @indent
    def dumpVariableAssignment(self, assign: Union[Node, str]) -> None:
        assign = cast(VariableAssignment, assign)
        self.dump('VariableAssignment')
        self.print_node(assign.var)
        self.print_node(assign.assign, False)

    @indent
    def dumpAssignment(self, assign: Union[Node, str]) -> None:
        assign = cast(Assignment, assign)
        self.dump('Assignment')
        if assign.operator is not None:
            self.print_node(assign.operator)
        self.print_node(assign.expr, False)

    @indent
    def dumpControlStructure(self, struct: Union[Node, str]) -> None:
        struct = cast(ControlStructure, struct)
        self.dump('ControlStructure: ' + struct.name)
        if struct.cond is not None:
            self.print_node(struct.cond)
        self.print_node_list("ControlStructureBody", struct.body, False)

    def dumpCondition(self, cond: Union[Node, str], is_next: bool) -> None:
        cond = cast(Condition, cond)
        self.print_node_list("ConditionBranches", cond.branches, is_next)

    @indent
    def dumpSwitchCase(self, node: Union[Node, str]) -> None:
        node = cast(SwitchCase, node)
        self.dump('Case')
        self.print_node_list('Tests', node.cases)
        self.print_node(node.body, False)

    def dumpSwitchCaseTest(self, node: Union[Node, str], is_next: bool) -> None:
        node = cast(SwitchCaseTest, node)
        if node.test is not None:
            self.print_node(node.test, is_next)
        else:
            self.print_str('default', is_next)

    def dumpSwitchCaseBody(self, node: Union[Node, str], _: bool) -> None:
        node = cast(SwitchCaseBody, node)
        self.print_str('Falls through: ' + ('yes' if node.fallthrough else 'no'))
        self.print_node_list('Body', node.contents, False)

    @indent
    def dumpReturn(self, ret: Union[Node, str]) -> None:
        ret = cast(Return, ret)
        self.dump('Return')
        if ret.expr is not None:
            self.print_node(ret.expr, False)

    @indent
    def dumpReferenceToType(self, ref: Union[Node, str]) -> None:
        ref = cast(ReferenceToType, ref)
        self.dump('Reference')
        if ref.is_const:
            self.print_str('Modifiers: const')
        self.print_node(ref.child, False)

    @indent
    def dumpReferenceToValue(self, ref: Union[Node, str]) -> None:
        ref = cast(ReferenceToValue, ref)
        self.dump('Reference')
        self.print_node(ref.child, False)

    @indent
    def dumpOperator(self, op: Union[Node, str]) -> None:
        op = cast(Operator, op)
        self.dump('Operator: ' + op.op)

    @indent
    def dumpArray(self, arr: Union[Node, str]) -> None:
        arr = cast(Array, arr)
        self.dump('Array')
        if arr.length is not None:
            self.print_str('Sub-type:')
            self.increment_prefix(True)
        self.print_node(arr.child, False)
        if arr.length is not None:
            self.decrement_prefix()
            self.print_str('Length:', False)
            self.increment_prefix(False)
            self.print_node(arr.length, False)
            self.decrement_prefix()

    @indent
    def dumpFunctionType(self, node: Union[Node, str]) -> None:
        node = cast(FunctionType, node)
        self.dump('FunctionType')
        self.print_node(node.ret, len(node.args) is not 0)
        if len(node.args) is not 0:
            self.print_node_list('Arguments:', node.args, False)

    def dumpCompoundIdentifier(self, node: Union[Node, str], is_next: bool) -> None:
        node = cast(CompoundIdentifier, node)
        if node.is_type and node.is_const:
            self.increment_prefix(is_next)
            self.dump('CompoundIdentifier')
            self.print_str('Modifiers: const')
            i = 0
            while i < len(node.elems):
                self.print_node(node.elems[i], i < len(node.elems) - 1)
                i += 1
            self.decrement_prefix()
        else:
            self.print_node_list('CompoundIdentifier', node.elems, is_next)

    @indent
    def dumpIdentifier(self, node: Union[Node, str]) -> None:
        node = cast(Identifier, node)
        self.dump('Identifier: ' + node.name)

    @indent
    def dumpTemplatedIdentifier(self, node: Union[Node, str]) -> None:
        node = cast(TemplatedIdentifier, node)
        self.dump('TemplatedIdentifier: ' + node.name)
        self.print_node_list('Types', node.types, False)

    @indent
    def dumpNumber(self, num: Union[Node, str]) -> None:
        num = cast(Number, num)
        self.dump('Number: ' + num.num)

    @indent
    def dumpDecimalNumber(self, node: Union[Node, str]) -> None:
        node = cast(DecimalNumber, node)
        self.dump('DecimalNumber: ' + node.num)

    @indent
    def dumpChar(self, char: Union[Node, str]) -> None:
        char = cast(Char, char)
        self.dump('Character: ' + char.char)

    @indent
    def dumpString(self, string: Union[Node, str]) -> None:
        string = cast(String, string)
        self.dump('String: ' + string.string)

    @indent
    def dumpNullValue(self, stmt: Union[Node, str]) -> None:
        stmt = cast(NullValue, stmt)
        self.dump('NullValue')

    @indent
    def dumpBoolValue(self, node: Union[Node, str]) -> None:
        node = cast(BoolValue, node)
        self.dump('BoolValue: ' + 'true' if node.val is True else 'false')

    @indent
    def dumpPrefixOperatorValue(self, val: Union[Node, str]) -> None:
        val = cast(PrefixOperatorValue, val)
        self.dump('PrefixOperatorValue')
        self.print_str('Operator: %s' % val.op)
        self.print_node(val.val, False)

    @indent
    def dumpSuffixOperatorValue(self, val: Union[Node, str]) -> None:
        val = cast(SuffixOperatorValue, val)
        self.dump('SuffixOperatorValue')
        self.print_str('Operator: %s' % val.op)
        self.print_node(val.val, False)

    @indent
    def dumpSizeof(self, node: Union[Node, str]) -> None:
        node = cast(Sizeof, node)
        self.dump('Sizeof')
        self.print_node(node.sz_typ, False)

    @indent
    def dumpAlias(self, node: Union[Node, str]) -> None:
        node = cast(Alias, node)
        self.dump('Alias')
        self.print_str('From:')
        self.increment_prefix(True)
        self.print_node(node.src_sym, False)
        self.decrement_prefix()
        self.print_str('To:', False)
        self.increment_prefix(False)
        self.print_node(node.dst, False)
        self.decrement_prefix()

    @indent
    def dumpStruct(self, node: Union[Node, str]) -> None:
        node = cast(Struct, node)
        self.dump('Struct')
        self.print_node(node.sym)
        if node.fields is None:
            self.print_str('Forward declaration')
        else:
            self.print_node_list('Fields', node.fields, False)

    @indent
    def dumpEhUnion(self, node: Union[Node, str]) -> None:
        node = cast(EhUnion, node)
        self.dump('Union')
        self.print_node(node.sym)
        if node.fields is None:
            self.print_str('Forward declaration')
        else:
            self.print_node_list('Fields', node.fields, False)
