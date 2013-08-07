import mock
import random
import subprocess
import time
import unittest

import server

amcp = server.AMCPServer(8000)


class MockProcess():
    def __init__(self):
        self.pid = random.randint(10000, 20000)

    def kill(self):
        pass


class TestAMCP(unittest.TestCase):

    @mock.patch('time.sleep')
    @mock.patch('subprocess.Popen')
    def test_all_systems(self, mock_popen, mock_sleep):
        mock_popen.return_value = MockProcess()
        for system in amcp.systems:
            for action in amcp.systems[system]:
                amcp.catch_all('/%s/%s' % (system, action), [1.0])


if __name__ == '__main__':
    unittest.main()
