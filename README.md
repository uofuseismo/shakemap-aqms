# shakemap-aqms
ShakeMap modules supporting the AQMS system.

These modules replace queue, eq2xml, and db2xml from ShakeMap V3.5.



Installation
------------

- Install ShakeMap V4 and its dependencies. See 
  https://github.com/usgs/shakemap for details.
- Use pip or conda to install the python library **cx\_Oracle**. See
  https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html for
  detailed instructions.
- If they are not already on your system, install the appropriate
  Oracle client libraries. This topic is covered in the cx\_Oracle
  install instructions mentioned above.
- Do ``pip install git+git://github.com/ggann/shakemap-aqms.git``. 
  As an alternative, you can clone the repo and use ``pip install``
  on the local directory where you cloned the repo.
- Configure your shake.conf file so that ``coremods`` includes
  ``shakemap_aqms.coremods``.
- Copy the file *aqms.conf* from the *shakemap_aqms/config* directory 
  into your
  *<INSTALL\_DIR>/config* directory and edit it following the 
  instructions therein. You must configure at least one database
  but you may configure multiple databases. The databases will be
  used in the lexicographic order of the names of their subsections.
- You should then be able to add ``aqms_eq2xml`` and ``aqms_db2xml`` to 
  your ``shake`` command line.
- The old 'queue' process has been replaced with two processes: 
  ``aqms_queue`` and ``sm_queue``. To use them, copy ``aqms_queue.conf``
  from the *shakemap_aqms/config* directory into your *<INSTALL\_DIR>/config*
  directory and edit it to receive messages on the same port (and 
  from the same servers that your current (SM 3.5) ``queue`` process
  does. You may then run ``aqms_queue`` and it will receive the 
  notifications from the old ``shake_alarm`` and ``shake_cancel``
  scripts that your AQMS systems are running. There are new python
  versions of ``shake_alarm`` and ``shake_cancel`` that may be used
  if desired. (Don't forget to edit those scripts to set the remote
  host and port number
  according to your installation and ``aqms_queue.conf``.) The next
  step is to get ``queue.conf`` from *shakemap/data* in the 
  shakemap repository and put it in your *<INSTALL\_DIR>/config*,
  and edit according to your preferences. You can then run ``sm_queue``.

  The way this setup works is that your database will use ``shake_alarm``
  (or ``shake_cancel``) (either the old Perl or new Python versions --
  they do the same thing) to notify ``aqms_queue`` of an event. 
  ``aqms_queue`` will then retrieve the event information and pass it
  to ``sm_queue``. ``sm_queue`` will make a decision on processing the
  event based on its configuration. If the event is to be processed, 
  ``sm_queue`` will create the event directory and write ``event.xml``
  into it, and then run ``shake --autorun <eventid>`` (which uses the
  ``autorun_modules`` settings in ``shake.conf`` to decide which modules
  to run). Note that in this case you do not need to include ``aqms_eq2xml``
  in the modules because ``event.xml`` will have already been written to
  the event's current directory by ``sm_queue``.

These modules are provided as-is, with no guarantee of anything. 
See the license file. 
