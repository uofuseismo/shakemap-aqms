#! /usr/bin/env python

# System imports
import os
import os.path
import logging
from logging.handlers import TimedRotatingFileHandler
import math
from datetime import datetime
from time import time

# Third-party imports
import sqlite3


class aftershockDB(object):
    """Class to build or retrieve a database for aftershock suppression. 
    The db file can be removed if the operator wants a fresh start.
    """
    def __init__(self, ipath):

        self.ASlogger = logging.getLogger('aftershock')
        self.ASlogger.setLevel(logging.INFO)
        self.ASlogger.propagate = False
        self.logFile = os.path.join(ipath, 'logs', 'aftershock.log')
        self.AShandler = TimedRotatingFileHandler(self.logFile,
                                                  when="d",
                                                  interval=1,
                                                  backupCount=60)
        self.ASlogger.addHandler(self.AShandler)
        self.ASlogger.info('aftershock DB initiated')

        exclude_table = """ CREATE TABLE excludes (
                                eid INTEGER PRIMARY KEY AUTOINCREMENT,
                                eruleid INTEGER NOT NULL,
                                ev1y REAL,
                                ev1x REAL,
                                ev2y REAL,
                                ev2x REAL,
                                ev3y REAL,
                                ev3x REAL,
                                emaglimit REAL DEFAULT 0.000,
                                eplacename TEXT,
                                added TEXT
                            ); """

        self.db_file = os.path.join(ipath, 'data', 'aftershock_excludes.db')
        db_exists = os.path.isfile(self.db_file)
        self._connection = sqlite3.connect(self.db_file, timeout=15, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        if self._connection is None:
            raise RuntimeError('Could not connect to %s' % self.db_file)
        self._connection.isolation_level = 'EXCLUSIVE'
        self._cursor = self._connection.cursor()
        self._cursor.execute('PRAGMA foreign_keys = ON')
        self._cursor.execute('PRAGMA journal_mode = WAL')
        if not db_exists:
            self._cursor.execute(exclude_table)



    def __del__(self):
        """Destructor.

        """
        if hasattr(self, '_connection') and self._connection is not None:
            self._disconnect()

    def _disconnect(self):
        self.commit()
        self._cursor.close()
        self._connection.close()
        self._connection = None
        self._cursor = None

    def commit(self):
        """Commit any operations to the database.
        """
        self._connection.commit()


    def insertAftershockZone(self, valuesDict):
        """Construct and insert a new aftershock exclusion zone into the database
        --source of the values--
        eid INTEGER PRIMARY KEY AUTOINCREMENT (keeps the triangle records unique)
        eruleid->comes from aftershock_define, determines if need to create or update zone
   
        (ev1y, ev1x, ev2y, ev2x, ev3y, ev3x)->three points of a triangle representing the region
        There are between 4-8 triangles constructed for a single aftershock exclusion zone
        After a single triangle is inserted a "dateline" check is run by the code.  
        If said triangle crosses this dateline, values are modified and yet another triangle is inserted into DB. 
        Values needed to construct the triangles:  mag, lon, lat

        emaglimit->magnitude limit for determining exclusion threshold, usually set to (mag - 2) 
        eplacename->is the event ID with net i.e. ci84838493
        added->the datetime added    
        """


        self.lat = valuesDict.get("lat")
        self.lon = valuesDict.get("lon")
        self.mag = valuesDict.get("mag")
        self.eventID = valuesDict.get("eventID")
        self.emaglimit = valuesDict.get("emaglimit")
        self.eruleID = 0

        sql = """SELECT max(eruleid) from excludes;"""
        self._cursor.execute(sql)
        rows = self._cursor.fetchall()
        for row in rows:
            if row[0] is not None:
                self.eruleID = row[0] + 1;
            self.ASlogger.info('Assigning eruleid %i to event %s' % (self.eruleID, self.eventID))

        gmdate = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    #
    # Got this formula from Morgan Page - sms 30apr2010
    # The old formula that I got from Lucy was making the zone too
    # big for large events. If we had another Sumatra event, the
    # aftershock zone would cover the entire Earth, and that is just
    # too broad a brush for this application. So Morgan dug out a
    # paper from her desk and found the following formula:
    # Wells and Coppersmith (1994) Surface rupture length (all slip types)
    # to magnitude
        ruptureLength = 10**(0.69 * self.mag - 3.22)
    #
    # Multiply by 2 for two rupture lengths
        ruptureLength = ruptureLength * 2
        self.ASlogger.info("Length is %f km" % ruptureLength)

        radToDeg = 57.295779
        earthradius = 6371            # earthradius in km
        sqrtThree = 1.732050807

        londiff = 2 * math.pi * ( ruptureLength / ( 2 * math.pi * earthradius ) ) * radToDeg
        eastlon = self.lon + londiff
        westlon = self.lon - londiff

        midlon   = londiff / 2
        eastlon2 = self.lon + midlon
        westlon2 = self.lon - midlon

        latdiff = 2 * math.pi * ( ( sqrtThree * ruptureLength / 2 ) / ( 2 * math.pi * earthradius ) ) * radToDeg
        northlat = self.lat + latdiff
        southlat = self.lat - latdiff

        self.ASlogger.info("Zone runs from %3.3f to %3.3f" % (eastlon,westlon))
        self.ASlogger.info("Lat goes from %3.3f to %3.3f" % (northlat,southlat))

        self.ASlogger.info("Proposed points are: ")
        self.ASlogger.info("%3.3f/%3.3f" % (self.lat,westlon))
        self.ASlogger.info("%3.3f/%3.3f" % (northlat,westlon2))
        self.ASlogger.info("%3.3f/%3.3f" % (northlat,eastlon2))
        self.ASlogger.info("%3.3f/%3.3f" % (self.lat,eastlon))
        self.ASlogger.info("%3.3f/%3.3f" % (southlat,eastlon2))
        self.ASlogger.info("%3.3f/%3.3f" % (southlat,westlon2))


        self.ASlogger.info("Triangles are:  ")
        self.ASlogger.info("%3.3f/%3.3f, %3.3f/%3.3f, %3.3f/%3.3f" % (self.lat, westlon,
          northlat, westlon2, northlat, eastlon2))
        self.ASlogger.info("%3.3f/%3.3f, %3.3f/%3.3f, %3.3f/%3.3f" % (self.lat, westlon,
          northlat, eastlon2, southlat, westlon2))
        self.ASlogger.info("%3.3f/%3.3f, %3.3f/%3.3f, %3.3f/%3.3f" % (northlat,
          eastlon2, self.lat, eastlon, southlat, westlon2))
        self.ASlogger.info("%3.3f/%3.3f, %3.3f/%3.3f, %3.3f/%3.3f" % (self.lat, eastlon,
          southlat, eastlon2, southlat, westlon2))

        triangleDict = {0: [self.lat, westlon, northlat, westlon2, northlat, eastlon2],
                        1: [self.lat, westlon, northlat, eastlon2, southlat, westlon2],
                        2: [northlat, eastlon2, self.lat, eastlon, southlat, westlon2],
                        3: [self.lat, eastlon, southlat, eastlon2, southlat, westlon2]}

        self.DBemaglimit = self.mag - self.emaglimit;
        self.ASlogger.info("Magnitude level is %3.1f" % self.DBemaglimit)


        for key, value in triangleDict.items():
            datelineflag = 0
            insertQuery = """INSERT INTO excludes (eruleid,ev1y,ev1x,ev2y,ev2x,ev3y,ev3x,emaglimit,eplacename,added)
                             VALUES ('%d','%4.2f','%4.2f','%4.2f','%4.2f','%4.2f','%4.2f','%3.1f','%s','%s');
                          """ % (self.eruleID, value[0], value[1], value[2], value[3], value[4], value[5], self.DBemaglimit, self.eventID, gmdate)
            self.ASlogger.info("SQL is " + insertQuery)
            self._cursor.execute(insertQuery)
            self.commit()
        
            datelineTriangle = triangleDict.get(0)

            if (datelineTriangle[1] > 180) or (datelineTriangle[3] > 180) or (datelineTriangle[5] > 180):
                self.ASlogger.info("This triangle crosses the Date Line at 180")
                datelineflag = 1

            if (datelineTriangle[1] < -180) or (datelineTriangle[3] < -180) or (datelineTriangle[5] < -180):
                self.ASlogger.info("This triangle crosses the Date Line at -180")
                datelineflag = -1

            if datelineflag != 0:
                datelineTriangle[1] = datelineTriangle[1] - datelineflag * 360
                datelineTriangle[3] = datelineTriangle[3] - datelineflag * 360
                datelineTriangle[5] = datelineTriangle[5] - datelineflag * 360
                insertQuery = """INSERT INTO excludes (eruleid,ev1y,ev1x,ev2y,ev2x,ev3y,ev3x,emaglimit,eplacename,added)
                                 VALUES ('%d','%4.2f','%4.2f','%4.2f','%4.2f','%4.2f','%4.2f','%3.1f','%s','%s');
                              """ % (self.eruleID, value[0], value[1], value[2], value[3], value[4], value[5], self.DBemaglimit, self.eventID, gmdate)
                self.ASlogger.info("SQL is " + insertQuery)
                self._cursor.execute(insertQuery)
                self.commit()

        return True


    def checkAftershockZone(self, valuesDict):

        self.lat = valuesDict.get("lat")
        self.lon = valuesDict.get("lon")
        self.mag = valuesDict.get("mag")
        self.excludename = valuesDict.get("eventID")
        self.emaglimit = valuesDict.get("emaglimit")

        self.excluderegion = 0    #start by assuming it's not in an exclude region
        self.olderuleid = 0
        self.oldmag = 0

        # 0 = not in an exclude region
        # 1 = in an exclude region, and it's smaller than the exclude level
        # 2 = in an exclude region, and it's larger than the exclude level
        # 3 = in an exclude region, and it's larger than the previous mainshock

        self.ASlogger.info("Checking to see if the event is in an already defined exclude region")
        self.sql = """SELECT DISTINCT eruleid,emaglimit,eplacename,(((((ev2x-(%s))*(ev3y-(%s))) - ((ev3x-(%s))*(ev2y-(%s))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0 AND ((((ev3x-(%s))*(ev1y-(%s))) - ((ev1x-(%s))*(ev3y-(%s))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0 AND ((((ev1x-(%s))*(ev2y-(%s))) - ((ev2x-(%s))*(ev1y-(%s))))/(((ev2x-ev1x)*(ev3y-ev1y)) - ((ev3x-ev1x)*(ev2y-ev1y))))>=0) as exclude from excludes;
                   """ % (self.lon, self.lat, self.lon, self.lat, self.lon, self.lat, self.lon, self.lat, self.lon, self.lat, self.lon, self.lat)
        self.ASlogger.info("SQL is %s" % self.sql)
        self._cursor.execute(self.sql)
        self.rows = self._cursor.fetchall()
        for row in self.rows:
            self.exclude = row[3]
            if self.exclude == 1:
                self.olderuleid = row[0]
                self.DBemaglimit = row[1]
                self.excludename = row[2]
                self.excluderegion = 1
                break

        if self.excluderegion > 0:
            self.ASlogger.info("This event falls inside an exclude region eruleid %d M%3.1f for event %s" % (self.olderuleid, self.DBemaglimit, self.excludename))
            if self.mag > self.DBemaglimit:
                self.excluderegion = 2
            self.oldmag = self.DBemaglimit + self.emaglimit
            if self.mag > self.oldmag:
                self.excluderegion = 3

        return (self.excluderegion, self.excludename, self.olderuleid, self.oldmag)




    def defineAftershockZone(self, valuesDict):
        self.lat = valuesDict.get("lat")
        self.lon = valuesDict.get("lon")
        self.mag = valuesDict.get("mag")
        self.eplacename = valuesDict.get("eventID")
        self.emaglimit = valuesDict.get("emaglimit")

        self.eruleID = None

        self.gmdate = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        self.ASlogger.info("Defining aftershock zone for event %s" % self.eplacename)
        self.ASlogger.info("Now it is %s" % self.gmdate)
        self.ASlogger.info("Event has location %s/%s. Magnitude is %s" % (self.lat, self.lon, self.mag))

        try:
            self.sql = "SELECT eruleid,added from excludes where eplacename='%s' LIMIT 1;" % self.eplacename
            self._cursor.execute(self.sql)
            rows = self._cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                    self.eruleID = row[0]
                    self.gmdate  = row[1]
                    self.ASlogger.info('Event %s has eruleID %s' % (self.eplacename, self.eruleID))

            if self.eruleID is not None:
                # There is already a region for this event, but we need to update it.
                self.ASlogger.info("There is already a defined exclude region for this event. Delete it and re-make it with the new event parameters")
                self.sql = "DELETE FROM excludes where eruleid=%s;" % self.eruleID
                self.ASlogger.info("SQL is %s" % self.sql)
                self._cursor.execute(self.sql)
                self.commit()

        except Exception as e:
            self.ASlogger.error("Aftershock DB query failed")
            self.ASlogger.error(e)
        zoneTuple = self.checkAftershockZone(valuesDict)
        self.excluderegion = zoneTuple[0]
        self.excludename = zoneTuple[1]
        self.olderuleID = zoneTuple[2]
        self.oldmag = zoneTuple[3]

        self.ASlogger.info("Values returned are: %d, %s, %d, %f" % (self.excluderegion, self.excludename, self.olderuleID, self.oldmag))

        if self.excluderegion == 0:
            self.ASlogger.info("This event does not fall in a previously defined exclude region")

        if self.excluderegion == 3:
            self.ASlogger.info("This event falls in the exclude region for event %s" % self.excludename)
            self.ASlogger.info("This event is larger than event %s, so it supersedes it" % self.excludename)
            self.ASlogger.info("This event is M%3.1f and is larger than M%3.1f for the old event. Create a new region for this event and delete the old one." % (self.mag, self.oldmag))

            self.sql = "DELETE FROM excludes where eruleid=%s;" % self.olderuleID
            self.ASlogger.info("SQL is %s" % self.sql)
            self._cursor.execute(self.sql)
            self.commit()


        # For excluderegion == 1||2, don't do anything, since this event is
        # inside an already-existing aftershock zone. It's most likely
        # just an aftershock of the previous event.

        if self.excluderegion == 0 or self.excluderegion == 3:
            # Create a new rule for this event.
            self.insertAftershockZone(valuesDict)

        return self.excluderegion



    def cleanupAftershockZones(self, emaglimit):
        """This cleans up any aftershock exclusion zones that have passed their expiration date.
           The number of days for an aftershock zone to be kept is calculated as 14.5*(($oldmag - 5.24)**2) + 10. 
           This approximates these values:

           M5.5-M6.0: 10 days
           M6.0-M6.5: 20 days
           M6.5-M7.0: 30 days
           M7.0-M8.0: 60 days
           M8.0+: 120 days
        """
        self.epochTime = int(time())

        sql = "SELECT eruleid,eplacename,emaglimit,added from excludes GROUP BY eruleid ORDER BY added;"
        self._cursor.execute(sql)
        rows = self._cursor.fetchall()
        for row in rows:
            if row[0] is not None:
                self.eruleID = row[0]
                self.eplacename = row[1]
                self.DBemaglimit = row[2]
                self.gmdate = row[3]
            self.ASlogger.info('Event eruleid %d (%s) has mag limit %3.1f. It was added on %s' % (self.eruleID, self.eplacename, self.DBemaglimit, self.gmdate))
            oldmag = emaglimit + self.DBemaglimit

            timelimit = 14.5*((oldmag - 5.24)**2) + 10
            self.ASlogger.info("timelimit is %3.2f days" % timelimit)

            cutofftime = self.epochTime - 86400 * timelimit
            testtime = int(datetime.strptime(self.gmdate, "%d-%b-%Y %H:%M:%S").timestamp())
            self.ASlogger.info("Added time is %d, cutoff is %f (%f days)" % (testtime, cutofftime, timelimit))
            timeleft = testtime - cutofftime
            daysleft = timeleft/86400
            self.ASlogger.info("Time left for this rule: %f (%f days)" % (timeleft, daysleft))

            if cutofftime > testtime:
                self.ASlogger.info("This exclusion rule (eruleid:%d) should be axed" % self.eruleID)
                self.sql1 = "DELETE from excludes where eruleid=%d;" % self.eruleID
                self.ASlogger.info("SQL is %s" % self.sql1)
                self._cursor.execute(self.sql1)
                self.commit()

        self.ASlogger.info("Ending aftershock exclusion zone cleanup run")
        return True
