from setuptools import find_packages, setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    
# needs find_packages to include repo url?
setup(
    name='HPWHulator',
    version='0.0.1',

    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/EcotopeResearch/HPWHulator",
    description="A public Heat Pump Water Heater (HPWH) sizing calculator that uses the Ecotope Modiefied ASHRAE method and the ASHRAE method.",

    python_requires='>=3.6',
    install_requires=requirements,

)