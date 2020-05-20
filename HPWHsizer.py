
import numpy as np;
from HPWHComponents import PrimarySystem_SP, ParallelLoopTank, SwingTank; # TrimTank, PrimarySystem_MP_NR, PrimarySystem_MP_R;
from cfg import rhoCp, W_TO_BTUHR, W_TO_BTUMIN


##############################################################################
class HPWHsizerRead:
    """ Class for gathering hpwh sizing inputs """
    
    schematicNames = ["primary", "swingtank", "paralleltank", "trimtank"];

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
        self.totalHWLoad    = 0;

        self.schematic      = ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.nApt           = 0.; # The number of apartments
        self.Wapt           = 0.; # The recirculation loop losses in terms of W/apt
        self.fdotRecirc     = 0.; # The reciculation loop flow rate (gpm)
        self.returnT        = 0.; # The reciculation loop return temperature (F)
        self.TMRuntime      = 0.; # The temperature maintenance minimum runtime.
        self.setpointTM     = 0.; # The setpoint of the temperature maintenance tank.
        self.TMonTemp       = 0.;
        self.UAFudge        = 0.;
        self.flushTime      = 0.;
        self.offTime        = 0.;
        
        self.singlePass     = True; # Single pass or multipass
        
    def initByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor, 
                    schematic, singlePass,
                    Wapt, returnT, fdotRecirc ):
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
        self.singlePass     = singlePass; # Single pass or multipass
        self.__checkInputs();
        self.__calcedVariables()
        self.setRecircVars( Wapt, returnT, fdotRecirc );
        self.__defaultTM();

    def initByPeople(self, nPeople, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor,
                    schematic, singlePass, 
                    nApt, Wapt, returnT, fdotRecirc ):
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
        self.singlePass     = singlePass; # Single pass or multipass

        self.nApt           = nApt;
        
        self.__checkInputs();
        self.__calcedVariables();
        self.setRecircVars( Wapt, returnT, fdotRecirc );
        self.__defaultTM();

    
    def __checkInputs(self):
        """Checks inputs are all valid"""
        if len(self.loadShapeNorm) != 24 :
            raise Exception("loadShapeNorm is not of length 24 but instead "+str(len(self.loadShapeNorm))+".")
        if self.schematic not in self.schematicNames:                    
            raise Exception('\nERROR: Invalid input given for the schematic: "'+ self.schematic +'".\n')    
        if self.percentUseable > 1 or self.percentUseable < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('\nERROR: Invalid input given for percentUseable.\n')    
        if self.aquaFract > 1 or self.aquaFract < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('\nERROR: Invalid input given for aquaFract.\n') 
        if self.defrostFactor > 1 or self.defrostFactor < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('\nERROR: Invalid input given for defrostFactor.\n')  
    
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
        self.UAFudge = 3
        #The overnight design for off time. 
        self.offTime = sum(np.append(self.loadShapeNorm,self.loadShapeNorm)[22:36] < 1./48.) 
        
    def setRecircVars(self, Wapt, returnT, fdotRecirc):
        """Takes the recirc variables and solves for one that's set to zero"""
        if any(x < 0 for x in [Wapt, returnT, fdotRecirc]):
            raise Exception("All recirculation variables must be postitive.")
        if self.supplyT <= returnT:
            raise Exception("The return temperature is greater than the supply temperature! This sizer doesn't support heat trace on the recirculation loop")
        if Wapt == 0.:
            self.Wapt       = rhoCp / self.nApt * fdotRecirc * (self.supplyT - returnT) / W_TO_BTUMIN;
            self.returnT    = returnT;
            self.fdotRecirc = fdotRecirc;
        elif returnT == 0. and self.schematic == 'paralleltank':
            self.Wapt       = Wapt
            self.returnT    = self.supplyT - Wapt * self.nApt *W_TO_BTUMIN / rhoCp / fdotRecirc;
            self.fdotRecirc = fdotRecirc;
        elif fdotRecirc == 0. and self.schematic == 'paralleltank':
            self.Wapt       = Wapt;
            self.returnT    = returnT;
            self.fdotRecirc = Wapt * self.nApt * W_TO_BTUMIN / rhoCp / (self.supplyT - returnT);
        elif self.schematic == 'paralleltank':
            raise Exception("In setting the recirculation variables for a temperature maintenance system one needs to be zero to solve for it.")
        elif self.schematic == 'swingtank':
            if self.Wapt == 0.:
                if Wapt == 0.:
                    raise Exception("In setting the recirculation variables for a swing tank system Wapt needs to be defined")
                else:
                    self.Wapt = Wapt    
    
    def __defaultTM(self):
        """Function to set the defualt variables of the temperature maintenance systems"""
        if self.schematic == "paralleltank":
            self.TMRuntime      = 1. if self.TMRuntime == 0 else self.TMRuntime; # The temperature maintenance minimum runtime.
            self.setpointTM     = 135 if self.setpointTM == 0 else self.setpointTM; # The setpoint of the temperature maintenance tank.
            self.TMonTemp       = self.returnT if self.TMonTemp == 0 else self.TMonTemp;
            self.flushTime      = 0.5 if self.flushTime == 0 else self.flushTime;
        if self.schematic == "swingtank":
            self.TMonTemp       = self.supplyT + 2. if self.TMonTemp == 0 else self.TMonTemp;
    
    def setTMVars(self, TMRuntime, setpointTM,):
        if self.schematic != "paralleltank":
            raise Exception("The schematic for this sizer is " +self.schematic +", but you are trying to access the temperature maintenance sizing init")
        self.TMRuntime = TMRuntime;
        self.setpointTM = setpointTM;
    
    def setSwingVars(self, swingOnT):
        if self.schematic != "swingtank":
            raise Exception("The schematic for this sizer is " +self.schematic +", but you are trying to access the swing tank sizing init")
        self.TMonTemp = swingOnT;
        
