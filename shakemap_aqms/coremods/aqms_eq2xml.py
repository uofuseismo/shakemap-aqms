# stdlib imports
import os
import os.path

# Third party imports

# local imports
from shakemap.coremods.base import CoreModule
from shakemap.utils.config import get_config_paths
from shakemap_aqms.util import get_aqms_config, get_eqinfo
from shakelib.rupture.origin import write_event_file


class AQMSEq2XMLModule(CoreModule):
    """
    aqms_eq2xml -- Get origin information from AQMS database, and write
                   event.xml to the event's current directory.
    """

    command_name = 'aqms_eq2xml'

    def execute(self):
        """
        Write event.xml to the event's current directory
        """
        install_path, data_path = get_config_paths()
        datadir = os.path.join(data_path, self._eventid, 'current')
        if not os.path.isdir(datadir):
            os.makedirs(datadir)
        datafile = os.path.join(datadir, 'event.xml')

        config = get_aqms_config()

        event = get_eqinfo(self._eventid, config, self.logger)

        outfile = open(datafile, 'wb')

        write_event_file(event, outfile)
