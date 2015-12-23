from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='ipbec',
      version='0.1',
      description='A PyQT application analyze absorption images of Bose-Einstein condensates',
      long_description=readme(),
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: X11 Applications :: Qt',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Multimedia :: Graphics :: Viewers',
                   'Topic :: Scientific/Engineering :: Physics',
                   'Topic :: Scientific/Engineering :: Visualization'],

      url='http://github.com/shreyaspotnis/ipbec',
      author='Shreyas Potnis',
      author_email='shreyaspotnis@gmail.com',
      license='MIT',
      packages=['ipbec'],
      install_requires=['PyQt4', 'pyqtgraph', 'numpy'],
      zip_safe=False)