# Helper Functions for reading and writing files 
    def __importArrLine(self, line, setLength):
        """Imports an array in line with a set length, setLength"""
        val = np.zeros(setLength-1);
        if len(line) > setLength: 
                raise Exception( '\nERROR: Too many data points given for array '+ str(len(line)-1)+'.\n')  
        for ii in range(1,setLength):
            try:
                val[ii-1]  = float(line[ii]);
            except IndexError:
                raise Exception('\nERROR: Not enough data points given for array '+str(ii)+'.\n') 
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
                self.schematic  = temp[1];
            elif temp[0] == "singlepass":
                self.singlePass  = temp[1] in ['true','1','t','y'];
                
            elif temp[0] == "swingont":
                self.swingOnT  = temp[1];
                
            elif temp[0] == "napt":
                self.nApt       = float(temp[1]);
                
            elif temp[0] == "tmruntime":
                self.TMRuntime  = float(temp[1]);
            elif temp[0] == "setpointtm":
                self.setpointTM  = float(temp[1]);
            elif temp[0] == "tmontemp":
                self.TMonTemp   = float(temp[1]);
                
            elif temp[0] == "wapt":
                Wapt      = float(temp[1]);
            elif temp[0] == "returnt":    
                returnT      = float(temp[1]);
            elif temp[0] == "fdotrecirc":    
                fdotRecirc      = float(temp[1]);
            else:
                raise Exception('\nERROR: Invalid input given: '+ line +'.\n')
        # End for loop reading file lines.    
        
        self.__checkInputs();
        self.__calcedVariables()
        if self.schematic == 'paralleltank':
            self.setRecircVars(Wapt, returnT, fdotRecirc)
        elif self.schematic == 'swingtank':
            self.Wapt = Wapt;
        self.__defaultTM();

##############################################################################
class writeClassAtts:               
    
    def __init__(self, obj1, fileName, permission):
        self.obj = obj1;
        self.fileName = fileName;
        f = open(fileName, permission);
        f.close();
        
    def __writeAttrLine(self, file, attrList):
        for field in attrList:
            var = getattr(self.obj, field);
            if isinstance(var, np.ndarray):
                file.write(field + ', ' + np.array2string(var, precision = 4, separator=",", max_line_width = 300.) + '\n');
            elif isinstance(var, float):
                file.write('%s, %5.3f \n' %( field ,var));
            else:
                file.write( field + ', ' + str(var) + '\n');
        
    def writeToFile(self):  
        """Writes the output to a file with file name filename."""
        objAtt = list(self.obj.__dict__.keys()) # Gets all the attributes in an object
                     
        with open(self.fileName, 'a') as file1:
            self.__writeAttrLine(file1, objAtt)
           
    def writeLine(self, text):
        with open(self.fileName, 'a') as file1:
             file1.write(text + '\n');

