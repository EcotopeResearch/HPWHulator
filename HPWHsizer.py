 # -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 09:07:05 2020

@author: paul
"""

import numpy as np;

class HPWHSizer:
    rhoCp = 8.353535;
    W_TO_BTUHR = 3.412142;
    W_TO_BTUMIN = W_TO_BTUHR/60;
    W_TO_TONS = 0.000284345;
    
    schematicNames = ["primary", "swingtank","tempmaint"];
    
    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""
        self.nBR            = np.zeros(6); # Number of bedrooms 0Br, 1Br...
        self.rBR            = np.zeros(6); # Ratio of people bedrooms 0Br, 1Br...
        self.nPeople        = 0.; # Nnumber of people
        self.gpdpp          = 0.; # Gallons per day per person
        self.loadShapeNorm  = np.zeros(24); # The normalized load shape
        self.supplyT        = 0.; # The supply temperature to the occupants
        self.incomingT      = 0.; # The incoming cold water temperature for the city
        self.storageT       = 0.; # The primary hot water storage temperature 
        self.compRuntime    = 0.; # The runtime?
        self.metered        = 0; # If the building as individual metering on the apartment or not
        self.percentUseable = 0; # The  percent of useable storage
        self.aquaFract      = 0.; # The aquastat fraction
        
        self.defrostFactor  = 1.; # The defrost factor. Derates the output power for defrost cycles.

        self.schematic      = ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.swingOnT       = 0.; # The temperature the swing tank turns on at
        self.nApt           = 0.; # The number of apartments
        self.Wapt           = 0.; # The recirculation loop losses in terms of W/apt
        self.fdotRecirc     = 0.; # The reciculation loop flow rate (gpm)
        self.returnT        = 0.; # The reciculation loop return temperature (F)
        self.TMRuntime      = 0.; # The temperature maintenance minimum runtime.
        self.setpointTM     = 0.; # The setpoint of the temperature maintenance tank.
        
        self.UAFudge        = 0.;
        self.totalHWLoad    = 0.;
        self.offTime        = 0.;
        
    def initByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor, 
                    schematic):
        self.nBR            = np.array(nBR); # Number of bedrooms 0Br, 1Br...
        self.rBR            = np.array(rBR); # Ratio of people bedrooms 0Br, 1Br...
        self.gpdpp          = gpdpp; # Gallons per day per person
        self.loadShapeNorm  = np.array(loadShapeNorm); # The normalized load shape
        self.supplyT        = supplyT; # The supply temperature to the occupants
        self.incomingT      = incomingT; # The incoming cold water temperature for the city
        self.storageT       = storageT; # The primary hot water storage temperature 
        self.compRuntime    = compRuntime; # The runtime?
        self.metered        = metered; # If the building as individual metering on the apartment or not
        self.percentUseable = percentUseable; #The  percent of useable storage
        
        self.aquaFract      = aquaFract; # The aquastat fraction
        self.defrostFactor  = defrostFactor; # The defrost factor. Derates the output power for defrost cycles.

        self.schematic      = schematic; # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.__calcedVariables()
    
    def initByPeople(self, nPeople, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor,
                    schematic, nApt):
        self.nPeople        = nPeople;
        self.gpdpp          = gpdpp; # Gallons per day per person
        self.loadShapeNorm  = np.array(loadShapeNorm); # The normalized load shape
        self.supplyT        = supplyT; # The supply temperature to the occupants
        self.incomingT      = incomingT; # The incoming cold water temperature for the city
        self.storageT       = storageT; # The primary hot water storage temperature 
        self.compRuntime    = compRuntime; # The runtime?
        self.metered        = metered; # If the building as individual metering on the apartment or not
        self.percentUseable = percentUseable; #The  percent of useable storage
        
        self.aquaFract      = aquaFract; # The aquastat fraction
        self.defrostFactor  = defrostFactor; # The defrost factor. Derates the output power for defrost cycles.
        self.schematic      = schematic; # The schematic for sizing maybe just primary maybe with temperature maintenance.
        
        self.nApt           = nApt;
        
        self.__calcedVariables();

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
     
    def setRecircVars(self, Wapt, returnT, fdotRecirc):
        """Takes the recirc variables and solves for one that's set to zero"""
        if any(x < 0 for x in [Wapt, returnT, fdotRecirc]):
            raise Exception("All recirculation variables must be postitive.")
        if self.supplyT <= returnT:
            raise Exception("The return temperature is greater than the supply temperature! This sizer doesn't support heat trace on the recirculation loop")
        if Wapt == 0:
            self.Wapt = self.rhoCp / self.nApt * fdotRecirc * (self.supplyT - returnT) / self.W_TO_BTUMIN;
            self.returnT    = returnT;
            self.fdotRecirc = fdotRecirc;
        elif returnT == 0 and self.schematic == 'tempmaint':
            self.Wapt    = Wapt
            self.returnT = self.supplyT - Wapt * self.nApt *self.W_TO_BTUMIN / self.rhoCp / fdotRecirc;
            self.fdotRecirc = fdotRecirc;
        elif fdotRecirc == 0 and self.schematic == 'tempmaint':
            self.Wapt       = Wapt;
            self.returnT    = returnT;
            self.fdotRecirc = Wapt * self.nApt * self.W_TO_BTUMIN / self.rhoCp / (self.supplyT - returnT);
        else:
            raise Exception("In setting the recirculation variables one needs to be zero to solve for it.")
        
    def setTMVars(self, TMRuntime, setpointTM, Wapt, returnT, fdotRecirc):
        self.TMRuntime = TMRuntime;
        self.setpointTM = setpointTM;
        self.setRecircVars(Wapt, returnT, fdotRecirc);
        
    def setSwingVars(self, swingOnT, Wapt):
        self.swingOnT = swingOnT;
        self.Wapt = Wapt;      
        
