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

# Functions to gather data from JSON
import os

import json
from scipy.stats import norm #lognorm

class hpwhDataFetch():
    '''
    Class used to retrieve data stored in .json file and perform specific 
    calculations with that data.

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

    getCAGPDPPDaily()
        Returns the expected daily gpdpp for every day of the year by bedroom
        size: studio, 1 bedroom, 2 bedroom, ...

    '''

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'hpwhdata.json')) as json_file:
            self.dataDict = json.load(json_file)

    def getLoadshape(self, shape = 'Stream'):
        try: 
            return self.dataDict['loadshapes'][shape]
        except KeyError:
            raise KeyError("Mapping key not found for loadshapes, valid keys are: 'Stream', or 'Stream_Avg'")

    def getGPDPP(self, key):
        try:
            return self.dataDict['gpdpp'][key]
        except KeyError:
            raise KeyError("Mapping key not found for gpdpp, valid keys are: 'ashLow', 'ashMed', or 'ecoMark', for California data see the function getCAGPDPPYearly()")

    def getRPepperBR(self, key):
        try:
            return self.dataDict['rpeople'][key.upper()]
        except KeyError:
            raise KeyError("Mapping key not found for ratio of people per bedroom, valid keys are CA, CTCAC, ASHSTD, ASHLOW")

    def getCDF(self, cdf_shift):
        params = self.dataDict['gpdppfit']

        norm_mean = params[0] # mean of normalized stream data
        norm_std = params[1] # standard deviation of normalized stream data

        # calculate fraction required to meet load shift days
        fract = norm_mean + norm_std*norm.ppf(cdf_shift)

        return fract if fract <= 1. else 1.

    def getCAGPDPPYearly(self, nBR_key):
        try:
            return self.dataDict['ca_gpdpp'][nBR_key.lower()]
        except KeyError:
            err_msg = "Mapping key " + nBR_key +" not found for CA gpdpp, valid keys are '0br', '1br', '2br','3br','4br','5br'"
            raise KeyError(err_msg)