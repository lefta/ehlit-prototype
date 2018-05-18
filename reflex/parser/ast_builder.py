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

from reflex.parser import ast

class ASTBuilder(PTNodeVisitor):
  def visit_comment(self, node, children): return None

  def visit_symbol(self, node, children): return ast.Symbol(node.position, str(node))
  def visit_char(self, node, children): return ast.Char(str(children[0]))
  def visit_string(self, node, children): return ast.String(str(children[0]))
  def visit_number(self, node, children): return ast.Number(str(node))
  def visit_null_value(self, node, children): return ast.NullValue()
  def visit_referenced_value(self, node, children): return ast.Reference(children[1])
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
  def visit_sizeof(self, node, children): return ast.Sizeof(children[1])
  def visit_array_access(self, node, children):
    res = None
    i = len(children) - 1
    while i >= 0:
      res = ast.ArrayAccess(res, children[i])
      i -= 1
    return res
  def visit_value(self, node, children):
    if len(children) == 1:
      return children[0]
    arr = res = children[1]
    while arr.child is not None:
      arr = arr.child
    arr.child = children[0]
    return res

  def visit_mathematical_operator(self, node, children): return ast.Operator(str(node))
  def visit_binary_operator(self, node, children): return ast.Operator(str(node))
  def visit_parenthesised_expression(self, node, children): return ast.Expression(children, True)
  def visit_expression(self, node, children): return ast.Expression(children, False)
  def visit_assignment(self, node, children): return ast.Assignment(children[0])
  def visit_operation_assignment(self, node, children):
    if len(children) is 1:
      return children[0]
    children[1].operator = children[0]
    return children[1]

  def visit_builtin_type(self, node, children): return ast.BuiltinType(str(node))
  def visit_modifier(self, node, children): return ast.MOD_CONST
  def visit_array_element(self, node, children):
    if len(children) is 0:
      return ast.Array(None, None)
    return ast.Array(None, children[0])
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
    arr = children[1]
    while arr.child is not None:
      arr = arr.child
    arr.child = ast.Reference(children[2])
    return children[1]
  def visit_full_type(self, node, children):
    mods = 0
    i = 0
    if len(children) > 0 and type(children[0]) is int:
      mods = children[0]
      i = 1

    res = children[i]
    children[i].set_modifiers(mods)

    if len(children) == i + 2:
      arr = res = children[i + 1]
      while arr.child is not None:
        arr = arr.child
      arr.child = children[i]
    return res

  def visit_declaration(self, node, children): return ast.Declaration(children[0], children[1])
  def visit_variable_declaration(self, node, children):
    return ast.VariableDeclaration(children[0], children[1] if len(children) == 2 else None)
  def visit_variable_assignment(self, node, children):
    if len(children) == 2:
      return ast.VariableAssignment(children[0], children[1])

    arr = res = children[1]
    while arr.child is not None:
      arr = arr.child
    arr.child = children[0]
    return ast.VariableAssignment(res, children[2])

  def visit_return_instruction(self, node, children): return ast.Return(children[1])
  def visit_statement(self, node, children): return ast.Statement(children[0])

  def visit_control_structure_body(self, node, children): return children
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

  def visit_function_prototype(self, node, children):
    args = []
    i = 2
    while i < len(children):
      args.append(children[i])
      i += 2
    return ast.FunctionDeclaration(children[0], children[1], args)
  def visit_function_declaration(self, node, children): return children[0]
  def visit_function_definition(self, node, children):
    return ast.FunctionDefinition(children[0], children[1])
  def visit_function(self, node, children): return children[0]

  def visit_include_instruction(self, node, children):
    return ast.Include(node.position, children[1])
  def visit_import_instruction(self, node, children): return ast.Import(node.position, children[1])

  def visit_alias(self, node, children): return ast.Alias(children[1], children[2])

  def visit_grammar(self, node, children): return ast.AST(children)
