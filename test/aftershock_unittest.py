#!/usr/bin/env python

"""aftershock_unittest runs unit tests on the aftershock script in shakemap-aqms"""

import os
import unittest
import time
import logging
import sqlite3

from aftershock import aftershockDB

from shakemap.utils.config import get_config_paths
from shakemap_aqms.util import (get_aqms_config,
                                get_eqinfo)


class TestAftershock(unittest.TestCase):
    """Checks the values of the outputs of aftershock"""
    @classmethod
    def setUpClass(cls):
        install_path, data_path = get_config_paths()
        cls.queue_conf = get_aqms_config('aqms_queue')
        cls.event = {"lat": 35.770, "lon": 117.599, "id": 12345678, "netid": "ci", "mag": 7.1, "emaglimit": 2}
        cls.insideRegionEvent = {"lat": 35.83, "lon": 117.33, "id": 22345678, "netid": "ci", "mag": 5.1, "emaglimit": 2}
        cls.outsideRegionEvent = {"lat": 36.61, "lon": 117.15, "id": 32345678, "netid": "ci", "mag": 5.0, "emaglimit": 2}
        cls.event.update({"eventID": (cls.event.get("netid") + str(cls.event.get("id")))})
        cls.insideRegionEvent.update({"eventID": (cls.insideRegionEvent.get("netid") + str(cls.insideRegionEvent.get("id")))})
        cls.outsideRegionEvent.update({"eventID": (cls.outsideRegionEvent.get("netid") + str(cls.outsideRegionEvent.get("id")))})
        dbfile="data/aftershock_excludes.db"
        logfile="logs/aftershock.log"
        if os.path.isfile(dbfile):
            os.remove(dbfile)
        if os.path.isfile(logfile):
            os.remove(logfile)
        cls.DB = aftershockDB("../test")
        cls._connection = sqlite3.connect(cls.DB.db_file, timeout=15, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cls._cursor = cls._connection.cursor()
        if cls._connection is None:
            raise RuntimeError('Could not connect to %s' % cls.DB.db_file)
    def testA_DefineAftershockZone(self):
        """Tests defining an aftershock zone"""
        # Tests to make sure aftershock flag is set
        self.assertTrue('aftershock' in self.queue_conf)
        """Tests to make sure you can insert an aftershock zone properly"""
        self.assertEqual(self.DB.defineAftershockZone(self.event), 0)
        time.sleep(5)
        """Tests that previous event of same ID will be replaced properly"""
        self.assertEqual(self.DB.defineAftershockZone(self.event), 0)

        
    def testB_CheckAftershockZone(self):
        """Tests that check for aftershock zone region accuracy"""
        # Tests for an event that should be in the aftershock zone region
        self.assertEqual(self.DB.defineAftershockZone(self.insideRegionEvent), 1)
        # Tests for an event that should be outside the aftershock zone region
        self.assertEqual(self.DB.defineAftershockZone(self.outsideRegionEvent), 0)

    def testC_CleanupAftershockZones(self):
        """Tests that check for proper aftershock database cleanup"""
        # Tests for an event that should be cleaned up
        self.sql = 'UPDATE excludes SET added = "13-Jan-2020 21:09:50" WHERE eplacename = "ci12345678";'
        self.__class__._cursor.execute(self.sql)
        self.__class__._connection.commit()
        self.assertTrue(self.DB.cleanupAftershockZones(2))



    @classmethod
    def tearDownClass(cls):
        cls._cursor.close()
        cls._connection.close()
        cls._connection = None
        cls._cursor = None


if __name__ == '__main__':
    unittest.main()
