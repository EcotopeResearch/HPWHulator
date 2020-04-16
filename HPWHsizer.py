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
        """Initialize the sizer object with 0's for the inputs"""
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
        
        self.aquaFract = 0.; # The aquastat fraction
        
        self.schematic  = ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.swingOnT   = 0.; # The temperature the swing tank turns on at
        self.nApt       = 0.; # The number of apartments
        self.Wapt       = 0.; # The recirculation loop losses in terms of W/apt
        self.TMRuntime  = 0.; # The temperature maintenance minimum runtime.

    def __calcedVariables(self):
        """ Calculate other variables needed."""
        if sum(self.nBR + self.nApt) == 0:
            raise Exception("Need input given for number of bedrooms by size or number of apartments")
        if self.nApt == 0:
            self.nApt = sum(self.nBR);
        if self.nPeople == 0:
            self.nPeople = sum(self.nBR * self.rBR);
        
        self.totalHWLoad = self.gpdpp * self.nPeople;
        #self.totalLoadShape = self.loadShapeNorm * self.totalHWLoad;
        self.UAFudge = 3;
        
        self.offTime = sum(np.append(self.loadShapeNorm,self.loadShapeNorm)[22:36] < 1./48.) #The overnight design for off time. 
     
    def primaryHeatHrs2kBTUHR(self, heathours):
        """Returns the heating capacity in kBTU/hr for the heating hours given by, heathours"""
        heatCap = self.totalHWLoad / heathours * self.rhoCp * (self.storageT - self.incomingT)/1000.;
        return heatCap;
    
    def sizePrimaryTankVolume(self, heatHrs):
        """Sizes the primary HPWH plant with the new methodology"""
        if heatHrs <= 0 or heatHrs > 24:
            raise Exception("The heating capacity scaled to hours is invalid, value is "+ heatCapHrs)
            
        diffN = 1/heatHrs - np.append(self.loadShapeNorm,self.loadShapeNorm); 
        diffN = np.cumsum(diffN[np.argmax(diffN < 0.):]); #Get the rest of the day from the start of the peak

        runningVol = -min(np.append(diffN[diffN<0.], -0.)); #Minimum value less than 0 or 0.
        totalVol = runningVol / (1-self.aquaFract) / self.percentUseable;
        
        return totalVol * self.totalHWLoad * (self.supplyT - self.incomingT) / (self.storageT - self.incomingT);

    def sizeSystem(self):
        """ Size system based on schemtic """    
        self.primaryHeatingRate = self.totalHWLoad / self.compRuntime;
        self.primaryHeatCap = self.primaryHeatHrs2kBTUHR(self.compRuntime);
        self.primaryVol = self.sizePrimaryTankVolume(self.compRuntime);    
        if self.schematic == "swingtank":
            self.sizeSwing();
        elif self.schematic == "tempmaint":
            self.sizeTemperatureMaintenance();
        
        #return [self.primaryHeatingRate, self.primaryVol]
    
    def primaryCurve(self):
        """"Size the primary system curve"""
        heatHours = np.linspace(self.compRuntime, 10., 10);
        volN = np.zeros(len(heatHours));
        for ii in range(0,len(heatHours)): 
            volN[ii] = self.sizePrimaryTankVolume(heatHours[ii]);
        return [volN, self.primaryHeatHrs2kBTUHR(heatHours)]

    
    def sizeSwing(self):
        self.TMVol = (self.Wapt +self.UAFudge) * self.nApt / self.rhoCp * self.W_TO_BTUHR * self.offTime/(self.storageT - self.swingOnT);
        self.TMCap = 2 * (self.Wapt +self.UAFudge) * self.nApt / 1000.;  ####Factor of TWO?!??!
        
    def sizeTemperatureMaintenance(self):####FIX
        self.TMCap =  100;####FIX
        self.TMVol =  100;####FIX
        ###FINISH
       
# Helper Functions for reading and writing files 
    def __importArrLine(self, line, setLength):
        """Imports an array in line with a set lenght, setLength"""
        val = np.zeros(setLength);
        if len(line) > setLength: 
                raise Exception( '\nERROR: Too many data points given for loadShapeNorm, should be 24 but received '+ str(len(line)-1)+'.\n')  
        for ii in range(1,setLength):
            try:
                val[ii-1]  = float(line[ii]);
            except IndexError:
                raise Exception('\nERROR: Not enough data points given for loadShapeNorm, should be 24 but received '+str(ii)+'.\n') 
        return val                
    def __writeAttrLine(self, file, attrList):
        for field in attrList:
            var = getattr(self, field);
            if isinstance(var, np.ndarray):
                file.write(field + ', ' + np.array2string(var, precision = 4, separator=",") + '\n')
            else:
                file.write(field + ', ' + str(var) + '\n')
                
    def initializeFromFile(self, fileName):
        """"Read in a formated file with filename"""

        # Using readlines() 
        file1 = open(fileName, 'r');
        fileLines = file1.read().splitlines();     
        file1.close();
        for line in fileLines:
            temp = line.lower().split();
            
            if temp[0] == "nbr":
                self.nBR =  self.__importArrLine(temp, 7);
            elif temp[0] == "rbr":   
                self.rBR = self.__importArrLine(temp, 7);
            elif temp[0] == "npeople":
                self.nPeople    = float(temp[1]);
            elif temp[0] == "gpdpp":
                self.gpdpp      = float(temp[1]);
            elif temp[0] == "loadshapenorm":
                self.loadShapeNorm  = self.__importArrLine(temp, 25);
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
                temp[1] = float(temp[1])
                if temp[1] > 1: # Check to make sure the percent is stored as anumber 0 to 1.
                    temp[1] = temp[1]/100.
                self.percentUseable = temp[1];#The  percent of useable storage
            elif temp[0] == "aquafract":
                temp[1] = float(temp[1])
                if temp[1] > 1: # Check to make sure the percent is stored as anumber 0 to 1.
                    temp[1] = temp[1]/100.
                self.percentUseable = temp[1];
            
            elif temp[0] == "schematic":
                if temp[1] in self.schematicNames:
                    self.schematic  = temp[1];
                else:
                    raise Exception('\nERROR: Invalid input given for the schematic: "'+ str(temp[1])+'".\n')    
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
                
        self.__calcedVariables()

           
    def writeOutput(self, fileName):        
        varListOut = ['totalHWLoad', 'UAFudge', 'offTime', 'primaryHeatingRate',
                      'primaryHeatCap','primaryVol', 'TMCap', 'TMVol'];
        
        varListIn = ['nPeople', 'gpdpp', 'loadShapeNorm', 'storageT','supplyT', 
                      'incomingT', 'compRuntime','metered', 'percentUseable', 
                     'aquaFract',
                     'schematic', 'swingOnT','nApt','Wapt',  'TMRuntime'];
        if sum(self.nBR*self.rBR) > 0:    
             ['nBR', 'rBR'] + varListIn
            
       
             
        with open(fileName, 'w+') as file1:
            file1.write('OUTPUTS\n')
            self.__writeAttrLine(file1, varListOut)
            pCurve = self.primaryCurve();
            file1.write('primaryCurve_vol, ')
            file1.write(np.array2string(pCurve[0], precision = 6, separator=","));
            file1.write('\n')
            file1.write('primaryCurve_heatCap, ')
            file1.write(np.array2string(pCurve[1], precision = 2, separator=","));
            file1.write('\n\n')
            file1.write('INPUTS\n')
            self.__writeAttrLine(file1, varListIn)
            
     

        