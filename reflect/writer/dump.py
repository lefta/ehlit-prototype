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

def indent(fn):
  def fn_wrapper(cls, node, is_next=True):
    cls.increment_prefix(is_next)
    fn(cls, node)
    cls.decrement_prefix()
  return fn_wrapper


class DumpWriter:
  def __init__(self, ast):
    self.prefix = ''
    logging.debug('')
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
    func = getattr(self, 'dump' + type(node).__name__)
    func(node, is_next)

  def print_node_list(self, string, lst, is_next=True):
    self.increment_prefix(is_next)
    self.dump(string)
    i = 0
    cnt = len(lst)
    while i < cnt:
      self.print_node(lst[i], i < cnt - 1)
      i += 1
    self.decrement_prefix()


  @indent
  def print_str(self, s):
    self.dump(s)

  @indent
  def dumpImport(self, imp):
    self.dump('Import')
    self.print_node(imp.lib)
    self.print_node_list('Symbols found', imp.syms, False)

  @indent
  def dumpDeclaration(self, decl):
    self.dump('Declaration')
    self.print_node(decl.typ)
    self.print_node(decl.sym, False)

  @indent
  def dumpVariableDeclaration(self, decl):
    self.dump('VariableDeclaration')
    if decl.assign is not None:
      self.print_node(decl.decl)
      self.print_node(decl.assign, False)
    else:
      self.print_node(decl.decl, False)

  @indent
  def dumpFunctionDeclaration(self, fun):
    self.dump('FunctionDeclaration')
    self.print_node(fun.typ)
    self.print_node(fun.sym)
    self.print_node_list('Arguments', fun.args, False)

  @indent
  def dumpFunctionDefinition(self, fun):
    self.dump('FunctionDefinition')
    self.print_node(fun.proto)
    self.print_node_list('FunctionBody', fun.body, False)

  @indent
  def dumpStatement(self, stmt):
    self.dump('Statement')
    self.print_node(stmt.expr, False)

  def dumpExpression(self, expr, is_next):
    self.print_node_list('Expression', expr.contents, is_next)

  @indent
  def dumpFunctionCall(self, call):
    if call.is_cast:
      self.dump('Cast')
      self.print_node(call.sym)
      self.print_node(call.args[0], False)
    else:
      self.dump('FunctionCall')
      self.print_node(call.sym)
      self.print_node_list('Arguments', call.args, False)

  @indent
  def dumpVariableAssignment(self, assign):
    self.dump('VariableAssignment')
    self.print_node(assign.var)
    self.print_node(assign.assign, False)

  @indent
  def dumpAssignment(self, assign):
    self.dump('Assignment')
    if assign.operator is not None:
      self.print_node(assign.operator)
    self.print_node(assign.expr, False)

  @indent
  def dumpControlStructure(self, struct):
    self.dump('ControlStructure: ' + struct.name)
    if struct.cond is not None:
      self.print_node(struct.cond)
    self.print_node_list("ControlStructureBody", struct.body, False)

  def dumpCondition(self, cond, is_next):
    self.print_node_list("ConditionBranches", cond.branches, is_next)

  @indent
  def dumpReturn(self, ret):
    self.dump('Return')
    self.print_node(ret.expr, False)

  @indent
  def dumpReference(self, ref):
    self.dump('Reference')
    self.print_node(ref.typ, False)

  @indent
  def dumpOperator(self, op):
    self.dump('Operator: ' + op.op)

  @indent
  def dumpType(self, typ):
    self.dump('Type')
    if typ.is_const:
      self.print_str('Modifiers: const')
    self.print_node(typ.sym, False)

  @indent
  def dumpBuiltinType(self, typ):
    self.dump('BuiltinType: ' + typ.name)

  @indent
  def dumpArray(self, arr):
    self.dump('Array')
    self.print_node(arr.typ, False)

  @indent
  def dumpSymbol(self, sym):
    self.dump('Symbol: ' + sym.name)

  @indent
  def dumpNumber(self, num):
    self.dump('Number: ' + num.num)

  @indent
  def dumpString(self, string):
    self.dump('String: ' + string.string)

  @indent
  def dumpNullValue(self, stmt):
    self.dump('NullValue')

  @indent
  def dumpReferencedValue(self, ref):
    self.dump('ReferencedValue')
    self.print_node(ref.val, False)

  @indent
  def dumpPrefixOperatorValue(self, val):
    self.dump('PrefixOperatorValue')
    self.print_str('Operator: %s' % val.op)
    self.print_node(val.val, False)

  @indent
  def dumpSuffixOperatorValue(self, val):
    self.dump('SuffixOperatorValue')
    self.print_str('Operator: %s' % val.op)
    self.print_node(val.val, False)
