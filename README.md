# HPWHulator

### Installing:
Steps for installing conda enviroment from the Anaconda prompt
1. Navigate to the HPWHulator directory.
2. Create new eviroment from .yml file

	$ conda env create --file HPWHSizer.yml
3. Check enviroment was created

	$ conda env list
4. Activate new enviroment

	$ conda activate HPWHSizer

If an enviroment already exits it can be removed with:

	$ conda remove --name envname --all
	
	
All the available enviroment can be found with:

	$ conda env list

### Testing:
From the parent directory in Anaconda prompt and type 

	$ python -m pytest

