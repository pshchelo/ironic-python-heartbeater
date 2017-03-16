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
