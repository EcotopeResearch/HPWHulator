# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 09:07:05 2020

@author: paul
"""

import numpy as np;

class HPWHSizer:
    rhoCp = 8.345;
    W_TO_BTUHR = 3.412142;
    W_TO_TONS = 0.000284345;
    
    schematicNames = ["primary", "swingtank","tempmaint"];
    
    def __init__(self):
        self.nBR        = np.zeros(6); # Number of bedrooms 0Br, 1Br...
        self.rBR        = np.zeros(6); # Ratio of people bedrooms 0Br, 1Br...
        self.nPeople    = 0.; # Nnumber of people
        self.gpdpp      = 0.; # Gallons per day per person
        self.loadShapeNorm  = np.zeros(24); # The normalized load shape
        self.supplyT    = 0.; # The supply temperature to the occupants
        self.incomingT  = 0.; # The incoming cold water temperature for the city
        self.storageT   = 0.; # The primary hot water storage temperature 
        self.compRuntime  = 0.; # The runtime?
        self.metered    = 0; # If the building as individual metering on the apartment or not
        self.percentUseable = 0; #The  percent of useable storage
        
        self.schematic  = ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.swingOnT   = 0.; # The temperature the swing tank turns on at
        self.nApt       = 0.; # The number of apartments
        self.Wapt       = 0.; # The recirculation loop losses in terms of W/apt
        self.TMRuntime  = 0.; # The temperature maintenance minimum runtime.

    def __calcedVariables(self):
        """ Calculate other variables needed."""
        if self.nApt == 0:
            self.nApt = sum(self.nBR);
        if self.nPeople == 0:
            self.nPeople = sum(self.nBR * self.rBR);
            
        self.totalHWLoad = self.gpdpp * self.nPeople;
        self.totalLoadShape = self.loadShapeNorm * self.totalHWLoad;
        self.UAFudge = 3;
        self.QdotRecirc = self.Wapt * self.nApt
        
        
    def sizePrimaryTankVolume(self, heatCap):
        """Sizer the primary HPWH plant"""
        diff = self.loadShape - 1/heatCap; #####FIX
        ###FINISH
        
    def sizeSwing(self):
        self.TMVol = (self.Wapt +self.UAFudge) * self.nApts / self.rhoCp * self.W_TO_BTUHR * self.offtime/(self.storageT - self.swingOnT);
        self.TMCap = 2 * (self.Wapt +self.UAFudge) * self.nApts / 1000.;  ####Factor of TWO?!??!
        
    def sizeTemperatureMaintenance(self):####FIX
        self.TMCap =  100;####FIX
        self.TMVol =  100;####FIX
        ###FINISH
        
    def sizeSystem(self, schematic):
        """ Size system based on schemtic """    
        self.primaryHeatingRate = self.totalHWLoad / self.compRuntime
        self.primaryVol = self.sizePrimaryTankVolume()    
        if schematic == "swingtank":
            self.sizeSwing();
        elif schematic == "tempmaint":
            self.sizeTemperatureMaintenance();
        
        return [self.primaryHeatingRate, self.primaryVol]
    
    def primaryCurve(self):
        """"Size the primary system curve"""
        regenRateN = np.linspace(self.compRuntime, 6., 20);
        volN = np.zeros(len(regenRateN));
        for ii in range(0,len(regenRateN)): 
            volN[ii] = self.sizePrimaryTankVolume(regenRateN(ii));
        return [volN, regenRateN]

    def initializeFromFile(self, fileName):
        """"Read in a formated file with filename"""

        # Using readlines() 
        file1 = open(fileName, 'r');
        fileLines = file1.read().splitlines();     
        file1.close();
        for line in fileLines:
            temp = line.lower().split();
            
            if temp[0] == "nbr":
                 for ii in range(1,7):
                    try:
                        self.nBR  = float(temp[ii]);
                    except IndexError:
                        raise Exception('\nERROR: Not enough data points given for nBR, should be 6 but received '+ii+'.\n') 
                        
            elif temp[0] == "rbr":   # Ratio of people per bedrooms 0Br, 1Br...
                 for ii in range(1,7):
                    try:
                        self.rBR  = float(temp[ii]);
                    except IndexError:
                        raise Exception('\nERROR: Not enough data points given for rBR, should be 6 but received '+ii+'.\n') 
                        
            elif temp[0] == "npeople":
                self.nPeople    = float(temp[1]);
            elif temp[0] == "gpdpp":
                self.gpdpp      = float(temp[1]);
                
            elif temp[0] == "loadshapenorm":
                for ii in range(1,25):
                    try:
                        self.loadShapeNorm  = float(temp[ii]);
                    except IndexError:
                        raise Exception('\nERROR: Not enough data points given for loadShapeNorm, should be 24 but received '+ii+'.\n') 
                        
            elif temp[0] == "supplyt":
                self.supplyT    = float(temp[1]);
            elif temp[0] == "incomingt":
                self.incomingT  = float(temp[1]);
            elif temp[0] == "storaget":
                self.storageT   = float(temp[1]);
            elif temp[0] == "compruntime":
                self.compRuntime  = float(temp[1]);
            elif temp[0] == "metered":
                self.metered    =  int(temp[1]); # If the building as individual metering on the apartment or not
            elif temp[0] == "percentuseable":
                self.percentUseable = float(temp[1]);#The  percent of useable storage
            elif temp[0] == "schematic":
                if temp[1] in self.schematicNames:
                    self.schematic  = temp[1];
                else:
                    raise Exception('\nERROR: Invalid input given for the schematic: ""'+ temp[1]+'"".\n')    

            elif temp[0] == "swingont":
                self.swingOnT   = float(temp[1]);
            elif temp[0] == "napt":
                self.nApt       = float(temp[1]);
            elif temp[0] == "wapt":
                self.Wapt       = float(temp[1]);
            elif temp[0] == "tmruntime":
                self.TMRuntime  = float(temp[1]);
            else:
                raise Exception('\nERROR: Invalid input given: '+ line +'.\n')
                
        self.__calcedVariables(self)
        
    def writeOutput(self, fileName):
        file1 = open(fileName, 'w+');

 #Finsih
        
        file1.close();
        
        