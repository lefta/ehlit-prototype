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

"""
	Reflect test case

	This module contains a class with tools to help Reflect test writing
"""

import io
from inspect import getsourcefile
import os.path, sys, logging
from unittest import TestCase

file_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))

sys.path.insert(0, file_dir[:file_dir.rfind(os.path.sep)])
import reflect
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


""" Extent to unittest.TestCase to ease writing of tests for Reflect """
class ReflectTestCase(TestCase):
	def __init__(self, arg):
		super().__init__(arg)
		self.maxDiff = None
		os.chdir(file_dir)
		logging.basicConfig(format='%(message)s', level=logging.INFO)

	"""
		Discover all tests

		All '.ref' files in the directory passed as parameter are considered as tests. A test must
		have a '.ref.c' file associated containing the expected output.

		@param directory The directory where tests are located
		@return list A list of tests
	"""
	def discover_tests(self, directory):
		return [x for x in os.listdir(directory) if x.endswith('.ref')]

	"""
		Run the Reflect compiler

		@param opts The arguments to provide to the compiler. This must be a dict compatible with
			Reflect options object
		@return dict Results of the compilation (stdout, stderr)
	"""
	def run_compiler(self, opts):
		with Pipe() as output:
			reflect.build(opts)
			return output

	"""
		Compile C code from a Reflect source file

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
			raise AssertionError(str(msg))
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
