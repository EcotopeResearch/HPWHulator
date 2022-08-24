![Python package](https://github.com/EcotopeResearch/HPWHulator/workflows/Python%20package/badge.svg)
# HPWHulator 	

### Installing:
Steps for installing conda environment from the Anaconda prompt
1. Navigate to the HPWHulator directory.
2. Create new environment from .yml file

	$ conda env create --file HPWHSizer.yml
3. Check environment was created

	$ conda env list
4. Activate new environment

	$ conda activate HPWHulator

If an environment already exits it can be removed with:

	$ conda remove --name envname --all


All the available environment can be found with:

	$ conda env list

### Testing:
From the parent directory in Anaconda prompt and type

	$ python -m pytest

### Updating Documentation:
1. If not installed in environment: pip install sphinx and numpydocs
2. Using Anaconda prompt navigate to docs directory and run:

	$ make html



### Contact Information
To get in touch with Ecotope Inc. go here: http://ecotope.com/contact/

