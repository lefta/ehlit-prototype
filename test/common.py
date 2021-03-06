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

"""
Ehlit test case

This module contains a class with tools to help Ehlit test writing
"""

import io
import logging
import os.path
import sys
from inspect import getsourcefile
from unittest import TestCase
import ehlit
import ehlit.parser
import ehlit.writer

__unittest = True


class Pipe():
    """
        Output (stdout & stderr) redirection

        Usage: `with Pipe() as output:`

        @variable stdout string
        @variable stderr string
    """

    def __enter__(self):
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        return self

    def __exit__(self, *args):
        self.stdout = sys.stdout.getvalue()
        self.stderr = sys.stderr.getvalue()
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class EhlitTestCase(TestCase):
    """ Extent to unittest.TestCase to ease writing of tests for the Ehlit language """

    def __init__(self, arg):
        super().__init__(arg)
        self.maxDiff = None
        os.chdir(os.path.dirname(os.path.abspath(getsourcefile(lambda: 0))))

    def setUp(self):
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
        self.logStream = io.StringIO()
        self.logHandler = logging.StreamHandler(self.logStream)
        self.log = logging.getLogger()
        for h in self.log.handlers:
            self.log.removeHandler(h)
        self.log.addHandler(self.logHandler)

    def tearDown(self):
        self.log.removeHandler(self.logHandler)
        self.logHandler.close()

    def discover_tests(self, directory):
        """
        Discover all tests

        All '.eh' files in the directory passed as parameter are considered as tests. A test must
        have a '.eh.c' file associated containing the expected output.

        @param directory The directory where tests are located
        @return list A list of tests
        """
        return [x for x in os.listdir(directory) if x.endswith('.eh')]

    def run_compiler(self, opts):
        """
        Run the Ehlit compiler

        @param opts The arguments to provide to the compiler. This must be a dict compatible with
        Ehlit options object
        @return dict Results of the compilation (stdout, stderr)
        """
        with Pipe() as output:
            ehlit.build(opts)
            return output

    def compile(self, src):
        """
        Compile C code from a Ehlit source file

        @param src The file to build
        @return dict Results of the compilation (stdout, stderr)
        """
        class opts:
            output_file = '-'
            output_import_file = None
            source = src
            verbose = False
        return self.run_compiler(opts)

    def dump(self, src):
        """
        Dump the AST resulting from parsing a file

        @param src The file to parse
        @return str Dump of the AST
        """
        self.setUp()
        with Pipe():
            class args:
                source = ''
                output_import_file = '-'
            failure = None
            try:
                ast = ehlit.parser.parse(src)
                ast.build_ast(args)
                ehlit.writer.WriteDump(ast)
            except ehlit.parser.ParseError as err:
                failure = '\n' + str(err)
            if failure is not None:
                self.fail(failure)
            self.logHandler.flush()
            self.tearDown()
            return self.logStream.getvalue().replace('\n--- AST ---\n', '')

    def assert_error(self, src, error):
        """
        Check that the compiler raises an error when building src

        @param src The file to compile
        @param error The error that must be triggered
        """
        msg = ''
        try:
            self.compile(src)
        except Exception as err:
            msg = str(err)
        self.assertEqual(msg, error)

    def assert_error_file(self, src, error_file):
        """
        Check that the compiler raises an error containing the same contents than src.err

        @param src The file to compile
        @param error_file The file to check the error against
        """
        with open(error_file, 'r', encoding="utf-8") as f:
            return self.assert_error(src, f.read())

    def assert_compiles(self, src):
        """
        Check the compiler output for file src against the contents of src.c

        @param src The file to compile
        """
        result = None
        failure = None
        try:
            result = self.compile(src)
        except Exception as err:
            failure = '\n' + str(err)
        if failure is not None:
            self.fail(failure)
        if result is None:
            self.fail('No output have been generated')
        self.assertEqual(result.stderr, "")
        self.assert_equal_to_file(result.stdout, "%s.c" % src)

    def assert_files_equal(self, file1, file2):
        """
        Check that 2 files have the exact same content

        @param file1 The first file to check
        @param file2 The second file to check
        """
        with open(file1, 'r', encoding="utf-8") as f:
            self.assert_equal_to_file(f.read(), file2)

    def assert_equal_to_file(self, string, filename, repls=None):
        """
        Check that a string is equal to a file contents

        @param string The string to test
        @param filename Path to the file containing reference output
        @param repls Dict of named replacements to be made in the expectation file
        """
        with open(filename, 'r', encoding="utf-8") as f:
            expected = f.read()
        if repls is not None:
            expected = expected.format(**repls)
        self.assertEqual(string, expected)

    def assert_dumps_to(self, src, repls=None):
        """
        Check that an AST dump of the file contents matches the contents of src.dump

        @param src The source file to test
        @param repls Dict of named replacements to be made in the expected dump file
        """
        dump = self.dump(src)
        self.assertNotEqual(dump, '', 'No dump have been generated.')
        self.assert_equal_to_file(dump, '{}.dump'.format(src), repls)

    def assert_declares(self, node, sym):
        res = node.find_declaration(sym)
        self.assertEqual(None, res._error)
        self.assertNotEqual(0, len(res))

    def assert_not_declares(self, node, sym, expected_err=None):
        res = node.find_declaration(sym)
        self.assertEqual(expected_err, res._error)
        self.assertEqual(0, len(res))
