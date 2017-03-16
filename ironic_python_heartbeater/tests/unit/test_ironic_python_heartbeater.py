#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import unittest

import mock

from ironic_python_heartbeater import ironic_python_heartbeater as iph


class IronicPythonHeartbeaterTestCase(unittest.TestCase):

    def test__parse_kernel_cmdline(self):
        fake_kernel_opts = "spam=ham foo=bar"
        expected_opts = {'spam': 'ham', 'foo': 'bar'}
        with mock.patch.object(iph, 'open',
                               new=mock.mock_open(read_data=fake_kernel_opts)):
            self.assertEqual(expected_opts, iph._parse_kernel_cmdline())
