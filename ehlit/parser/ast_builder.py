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

from arpeggio import PTNodeVisitor
from typing import Optional, Union

from ehlit.parser import ast


class ArrayBuilder:
  def __init__(self, child: Optional[Union[ast.Node, 'ArrayBuilder']],
               param: Optional[ast.Node]) -> None:
    self.child: Optional[Union[ast.Node, ArrayBuilder]] = child
    self.param: Optional[ast.Node] = param

  def set_child(self, child: ast.Node) -> None:
    if self.child is None:
      self.child = child
    else:
      assert isinstance(self.child, ArrayBuilder)
      self.child.set_child(child)

  def to_array(self) -> ast.Array:
    if isinstance(self.child, ArrayBuilder):
      self.child = self.child.to_array()
    assert isinstance(self.child, ast.Type)
    return ast.Array(self.child, self.param)

  def to_array_access(self) -> ast.ArrayAccess:
    if isinstance(self.child, ArrayBuilder):
      self.child = self.child.to_array_access()
    assert self.child is not None
    assert isinstance(self.param, ast.Expression)
    assert isinstance(self.child, ast.Value)
    return ast.ArrayAccess(self.child, self.param)


class ASTBuilder(PTNodeVisitor):
  # Comments
  ##########

  def visit_comment(self, node, children):
    return None

  def visit_trailing_comma(self, node, children):
    return None

  # Values
  ########

  def visit_builtin_type(self, node, children):
    return '@' + str(node)

  def visit_identifier(self, node, children):
    return ast.Identifier(node.position, str(children[0]))

  def visit_compound_identifier(self, node, children):
    return ast.CompoundIdentifier(children)

  def visit_char(self, node, children):
    return ast.Char(str(children[0]))

  def visit_string(self, node, children):
    return ast.String(str(children[0]))

  def visit_number(self, node, children):
    return ast.Number(str(node))

  def visit_null_value(self, node, children):
    return ast.NullValue()

  def visit_bool_value(self, node, children):
    return ast.BoolValue(children[0] == 'true')

  def visit_referenced_value(self, node, children):
    return ast.Reference(children[1])

  def visit_function_call(self, node, children):
    args = []
    i = 1
    while i < len(children):
      args.append(children[i])
      i += 2
    return ast.FunctionCall(node.position, children[0], args)

  def visit_prefix_operator_value(self, node, children):
    return ast.PrefixOperatorValue(str(children[0]), children[1])

  def visit_suffix_operator_value(self, node, children):
    return ast.SuffixOperatorValue(str(children[1]), children[0])

  def visit_sizeof(self, node, children):
    return ast.Sizeof(children[1])

  def visit_array_access(self, node, children):
    res = None
    i = len(children) - 1
    while i >= 0:
      res = ArrayBuilder(res, children[i])
      i -= 1
    return res

  def visit_value(self, node, children):
    if len(children) == 1:
      return children[0]
    children[1].set_child(children[0])
    return children[1].to_array_access()

  # Operators
  ###########

  def visit_equality_sequence(self, node, children):
    res = [children[0], ast.Operator('=='), children[1]]
    i = 2
    while i < len(children):
      res += [ast.Operator('&&'), children[0], ast.Operator('=='), children[i]]
      i += 1
    return res

  def visit_inequality_sequence(self, node, children):
    res = [children[0], ast.Operator('!='), children[1]]
    i = 2
    while i < len(children):
      res += [ast.Operator('&&'), children[0], ast.Operator('!='), children[i]]
      i += 1
    return res

  def visit_lesser_than_sequence(self, node, children):
    return [children[0], ast.Operator(str(children[1])), children[2], ast.Operator('&&'),
            children[2], ast.Operator(str(children[3])), children[4]]

  def visit_greater_than_sequence(self, node, children):
    return [children[0], ast.Operator(str(children[1])), children[2], ast.Operator('&&'),
            children[2], ast.Operator(str(children[3])), children[4]]

  def visit_operator_sequence(self, node, children):
    return children[0]

  def visit_mathematical_operator(self, node, children):
    return ast.Operator(str(node))

  def visit_boolean_operator(self, node, children):
    return ast.Operator(str(node))

  def visit_parenthesised_expression(self, node, children):
    return ast.Expression(children, True)

  def visit_expression(self, node, children):
    if type(children[0]) is list:
      return ast.Expression(children[0], False)
    return ast.Expression(children, False)

  def visit_assignment(self, node, children):
    return ast.Assignment(children[0])

  def visit_operation_assignment(self, node, children):
    if len(children) is 1:
      return children[0]
    children[1].operator = children[0]
    return children[1]

  # Types
  #######

  def visit_modifier(self, node, children):
    return ast.MOD_CONST

  def visit_array_element(self, node, children):
    if len(children) is 0:
      return ArrayBuilder(None, None)
    return ArrayBuilder(None, children[0])

  def visit_array(self, node, children):
    res = None
    i = len(children) - 1
    while i >= 0:
      children[i].child = res
      res = children[i]
      i -= 1
    return res

  def visit_reference(self, node, children):
    if len(children) == 2:
      return ast.Reference(children[1])
    children[1].set_child(ast.Reference(children[2]))
    return children[1].to_array()

  def visit_function_type_args(self, node, children):
    res = []
    for c in children:
      res.append(ast.Declaration(c, None))
    return res

  def visit_function_type(self, node, children):
    return ast.TemplatedIdentifier('@func', [ast.FunctionType(
      children[1],
      [] if len(children) is 2 else children[2]
    )])

  def visit_full_type(self, node, children):
    mods = 0
    i = 0
    if len(children) > 0 and type(children[0]) is int:
      mods = children[0]
      i = 1
    children[i].set_modifiers(mods)
    if len(children) == i + 2:
      children[i + 1].set_child(children[i])
      return children[i + 1].to_array()
    return children[i]

  # Statements
  ############

  def visit_variable_declaration(self, node, children):
    return ast.VariableDeclaration(children[0], children[1], None)

  def visit_variable_declaration_assignable(self, node, children):
    if len(children) == 2:
      children[0].assign = children[1]
    return children[0]

  def visit_variable_assignment(self, node, children):
    if len(children) == 2:
      return ast.VariableAssignment(children[0], children[1])
    children[1].set_child(children[0])
    return ast.VariableAssignment(children[1].to_array_access(), children[2])

  def visit_return_instruction(self, node, children):
    if len(children) is 0:
      return ast.Return()
    return ast.Return(children[1])

  def visit_statement(self, node, children):
    return ast.Statement(children[0])

  # Control Structures
  ####################

  def visit_control_structure_body(self, node, children):
    return children

  def visit_control_structure(self, node, children):
    body = children[1]
    if type(body) is ast.Statement:
      body = [body]
    return children[0], body

  def visit_if_condition(self, node, children):
    return ast.ControlStructure('if', children[1][0], children[1][1])

  def visit_elif_condition(self, node, children):
    return ast.ControlStructure('elif', children[1][0], children[1][1])

  def visit_else_condition(self, node, children):
    body = children[1]
    if type(body) == ast.Statement:
      body = [body]
    return ast.ControlStructure('else', None, body)

  def visit_condition(self, node, children):
    return ast.Condition(children)

  def visit_while_loop(self, node, children):
    return ast.ControlStructure('while', children[1][0], children[1][1])

  def visit_switch_case_test(self, node, children):
    if children[0] == 'default':
      return ast.SwitchCaseTest(None)
    return ast.SwitchCaseTest(children[1])

  def visit_switch_case_body(self, node, children):
    if children[-1] == 'fallthrough':
      return ast.SwitchCaseBody(children[:-1], False, True)
    return ast.SwitchCaseBody(children, False, False)

  def visit_switch_case_body_block(self, node, children):
    if children[-1] == 'fallthrough':
      return ast.SwitchCaseBody(children[:-1], True, True)
    return ast.SwitchCaseBody(children, True, False)

  def visit_switch_cases(self, node, children):
    return ast.SwitchCase(children[:-1], children[-1])

  def visit_switch(self, node, children):
    return ast.ControlStructure('switch', children[1], children[2:])

  # Control structures stub
  #########################

  def visit_control_structure_body_stub_braces(self, node, children):
    res = ''
    for s in children:
      res += str(s)
    return res

  def visit_control_structure_body_stub_inner(self, node, children):
    res = ''
    for s in children:
      res += str(s)
    return res

  def visit_control_structure_body_stub(self, node, children):
    return ast.UnparsedContents(children[0], node.position)

  # Functions
  ###########

  def visit_function_prototype(self, node, children):
    args = []
    i = 2
    while i < len(children):
      args.append(children[i])
      i += 2
    return ast.TemplatedIdentifier('@func', [ast.FunctionType(children[0], args)]), children[1]

  def visit_function_declaration(self, node, children):
    return ast.FunctionDeclaration(*children[0])

  def visit_function_definition(self, node, children):
    return ast.FunctionDefinition(children[0][0], children[0][1], children[1])

  def visit_function(self, node, children):
    return children[0]

  # External includes
  ###################

  def visit_include_part(self, node, children):
    return str(node)

  def visit_include_instruction(self, node, children):
    return ast.Include(node.position, children[1::2])

  def visit_import_part(self, node, children):
    return str(node)

  def visit_import_instruction(self, node, children):
    return ast.Import(node.position, children[1::2])

  # Misc
  ######

  def visit_alias(self, node, children):
    return ast.Alias(children[1], children[2])

  # Container structures
  ######################

  def visit_struct(self, node, children):
    if len(children) is 2:
      return ast.Struct(node.position, children[1], None)
    return ast.Struct(node.position, children[1], children[2:])

  def visit_union(self, node, children):
    if len(children) is 2:
      return ast.EhUnion(node.position, children[1], None)
    return ast.EhUnion(node.position, children[1], children[2:])

  # Root grammars
  ###############

  def visit_function_body_grammar(self, node, children):
    return children

  def visit_grammar(self, node, children):
    return ast.AST(children)
