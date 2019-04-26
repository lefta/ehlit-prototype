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
    return ['null', 'ref', 'if', 'elif', 'else', 'while', 'do', 'for', 'return', 'func', 'alias',
            'switch', 'case', 'fallthrough', 'default', 'struct', 'union', 'const', 'restrict',
            'volatile', 'inline', 'priv', 'namespace', 'class', bool_value]


def builtin_type() -> GrammarType:
    return ['int', 'int8', 'int16', 'int32', 'int64', 'uint', 'uint8', 'uint16', 'uint32', 'uint64',
            'float', 'double', 'decimal', 'char', 'str', 'bool', 'void', 'any', 'size']


def identifier() -> GrammarType:
    return Not(builtin_keyword), [builtin_type,
                                  RegExMatch(r'[A-Za-z_][A-Za-z0-9_]*', str_repr='identifier')]


def compound_identifier() -> GrammarType:
    return identifier, ZeroOrMore('.', identifier)


def char() -> GrammarType:
    return ('\'',
            Sequence(RegExMatch(r'\\[abefnrtv0\\]|[^\']', str_repr='character'), skipws=False),
            '\'')


def string() -> GrammarType:
    return '"', RegExMatch(r'(\\"|[^"])*'), '"'


def number() -> GrammarType:
    return RegExMatch(r'-?[0-9]+', str_repr='number')


def decimal_number() -> GrammarType:
    return RegExMatch(r'-?[0-9]+\.[0-9]+', str_repr='decimal number')


def null_value() -> GrammarType:
    return 'null'


def bool_value() -> GrammarType:
    return ['true', 'false']


def referenced_value() -> GrammarType:
    return 'ref', writable_value, array_access


def function_args() -> GrammarType:
    return '(', ZeroOrMore(expression, sep=','), trailing_comma, ')'


def function_call() -> GrammarType:
    return [full_type, compound_identifier], function_args


def writable_value() -> GrammarType:
    return [referenced_value, compound_identifier]


def disambiguated_prefix_operator_value() -> GrammarType:
    return "", Sequence(['++', '--'], And(['ref', compound_identifier]), skipws=False)


def prefix_operator_value() -> GrammarType:
    return [disambiguated_prefix_operator_value, '!', '~'], writable_value


def suffix_operator_value() -> GrammarType:
    return writable_value, Sequence(['++', '--'], skipws=False)


def sizeof() -> GrammarType:
    return 'sizeof', '(', full_type, ')'


def array_access() -> GrammarType:
    return ZeroOrMore('[', expression, ']')


def anonymous_array() -> GrammarType:
    return '[', OneOrMore(expression, sep=','), ']'


def cast() -> GrammarType:
    return 'cast', '<', full_type, '>', '(', expression, ')'


def value() -> GrammarType:
    return [cast, null_value, bool_value, sizeof, function_call, prefix_operator_value,
            suffix_operator_value, writable_value, string, char, decimal_number, number,
            anonymous_array], array_access


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
    return ['||', '&&']


def comparison_operator() -> GrammarType:
    return ['==', '!=', '>=', '<=', '>', '<']


def bitwise_operator() -> GrammarType:
    return ['|', '&', '^', '<<', '>>']


def operator() -> GrammarType:
    return [mathematical_operator, boolean_operator, bitwise_operator, comparison_operator]


def parenthesised_expression() -> GrammarType:
    return '(', expression, ')'


def expression() -> GrammarType:
    return [operator_sequence, value, parenthesised_expression], Optional(operator, expression)


def assignment() -> GrammarType:
    return '=', expression


def operation_assignment() -> GrammarType:
    return Optional([mathematical_operator, bitwise_operator]), assignment


# Types
#######

def qualifier() -> GrammarType:
    return ZeroOrMore(['const', 'restrict', 'volatile'])


def array_element() -> GrammarType:
    return '[', Optional(expression), ']'


def array() -> GrammarType:
    return ZeroOrMore(array_element)


def reference() -> GrammarType:
    return 'ref', array, full_type


def function_type_args() -> GrammarType:
    return Optional([
        # The `Not` rule is necessary to prevent the full_type rule to match, that prevents Arpeggio
        # to try the variadic dots rule
        Sequence(OneOrMore(full_type, Not('...'), sep=','),
                 Optional(',', Optional(full_type), function_variadic_dots)),
        Sequence(Optional(full_type), function_variadic_dots)
    ]), trailing_comma


