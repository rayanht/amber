#!/usr/bin/env python
#
# Copyright 2018 The Amber Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import difflib
import optparse
import os
import re
import subprocess
import sys
import tempfile

class TestCase:
  def __init__(self, input_path, parse_only):
    self.input_path = input_path
    self.parse_only = parse_only

    self.results = {}

  def IsExpectedFail(self):
    fail_re = re.compile('^.+[.]expect_fail[.]amber')
    return fail_re.match(self.GetInputPath())

  def IsParseOnly(self):
    return self.parse_only

  def GetInputPath(self):
    return self.input_path

  def GetResult(self, fmt):
    return self.results[fmt]


class TestRunner:
  def RunTest(self, tc):
    print "Testing %s" % tc.GetInputPath()

    cmd = [self.options.test_prog_path]
    if tc.IsParseOnly():
      cmd += ['-p']
    cmd += [tc.GetInputPath()]

    try:
      subprocess.check_output(cmd)
    except Exception as e:
      if not tc.IsExpectedFail():
        print e
      return False

    return True


  def RunTests(self):
    for tc in self.test_cases:
      result = self.RunTest(tc)

      if not tc.IsExpectedFail() and not result:
        self.failures.append(tc.GetInputPath())
      elif tc.IsExpectedFail() and result:
        print("Expected: " + tc.GetInputPath() + " to fail but passed.")
        self.failures.append(tc.GetInputPath())

  def SummarizeResults(self):
    if len(self.failures) > 0:
      self.failures.sort()

      print '\nSummary of Failures:'
      for failure in self.failures:
        print failure

    print
    print 'Test cases executed: %d' % len(self.test_cases)
    print '  Successes: %d' % (len(self.test_cases) - len(self.failures))
    print '  Failures:  %d' % len(self.failures)
    print


  def Run(self):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    usage = 'usage: %prog [options] (file)'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--build-dir',
                      default=os.path.join(base_path, 'out', 'Debug'),
                      help='path to build directory')
    parser.add_option('--test-dir',
                      default=os.path.join(os.path.dirname(__file__), 'cases'),
                      help='path to directory containing test files')
    parser.add_option('--test-prog-path', default=None,
                      help='path to program to test')
    parser.add_option('--parse-only',
                      action="store_true", default=False,
                      help='only parse test cases; do not execute')

    self.options, self.args = parser.parse_args()

    if self.options.test_prog_path == None:
      test_prog = os.path.abspath(os.path.join(self.options.build_dir, 'amber'))
      if not os.path.isfile(test_prog):
        print "Cannot find test program %s" % test_prog
        return 1

      self.options.test_prog_path = test_prog

    if not os.path.isfile(self.options.test_prog_path):
      print "--test-prog-path must point to an executable"
      return 1

    input_file_re = re.compile('^.+[.]amber')
    self.test_cases = []

    if self.args:
      for filename in self.args:
        input_path = os.path.join(self.options.test_dir, filename)
        if not os.path.isfile(input_path):
          print "Cannot find test file '%s'" % filename
          return 1

        self.test_cases.append(TestCase(input_path, self.options.parse_only))

    else:
      for file_dir, _, filename_list in os.walk(self.options.test_dir):
        for input_filename in filename_list:
          if input_file_re.match(input_filename):
            input_path = os.path.join(file_dir, input_filename)
            if os.path.isfile(input_path):
              self.test_cases.append(
                  TestCase(input_path, self.options.parse_only))

    self.failures = []

    self.RunTests()
    self.SummarizeResults()

    return len(self.failures) != 0

def main():
  runner = TestRunner()
  return runner.Run()


if __name__ == '__main__':
  sys.exit(main())
