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

from arpeggio import RegExMatch, Optional, Sequence, ZeroOrMore, Not, And, EOF

class Context:
  return_value = True

def block_comment(): return ('/*', RegExMatch(r'[^*/]*'), '*/')
def line_comment(): return ('//', RegExMatch(r'.*$'))
def comment(): return [line_comment, block_comment]

def builtin_keyword(): return ['null', 'ref', 'if', 'elif', 'else', 'while', 'return', 'func',
  'alias', builtin_type, bool_value]
def identifier():
  return Not(builtin_keyword), RegExMatch(r'[A-Za-z_][A-Za-z0-9_]*', str_repr='identifier')
def symbol():
  return identifier, ZeroOrMore('.', identifier)
def char():
  return ('\'', Sequence(RegExMatch(r'\\[abefnrtv0\\]|[^\']', str_repr='character'), skipws=False),
    '\'')
def string(): return '"', RegExMatch(r'[^"]*'), '"'
def number(): return RegExMatch(r'-?[0-9]+', str_repr='number')
def null_value(): return 'null'
def bool_value(): return ['true', 'false']
def referenced_value(): return 'ref', value
def function_call(): return [full_type, symbol], '(', ZeroOrMore(expression, sep=','), ')'
def writable_value(): return [referenced_value, symbol]
def disambiguated_prefix_operator_value(): return ("",
  Sequence(['++', '--'], And(['ref', symbol]), skipws=False))
def prefix_operator_value(): return [disambiguated_prefix_operator_value, '!'], writable_value
def suffix_operator_value(): return writable_value, Sequence(['++', '--'], skipws=False)
def sizeof(): return 'sizeof', '(', full_type, ')'
def array_access(): return ZeroOrMore('[', expression, ']')
def value():
  return [null_value, bool_value, sizeof, function_call, prefix_operator_value,
    suffix_operator_value, writable_value, string, char, number], array_access

def mathematical_operator(): return ['+', '-', '*', '/', '%']
def binary_operator(): return ['==', '!=', '>=', '<=', '>', '<', '||', '&&']
def operator(): return [mathematical_operator, binary_operator]
def parenthesised_expression(): return '(', expression, ')'
def expression(): return [value, parenthesised_expression], Optional(operator, expression)
def assignment(): return '=', expression
def operation_assignment(): return Optional(mathematical_operator), assignment

def builtin_type():
  return ['char', 'int', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
    'size', 'str', 'any', 'void', 'bool']
def modifier(): return Optional('const')
def array_element(): return '[', Optional(expression), ']'
def array(): return ZeroOrMore(array_element)
def reference(): return 'ref', array, full_type
def function_type_args(): return Optional(full_type), ZeroOrMore(',', full_type)
def function_type(): return 'func', '<', full_type, '(', function_type_args, ')', '>'
def full_type(): return [function_type, (modifier, [reference, builtin_type, symbol], array)]

def declaration(): return full_type, identifier
def variable_declaration(): return declaration, Optional(assignment)
def variable_assignment():
  return [referenced_value, symbol], Optional(array_access), operation_assignment
def return_instruction():
  if Context.return_value:
    return 'return', expression
  return 'return'
def statement(): return [return_instruction, variable_assignment, variable_declaration,
  expression]
def instruction(): return [comment, condition, while_loop, alias, statement]

def control_structure_body(): return '{', ZeroOrMore(instruction), '}'
def control_structure(): return expression, [instruction, control_structure_body]
def if_condition(): return 'if', control_structure
def elif_condition(): return 'elif', control_structure
def else_condition(): return 'else', [instruction, control_structure_body]
def condition(): return if_condition, ZeroOrMore(elif_condition), Optional(else_condition)
def while_loop(): return 'while', control_structure

def control_structure_body_stub_parens():
  return RegExMatch('{[^{}]*'), control_structure_body_stub_inner, RegExMatch('[^{}]*}')
def control_structure_body_stub_inner():
  return Optional([RegExMatch('{[^{}]*}'), control_structure_body_stub_parens])
def control_structure_body_stub(): return control_structure_body_stub_inner

def function_prototype(): return full_type, identifier, '(', ZeroOrMore(declaration, sep=','), ')'
def function_declaration(): return function_prototype, Not('{')
def function_definition(): return function_prototype, control_structure_body_stub
def function(): return [function_definition, function_declaration]

def include_instruction(): return 'include', identifier
def import_instruction(): return 'import', identifier

def alias(): return 'alias', full_type, symbol

def struct(): return 'struct', identifier, '{', ZeroOrMore(variable_declaration), '}'

def function_body_grammar(): return '{', ZeroOrMore(instruction), '}', EOF
def grammar(): return ZeroOrMore([comment, import_instruction, include_instruction, struct, alias,
  function]), EOF
