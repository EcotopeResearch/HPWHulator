from setuptools import find_packages, setup

# needs __init__.py file added?
# needs find_packages to include repo url?
setup(
    name='HPWHulator',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True
)