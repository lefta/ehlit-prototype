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

from arpeggio import RegExMatch, Optional, Sequence, ZeroOrMore, OneOrMore, Not, And, EOF
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from arpeggio import GrammarType
else:
  # Should fail passing if taken into account, set only to avoid an `undefined identifier
  # "GrammarType"` error at runtime.
  GrammarType = int


class Context:
  return_value: bool = True


# Utilities
###########

def trailing_comma() -> GrammarType:
  return Optional(',')


# Comments
##########

def block_comment() -> GrammarType:
  return ('/*', RegExMatch(r'[\s\S]*?(?=\*\/)'), '*/')


def line_comment() -> GrammarType:
  return ('//', RegExMatch(r'.*$'))


def comment() -> GrammarType:
  return [line_comment, block_comment]


# Values
########

def builtin_keyword() -> GrammarType:
  return ['null', 'ref', 'if', 'elif', 'else', 'while', 'return', 'func', 'alias', 'switch', 'case',
          'fallthrough', 'default', 'struct', 'union', bool_value]


def builtin_type() -> GrammarType:
  return ['int', 'int8', 'int16', 'int32', 'int64', 'uint', 'uint8', 'uint16', 'uint32', 'uint64',
          'char', 'str', 'bool', 'void', 'any', 'size']


def identifier() -> GrammarType:
  return Not(builtin_keyword), [builtin_type,
                                RegExMatch(r'[A-Za-z_][A-Za-z0-9_]*', str_repr='identifier')]


def compound_identifier() -> GrammarType:
  return identifier, ZeroOrMore('.', identifier)


def char() -> GrammarType:
  return ('\'', Sequence(RegExMatch(r'\\[abefnrtv0\\]|[^\']', str_repr='character'), skipws=False),
          '\'')


def string() -> GrammarType:
  return '"', RegExMatch(r'(\\"|[^"])*'), '"'


def number() -> GrammarType:
  return RegExMatch(r'-?[0-9]+', str_repr='number')


def null_value() -> GrammarType:
  return 'null'


def bool_value() -> GrammarType:
  return ['true', 'false']


def referenced_value() -> GrammarType:
  return 'ref', writable_value, array_access


def function_call() -> GrammarType:
  return [full_type, compound_identifier], '(', ZeroOrMore(expression, sep=','), trailing_comma, ')'


def writable_value() -> GrammarType:
  return [referenced_value, compound_identifier]


def disambiguated_prefix_operator_value() -> GrammarType:
  return "", Sequence(['++', '--'], And(['ref', compound_identifier]), skipws=False)


def prefix_operator_value() -> GrammarType:
  return [disambiguated_prefix_operator_value, '!'], writable_value


def suffix_operator_value() -> GrammarType:
  return writable_value, Sequence(['++', '--'], skipws=False)


def sizeof() -> GrammarType:
  return 'sizeof', '(', full_type, ')'


def array_access() -> GrammarType:
  return ZeroOrMore('[', expression, ']')


def value() -> GrammarType:
  return [null_value, bool_value, sizeof, function_call, prefix_operator_value,
          suffix_operator_value, writable_value, string, char, number], array_access


# Operators & assigment
#######################

def equality_sequence() -> GrammarType:
  return value, '==', value, OneOrMore('==', value)


def inequality_sequence() -> GrammarType:
  return value, '!=', value, OneOrMore('!=', value)


def lesser_than_sequence() -> GrammarType:
  return value, ['<=', '<'], value, ['<=', '<'], value


def greater_than_sequence() -> GrammarType:
  return value, ['>=', '>'], value, ['>=', '>'], value


def operator_sequence() -> GrammarType:
  return [equality_sequence, inequality_sequence, lesser_than_sequence, greater_than_sequence]


def mathematical_operator() -> GrammarType:
  return ['+', '-', '*', '/', '%']


def boolean_operator() -> GrammarType:
  return ['==', '!=', '>=', '<=', '>', '<', '||', '&&']


def operator() -> GrammarType:
  return [mathematical_operator, boolean_operator]


def parenthesised_expression() -> GrammarType:
  return '(', expression, ')'


def expression() -> GrammarType:
  return [operator_sequence, value, parenthesised_expression], Optional(operator, expression)


def assignment() -> GrammarType:
  return '=', expression


def operation_assignment() -> GrammarType:
  return Optional(mathematical_operator), assignment


# Types
#######

def modifier() -> GrammarType:
  return Optional('const')


def array_element() -> GrammarType:
  return '[', Optional(expression), ']'


def array() -> GrammarType:
  return ZeroOrMore(array_element)


