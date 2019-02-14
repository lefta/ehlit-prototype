# Copyright © 2018 Cedric Legrand
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

import os.path
from common import EhlitTestCase


class TestCParser(EhlitTestCase):
    """ Test the interfacing with C """

    def __init__(self, arg):
        super().__init__(arg)
        self.test_dir = 'c_parser'
        self.cases = self.discover_tests(self.test_dir)

    def test_c_parser(self):
        for c in self.cases:
            with self.subTest(case=c):
                f = os.path.join(self.test_dir, c)
                self.assert_dumps_to(f)

    def test_c_variadic_function_call(self):
        self.assert_compiles('c_parser/function.eh')

    def test_c_macro_usage(self):
        self.assert_compiles('c_parser/macro.eh')
