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

import logging

class DumpWriter:
  def __init__(self, ast):
    self.prefix = ''
    logging.debug('--- AST ---')
    i = 0
    count = len(ast)
    self.prev_have_next = count > 1
    self.upd_prefix = False
    while i < count:
      self.print_node(ast[i], i < count - 1)
      i += 1

  def dump(self, string):
    logging.debug('%s%s', self.prefix, string)

  def decrement_prefix(self):
    self.prefix = self.prefix[:-3]
    self.upd_prefix = False

  def increment_prefix(self, is_next):
    if self.upd_prefix:
      self.prefix = self.prefix[:-3]
      if self.prev_have_next:
        self.prefix += '\u2502  '
      else:
        self.prefix += '   '
      self.upd_prefix = False

    self.prev_have_next = is_next
    if is_next:
      self.prefix += '\u251c'+'\u2500 '
    else:
      self.prefix += '\u2514'+'\u2500 '
    self.upd_prefix = True

  def print_node(self, node, is_next=True):
    self.increment_prefix(is_next)
    func = getattr(self, 'dump' + type(node).__name__)
    func(node)
    self.decrement_prefix()

  def print_node_list(self, string, lst, is_next=True):
    self.increment_prefix(is_next)
    self.dump(string)
    i = 0
    cnt = len(lst)
    while i < cnt:
      self.print_node(lst[i], i < cnt - 1)
      i += 1
    self.decrement_prefix()


  def dumpImport(self, imp):
    self.dump('Import')
    self.print_node(imp.lib, False)

  def dumpDeclaration(self, decl):
    self.dump('Declaration')
    self.print_node(decl.typ)
    self.print_node(decl.sym, False)

  def dumpVariableDeclaration(self, decl):
    self.dump('VariableDeclaration')
    if decl.assign is not None:
      self.print_node(decl.decl)
      self.print_node(decl.assign, False)
    else:
      self.print_node(decl.decl, False)

  def dumpFunctionDeclaration(self, fun):
    self.dump('FunctionDeclaration')
    self.print_node(fun.typ)
    self.print_node(fun.sym)
    self.print_node_list('Arguments', fun.args, False)

  def dumpFunctionDefinition(self, fun):
    self.dump('FunctionDefinition')
    self.print_node(fun.proto)
    self.print_node_list('FunctionBody', fun.content, False)

  def dumpInstruction(self, instruction):
    self.dump('Instruction')
    self.print_node(instruction.expr, False)

  def dumpExpression(self, expr):
    # Dirty hack to compensate that we do not print anything. This deforms the AST a little, but
    # give us more clarity by removing useless informations (an expression is always a list of
    # operations resulting in a single value)
    self.decrement_prefix()
    self.print_node_list('Expression', expr.contents, False)
    self.increment_prefix(False)

  def dumpFunctionCall(self, call):
    self.dump('FunctionCall')
    self.print_node(call.sym)
    self.print_node_list('Arguments', call.args, False)

  def dumpVariableUsage(self, use):
    self.dump('VariableUsage')
    self.print_node(use.var, False)

  def dumpVariableAssignment(self, assign):
    self.dump('VariableAssignment')
    self.print_node(assign.var)
    self.print_node(assign.assign, False)

  def dumpAssignment(self, assign):
    self.dump('Assignment')
    self.print_node(assign.expr)

  def dumpReturn(self, ret):
    self.dump('Return')
    self.print_node(ret.expr, False)

  def dumpType(self, typ):
    self.dump('Type')
    self.print_node(typ.sym, False)

  def dumpBuiltinType(self, typ):
    self.dump('BuiltinType: ' + typ.name)

  def dumpArray(self, arr):
    self.dump('Array')
    self.print_node(arr.typ, False)

  def dumpSymbol(self, sym):
    self.dump('Symbol: ' + sym.name)

  def dumpNumber(self, num):
    self.dump('Number: ' + num.num)

  def dumpString(self, string):
    self.dump('String: ' + string.string)
