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

"""
	Ehlit test case

	This module contains a class with tools to help Ehlit test writing
"""

import io
import re
from inspect import getsourcefile
import os.path, sys, logging
from unittest import TestCase

file_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))

sys.path.insert(0, file_dir[:file_dir.rfind(os.path.sep)])
import ehlit
import ehlit.parser
import ehlit.writer
sys.path.pop(0)

__unittest = True


"""
  Output (stdout & stderr) redirection

	Usage: `with Pipe() as output:`

	@variable stdout string
	@variable stderr string
"""

class Pipe():
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


""" Extent to unittest.TestCase to ease writing of tests for the Ehlit language """
class EhlitTestCase(TestCase):
	def __init__(self, arg):
		super().__init__(arg)
		self.maxDiff = None
		os.chdir(file_dir)

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

	"""
		Discover all tests

		All '.eh' files in the directory passed as parameter are considered as tests. A test must
		have a '.eh.c' file associated containing the expected output.

		@param directory The directory where tests are located
		@return list A list of tests
	"""
	def discover_tests(self, directory):
		return [x for x in os.listdir(directory) if x.endswith('.eh')]

	"""
		Run the Ehlit compiler

		@param opts The arguments to provide to the compiler. This must be a dict compatible with
			Ehlit options object
		@return dict Results of the compilation (stdout, stderr)
	"""
	def run_compiler(self, opts):
		with Pipe() as output:
			ehlit.build(opts)
			return output

	"""
		Compile C code from a Ehlit source file

		@param src The file to build
		@return dict Results of the compilation (stdout, stderr)
	"""
	def compile(self, src):
		class opts:
			output_file = '-'
			output_import_file = None
			source = src
			verbose = False
		return self.run_compiler(opts)

	# TODO This is only temporary waiting for C compatibility to be fully implemented
	dump_repl = re.compile(r'(c_compat: unimplemented: [a-zA-Z_]+\n)', flags=re.MULTILINE)
	"""
		Dump the AST resulting from parsing a file

		@param src The file to parse
		@return str Dump of the AST
	"""
	def dump(self, src):
		self.setUp()
		with Pipe():
			class args:
				source = ''
				output_import_file = '-'
			ast = ehlit.parser.parse(src)
			ast.build(args)
			ehlit.writer.WriteDump(ast)
			self.logHandler.flush()
			self.tearDown()
			return re.sub(self.dump_repl, '', self.logStream.getvalue().replace('\n--- AST ---\n', ''))

	"""
		Check that the compiler raises an error when building src

		@param src The file to compile
		@param error The error that must be triggered
	"""
	def assert_error(self, src, error):
		msg = ''
		try:
			self.compile(src)
		except Exception as err:
			msg = str(err)
		self.assertEqual(msg, error)

	"""
		Check that the compiler raises an error containing the same contents than src.err

		@param src The file to compile
		@param error_file The file to check the error against
	"""
	def assert_error_file(self, src, error_file):
		with open(error_file, 'r') as f:
			return self.assert_error(src, f.read())

	"""
		Check the compiler output for file src against the contents of src.c

		@param src The file to compile
	"""
	def assert_compiles(self, src):
		result = None
		try:
			result = self.compile(src)
		except Exception as err:
			msg = str(err)
		if result is None:
			raise AssertionError(str('No output have been generated'))
		self.assertEqual(result.stderr, "")
		self.assert_equal_to_file(result.stdout, "%s.c" % src)

	"""
		Check that a string is equal to a file contents

		@param string The string to test
		@param filename Path to the file containing reference output
	"""
	def assert_equal_to_file(self, string, filename):
		with open(filename, 'r') as f:
			expected = f.read()
		self.assertEqual(string, expected)

	"""
		Check that an AST dump of the file contents matches the contents of src.dump

		@param src The source file to test
	"""
	def assert_dumps_to(self, src):
		dump = self.dump(src)
		self.assertNotEqual(dump, '', 'No dump have been generated.')
		with open('{}.dump'.format(src), 'r') as f:
			self.assertEqual(dump, f.read())
