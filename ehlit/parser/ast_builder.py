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

from arpeggio import ParseTreeNode, PTNodeVisitor, RegExMatch, StrMatch
from typing import List, Optional, Tuple, Union

from ehlit.parser import ast


class ArrayBuilder:
    def __init__(self, child: Optional[Union[ast.Symbol, 'ArrayBuilder']],
                 param: Optional[ast.Node]) -> None:
        self.child: Optional[Union[ast.Symbol, ArrayBuilder]] = child
        self.param: Optional[ast.Node] = param

    def set_child(self, child: ast.Symbol) -> None:
        if self.child is None:
            self.child = child
        else:
            assert isinstance(self.child, ArrayBuilder)
            self.child.set_child(child)

    def to_array(self) -> ast.Array:
        if isinstance(self.child, ArrayBuilder):
            self.child = self.child.to_array()
        assert self.child is not None
        return ast.Array(self.child, self.param)

    def to_array_access(self) -> ast.ArrayAccess:
        if isinstance(self.child, ArrayBuilder):
            self.child = self.child.to_array_access()
        assert self.child is not None
        assert isinstance(self.param, ast.Expression)
        return ast.ArrayAccess(self.child, self.param)


OperatorSequence = List[Union[ast.Value, ast.Operator]]
ComparisonSequence = Tuple[ast.Value, StrMatch, ast.Value, StrMatch, ast.Value]
ControlStructureArgs = Tuple[ast.Expression, List[ast.Statement]]
ForDoInitializer = Union[ast.VariableDeclaration, ast.VariableAssignment]
ForDoAction = Union[ast.Expression, ast.VariableAssignment]


