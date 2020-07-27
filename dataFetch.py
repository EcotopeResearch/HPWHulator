

# Functions to gather data from JSON
import os

import json
#from scipy.stats import lognorm
import scipy.stats as st

class hpwhDataFetch():

    '''
    Class used to retrieve data stored in .json file and perform specific calculations with that data.

    Attributes
    ----------
    dataDict : json
        Data dictionary

    Methods
    -------
    getLoadshape()
        Get numpy array of building load shape.

    getGPDPP()
        Get gallons per person per day from ASHRAE, Ecotope, or California method.

    getRPepperBR()
        Get people per bedroom from ASHRAE or California method.

    getCDF()
        Calculate fraction of strorage required percentage of load shift days.

    '''

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'hpwhdata.json')) as json_file:
            self.dataDict = json.load(json_file)

    def getLoadshape(self):
        return self.dataDict['loadshapes']['Stream']

    def getGPDPP(self, key):
        try:
            return self.dataDict['gpdpp'][key]
        except KeyError:
            raise KeyError("Mapping key not found for gpdpp, valid keys are ashLow, ashMed, ecoMark, CA")

    def getRPepperBR(self, key):
        try:
            return self.dataDict['rpeople'][key]
        except KeyError:
            raise KeyError("Mapping key not found for ratio of people per bedroom, valid keys are CA, ASHSTD, ASHLOW")

    def getCDF(self, cdf_shift):
        params = self.dataDict['gpdppfit']

        norm_mean = params[0] # mean of normalized stream data
        norm_std = params[1] # standard deviation of normalized stream data

        # calculate fraction of strorage required to meet load shift days
        storage_fract = norm_mean + norm_std*st.norm.ppf(cdf_shift)

        return(storage_fract)
