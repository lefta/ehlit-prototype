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

from reflect import options, build
from reflect.parser import ParseError

try:
  opts = options.parse_arguments()

  logging.addLevelName(logging.ERROR, '\033[1;31mError\033[m: ')
  logging.addLevelName(logging.WARNING, '\033[1;33mWarning\033[m: ')
  logging.addLevelName(logging.DEBUG, '> ')
  logging.basicConfig(format='%(levelname)s%(message)s',
    level=logging.DEBUG if opts.verbose else logging.INFO)

  build(opts)

except ParseError as err:
  logging.error('%d:%d: %s' % (err.line, err.col, err.msg))
  exit(-1)

except options.ArgError as err:
  logging.error(err)
  exit(-1)
