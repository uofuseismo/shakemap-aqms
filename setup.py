from distutils.core import setup
import os.path


setup(name='shakemap_aqms',
      version=1.0,
      description='AQMS Modules for ShakeMap',
      author='Bruce Worden',
      author_email='cbworden@usgs.gov',
      url='http://github.com/cbworden/shakemap-aqms',
      packages=['shakemap_aqms',
                'shakemap_aqms.coremods',
                ],
      package_data={
          'shakemap_aqms': [os.path.join('config', '*')]
      },
      scripts=[],
      )
