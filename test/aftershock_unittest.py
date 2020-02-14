#!/usr/bin/env python

"""aftershock_unittest runs unit tests on the aftershock script in shakemap-aqms"""

import os
import unittest
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
        cls.insideRegionEvent.update({"eventID": (cls.event.get("netid") + str(cls.event.get("id")))})
        cls.outsideRegionEvent.update({"eventID": (cls.event.get("netid") + str(cls.event.get("id")))})
        dbfile="../test/data/aftershock_excludes.db"
        logfile="../bin/aftershock.log"
        if os.path.isfile(dbfile):
            os.remove(dbfile)
        if os.path.isfile(logfile):
            os.remove(logfile)
        cls.DB = aftershockDB("../test")
        cls._connection = sqlite3.connect(cls.DB.db_file, timeout=15, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cls._cursor = cls._connection.cursor()
        if cls._connection is None:
            raise RuntimeError('Could not connect to %s' % cls.DB.db_file)
    def testAInsertAftershockZone(self):
        """Tests to make sure aftershock flag is set"""
        self.assertTrue('aftershock' in self.queue_conf)
        """Tests to make sure you can insert an aftershock zone properly"""
        self.assertTrue(self.DB.insertAftershockZone(self.event))
    def testBCheckAftershockZone(self):
        print(self.DB.checkAftershockZone(self.insideRegionEvent))
        print(self.DB.checkAftershockZone(self.outsideRegionEvent))

#        self.inRegion = False
#        """Test region for an event inside the exclusion zone"""
#        self.inRegionQuery = """SELECT DISTINCT eruleid,emaglimit,eplacename,(((((ev2x-(117.33))*(ev3y-(35.83))) - ((ev3x-(117.33))*(ev2y-(35.83))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0 AND ((((ev3x-(117.33))*(ev1y-(35.83))) - ((ev1x-(117.33))*(ev3y-(35.83))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0 AND ((((ev1x-(117.33))*(ev2y-(35.83))) - ((ev2x-(117.33))*(ev1y-(35.83))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0) as exclude from excludes;"""
#        self._cursor.execute(self.inRegionQuery)
#        self.rows = self._cursor.fetchall()
#        for row in self.rows:
#            print(row)
#            self.exclude = row[3]
#            if self.exclude == 1:
#                self.inRegion = True
#                break
#        self.assertTrue(self.inRegion)

    def testOutsideAftershockZone(self):
        self.inRegion = False
        """Test region for an event outside the exclusion zone"""
        self.inRegionQuery = """SELECT DISTINCT eruleid,emaglimit,eplacename,(((((ev2x-(117.15))*(ev3y-(36.61))) - ((ev3x-(117.15))*(ev2y-(36.61))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0 AND ((((ev3x-(117.15))*(ev1y-(36.61))) - ((ev1x-(117.15))*(ev3y-(36.61))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0 AND ((((ev1x-(117.15))*(ev2y-(36.61))) - ((ev2x-(117.15))*(ev1y-(36.61))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0) as exclude from excludes;"""
        self._cursor.execute(self.inRegionQuery)
        self.rows = self._cursor.fetchall()
        for row in self.rows:
            print(row)
            self.exclude = row[3]
            if self.exclude == 1:
                self.inRegion = True
                break
        self.assertFalse(self.inRegion)


    @classmethod
    def tearDownClass(cls):
        cls._cursor.close()
        cls._connection.close()
        cls._connection = None
        cls._cursor = None


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
