
import numpy as np
from HPWHComponents import PrimarySystem_SP, ParallelLoopTank, SwingTank # TrimTank, PrimarySystem_MP_NR, PrimarySystem_MP_R
from ashraesizer import ASHRAEsizer
from cfg import rhoCp, W_TO_BTUMIN

from plotly.graph_objs import Figure, Scatter
from plotly.offline import plot

##############################################################################
class HPWHsizerRead:
    """ Class for gathering hpwh sizing inputs """

    schematicNames = ["primary", "swingtank", "paralleltank", "trimtank"]

    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""
        self.nBR            = np.zeros(6) # Number of bedrooms 0Br, 1Br...
        self.rBR            = np.zeros(6) # Ratio of people bedrooms 0Br, 1Br...
        self.nPeople        = 0. # Nnumber of people
        self.gpdpp          = 0. # Gallons per day per person
        self.loadShapeNorm  = np.zeros(24) # The normalized load shape
        self.supplyT_F      = 0. # The supply temperature to the occupants
        self.incomingT_F    = 0. # The incoming cold water temperature for the city
        self.storageT_F     = 0. # The primary hot water storage temperature
        self.compRuntime_hr = 0. # The runtime?
        #self.metered        = 0 # If the building as individual metering on the apartment or not
        self.percentUseable = 0 # The  percent of useable storage

        self.defrostFactor  = 1. # The defrost factor. Derates the output power for defrost cycles.
        self.totalHWLoad_G  = 0

        self.schematic      = "" # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.nApt           = 0. # The number of apartments
        self.Wapt           = 0. # The recirculation loop losses in terms of W/apt
        self.fdotRecirc_gpm = 0. # The reciculation loop flow rate (gpm)
        self.returnT_F      = 0. # The reciculation loop return temperature (F)
        self.TMRuntime_hr   = 0. # The temperature maintenance minimum runtime.
        self.setpointTM_F   = 0. # The setpoint of the temperature maintenance tank.
        self.TMonTemp_F     = 0. # The temperature the temperature maintenance heat pump or resistance element turns on
        self.UAFudge        = 100. # A fudge factor used to adjust loop losses.
        self.offTime_hr     = 0. # The numbers of hours the tempeature maintenence system is designed to be off for.

        self.singlePass     = True # Single pass or multipass

    def initPrimaryByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass):
        self.nBR            = np.array(nBR) # Number of bedrooms 0Br, 1Br...
        self.rBR            = np.array(rBR) # Ratio of people bedrooms 0Br, 1Br...
        self.gpdpp          = gpdpp # Gallons per day per person
        self.loadShapeNorm  = np.array(loadShapeNorm) # The normalized load shape
        self.supplyT_F      = supplyT_F # The supply temperature to the occupants
        self.incomingT_F    = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F     = storageT_F # The primary hot water storage temperature
        self.compRuntime_hr = compRuntime_hr # The runtime?
        self.metered        = metered # If the building as individual metering on the apartment or not
        self.percentUseable = percentUseable #The  percent of useable storage

        self.defrostFactor  = defrostFactor # The defrost factor. Derates the output power for defrost cycles.

        self.schematic      = schematic # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.singlePass     = singlePass # Single pass or multipass

        self.__checkInputs()
        self.__calcedVariables()

    def initPrimaryByPeople(self, nPeople, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass, nApt):
        self.nPeople        = nPeople
        self.gpdpp          = gpdpp # Gallons per day per person
        self.loadShapeNorm  = np.array(loadShapeNorm) # The normalized load shape
        self.supplyT_F        = supplyT_F # The supply temperature to the occupants
        self.incomingT_F      = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F       = storageT_F # The primary hot water storage temperature
        self.compRuntime_hr    = compRuntime_hr # The runtime?
        self.metered        = metered # If the building as individual metering on the apartment or not
        self.percentUseable = percentUseable #The  percent of useable storage

        self.defrostFactor  = defrostFactor # The defrost factor. Derates the output power for defrost cycles.
        self.schematic      = schematic # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.singlePass     = singlePass # Single pass or multipass

        self.nApt           = nApt

        self.__checkInputs()
        self.__calcedVariables()

    def initTempMaint(self, Wapt, offTime_hr=0, TMRuntime_hr=0, setpointTM_F=0, TMonTemp_F=0):
        self.Wapt = Wapt
        if self.schematic == "swingtank":
            pass
        elif self.schematic == "paralleltank":
            if any(x==0 for x in [offTime_hr,TMRuntime_hr,setpointTM_F,TMonTemp_F]):
                raise Exception("ERROR in initTempMaint, paralleltank needs inputs != 0")
            else:
                self.offTime_hr       = offTime_hr
                self.TMRuntime_hr     = TMRuntime_hr
                self.setpointTM_F     = setpointTM_F
                self.TMonTemp_F       = TMonTemp_F
                
    def __checkInputs(self):
        """Checks inputs are all valid"""
        if len(self.loadShapeNorm) != 24 :
            raise Exception("loadShapeNorm is not of length 24 but instead "+str(len(self.loadShapeNorm))+".")
        if self.schematic not in self.schematicNames:
            raise Exception('\nERROR: Invalid input given for the schematic: "'+ self.schematic +'".\n')
        if self.percentUseable > 1 or self.percentUseable < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('\nERROR: Invalid input given for percentUseable.\n')
        if self.defrostFactor > 1 or self.defrostFactor < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('\nERROR: Invalid input given for defrostFactor.\n')

    def __calcedVariables(self):
        """ Calculate other variables needed."""
        if sum(self.nBR + self.nApt) == 0:
            raise Exception("Need input given for number of bedrooms by size or number of apartments")
        if self.nApt == 0:
            self.nApt = sum(self.nBR)
        if self.nPeople == 0:
            self.nPeople = sum(self.nBR * self.rBR)

        self.totalHWLoad_G = self.gpdpp * self.nPeople

