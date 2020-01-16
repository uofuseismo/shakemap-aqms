#!/usr/bin/env python

"""aftershock_unittest runs unit tests on the aftershock script in shakemap-aqms"""

import unittest

import sqlite3

import aftershock

from shakemap.utils.config import get_config_paths
from shakemap_aqms.util import (get_aqms_config,
                                get_eqinfo)


class TestAftershock(unittest.TestCase):
    """Checks the values of the outputs of aftershock"""
    def setUp(self):
        install_path, data_path = get_config_paths()
        self.queue_conf = get_aqms_config('aqms_queue')
        self.aftershockDB = aftershock.aftershockDB(install_path)
    def testAftershockDB(self):
        """Tests to make sure a DB was created properly"""
        self.assertTrue(sqlite3.connect(self.aftershockDB.db_file, timeout=15))
        """Tests to make sure aftershock flag is set"""
        self.assertTrue('aftershock' in self.queue_conf)
#        if self._connection is None:
#            raise RuntimeError('Could not connect to %s' % self.db_file)


#    def testGetDistance(self):
#        """Tests the function that returns distance between two points"""
        # First check for the expected values in kilometers
#        self.assertTrue(round(getDistance(self.pointA, self.pointB))==self.expectedDistanceKM)
        # Now check for the expected values in miles
#        self.assertTrue(round(getDistance(self.pointA, self.pointB, True))==self.expectedDistanceMI)

#    def testCheckThresholds(self):
#        """Test thresholds are being used properly"""
#        self.assertTrue(len(checkThresholds(self.SAMessage)) == self.expectedThresholdLen)

#    def testCheckLastProcessedEvent(self):
#        """Test that we can check against the values of the last event to be processed"""
#        self.assertFalse(checkLastProcessedEvent(34, -119, 1560384464))


if __name__ == '__main__':
    unittest.main()