# The meat of the script        
    def primaryHeatHrs2kBTUHR(self, heathours):
        """Returns the heating capacity in kBTU/hr for the heating hours given by, heathours"""
        heatCap = self.totalHWLoad / heathours * self.rhoCp * \
            (self.storageT - self.incomingT) / self.defrostFactor /1000.;
        return heatCap;
    
    def sizePrimaryTankVolume(self, heatHrs):
        """Sizes the primary HPWH plant with the new methodology"""
        if heatHrs <= 0 or heatHrs > 24:
            raise Exception("The heating capacity scaled to hours is invalid, value is "+ heatHrs)
            
        diffN = 1/heatHrs - np.append(self.loadShapeNorm,self.loadShapeNorm); 
        diffN = np.cumsum(diffN[np.argmax(diffN < 0.):]); #Get the rest of the day from the start of the peak

        runningVol = -min(np.append(diffN[diffN<0.], -0.)); #Minimum value less than 0 or 0.
        totalVol = runningVol / (1-self.aquaFract) / self.percentUseable;
        
        return totalVol * self.totalHWLoad * (self.supplyT - self.incomingT) / \
            (self.storageT - self.incomingT);

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
        self.TMVol = (self.Wapt + self.UAFudge) * self.nApt / self.rhoCp * \
            self.W_TO_BTUHR * self.offTime / (self.storageT - self.swingOnT);
        self.TMCap = 1.5 * (self.Wapt + self.UAFudge) * self.nApt * self.W_TO_BTUHR / 1000.;  #FACTOR OF 1.5!?!?
        
    def sizeTemperatureMaintenance(self):####FIX
        minRunTime = 1; # Hour
        self.TMCap =  24./self.TMRuntime * (self.Wapt + self.UAFudge) * self.nApt * self.W_TO_BTUHR / 1000.; #should we have this factor
        self.TMVol =  (self.Wapt + self.UAFudge) * self.nApt / self.rhoCp * \
            self.W_TO_BTUHR * minRunTime / (self.setpointTM - self.returnT);
        ###FINISH
       
