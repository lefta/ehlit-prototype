# Copyright © 2017 Cedric Legrand
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

from modgrammar import *
from reflect.parser import ast

def parse_list(lst):
  res = []
  for node in lst.elements[::2]:
    res.append(node.parse())
  return res

class Whitespace(Grammar): grammar = REPEAT(WHITESPACE)
class OptionalWhitespace(Grammar): grammar = OPTIONAL(Whitespace)
class ArgumentSeparator(Grammar): grammar = (OptionalWhitespace, ",", OptionalWhitespace)

class Symbol(Grammar):
  grammar = (WORD("A-Za-z_", "A-Za-z0-9_"))

  def parse(self):
    return ast.Symbol(str(self[0]))

class String(Grammar):
  grammar = ('"', WORD('^"'), '"')

  def parse(self):
    return ast.String(str(self[1]))

class Number(Grammar):
  grammar = (WORD("0-9"))

  def parse(self):
    return ast.Number(str(self[0]))

class NullStmt(Grammar):
  grammar = ('null')

  def parse(self):
    return ast.NullStmt()

class VariableUsage(Grammar):
  grammar = (OR(NullStmt, Symbol, String, Number))

  def parse(self):
    return ast.VariableUsage(self[0].parse())

class FunctionCall(Grammar):
  grammar = (Symbol, OptionalWhitespace, "(", OptionalWhitespace,
    LIST_OF(VariableUsage, sep=ArgumentSeparator), OptionalWhitespace, ")")

  def parse(self):
    return ast.FunctionCall(self[0].parse(), parse_list(self[4]))

class Operator(Grammar):
  grammar = (OptionalWhitespace, OR("==", "!=", ">", "<", ">=", "<=", "+", "-", "*", "/", "%"),
    OptionalWhitespace)

  def parse(self):
    return ast.Operator(str(self[1]))

class Expression(Grammar):
  grammar = (LIST_OF(OR(FunctionCall, VariableUsage), sep=Operator))

  def parse(self):
    expr = ast.Expression()
    for node in self[0].elements:
      expr.append(node.parse())
    return expr

class Return(Grammar):
  grammar = ("return", Whitespace, Expression)

  def parse(self):
    return ast.Return(self[2].parse())

class Assignment(Grammar):
  grammar = ('=', OptionalWhitespace, Expression)

  def parse(self):
    return ast.Assignment(self[2].parse())


class BuiltinType(Grammar):
  grammar = (OR("int", "str", "any", "void", "size"))

  def parse(self):
    return ast.BuiltinType(str(self[0]))

class Type(Grammar):
  grammar = (OR(BuiltinType, Symbol), OptionalWhitespace, OPTIONAL("[]"))
  grammar_error_override = True
  grammar_desc = 'type'

  def parse(self):
    typ = ast.Type(self[0].parse())
    if self[2] is not None:
      return ast.Array(typ)
    return typ


class Import(Grammar):
  grammar = ("import", Whitespace, Symbol)

  def parse(self):
    return ast.Import(self[2].parse())


class Declaration(Grammar):
  grammar = (Type, Whitespace, Symbol)

  def parse(self):
    return ast.Declaration(self[0].parse(), self[2].parse())

class VariableDeclaration(Grammar):
  grammar = (Declaration, OptionalWhitespace, OPTIONAL(Assignment))

  def parse(self):
    assign = self[2].parse() if self[2] is not None else None
    return ast.VariableDeclaration(self[0].parse(), assign)

class VariableAssignment(Grammar):
  grammar = (Symbol, OptionalWhitespace, Assignment)

  def parse(self):
    return ast.VariableAssignment(self[0].parse(), self[2].parse())

class Instruction(Grammar):
  grammar = (OR(Return, VariableDeclaration, VariableAssignment, Expression))

  def parse(self):
    return ast.Instruction(self[0].parse())


class StructureBody(Grammar):
  grammar = ("{", OptionalWhitespace, LIST_OF(Instruction, sep=Whitespace), OptionalWhitespace,
    "}")

  def parse(self):
    return parse_list(self[2])

class ArgumentDefinitionList(Grammar):
  grammar = (LIST_OF(Declaration, sep=ArgumentSeparator))

  def parse(self):
    return parse_list(self[0])

class FunctionDeclaration(Grammar):
  grammar = (Type, Whitespace, Symbol, OptionalWhitespace, "(", OptionalWhitespace,
    OPTIONAL(ArgumentDefinitionList), OptionalWhitespace, ")")

  def parse(self):
    args = self[6].parse() if self[6] else []
    return ast.FunctionDeclaration(self[0].parse(), self[2].parse(), args)

class FunctionDefinition(Grammar):
  grammar = (FunctionDeclaration, OptionalWhitespace, StructureBody)

  def parse(self):
    return ast.FunctionDefinition(self[0].parse(), self[2].parse())

class Function(Grammar):
  grammar = OR(FunctionDefinition, FunctionDeclaration)
  grammar_error_override = True
  grammar_desc = 'function declaration'

  def parse(self):
    return self[0].parse()


class ReflectGrammar(Grammar):
  grammar = (OR(Import, Function, Whitespace))

  def parse(self):
    return self[0].parse() if type(self[0]) is not Whitespace else None
