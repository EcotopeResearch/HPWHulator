
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
        self.UAFudge        = 0. # A fudge factor used to adjust loop losses.
        self.offTime_hr     = 0. # The numbers of hours the tempeature maintenence system is designed to be off for.

        self.singlePass     = True # Single pass or multipass

    def initByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass,
                    Wapt, returnT_F, fdotRecirc_gpm):
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
        self.__defaultTM()

    def initByPeople(self, nPeople, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass,
                    nApt, Wapt, returnT_F, fdotRecirc_gpm):
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
        self.setRecircVars( Wapt, returnT_F, fdotRecirc_gpm )
        self.__calcedVariables()
        self.__defaultTM()

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
        self.UAFudge = 3

    def setRecircVars(self, Wapt, returnT_F, fdotRecirc_gpm):
        """Takes the recirc variables and solves for one that's set to zero"""
        if any(x < 0 for x in [Wapt, returnT_F, fdotRecirc_gpm]):
            raise Exception("All recirculation variables must be postitive.")
        if self.supplyT_F <= returnT_F:
            raise Exception("The return temperature is greater than the supply temperature! This sizer doesn't support heat trace on the recirculation loop")
        if Wapt == 0.:
            self.Wapt       = rhoCp / self.nApt * fdotRecirc_gpm * (self.supplyT_F - returnT_F) / W_TO_BTUMIN
            self.returnT_F    = returnT_F
            self.fdotRecirc_gpm = fdotRecirc_gpm
        elif returnT_F == 0. and self.schematic == 'paralleltank':
            self.Wapt       = Wapt
            self.returnT_F    = self.supplyT_F - Wapt * self.nApt *W_TO_BTUMIN / rhoCp / fdotRecirc_gpm
            self.fdotRecirc_gpm = fdotRecirc_gpm
        elif fdotRecirc_gpm == 0. and self.schematic == 'paralleltank':
            self.Wapt       = Wapt
            self.returnT_F    = returnT_F
            self.fdotRecirc_gpm = Wapt * self.nApt * W_TO_BTUMIN / rhoCp / (self.supplyT_F - returnT_F)
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
            self.TMRuntime_hr     = 1. if self.TMRuntime_hr == 0 else self.TMRuntime_hr # The temperature maintenance minimum runtime.
            self.setpointTM_F     = 135 if self.setpointTM_F == 0 else self.setpointTM_F # The setpoint of the temperature maintenance tank.
            self.TMonTemp_F       = self.returnT_F if self.TMonTemp_F == 0 else self.TMonTemp_F
            self.offTime_hr       = 0.5 if self.offTime_hr == 0 else self.offTime_hr
        if self.schematic == "swingtank":
            self.TMonTemp_F       = self.supplyT_F + 2. if self.TMonTemp_F == 0 else self.TMonTemp_F
            #The overnight design for off time.
            if self.offTime_hr == 0:
                self.offTime_hr = sum(np.append(self.loadShapeNorm,self.loadShapeNorm)[22:36] < 1./48.)

    def setTMVars(self, TMonTemp_F, setpointTM_F, offTime_hr, TMRuntime_hr):
        if self.schematic != "paralleltank":
            raise Exception("The schematic for this sizer is " +self.schematic +", but you are trying to access the temperature maintenance sizing init")
        self.TMRuntime_hr = TMRuntime_hr
        self.offTime_hr = offTime_hr
        self.setpointTM_F = setpointTM_F
        self.TMonTemp_F = TMonTemp_F

    def setSwingVars(self, TMonTemp_F):
        if self.schematic != "swingtank":
            raise Exception("The schematic for this sizer is " +self.schematic +", but you are trying to access the swing tank sizing init")
        self.TMonTemp_F = TMonTemp_F

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

        Wapt = 0.
        returnT_F = 0.
        fdotRecirc_gpm = 0.

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
                Wapt      = float(temp[1])
            elif temp[0] == "returnt_f":
                returnT_F      = float(temp[1])
            elif temp[0] == "fdotRecirc_gpm":
                fdotRecirc_gpm      = float(temp[1])
            else:
                raise Exception('\nERROR: Invalid input given: '+ line +'.\n')
        # End for loop reading file lines.

        self.__checkInputs()
        self.__calcedVariables()
        if self.schematic == 'paralleltank':
            self.setRecircVars(Wapt, returnT_F, fdotRecirc_gpm)
        elif self.schematic == 'swingtank':
            self.Wapt = Wapt
        self.__defaultTM()

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

    def initByUnits(self, nBR, rBR, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass,
                    Wapt, returnT_F, fdotRecirc_gpm):
        self.translate.initByUnits(nBR, rBR, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass,
                    Wapt, returnT_F, fdotRecirc_gpm)

    def initByPeople(self,  nPeople, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass,
                    nApt, Wapt, returnT_F, fdotRecirc_gpm):

        self.translate.initByPeople(nPeople, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, metered, percentUseable, defrostFactor,
                    schematic, singlePass,
                    nApt, Wapt, returnT_F, fdotRecirc_gpm )

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
                                     self.translate.storageT_F,
                                     self.translate.Wapt,
                                     self.translate.UAFudge,
                                     self.translate.offTime_hr,
                                     self.translate.TMonTemp_F)
        elif self.translate.schematic == "trimtank":
            raise Exception("Trim tanks are not supported yet")
        else:
            raise Exception ("Invalid schematic set up: " + self.translate.schematic)

        if self.primarySystem != 0:
            self.validbuild = True

    def sizeSystem(self):
        """Sizes the built system"""
        if self.validbuild:
            self.primarySystem.sizeVol_Cap()
            # It is fine if the temperature maintenance system is 0
            if self.tempmaintSystem != 0:
                self.tempmaintSystem.sizeVol_Cap()
        else:
            raise Exception("The system can not be sized without a valid build")

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