class ASTBuilder(PTNodeVisitor):
    # Comments
    ##########

    def visit_comment(self, node: RegExMatch, children: Tuple[RegExMatch]) -> None:
        return None

    def visit_trailing_comma(self, node: ParseTreeNode, children: Tuple[StrMatch]) -> None:
        return None

    # Values
    ########

    def visit_builtin_type(self, node: ParseTreeNode, children: Tuple[StrMatch]) -> str:
        return '@' + str(node)

    def visit_identifier(self, node: ParseTreeNode, children: Tuple[Union[RegExMatch, StrMatch]]
                         ) -> ast.Identifier:
        return ast.Identifier(node.position, str(children[0]))

    def visit_compound_identifier(self, node: ParseTreeNode, children: List[ast.Identifier]
                                  ) -> ast.CompoundIdentifier:
        return ast.CompoundIdentifier(children)

    def visit_char(self, node: ParseTreeNode, children: Tuple[RegExMatch]) -> ast.Char:
        return ast.Char(str(children[0]))

    def visit_string(self, node: ParseTreeNode, children: Tuple[RegExMatch]) -> ast.String:
        return ast.String(str(children[0]))

    def visit_number(self, node: ParseTreeNode, children: Tuple[RegExMatch]) -> ast.Number:
        return ast.Number(str(node))

    def visit_decimal_number(self, node: ParseTreeNode, children: Tuple[RegExMatch]
                             ) -> ast.DecimalNumber:
        return ast.DecimalNumber(str(node))

    def visit_null_value(self, node: ParseTreeNode, children: Tuple[StrMatch]) -> ast.NullValue:
        return ast.NullValue()

    def visit_bool_value(self, node: ParseTreeNode, children: Tuple[StrMatch]) -> ast.BoolValue:
        return ast.BoolValue(children[0] == 'true')

    def visit_referenced_value(self, node: ParseTreeNode,
                               children: Union[Tuple[StrMatch, ast.Symbol],
                                               Tuple[StrMatch, ast.Symbol, ArrayBuilder]]
                               ) -> ast.Reference:
        if len(children) == 2:
            return ast.Reference(children[1])
        children[2].set_child(children[1])
        return ast.Reference(children[2].to_array_access())

    # children is variable length here, but typings do not allow to show it
    def visit_function_call(self, node: ParseTreeNode,
                            children: Tuple[ast.Symbol, ast.Expression]) -> ast.FunctionCall:
        args: List[ast.Expression] = []
        i = 1
        while i < len(children):
            exp: Union[ast.Symbol, ast.Expression] = children[i]
            assert isinstance(exp, ast.Expression)
            args.append(exp)
            i += 2
        return ast.FunctionCall(node.position, children[0], args)

    def visit_prefix_operator_value(self, node: ParseTreeNode,
                                    children: Tuple[StrMatch, ast.Symbol]
                                    ) -> ast.PrefixOperatorValue:
        return ast.PrefixOperatorValue(str(children[0]), children[1])

    def visit_suffix_operator_value(self, node: ParseTreeNode,
                                    children: Tuple[ast.Symbol, StrMatch]
                                    ) -> ast.SuffixOperatorValue:
        return ast.SuffixOperatorValue(str(children[1]), children[0])

    def visit_sizeof(self, node: ParseTreeNode, children: Tuple[StrMatch, ast.Symbol]
                     ) -> ast.Sizeof:
        return ast.Sizeof(children[1])

    def visit_array_access(self, node: ParseTreeNode, children: Tuple[ast.Expression, ...]
                           ) -> Optional[ArrayBuilder]:
        res: Optional[ArrayBuilder] = None
        i: int = len(children) - 1
        while i >= 0:
            res = ArrayBuilder(res, children[i])
            i -= 1
        return res

    def visit_anonymous_array(self, node: ParseTreeNode, children: Tuple[ast.Value, StrMatch]
                              ) -> ast.AnonymousArray:
        return ast.AnonymousArray(node.position, list(children[::2]))

    def visit_value(self, node: ParseTreeNode, children: Tuple[ast.Symbol, ArrayBuilder]
                    ) -> ast.Symbol:
        if len(children) == 1:
            return children[0]
        children[1].set_child(children[0])
        return children[1].to_array_access()

    # Operators
    ###########

    def visit_equality_sequence(self, node: ParseTreeNode, children: Tuple[ast.Value, ...]
                                ) -> OperatorSequence:
        res: OperatorSequence = [children[0], ast.Operator('=='), children[1]]
        i: int = 2
        while i < len(children):
            res += [ast.Operator('&&'), children[0], ast.Operator('=='), children[i]]
            i += 1
        return res

    def visit_inequality_sequence(self, node: ParseTreeNode, children: Tuple[ast.Value, ...]
                                  ) -> OperatorSequence:
        res: OperatorSequence = [children[0], ast.Operator('!='), children[1]]
        i: int = 2
        while i < len(children):
            res += [ast.Operator('&&'), children[0], ast.Operator('!='), children[i]]
            i += 1
        return res

    def visit_lesser_than_sequence(self, node: ParseTreeNode, children: ComparisonSequence
                                   ) -> OperatorSequence:
        return [children[0], ast.Operator(str(children[1])), children[2], ast.Operator('&&'),
                children[2], ast.Operator(str(children[3])), children[4]]

    def visit_greater_than_sequence(self, node: ParseTreeNode, children: ComparisonSequence
                                    ) -> OperatorSequence:
        return [children[0], ast.Operator(str(children[1])), children[2], ast.Operator('&&'),
                children[2], ast.Operator(str(children[3])), children[4]]

    def visit_operator_sequence(self, node: ParseTreeNode, children: Tuple[OperatorSequence]
                                ) -> OperatorSequence:
        return children[0]

    def visit_mathematical_operator(self, node: ParseTreeNode, children: StrMatch) -> ast.Operator:
        return ast.Operator(str(node))

    def visit_boolean_operator(self, node: ParseTreeNode, children: StrMatch) -> ast.Operator:
        return ast.Operator(str(node))

    def visit_bitwise_operator(self, node: ParseTreeNode, children: StrMatch) -> ast.Operator:
        return ast.Operator(str(node))

    def visit_comparison_operator(self, node: ParseTreeNode, children: StrMatch) -> ast.Operator:
        return ast.Operator(str(node))

    def visit_parenthesised_expression(self, node: ParseTreeNode, children: Tuple[ast.Expression]
                                       ) -> ast.Expression:
        return ast.Expression(list(children), True)

    def visit_expression(self, node: ParseTreeNode,
                         children: Tuple[Union[List[ast.Value], ast.Value]]) -> ast.Expression:
        if isinstance(children[0], list):
            return ast.Expression(children[0], False)
        # Ignore type because we can't check which variant of Tuple
        return ast.Expression(list(children), False)  # type: ignore

    def visit_assignment(self, node: ParseTreeNode, children: Tuple[ast.Expression]
                         ) -> ast.Assignment:
        return ast.Assignment(children[0])

    def visit_operation_assignment(self, node: ParseTreeNode,
                                   children: Union[Tuple[StrMatch, ast.Assignment],
                                                   Tuple[ast.Assignment]]) -> ast.Assignment:
        if len(children) == 1:
            return children[0]
        children[1].operator = children[0]
        return children[1]

    # Types
    #######

    def visit_qualifier(self, node: ParseTreeNode, children: Tuple[StrMatch, ...]) -> int:
        qualifier = ast.Qualifier.NONE
        for q in children:
            if q == 'const':
                qualifier = qualifier | ast.Qualifier.CONST
            elif q == 'restrict':
                qualifier = qualifier | ast.Qualifier.RESTRICT
            elif q == 'volatile':
                qualifier = qualifier | ast.Qualifier.VOLATILE
        return qualifier

    def visit_array_element(self, node: ParseTreeNode, children: Tuple[Union[None, ast.Expression]]
                            ) -> ArrayBuilder:
        if len(children) == 0:
            return ArrayBuilder(None, None)
        return ArrayBuilder(None, children[0])

    def visit_array(self, node: ParseTreeNode, children: Tuple[ArrayBuilder, ...]
                    ) -> Optional[ArrayBuilder]:
        res: Optional[ArrayBuilder] = None
        i: int = len(children) - 1
        while i >= 0:
            children[i].child = res
            res = children[i]
            i -= 1
        return res

    def visit_reference(self, node: ParseTreeNode,
                        children: Union[Tuple[StrMatch, ast.Type],
                                        Tuple[StrMatch, ArrayBuilder, ast.Type]]
                        ) -> Union[ast.Array, ast.Reference]:
        if len(children) == 2:
            return ast.Reference(children[1])
        children[1].set_child(ast.Reference(children[2]))
        return children[1].to_array()

    def visit_function_type_args(self, node: ParseTreeNode, children: Tuple[ast.Symbol, ...]
                                 ) -> Tuple[ast.Symbol, ...]:
        return children

    def visit_function_type(self, node: ParseTreeNode,
                            children: Union[Tuple[StrMatch, ast.Symbol],
                                            Tuple[StrMatch, ast.Symbol, Tuple[ast.Symbol, ...]]]
                            ) -> ast.TemplatedIdentifier:
        args: List[ast.VariableDeclaration] = []
        variadic: bool = False
        variadic_type: Optional[ast.Symbol] = ast.CompoundIdentifier([ast.Identifier(0, '@any')])
        if len(children) > 2:
            i = 0
            while i < len(children[2]):
                arg = children[2][i]
                if arg == '...':
                    variadic = True
                elif len(children[2]) > i + 1 and children[2][i + 1] == '...':
                    assert isinstance(arg, ast.Symbol)
                    variadic_type = arg
                    variadic = True
                else:
                    args.append(ast.VariableDeclaration(arg, None))
                i += 2
        return ast.TemplatedIdentifier(
            '@func',
            [ast.FunctionType(children[1], args, variadic, variadic_type)]
        )

    def visit_full_type(self, node: ParseTreeNode,
                        children: Tuple[Optional[ast.Qualifier], ast.Symbol, ast.Symbol,
                                        Optional[ArrayBuilder]]
                        ) -> ast.Symbol:
        qualifiers: ast.Qualifier = ast.Qualifier.NONE
        i: int = 0
        if len(children) > 0 and isinstance(children[0], int):
            qualifiers = children[0]
            i = 1
        typ = children[i]
        assert isinstance(typ, ast.Symbol)
        typ.set_qualifiers(qualifiers)
        if len(children) == i + 2:
            array = children[i + 1]
            assert isinstance(array, ArrayBuilder)
            array.set_child(typ)
            return array.to_array()
        return typ

    # Statements
    ############

    def visit_variable_declaration(self, node: ParseTreeNode,
                                   children: Tuple[ast.Symbol, ast.Identifier]
                                   ) -> ast.VariableDeclaration:
        return ast.VariableDeclaration(children[0], children[1], None)

    def visit_variable_declaration_assignable(self, node: ParseTreeNode,
                                              children: Tuple[ast.VariableDeclaration,
                                                              Optional[ast.Assignment]]
                                              ) -> ast.VariableDeclaration:
        if len(children) == 2:
            children[0].assign = children[1]
        return children[0]

    def visit_local_variable_declaration(self, node: ParseTreeNode,
                                         children: Union[Tuple[ast.VariableDeclaration],
                                                         Tuple[StrMatch, ast.VariableDeclaration]]
                                         ) -> ast.VariableDeclaration:
        if len(children) == 2:
            children[1].static = True
            return children[1]
        return children[0]

    def visit_variable_assignment(self, node: ParseTreeNode,
                                  children: Union[Tuple[ast.Symbol, ArrayBuilder, ast.Assignment],
                                                  Tuple[ast.Symbol, ast.Assignment]]
                                  ) -> ast.VariableAssignment:
        if len(children) == 2:
            return ast.VariableAssignment(children[0], children[1])
        children[1].set_child(children[0])
        return ast.VariableAssignment(children[1].to_array_access(), children[2])

    def visit_return_instruction(self, node: ParseTreeNode,
                                 children: Tuple[StrMatch, ast.Expression]) -> ast.Return:
        if len(children) == 0:
            return ast.Return()
        return ast.Return(children[1])

    def visit_statement(self, node: ParseTreeNode, children: Tuple[ast.Node]) -> ast.Statement:
        return ast.Statement(children[0])

    def visit_global_variable(self, node: ParseTreeNode,
                              children: Union[Tuple[ast.VariableDeclaration],
                                              Tuple[str, ast.VariableDeclaration],
                                              Tuple[str, str, ast.VariableDeclaration]]
                              ) -> ast.Statement:
        private: bool = False
        cdecl: bool = False
        i: int = 0
        while isinstance(children[i], str):
            if children[i] == 'priv':
                private = True
            elif children[i] == 'cdecl':
                cdecl = True
            else:
                raise Exception('unimplemented variable modifier: {}'.format(children[i]))
            i += 1
        assert isinstance(children[i], ast.VariableDeclaration)
        if private:
            children[i].private = True
        if cdecl:
            children[i].declaration_type = ast.DeclarationType.C
        return ast.Statement(children[i])

    # Control Structures
    ####################

    def visit_control_structure_body(self, node: ParseTreeNode, children: Tuple[ast.Node]
                                     ) -> Tuple[ast.Node]:
        return children

    def visit_control_structure(self, node: ParseTreeNode,
                                children: Tuple[ast.Expression, Union[List[ast.Statement],
                                                                      ast.Statement]]
                                ) -> ControlStructureArgs:
        body = children[1]
        if isinstance(body, ast.Statement):
            body = [body]
        return children[0], body

    def visit_if_condition(self, node: ParseTreeNode,
                           children: Tuple[StrMatch, ControlStructureArgs]) -> ast.ControlStructure:
        return ast.ControlStructure(node.position, 'if', children[1][0], children[1][1])

    def visit_elif_condition(self, node: ParseTreeNode,
                             children: Tuple[StrMatch, ControlStructureArgs]
                             ) -> ast.ControlStructure:
        return ast.ControlStructure(node.position, 'elif', children[1][0], children[1][1])

    def visit_else_condition(self, node: ParseTreeNode,
                             children: Tuple[StrMatch, Union[List[ast.Statement], ast.Statement]]
                             ) -> ast.ControlStructure:
        body = children[1]
        if isinstance(body, ast.Statement):
            body = [body]
        return ast.ControlStructure(node.position, 'else', None, body)

    def visit_condition(self, node: ParseTreeNode, children: Tuple[ast.ControlStructure, ...]
                        ) -> ast.Condition:
        return ast.Condition(list(children))

    def visit_while_loop(self, node: ParseTreeNode,
                         children: Tuple[StrMatch, ControlStructureArgs]) -> ast.ControlStructure:
        return ast.ControlStructure(node.position, 'while', children[1][0], children[1][1])

    def visit_do_while_loop(self, node: ParseTreeNode,
                            children: Tuple[StrMatch, Union[ast.Statement, List[ast.Statement]],
                                            StrMatch, ast.Expression]
                            ) -> ast.ControlStructure:
        body: List[ast.Statement]
        if isinstance(children[1], ast.Statement):
            body = [children[1]]
        else:
            body = children[1]
        return ast.DoWhileLoop(node.position, children[3], body)

    def visit_for_do_loop_initializers(self, node: ParseTreeNode,
                                       children: Tuple[ForDoInitializer, ...]
                                       ) -> List[ForDoInitializer]:
        return list(children[::2])

    def visit_for_do_loop_actions(self, node: ParseTreeNode, children: Tuple[ForDoAction]
                                  ) -> List[ForDoAction]:
        return list(children[::2])

    def visit_for_do_loop(self, node: ParseTreeNode,
                          children: Tuple[StrMatch, List[ForDoInitializer], StrMatch,
                                          List[ForDoAction], StrMatch, ControlStructureArgs]
                          ) -> ast.ControlStructure:
        return ast.ForDoLoop(node.position, children[1], children[3], children[5][0],
                             children[5][1])

    def visit_switch_case_test(self, node: ParseTreeNode,
                               children: Tuple[StrMatch, Optional[ast.Value]]
                               ) -> List[ast.SwitchCaseTest]:
        if children[0] == 'default':
            return [ast.SwitchCaseTest(None)]
        return [ast.SwitchCaseTest(test) for test in children[1::2]]

    def visit_switch_case_body(self, node: ParseTreeNode,
                               children: Union[Tuple[ast.Statement, StrMatch],
                                               Tuple[ast.Statement, ...]]
                               ) -> ast.SwitchCaseBody:
        if children[-1] == 'fallthrough':
            return ast.SwitchCaseBody(list(children[:-1]), True)
        # Ignore type because we can't check which variant of Tuple
        return ast.SwitchCaseBody(list(children), False)  # type: ignore

    def visit_switch_cases(self, node: ParseTreeNode,
                           children: Tuple[List[ast.SwitchCaseTest], ast.SwitchCaseBody]
                           ) -> ast.SwitchCase:
        return ast.SwitchCase(children[0], children[1])

    def visit_switch(self, node: ParseTreeNode,
                     children: Tuple[StrMatch, ast.Expression, ast.Statement]
                     ) -> ast.ControlStructure:
        return ast.ControlStructure(node.position, 'switch', children[1], list(children[2:]))

    # Control structures stub
    #########################

    def visit_control_structure_body_stub_braces(self, node: ParseTreeNode,
                                                 children: Tuple[RegExMatch, ...]) -> str:
        res = ''
        for s in children:
            res += str(s)
        return res

    def visit_control_structure_body_stub_inner(self, node: ParseTreeNode,
                                                children: Tuple[RegExMatch, ...]) -> str:
        res = ''
        for s in children:
            res += str(s)
        return res

    def visit_control_structure_body_stub(self, node: ParseTreeNode, children: Tuple[str]
                                          ) -> ast.UnparsedContents:
        return ast.UnparsedContents(children[0], node.position)

    # Functions
    ###########

    def visit_function_variadic_dots(self, node: ParseTreeNode, children: None) -> str:
        return '...'

    def visit_function_prototype(self, node: ParseTreeNode,
                                 children: Tuple[ast.Symbol, ast.Identifier,
                                                 ast.VariableDeclaration]
                                 ) -> Tuple[ast.TemplatedIdentifier, ast.Identifier]:
        args: List[ast.VariableDeclaration] = []
        variadic: bool = False
        variadic_type: Optional[ast.Symbol] = ast.CompoundIdentifier([ast.Identifier(0, '@any')])
        i = 2
        while i < len(children):
            arg = children[i]
            if isinstance(arg, ast.VariableDeclaration):
                args.append(arg)
            else:
                if arg != '...':
                    assert isinstance(arg, ast.Symbol)
                    variadic_type = arg
                variadic = True
                break
            i += 2
        return ast.TemplatedIdentifier(
            '@func',
            [ast.FunctionType(children[0], args, variadic, variadic_type)]
        ), children[1]

    def visit_function_declaration(self, node: ParseTreeNode,
                                   children: Tuple[Tuple[ast.TemplatedIdentifier, ast.Identifier]]
                                   ) -> ast.FunctionDeclaration:
        i: int = 0
        cdecl: bool = False
        if isinstance(children[0], str) and children[0] == 'cdecl':
            cdecl = True
            i += 1
        res = ast.FunctionDeclaration(node.position, ast.Qualifier.NONE, *children[i])
        if cdecl:
            res.declaration_type = ast.DeclarationType.C
        return res

    def parse_function_definition(self,
                                  children: Tuple[Tuple[ast.TemplatedIdentifier, ast.Identifier],
                                                  ast.UnparsedContents]
                                  ) -> Tuple[ast.Qualifier, ast.TemplatedIdentifier, ast.Identifier,
                                             ast.UnparsedContents, bool]:
        qualifiers: ast.Qualifier = ast.Qualifier.NONE
        cdecl: bool = False
        i: int = 0
        while isinstance(children[i], str):
            if children[i] == 'inline':
                qualifiers |= ast.Qualifier.INLINE
            elif children[i] == 'priv':
                qualifiers |= ast.Qualifier.PRIVATE
            elif children[i] == 'cdecl':
                cdecl = True
            i += 1
        body = children[i + 1]
        assert isinstance(body, ast.UnparsedContents)
        decl = children[i]
        assert isinstance(decl, tuple)
        return qualifiers, decl[0], decl[1], body, cdecl

    def visit_function_definition(self, node: ParseTreeNode,
                                  children: Tuple[Tuple[ast.TemplatedIdentifier, ast.Identifier],
                                                  ast.UnparsedContents]
                                  ) -> ast.FunctionDefinition:
        qualifiers, typ, sym, body, cdecl = self.parse_function_definition(children)
        res = ast.FunctionDefinition(node.position, qualifiers, typ, sym, body)
        if cdecl:
            res.declaration_type = ast.DeclarationType.C
        return res

    def visit_function(self, node: ParseTreeNode, children: Tuple[ast.FunctionDeclaration]
                       ) -> ast.FunctionDeclaration:
        return children[0]

    # External includes
    ###################

    def visit_include_part(self, node: ParseTreeNode, children: Tuple[RegExMatch]) -> str:
        return str(node)

    def visit_include_instruction(self, node: ParseTreeNode, children: Tuple[str, ...]
                                  ) -> ast.Include:
        return ast.Include(node.position, list(children[1::2]))

    def visit_import_part(self, node: ParseTreeNode, children: Tuple[RegExMatch]) -> str:
        return str(node)

    def visit_import_instruction(self, node: ParseTreeNode, children: Tuple[str, ...]
                                 ) -> ast.Import:
        return ast.Import(node.position, list(children[1::2]))

    # Misc
    ######

    def visit_alias(self, node: ParseTreeNode, children: Tuple[StrMatch, ast.Symbol, ast.Identifier]
                    ) -> ast.Alias:
        return ast.Alias(children[1], children[2])

    def visit_namespace(self, node: ParseTreeNode,
                        children: Tuple[StrMatch, ast.CompoundIdentifier, ast.Node]
                        ) -> ast.Namespace:
        ns: List[ast.Identifier] = children[1].elems
        top: ast.Namespace = ast.Namespace(node.position, ns[0])
        cur: ast.Namespace = top
        for sub_ns in ns[1:]:
            tmp: ast.Namespace = ast.Namespace(sub_ns.pos, sub_ns)
            cur.contents = [tmp]
            cur = tmp
        cur.contents = list(children[2:])
        return top

    # Container structures
    ######################

    def visit_struct(self, node: ParseTreeNode,
                     children: Tuple[StrMatch, ast.Identifier, ast.VariableDeclaration]
                     ) -> ast.Struct:
        if len(children) == 2:
            return ast.Struct(node.position, children[1], None)
        return ast.Struct(node.position, children[1], list(children[2:]))

    def visit_union(self, node: ParseTreeNode,
                    children: Tuple[StrMatch, ast.Identifier, ast.VariableDeclaration]
                    ) -> ast.EhUnion:
        if len(children) == 2:
            return ast.EhUnion(node.position, children[1], None)
        return ast.EhUnion(node.position, children[1], list(children[2:]))

    def visit_enum(self, node: ParseTreeNode,
                   children: Tuple[StrMatch, ast.Identifier, ast.Identifier]
                   ) -> ast.EhEnum:
        if len(children) == 2:
            return ast.EhEnum(node.position, children[1], None)
        return ast.EhEnum(node.position, children[1], list(children[2:]))

    def visit_class_method(self, node: ParseTreeNode,
                           children: Tuple[Tuple[ast.TemplatedIdentifier, ast.Identifier],
                                           ast.UnparsedContents]) -> ast.ClassMethod:
        qualifiers, typ, sym, body, cdecl = self.parse_function_definition(children)
        res = ast.ClassMethod(node.position, qualifiers, typ, sym, body)
        if cdecl:
            res.declaration_type = ast.DeclarationType.C
        return res

    def visit_class_property(self, node: ParseTreeNode, children: Tuple[ast.Symbol, ast.Identifier]
                             ) -> ast.ClassProperty:
        return ast.ClassProperty(children[0], children[1], None)

    def visit_eh_class(self, node: ParseTreeNode,
                       children: Tuple[StrMatch, ast.Identifier,
                                       Union[ast.ClassMethod, ast.ClassProperty]]
                       ) -> ast.EhClass:
        if len(children) == 2:
            return ast.EhClass(node.position, children[1], None)
        return ast.EhClass(node.position, children[1], list(children[2:]))

    # Root grammars
    ###############

    def visit_function_body_grammar(self, node: ParseTreeNode, children: Tuple[ast.Node, ...]
                                    ) -> List[ast.Node]:
        return list(children)

    def visit_grammar(self, node: ParseTreeNode, children: Tuple[ast.Node, ...]) -> ast.AST:
        return ast.AST(list(children))