# Helper Functions for reading and writing files
    def __importArrLine(self, line, setLength):
        """Imports an array in line with a set length, setLength"""
        val = np.zeros(setLength-1)
        if len(line) > setLength:
                raise Exception( '\nERROR: Too many data points given for array '+ str(len(line)-1)+'.\n')
        for ii in range(1,setLength):
            try:
                val[ii-1]  = float(line[ii])
            except IndexError:
                raise Exception('\nERROR: Not enough data points given for array '+str(ii)+'.\n')
        return val

    def initializeFromFile(self, fileName):
        """"Read in a formated file with filename"""
        # Get file inputs and assign them to the variables
        file1 = open(fileName, 'r')
        fileLines = file1.read().splitlines()
        file1.close()
        for line in fileLines:
            temp = line.lower().split()

            if temp[0] == "nbr":
                self.nBR =  self.__importArrLine(temp, 7)
            elif temp[0] == "rbr":
                self.rBR = self.__importArrLine(temp, 7)
            elif temp[0] == "npeople":
                self.nPeople    = float(temp[1])
            elif temp[0] == "gpdpp":
                self.gpdpp      = float(temp[1])
            elif temp[0] == "loadshapenorm":
                self.loadShapeNorm  = self.__importArrLine(temp, 25)
            elif temp[0] == "supplyt_f":
                self.supplyT_F    = float(temp[1])
            elif temp[0] == "incomingt_f":
                self.incomingT_F  = float(temp[1])
            elif temp[0] == "storaget_f":
                self.storageT_F   = float(temp[1])
            elif temp[0] == "compruntime_hr":
                self.compRuntime_hr  = float(temp[1])
            elif temp[0] == "metered":
                self.metered    =  int(temp[1]) # If the building as individual metering on the apartment or not

            elif temp[0] == "percentuseable":
                temp[1] = float(temp[1])
                if temp[1] > 1: # Check to make sure the percent is stored as anumber 0 to 1.
                    temp[1] = temp[1]/100.
                self.percentUseable = temp[1]#The  percent of useable storage

            elif temp[0] == "defrostfactor":
                temp[1] = float(temp[1])
                if temp[1] > 1: # Check to make sure the percent is stored as anumber 0 to 1.
                    temp[1] = temp[1]/100.
                self.defrostFactor = temp[1]

            elif temp[0] == "schematic":
                self.schematic  = temp[1]
            elif temp[0] == "singlepass":
                self.singlePass  = temp[1] in ['true','1','t','y']

            elif temp[0] == "napt":
                self.nApt       = float(temp[1])

            elif temp[0] == "tmruntime_hr":
                self.TMRuntime_hr  = float(temp[1])
            elif temp[0] == "setpointtm_f":
                self.setpointTM_F  = float(temp[1])
            elif temp[0] == "tmontemp_f":
                self.TMonTemp_F   = float(temp[1])
            elif temp[0] == "offtime_hr":
                self.offTime_hr   = float(temp[1])
            elif temp[0] == "wapt":
                self.Wapt      = float(temp[1])
            else:
                raise Exception('\nERROR: Invalid input given: '+ line +'.\n')
        # End for loop reading file lines.

        self.__checkInputs()
        self.__calcedVariables()

