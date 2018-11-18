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

    def visit_parenthesised_expression(self, node: ParseTreeNode, children: Tuple[ast.Expression]
                                       ) -> ast.Expression:
        return ast.Expression(list(children), True)

    def visit_expression(self, node: ParseTreeNode,
                         children: Tuple[Union[List[ast.Value], ast.Value]]) -> ast.Expression:
        if isinstance(children[0], list):
            return ast.Expression(children[0], False)
        # Ignore type because we can't check which variant of Tuple
        values: List[ast.Value] = list(children)  # type: ignore
        return ast.Expression(values, False)

    def visit_assignment(self, node: ParseTreeNode, children: Tuple[ast.Expression]
                         ) -> ast.Assignment:
        return ast.Assignment(children[0])

    def visit_operation_assignment(self, node: ParseTreeNode,
                                   children: Union[Tuple[StrMatch, ast.Assignment],
                                                   Tuple[ast.Assignment]]) -> ast.Assignment:
        if len(children) is 1:
            return children[0]
        children[1].operator = children[0]
        return children[1]

    # Types
    #######

    def visit_qualifier(self, node: ParseTreeNode, children: Tuple[StrMatch, ...]) -> int:
        qualifier = ast.TypeQualifier.NONE
        for q in children:
            if q == 'const':
                qualifier = qualifier | ast.TypeQualifier.CONST
            elif q == 'restrict':
                qualifier = qualifier | ast.TypeQualifier.RESTRICT
            elif q == 'volatile':
                qualifier = qualifier | ast.TypeQualifier.VOLATILE
        return qualifier

    def visit_array_element(self, node: ParseTreeNode, children: Tuple[Union[None, ast.Expression]]
                            ) -> ArrayBuilder:
        if len(children) is 0:
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
                                 ) -> List[ast.Declaration]:
        res: List[ast.Declaration] = []
        for c in children:
            res.append(ast.Declaration(c, None))
        return res

    def visit_function_type(self, node: ParseTreeNode,
                            children: Tuple[StrMatch, ast.Symbol,
                                            Optional[List[ast.VariableDeclaration]]]
                            ) -> ast.TemplatedIdentifier:
        return ast.TemplatedIdentifier('@func', [ast.FunctionType(
            children[1],
            children[2] if len(children) > 2 and isinstance(children[2], list) else []
        )])

    def visit_full_type(self, node: ParseTreeNode,
                        children: Tuple[Optional[ast.TypeQualifier], ast.Symbol, ast.Symbol,
                                        Optional[ArrayBuilder]]
                        ) -> ast.Symbol:
        qualifiers: ast.TypeQualifier = ast.TypeQualifier.NONE
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
        if len(children) is 0:
            return ast.Return()
        return ast.Return(children[1])

    def visit_statement(self, node: ParseTreeNode, children: Tuple[ast.Node]) -> ast.Statement:
        return ast.Statement(children[0])

    def visit_global_statement(self, node: ParseTreeNode, children: Tuple[ast.VariableDeclaration,
                                                                          Optional[ast.Assignment]]
                               ) -> ast.Statement:
        if len(children) == 2:
            children[0].assign = children[1]
        return ast.Statement(children[0])

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
        return ast.ControlStructure('if', children[1][0], children[1][1])

    def visit_elif_condition(self, node: ParseTreeNode,
                             children: Tuple[StrMatch, ControlStructureArgs]
                             ) -> ast.ControlStructure:
        return ast.ControlStructure('elif', children[1][0], children[1][1])

    def visit_else_condition(self, node: ParseTreeNode,
                             children: Tuple[StrMatch, Union[List[ast.Statement], ast.Statement]]
                             ) -> ast.ControlStructure:
        body = children[1]
        if isinstance(body, ast.Statement):
            body = [body]
        return ast.ControlStructure('else', None, body)

    def visit_condition(self, node: ParseTreeNode, children: Tuple[ast.ControlStructure, ...]
                        ) -> ast.Condition:
        return ast.Condition(list(children))

    def visit_while_loop(self, node: ParseTreeNode,
                         children: Tuple[StrMatch, ControlStructureArgs]) -> ast.ControlStructure:
        return ast.ControlStructure('while', children[1][0], children[1][1])

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
        blocks: List[ast.Statement] = list(children)  # type: ignore
        return ast.SwitchCaseBody(blocks, False)

    def visit_switch_cases(self, node: ParseTreeNode,
                           children: Tuple[List[ast.SwitchCaseTest], ast.SwitchCaseBody]
                           ) -> ast.SwitchCase:
        return ast.SwitchCase(children[0], children[1])

    def visit_switch(self, node: ParseTreeNode,
                     children: Tuple[StrMatch, ast.Expression, ast.Statement]
                     ) -> ast.ControlStructure:
        return ast.ControlStructure('switch', children[1], list(children[2:]))

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
        return ast.FunctionDeclaration(*children[0])

    def visit_function_definition(self, node: ParseTreeNode,
                                  children: Tuple[Tuple[ast.TemplatedIdentifier, ast.Identifier],
                                                  ast.UnparsedContents]
                                  ) -> ast.FunctionDefinition:
        return ast.FunctionDefinition(children[0][0], children[0][1], children[1])

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

    # Container structures
    ######################

    def visit_struct(self, node: ParseTreeNode,
                     children: Tuple[StrMatch, ast.Identifier, ast.VariableDeclaration]
                     ) -> ast.Struct:
        if len(children) is 2:
            return ast.Struct(node.position, children[1], None)
        return ast.Struct(node.position, children[1], list(children[2:]))

    def visit_union(self, node: ParseTreeNode,
                    children: Tuple[StrMatch, ast.Identifier, ast.VariableDeclaration]
                    ) -> ast.EhUnion:
        if len(children) is 2:
            return ast.EhUnion(node.position, children[1], None)
        return ast.EhUnion(node.position, children[1], list(children[2:]))

    # Root grammars
    ###############

    def visit_function_body_grammar(self, node: ParseTreeNode, children: Tuple[ast.Node, ...]
                                    ) -> List[ast.Node]:
        return list(children)

    def visit_grammar(self, node: ParseTreeNode, children: Tuple[ast.Node, ...]) -> ast.AST:
        return ast.AST(list(children))