def function_type() -> GrammarType:
    return 'func', '<', full_type, '(', function_type_args, ')', '>'


def full_type() -> GrammarType:
    return [function_type, (qualifier, [reference, compound_identifier], array)]


# Statements
############

def variable_declaration() -> GrammarType:
    return full_type, identifier


def variable_declaration_assignable() -> GrammarType:
    return variable_declaration, Optional([assignment, function_args])


def local_variable_declaration() -> GrammarType:
    return Optional('static'), variable_declaration_assignable


def variable_assignment() -> GrammarType:
    return [referenced_value, compound_identifier], Optional(array_access), operation_assignment


def return_instruction() -> GrammarType:
    if Context.return_value:
        return 'return', expression
    return 'return'


def statement() -> GrammarType:
    return [return_instruction, variable_assignment, local_variable_declaration, expression]


def global_variable() -> GrammarType:
    return ZeroOrMore(['priv', 'cdecl']), variable_declaration_assignable


def instruction() -> GrammarType:
    return [comment, condition, for_do_loop, do_while_loop, while_loop, switch, alias, statement]


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


def do_while_loop() -> GrammarType:
    return 'do', [instruction, control_structure_body], 'while', expression


def for_do_loop_initializers() -> GrammarType:
    return OneOrMore([variable_declaration_assignable, variable_assignment], sep=',')


def for_do_loop_actions() -> GrammarType:
    return OneOrMore([variable_assignment, expression], sep=',')


def for_do_loop() -> GrammarType:
    return 'for', for_do_loop_initializers, 'do', for_do_loop_actions, 'while', control_structure


def switch_case_test() -> GrammarType:
    return ['default', ('case', OneOrMore(value, sep=','))]


def switch_case_body() -> GrammarType:
    return OneOrMore(instruction), Optional('fallthrough')


def switch_cases() -> GrammarType:
    return switch_case_test, switch_case_body


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

def function_variadic_dots() -> GrammarType:
    return '...'


def function_arguments() -> GrammarType:
    return (Optional([Sequence(OneOrMore(variable_declaration_assignable, sep=','),
                               Optional(',', Optional(full_type), function_variadic_dots)),
                      Sequence(Optional(full_type), function_variadic_dots)]), trailing_comma)


def function_prototype() -> GrammarType:
    return full_type, identifier, '(', function_arguments, ')'


def function_declaration() -> GrammarType:
    return Optional('cdecl'), function_prototype, Not('{')


def function_definition() -> GrammarType:
    return ZeroOrMore(['priv', 'inline', 'cdecl']), function_prototype, control_structure_body_stub


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


def namespace() -> GrammarType:
    return 'namespace', compound_identifier, '{', ZeroOrMore(global_statement), '}'


def global_statement() -> GrammarType:
    return [comment, eh_class, struct, union, enum, alias, namespace, function, global_variable]


# Container structures
######################

def struct() -> GrammarType:
    return 'struct', identifier, Optional('{', ZeroOrMore(variable_declaration), '}')


def union() -> GrammarType:
    return 'union', identifier, Optional('{', ZeroOrMore(variable_declaration), '}')


def enum() -> GrammarType:
    return 'enum', identifier, Optional('{', ZeroOrMore(identifier), '}')


def constructor() -> GrammarType:
    return (ZeroOrMore(['priv', 'inline']), 'ctor', '(', function_arguments, ')',
            Optional(control_structure_body_stub))


def class_method() -> GrammarType:
    return ZeroOrMore(['priv', 'inline', 'cdecl']), function_prototype, control_structure_body_stub


def class_property() -> GrammarType:
    return full_type, identifier


def class_contents() -> GrammarType:
    return [constructor, class_method, class_property]


def eh_class() -> GrammarType:
    return 'class', identifier, Optional('{', ZeroOrMore(class_contents), '}')


# Root grammars
###############

def function_body_grammar() -> GrammarType:
    return '{', ZeroOrMore(instruction), '}', EOF


def grammar() -> GrammarType:
    return ZeroOrMore([import_instruction, include_instruction, global_statement]), EOF