def reference() -> GrammarType:
  return 'ref', array, full_type


def function_type_args() -> GrammarType:
  return Optional(full_type), ZeroOrMore(',', full_type), trailing_comma


def function_type() -> GrammarType:
  return 'func', '<', full_type, '(', function_type_args, ')', '>'


def full_type() -> GrammarType:
  return [function_type, (modifier, [reference, compound_identifier], array)]


# Statements
############

def variable_declaration() -> GrammarType:
  return full_type, identifier


def variable_declaration_assignable() -> GrammarType:
  return variable_declaration, Optional(assignment)


def variable_assignment() -> GrammarType:
  return [referenced_value, compound_identifier], Optional(array_access), operation_assignment


def return_instruction() -> GrammarType:
  if Context.return_value:
    return 'return', expression
  return 'return'


def statement() -> GrammarType:
  return [return_instruction, variable_assignment, variable_declaration_assignable, expression]


def instruction() -> GrammarType:
  return [comment, condition, while_loop, switch, alias, statement]


# Control Structures
####################

def control_structure_body() -> GrammarType:
  return '{', ZeroOrMore(instruction), '}'


def control_structure() -> GrammarType:
  return expression, [instruction, control_structure_body]


def if_condition() -> GrammarType:
  return 'if', control_structure


def elif_condition() -> GrammarType:
  return 'elif', control_structure


def else_condition() -> GrammarType:
  return 'else', [instruction, control_structure_body]


def condition() -> GrammarType:
  return if_condition, ZeroOrMore(elif_condition), Optional(else_condition)


def while_loop() -> GrammarType:
  return 'while', control_structure


def switch_case_test() -> GrammarType:
  return ['default', ('case', value)]


def switch_case_body() -> GrammarType:
  return OneOrMore(instruction), Optional('fallthrough')


def switch_case_body_block() -> GrammarType:
  return '{', OneOrMore(instruction), Optional('fallthrough'), '}'


def switch_cases() -> GrammarType:
  return OneOrMore(switch_case_test), [switch_case_body, switch_case_body_block]


def switch() -> GrammarType:
  return 'switch', value, '{', ZeroOrMore(switch_cases), '}'


# Control structures stub
#########################

def open_brace() -> GrammarType:
  return RegExMatch(r'\s*{')


def close_brace() -> GrammarType:
  return RegExMatch(r'[^{}]*}')


def control_structure_potential_closing_brace() -> GrammarType:
  return [And(RegExMatch('[^{}]*}')), RegExMatch('[^{}]*')]


def control_structure_body_stub_braces() -> GrammarType:
  return ZeroOrMore(RegExMatch('[^{}]*{[^{}]*'),
                    ZeroOrMore(control_structure_body_stub_inner, Optional(RegExMatch('[^{}]*'))),
                    close_brace, control_structure_potential_closing_brace)


def control_structure_body_stub_inner() -> GrammarType:
  return (open_brace, [control_structure_body_stub_braces,
          control_structure_potential_closing_brace], close_brace)


def control_structure_body_stub() -> GrammarType:
  return Sequence(control_structure_body_stub_inner, skipws=False)


# Functions
###########

def function_prototype() -> GrammarType:
  return (full_type, identifier, '(', ZeroOrMore(variable_declaration_assignable, sep=','),
          trailing_comma, ')')


def function_declaration() -> GrammarType:
  return function_prototype, Not('{')


def function_definition() -> GrammarType:
  return function_prototype, control_structure_body_stub


def function() -> GrammarType:
  return [function_definition, function_declaration]


# External includes
###################

def include_part() -> GrammarType:
  return RegExMatch(r'[^/ \n\t\r\f\v]+', str_repr='include path part')


def include_instruction() -> GrammarType:
  return 'include', OneOrMore(include_part, sep='/')


def import_part() -> GrammarType:
  return RegExMatch(r'[^/. \n\t\r\f\v]+', str_repr='import path part')


def import_instruction() -> GrammarType:
  return 'import', OneOrMore(import_part, sep='.')


# Misc
######

def alias() -> GrammarType:
  return 'alias', full_type, identifier


# Container structures
######################

def struct() -> GrammarType:
  return 'struct', identifier, Optional('{', ZeroOrMore(variable_declaration), '}')


def union() -> GrammarType:
  return 'union', identifier, Optional('{', ZeroOrMore(variable_declaration), '}')


# Root grammars
###############

def function_body_grammar() -> GrammarType:
  return '{', ZeroOrMore(instruction), '}', EOF


def grammar() -> GrammarType:
  return ZeroOrMore([comment, import_instruction, include_instruction, struct, union, alias,
                     function]), EOF
