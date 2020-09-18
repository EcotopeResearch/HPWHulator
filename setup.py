""" 
	HPWHulator
    Copyright (C) 2020  Ecotope Inc.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


from setuptools import find_packages, setup, Distribution

# Make sure versiontag exists before going any further. This won't actually install
# the package. It will just download the egg file into `.eggs` so that it can be used
# henceforth in setup.py.
Distribution().fetch_build_eggs('versiontag')

# Import versiontag components
from versiontag import get_version, cache_git_tag

# This caches for version in version.txt so that it is still accessible if
# the .git folder disappears, for example, after the slug is built on Heroku.
cache_git_tag()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()
	
# needs find_packages to include repo url?
setup(
    name='HPWHulator',
	
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/EcotopeResearch/HPWHulator",
    description="A public Heat Pump Water Heater (HPWH) sizing calculator that uses the Ecotope Modiefied ASHRAE method and the ASHRAE method.",
	
    long_description=long_description,
    long_description_content_type="text/markdown",
	classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPL v.3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=requirements,
	
	setup_requires=['setuptools_scm'],
	use_scm_version=True,

)