# Helper Functions for reading and writing files 
    def __importArrLine(self, line, setLength):
        """Imports an array in line with a set length, setLength"""
        val = np.zeros(setLength);
        if len(line) > setLength: 
                raise Exception( '\nERROR: Too many data points given for loadShapeNorm, should be 24 but received '+ str(len(line)-1)+'.\n')  
        for ii in range(1,setLength):
            try:
                val[ii-1]  = float(line[ii]);
            except IndexError:
                raise Exception('\nERROR: Not enough data points given for loadShapeNorm, should be 24 but received '+str(ii)+'.\n') 
        return val         

    def initializeFromFile(self, fileName):
        """"Read in a formated file with filename"""
        
        Wapt = 0.; returnT = 0.; fdotRecirc = 0.;
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
                self.aquaFract = temp[1];
            elif temp[0] == "defrostfactor":
                temp[1] = float(temp[1])
                if temp[1] > 1: # Check to make sure the percent is stored as anumber 0 to 1.
                    temp[1] = temp[1]/100.
                self.defrostFactor = temp[1];
                
            elif temp[0] == "schematic":
                if temp[1] in self.schematicNames:
                    self.schematic  = temp[1];
                else:
                    raise Exception('\nERROR: Invalid input given for the schematic: "'+ str(temp[1])+'".\n')    
            elif temp[0] == "swingont":
                self.swingOnT   = float(temp[1]);
            elif temp[0] == "napt":
                self.nApt       = float(temp[1]);
                
            elif temp[0] == "tmruntime":
                self.TMRuntime  = float(temp[1]);
            elif temp[0] == "setpointtm":
                self.setpointTM  = float(temp[1]);
                  
            elif temp[0] == "wapt":
                Wapt      = float(temp[1]);
            elif temp[0] == "returnt":    
                returnT      = float(temp[1]);
            elif temp[0] == "fdotrecirc":    
                fdotRecirc      = float(temp[1]);
            else:
                raise Exception('\nERROR: Invalid input given: '+ line +'.\n')
        # End for loop reading file lines.    
        self.__calcedVariables()
        if self.schematic == 'tempmaint':
            self.setRecircVars(Wapt, returnT, fdotRecirc)
        elif self.schematic == 'swingtank':
            self.Wapt = Wapt;
            
    def __writeAttrLine(self, file, attrList):
        for field in attrList:
            var = getattr(self, field);
            if isinstance(var, np.ndarray):
                file.write(field + ', ' + np.array2string(var, precision = 4, separator=",", max_line_width = 300.) + '\n');
            elif isinstance(var, float):
                file.write('%s, %5.3f \n' %( field ,var));
            else:
                file.write( field + ', ' + str(var) + '\n');
                      
    def writeOutput(self, fileName):  
        """Writes the output to a file with file name filename."""
        varListOut = ['totalHWLoad','offTime', 'primaryHeatingRate',
                      'primaryHeatCap','primaryVol', 'TMCap', 'TMVol'];
        
        varListIn = ['nPeople', 'gpdpp', 'loadShapeNorm', 'storageT','supplyT', 
                      'incomingT', 'compRuntime','metered', 'percentUseable', 
                     'aquaFract', 'defrostFactor', 'schematic',
                     'nApt', 'Wapt', 'returnT', 'fdotRecirc', 'UAFudge',
                     'swingOnT', 'setpointTM', 'TMRuntime'];
        if sum(self.nBR*self.rBR) > 0:    
             ['nBR', 'rBR'] + varListIn
             
        with open(fileName, 'w+') as file1:
            file1.write('OUTPUTS\n')
            self.__writeAttrLine(file1, varListOut)
            pCurve = self.primaryCurve();
            file1.write('primaryCurve_vol, ')
            file1.write(np.array2string(pCurve[0], precision = 2, separator=",", max_line_width = 300.));
            file1.write('\n')
            file1.write('primaryCurve_heatCap, ')
            file1.write(np.array2string(pCurve[1], precision = 2, separator=",", max_line_width = 300.));
            file1.write('\n\n')
            file1.write('INPUTS\n')
            self.__writeAttrLine(file1, varListIn)
            
     

        