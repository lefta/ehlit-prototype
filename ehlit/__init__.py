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

import logging

def build(args):
  # Avoid importing submodules in global scope, otherwise they may use the logger before it is
  # initialized
  from ehlit.parser import parse, ParseError
  from ehlit.writer import WriteSource, WriteDump, WriteImport
  from ehlit.options import check_arguments

  check_arguments(args)
  logging.debug('building %s to %s\n', args.source, args.output_file)

  failure = None
  ast = None
  try:
    ast = parse(args.source)
    ast.build(args)
  except ParseError as err:
    failure = err

  if ast and args.verbose:
    WriteDump(ast)

  if failure is not None and failure.max_level > ParseError.Severity.Warning:
    raise failure

  WriteSource(ast, args.output_file)
  WriteImport(ast, args.output_import_file)

  if failure is not None:
    raise failure
