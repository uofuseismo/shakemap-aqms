# stdlib imports
import os
import os.path
import logging
import pkg_resources
from datetime import datetime

# Third party imports
import cx_Oracle
from configobj import ConfigObj
from validate import Validator

# Local imports
from shakemap.utils.config import get_config_paths, config_error
from shakelib.rupture import constants  # added by GG
import shakemap.utils.queue as queue


def get_aqms_config(cname=None):
    """
    Returns the ConfigObj object resulting from parsing aqms.conf.

    Args:
        none

    Returns:
        ConfigObj: The ConfigObj object representing aqms.conf.

    Raises:
        FileNotFoundError: if aqms.conf or aqmsspec.conf is not found.
        RuntimeError: if there is an error parsing aqms.conf
    """
    if cname is None:
        cname = 'aqms'

    install_path, _ = get_config_paths()
    conf_file = os.path.join(install_path, 'config', cname + '.conf')
    if not os.path.isfile(conf_file):
        raise FileNotFoundError('No file "%s" exists.' % conf_file)
    spec_path = pkg_resources.resource_filename('shakemap_aqms', 'config')
    spec_file = os.path.join(spec_path, cname + 'spec.conf')
    if not os.path.isfile(spec_file):
        raise FileNotFoundError('No file "%s" exists.' % spec_file)
    config = ConfigObj(conf_file, configspec=spec_file)

    val = Validator()
    results = config.validate(val)
    if not isinstance(results, bool) or not results:
        try:
            config_error(config, results)
        except RuntimeError as err:
            logging.error('Error in {0}.conf: {1}'.format(cname, err))
            raise

    return config


def get_eqinfo(eventid, config, logger):
    """Get a dictionary of event information for the given eventid.

    Args:
        eventid (str): The event ID.
        config (dict): The AQMS configuration dictionary.
        logger (logger): The logger for this process.

    Returns:
        dict: A dictionary containing the following keys:

            - 'id' (str, "9108645")
            - 'netid' (str, 'ci')
            - 'network' (str, 'Southern California Seismic Network'')
            - lat (float)
            - lon (float)
            - depth (float)
            - mag (float)
            - time (datetime object)
            - locstring (str)
            - mech (str)
    """
    success = False
    for dbname in sorted(config['dbs'].keys()):
        db = config['dbs'][dbname]
        dsn_tns = cx_Oracle.makedsn(db['host'], db['port'],
                                    sid=db['sid'])
        try:
            con = cx_Oracle.connect(user=db['user'],
                                    password=db['password'],
                                    dsn=dsn_tns)
        except cx_Oracle.DatabaseError as err:
            logger.warn('Error connecting to database: %s' % dbname)
            logger.warn('Error: %s' % err)
            continue
        cursor = con.cursor()
        query = ('BEGIN '
                 'SELECT o.lat, o.lon, n.magnitude, o.depth, '
                 'TrueTime.getStringf(o.datetime), '
                 'm.rake1, m.rake2 '
                 'INTO :lat, :lon, :mag, :depth, :datetime, '
                 ':rake1, :rake2 '
                 'FROM netmag n, origin o, event e '
                 'LEFT OUTER JOIN mec m ON e.prefmec = m.mecid '
                 'WHERE e.evid = :evid ' 
                 'AND e.selectflag = 1 '
                 'AND o.orid = e.prefor '
                 'AND n.magid = e.prefmag; '
                 'Wheres.Town(:lat, :lon, 0.0, :dist, :az, :elev, '
                 ':place); '
                 ':dir := Wheres.Compass_PT(:az); '
                 'END;')
        lat = cursor.var(cx_Oracle.NUMBER)
        lon = cursor.var(cx_Oracle.NUMBER)
        mag = cursor.var(cx_Oracle.NUMBER)
        depth = cursor.var(cx_Oracle.NUMBER)
        date = cursor.var(cx_Oracle.STRING)
        rake1 = cursor.var(cx_Oracle.NUMBER)
        rake2 = cursor.var(cx_Oracle.NUMBER)
        dist = cursor.var(cx_Oracle.NUMBER)
        az = cursor.var(cx_Oracle.NUMBER)
        elev = cursor.var(cx_Oracle.NUMBER)
        place = cursor.var(cx_Oracle.STRING)
        direction = cursor.var(cx_Oracle.STRING)
        try:
            cursor.execute(query, {'lat': lat,
                                   'lon': lon,
                                   'mag': mag,
                                   'depth': depth,
                                   'datetime': date,
                                   'rake1': rake1,
                                   'rake2': rake2,
                                   'dist': dist,
                                   'az': az,
                                   'elev': elev,
                                   'place': place,
                                   'dir': direction,
                                   'evid': eventid})
        except cx_Oracle.DatabaseError as err:
            logger.warn('Error: %s' % err)
            cursor.close()
            con.close()
            continue
        cursor.close()
        con.close()
        success = True
        break
    if not success:
        logger.warning('Could not retrieve event from database(s)')
        return None

    dt = datetime.strptime(date.getvalue(), '%Y/%m/%d %H:%M:%S.%f')
    date = dt.strftime(constants.TIMEFMT) # changed source of TIMEFMT to proper local library - GG

    distmi = dist.getvalue() * 0.62137

    rake1 = rake1.getvalue()
    rake2 = rake2.getvalue()

    mech = 'ALL'
    if rake1 is not None and rake2 is not None:  # RAKE VALUES ARE NOT ALWAYS PRESENT FOR EVENTS, DEFAULTING TO-> mech = 'ALL' - GG
        if rake1 > 180:
            rake1 -= 360
        if rake2 > 180:
            rake2 -= 360
        if rake1 < -180:
            rake1 += 360
        if rake2 < -180:
            rake2 += 360

        if rake1 >= -135 and rake1 <= -45 and rake2 >= -135 and rake2 <= -45:
            mech = 'NM'  # Normal
        elif (rake1 >= -135 and rake1 <= -45) or (rake2 >= -135 and rake2 <= -45):
            mech = 'NM'  # Oblique Normal
        elif rake1 >= 45 and rake1 <= 135 and rake2 >= 45 and rake2 <= 135:
            mech = 'RS'  # Reverse
        elif (rake1 >= 45 and rake1 <= 135) or (rake2 >= 45 and rake2 <= 135):
            mech = 'RS'  # Oblique Reverse
        elif rake1 >= -45 and rake1 <= 45 and \
            ((rake2 >= 135 and rake2 <= 225) or
                (rake2 >= -225 and rake2 <= -135)):
            mech = 'SS'
        elif rake2 >= -45 and rake2 <= 45 and \
            ((rake1 >= 135 and rake1 <= 225) or
                (rake1 >= -225 and rake1 <= -135)):
            mech = 'SS'


    direction = direction.getvalue().replace(' ', '')
    loc = '%.1f km (%.1f mi) %s of %s' % \
          (dist.getvalue(), distmi, direction, place.getvalue())

    event = {'id': eventid,
             'netid': config['netid'],
             'network': config['network'],
             'lat': lat.getvalue(),
             'lon': lon.getvalue(),
             'depth': depth.getvalue(),
             'mag': mag.getvalue(),
             'time': date,
             'locstring': loc,
             'mech': mech,
             'alt_eventids': "NONE"}  # ADDED alt_eventids key because sm_queue is expecting and attempts to access this dict value - GG
    return event
