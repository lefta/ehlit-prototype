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

from argparse import ArgumentParser
from os import path, makedirs


class OptionsStruct:
  output_import_file: str
  source: str


class ArgError(Exception):
  def __init__(self, msg):
    self.msg = msg


def check_arguments(args):
  src, ext = path.splitext(args.source)
  if ext != ".eh":
    raise ArgError("%s: not an ehlit source file" % args.source)
  elif not path.isfile(args.source):
    raise ArgError("%s: no such file or directory" % args.source)

  if args.output_file is None:
    args.output_file = 'out/src/' + src + ".c"
  if args.output_file != '-':
    makedirs(path.dirname(args.output_file), exist_ok=True)

  if args.output_import_file is None:
    args.output_import_file = 'out/include/' + src + ".eh"
  if args.output_import_file != '-':
    makedirs(path.dirname(args.output_import_file), exist_ok=True)


def parse_arguments():
  parser = ArgumentParser(description="Compile Ehlit source files")

  parser.add_argument('source', help="Source files to build")

  # Generation options
  gen_args = parser.add_argument_group('Generation arguments')
  gen_args.add_argument("-o", "--gen-output", dest="output_file",
                        help="File where to write the output. You may use '-' for stdout")
  gen_args.add_argument("--gen-import-output", dest="output_import_file",
                        help="File where to write the import file. You may use '-' for stdout")

  gen_args.add_argument("-v", "--gen-verbose", dest="verbose", action="store_true",
                        help="Print debug messages")
  gen_args.add_argument("-q", "--gen-quiet", dest="verbose", action="store_false", default=False,
                        help="Do not print debug messages [default]")

  # Warning options
  warn_args = parser.add_argument_group('Warning behavior arguments')
  warn_args.add_argument("--warn-error", dest="warn_error", action="store_true", default=True,
                         help="Treat all warnings as errors")
  warn_args.add_argument("--warn-no-error", dest="warn_error", action="store_false",
                         help="Do not treat any warning as error [default]")

  return parser.parse_args()