##############################################################################
class writeClassAtts:

    def __init__(self, obj1, fileName, permission):
        self.obj = obj1
        self.fileName = fileName
        f = open(fileName, permission)
        f.close()

    def __writeAttrLine(self, file, attrList):
        for field in attrList:
            var = getattr(self.obj, field)
            if isinstance(var, np.ndarray):
                file.write(field + ', ' + np.array2string(var, precision = 4, separator=",", max_line_width = 300.) + '\n')
            elif isinstance(var, float):
                file.write('%s, %5.3f\n' %( field ,var))
            else:
                file.write( field + ', ' + str(var) + '\n')

    def writeToFile(self):
        """Writes the output to a file with file name filename."""
        objAtt = list(self.obj.__dict__.keys()) # Gets all the attributes in an object

        with open(self.fileName, 'a') as file1:
            self.__writeAttrLine(file1, objAtt)

    def writeLine(self, text):
        with open(self.fileName, 'a') as file1:
             file1.write(text + '\n')

##############################################################################
class HPWHsizer:
    """ Organizes a primary and temperature maintenance system and sizes it"""
    def __init__(self):
        self.validbuild = False

        self.primarySystem = 0
        self.tempmaintSystem = 0
        self.translate = HPWHsizerRead()
        self.ashraeSize = 0.
        
    def initializeFromFile(self, fileName):
        self.translate.initializeFromFile(fileName)

    def initPrimaryByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass):
        self.translate.initPrimaryByUnits(nBR, rBR, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass)

    def initPrimaryByPeople(self,  nPeople, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass, nApt):
        self.translate.initPrimaryByPeople(nPeople, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass, nApt )

    def initTempMaint(self, Wapt, offTime_hr = 1, TMRuntime_hr = 2, setpointTM_F = 135, TMonTemp_F = 0):
        """Initializes the temperature maintanence system after the primary system"""
        if self.translate.totalHWLoad_G == 0:
            raise Exception("must initialize the primary system first")
            
        if self.translate.schematic == "swingtank":
            self.translate.initTempMaint(Wapt, 0, 0, 0, 0) 
            
        elif  self.translate.schematic == "paralleltank":
            if TMonTemp_F == 0: 
                TMonTemp_F = self.translate.supplyT_F + 2;
            self.translate.initTempMaint(Wapt, offTime_hr, TMRuntime_hr, setpointTM_F, TMonTemp_F)

    def buildSystem(self):
        """Builds a single pass or multi pass centralized HPWH plant"""
        self.ashraeSize = ASHRAEsizer(self.translate.nPeople,
                                        self.translate.gpdpp,
                                        self.translate.incomingT_F,
                                        self.translate.supplyT_F,
                                        self.translate.storageT_F,
                                        self.translate.defrostFactor,
                                        self.translate.percentUseable,
                                        self.translate.compRuntime_hr)

        if self.translate.singlePass:
            self.primarySystem = PrimarySystem_SP(self.translate.totalHWLoad_G,
                                                 self.translate.loadShapeNorm,
                                                 self.translate.nPeople,
                                                 self.translate.incomingT_F,
                                                 self.translate.supplyT_F,
                                                 self.translate.storageT_F,
                                                 self.translate.defrostFactor,
                                                 self.translate.percentUseable,
                                                 self.translate.compRuntime_hr)

        # Multipass world: will have multipass no recirc, multipass with recirc, and multipass with trim tank.
        elif not self.translate.singlePass:
            # Multipass systems not yet supported
            raise Exception("Multipass not yet supported")

        if self.translate.schematic == "primary":
            pass
        elif self.translate.schematic == "paralleltank":
            self.tempmaintSystem = ParallelLoopTank(self.translate.nApt,
                                     self.translate.Wapt,
                                     self.translate.UAFudge,
                                     self.translate.offTime_hr,
                                     self.translate.TMRuntime_hr,
                                     self.translate.setpointTM_F,
                                     self.translate.TMonTemp_F)
        elif self.translate.schematic == "swingtank":
            self.tempmaintSystem = SwingTank(self.translate.nApt,
                                     self.translate.Wapt,
                                     self.translate.UAFudge)
        elif self.translate.schematic == "trimtank":
            raise Exception("Trim tanks are not supported yet")
        else:
            raise Exception ("Invalid schematic set up: " + self.translate.schematic)

        if self.primarySystem != 0:
            self.validbuild = True
        else:
            raise Exception ("The HPWH system did not build properly") 

    def sizeSystem(self):
        """Sizes the built system"""
        if self.validbuild:
            self.primarySystem.sizeVol_Cap()
            # It is fine if the temperature maintenance system is 0
            if self.tempmaintSystem != 0:
                self.tempmaintSystem.sizeVol_Cap()
        else:
            raise Exception("The system can not be sized without a valid build")

    def build_size(self):
        """
        One function to build and size the HPWH system after initalization, that returns minimum results 
        Returns
        -------
        array 
            [PVol_G_atStorageT, PCap, aquaFract, TMVol_G_atStorageT, TMCap]
        """
        self.buildSystem()
        self.sizeSystem()
        return([self.primarySystem.getSizingResults(), self.tempmaintSystem.getSizingResults()])
        
    def plotSizingCurve(self, return_as_div = True):
        """
        Returns a plot of the sizing curve as a div
        
        Parameters
        ----------
        return_as_div
            A logical on the output, as a div (true) or as a figure (false)
        Returns
        -------
        div/fig
            plot_div
        """
        fig = Figure()

        [x_data, y_data] = self.primarySystem.primaryCurve()
        fig.add_trace(Scatter(x=x_data, y=y_data,
                              mode='lines', name='Primary Sizing Curve',
                              opacity=0.8, marker_color='green'))
        
        [x_data, y_data] = self.ashraeSize.primaryCurve()
        fig.add_trace(Scatter(x=x_data[:-1], y=y_data[:-1], #Drops the last point
                              mode='lines', name='ASHRAE Sizing Curve',
                              opacity=0.8, marker_color='red'))
        
        fig.add_trace(Scatter(x=(0,x_data[-2]), 
                              y=(self.primarySystem.PCap,self.primarySystem.PCap),
                              mode='lines', name='Minimum Size',
                              opacity=0.8, marker_color='grey'))     
        
        fig.update_layout(xaxis_title="Primary Tank Volume (Gallons)",
                          yaxis_title="Primary Heating Capacity (kBTU/hr)")
        
        if return_as_div:
            plot_div = plot(fig,  output_type='div', show_link=False, link_text="",
                        include_plotlyjs = False)
            return plot_div
        else:
            return fig
    
    def writeToFile(self,fileName):
        primaryWriter = writeClassAtts(self.primarySystem, fileName, 'w+')
        primaryWriter.writeLine('primarySystem:\n')
        primaryWriter.writeToFile()
        pCurve = self.primarySystem.primaryCurve()
        primaryWriter.writeLine('primaryCurve_vol, ' +np.array2string(pCurve[0], precision = 2, separator=",", max_line_width = 300.))
        primaryWriter.writeLine('primaryCurve_heatCap, ' +np.array2string(pCurve[1], precision = 2, separator=",", max_line_width = 300.))

        TMWriter = writeClassAtts(self.tempmaintSystem, fileName, 'a')
        TMWriter.writeLine('\ntemperatureMaintenanceSystem:')
        TMWriter.writeLine('schematic, '+ self.translate.schematic)
        TMWriter.writeToFile()
