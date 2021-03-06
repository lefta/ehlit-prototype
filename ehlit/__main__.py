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

import logging
from ehlit import options

opts: options.OptionsStruct = options.parse_arguments()

logging.addLevelName(logging.ERROR, '\033[1;31mError\033[m: ')
logging.addLevelName(logging.WARNING, '\033[1;35mWarning\033[m: ')
logging.addLevelName(logging.INFO, '\033[1;37mNote\033[m: ')
logging.addLevelName(logging.DEBUG, '> ')
logging.basicConfig(format='%(levelname)s%(message)s',
                    level=logging.DEBUG if opts.verbose else logging.INFO)

# Do not import submodules before the logger is initialized, as they may use it
from ehlit.parser import ParseError
from ehlit import build

try:
    build(opts)

except ParseError as err:
    for f in err.failures:
        if f.severity < ParseError.Severity.Error:
            logging.warning(str(f))
        else:
            logging.error(str(f))

    logging.info(err.summary)
    if err.max_level > ParseError.Severity.Warning:
        exit(-1)

except options.ArgError as err:
    logging.error(str(err))
    exit(-1)