##############################################################################       
class HPWHsizer:
    """ Organizes a primary and temperature maintenance system and sizes it"""
    def __init__(self):
        self.validbuild = False;

        self.primarySystem = 0;
        self.paralleltankSystem = 0;
        self.translate = HPWHsizerRead();
        
    def initializeFromFile(self, fileName):
        self.translate.initializeFromFile(fileName);
    
    def initByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor, 
                    schematic, singlePass,
                    Wapt, returnT, fdotRecirc ):
        self.translate.initByUnits(nBR, rBR, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor, 
                    schematic, singlePass,
                    Wapt, returnT, fdotRecirc )
    
    def initByPeople(self,  nPeople, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor,
                    schematic, singlePass,
                    nApt, Wapt, returnT, fdotRecirc):
        self.translate.initByPeople(nPeople, gpdpp, loadShapeNorm, supplyT, incomingT, 
                    storageT, compRuntime, metered, percentUseable, aquaFract, defrostFactor,
                    schematic, singlePass,
                    nApt, Wapt, returnT, fdotRecirc );

    def buildSystem(self):
        """Builds a single pass or multi pass centralized HPWH plant"""
        if self.translate.singlePass:
            self.primarySystem = PrimarySystem_SP(self.translate.totalHWLoad, 
                                                 self.translate.loadShapeNorm, 
                                                 self.translate.incomingT, 
                                                 self.translate.supplyT, 
                                                 self.translate.storageT,
                                                 self.translate.defrostFactor, 
                                                 self.translate.percentUseable,
                                                 self.translate.aquaFract,
                                                 self.translate.compRuntime);
                            
        # Multipass world: will have multipass no recirc, multipass with recirc, and multipass with trim tank.
        elif not self.translate.singlePass:     
            # Multipass systems not yet supported
            raise Exception("Multipass not yet supported")
            
        if self.translate.schematic == "primary":
            pass;
        elif self.translate.schematic == "paralleltank":
            self.paralleltankSystem = ParallelLoopTank(self.translate.nApt,  
                                     self.translate.Wapt,  
                                     self.translate.UAFudge, 
                                     self.translate.flushTime, 
                                     self.translate.TMRuntime, 
                                     self.translate.setpointTM, 
                                     self.translate.TMonTemp);
        elif self.translate.schematic == "swingtank":
            self.paralleltankSystem = SwingTank(self.translate.nApt, 
                                     self.translate.storageT, 
                                     self.translate.Wapt, 
                                     self.translate.UAFudge,
                                     self.translate.offTime, 
                                     self.translate.TMonTemp);
        elif self.translate.schematic == "trimtank":
            raise Exception("Trim tanks are not supported yet")
        else: 
            raise Exception ("Invalid schematic set up: " + self.translate.schematic)
        if self.primarySystem != 0:    
            self.validbuild = True;
        
    def sizeSystem(self):
        """Sizes the built system"""
        if self.validbuild:
            self.primarySystem.sizeVol_Cap();
            # It is fine if the temperature maintenance system is 0    
            if self.paralleltankSystem != 0: 
                self.paralleltankSystem.sizeVol_Cap();             
        else:
            raise Exception("The system can not be sized without a valid build")
    
    def writeToFile(self,fileName):
        primaryWriter = writeClassAtts(self.primarySystem, fileName, 'w+');
        primaryWriter.writeLine('primarySystem:\n');
        primaryWriter.writeToFile();
        pCurve = self.primarySystem.primaryCurve();
        primaryWriter.writeLine('primaryCurve_vol, ' +np.array2string(pCurve[0], precision = 2, separator=",", max_line_width = 300.))
        primaryWriter.writeLine('primaryCurve_heatCap, ' +np.array2string(pCurve[1], precision = 2, separator=",", max_line_width = 300.))
    
        TMWriter = writeClassAtts(self.paralleltankSystem, fileName, 'a');
        TMWriter.writeLine('\ntemperatureMaintenanceSystem:');
        TMWriter.writeLine('schematic, '+ self.translate.schematic)
        TMWriter.writeToFile();

