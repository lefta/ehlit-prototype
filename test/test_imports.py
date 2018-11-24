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

from common import EhlitTestCase
from ehlit.parser import parse, ParseError


class TestImports(EhlitTestCase):
    """ Test import files behavior """

    def __init__(self, arg):
        super().__init__(arg)

    def test_import_generation(self):
        output = self.compile('import_tests/source.eh')
        self.assertEqual(output.stderr, '')
        self.assert_files_equal('import_tests/source.inc.eh',
                                'out/include/import_tests/source.eh')

    def test_importing_file(self):
        ast = None
        failure = None

        class opts:
            output_file = '-'
            output_import_file = 'out/include/import_tests/importing.eh'
            source = 'import_tests/importing.eh'
            verbose = False
        try:
            ast = parse(opts.source)
            ast.build_ast(opts)
        except ParseError as err:
            failure = err
        self.assertEqual(None, failure)
        self.assert_declares(ast.nodes[0], 'global')
        self.assert_declares(ast.nodes[0], 'fun_proto_args')
