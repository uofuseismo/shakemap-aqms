# shakemap-aqms
ShakeMap modules supporting the AQMS system.

These modules replace queue, eq2xml, and db2xml from ShakeMap V3.5.

NOTICE: I do not intend to support these
modules. Hopefully, a conscientious AQMS user will fork this repo and
take over maintenance of these modules. If that's you, contact me
and let me know, and I'll freeze this repo and point our documentation
to your repo.

Installation
------------

- Install ShakeMap V4 and its dependencies. See 
  https://github.com/usgs/shakemap for details.
- Use pip or conda to install the python library **cx\_Oracle**. See
  http://cx-oracle.readthedocs.io/en/latest/installation.html# for
  detailed instructions.
- If they are not already on your system, install the appropriate
  Oracle client libraries. This topic is covered in the cx\_Oracle
  install instructions mentioned above.
- Do ``pip install git+git://github.com/cbworden/shakemap-aqms.git``. 
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
- You should then be able to add ``eq2xml`` and ``db2xml`` to your 
  ``shake`` command line.

These modules are provided as-is, with no guarantee of anything. 
See the license file. 
