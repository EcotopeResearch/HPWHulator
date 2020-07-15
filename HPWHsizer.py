
import numpy as np
from HPWHComponents import PrimarySystem_SP, ParallelLoopTank, SwingTank # TrimTank, PrimarySystem_MP_NR, PrimarySystem_MP_R
from ashraesizer import ASHRAEsizer

from plotly.graph_objs import Figure, Scatter
from plotly.offline import plot


##############################################################################
class HPWHsizer:
    """ Organizes a primary and temperature maintenance system and sizes it"""
    def __init__(self):
        self.validbuild     = False
        self.primaryInit    = False
        self.systemSized    = False
        self.doLoadShift    = False
        self.inputs = HPWHsizerRead()

        self.primarySystem = None
        self.tempmaintSystem = None
        self.ashraeSize = None

        self.swingTankLoad_W = 0.


    def initializeFromFile(self, fileName):
        self.inputs.initializeFromFile(fileName)

    def initPrimaryByUnits(self, nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, defrostFactor, aquaFract,
                    schematic, singlePass=True):
        self.inputs.initPrimaryByUnits(nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, defrostFactor, aquaFract,
                    schematic, singlePass)
        self.primaryInit = True

    def initPrimaryByPeople(self,  nPeople, nApt,  gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, defrostFactor, aquaFract,
                    schematic, singlePass=True):
        self.inputs.initPrimaryByPeople(nPeople, nApt, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, defrostFactor, aquaFract,
                    schematic, singlePass )

    def initTempMaint(self, Wapt, setpointTM_F = 135, TMonTemp_F = 0 ):
        """
        Initializes the temperature maintanence system after the primary system
        with either "swingtank" or "paralleltank".

        """
        if self.primaryInit is None:
            raise Exception("must initialize the primary system first")

        if self.inputs.schematic == "swingtank" or self.inputs.schematic == "paralleltank":
            if TMonTemp_F == 0:
                TMonTemp_F = self.inputs.supplyT_F + 2;
            self.inputs.initTempMaint(Wapt, setpointTM_F, TMonTemp_F)

    def setLoadShiftforPrimary(self, ls_arr):
        """
        Resets the load shift to user defined values

        Args:
            ls_arr (array): Array of zeros and ones to define when HPWH's are allowed to run for load shift.

        Returns:
            None.

        """
        self.inputs.setLoadShift(ls_arr)
        self.doLoadShift    = True

    def buildSystem(self):
        """Builds a single pass or multi pass centralized HPWH plant"""
        self.ashraeSize = ASHRAEsizer(self.inputs.nPeople,
                                        self.inputs.gpdpp,
                                        self.inputs.incomingT_F,
                                        self.inputs.supplyT_F,
                                        self.inputs.storageT_F,
                                        self.inputs.defrostFactor,
                                        self.inputs.percentUseable,
                                        self.inputs.compRuntime_hr)

        if self.inputs.schematic == "primary":
            pass
        elif self.inputs.schematic == "paralleltank":
            self.tempmaintSystem = ParallelLoopTank(self.inputs.nApt,
                                     self.inputs.Wapt,
                                     self.inputs.setpointTM_F,
                                     self.inputs.TMonTemp_F)
        elif self.inputs.schematic == "swingtank":
            self.tempmaintSystem = SwingTank(self.inputs.nApt,
                                     self.inputs.Wapt)
            # Get part of recicualtion loop losses added to primary system
            self.swingTankLoad_W = self.tempmaintSystem.getSwingLoadOnPrimary_W()

        elif self.inputs.schematic == "trimtank":
            raise Exception("Trim tanks are not supported yet")
        else:
            raise Exception ("Invalid schematic set up: " + self.inputs.schematic)


        if self.inputs.singlePass:
            self.primarySystem = PrimarySystem_SP(self.inputs.totalHWLoad_G,
                                                 self.inputs.loadShapeNorm,
                                                 self.inputs.nPeople,
                                                 self.inputs.incomingT_F,
                                                 self.inputs.supplyT_F,
                                                 self.inputs.storageT_F,
                                                 self.inputs.defrostFactor,
                                                 self.inputs.percentUseable,
                                                 self.inputs.compRuntime_hr,
                                                 self.inputs.aquaFract,
                                                 self.swingTankLoad_W)
            if self.doLoadShift:
                self.primarySystem.setLoadShift(self.inputs.loadshift)

        elif not self.inputs.singlePass:
            # Multipass systems not yet supported
            raise Exception("Multipass is yet supported")


        if self.primarySystem is not None:
            self.validbuild = True
        else:
            raise Exception ("The HPWH system did not build properly")

    def sizeSystem(self):
        """
        Sizes the built system

        Returns
        -------
        list
            [PVol_G_atStorageT, PCap_kBTUhr, TMVol_G_atStorageT, TMCap_kBTUhr]
        """
        if self.validbuild:
            self.primarySystem.sizeVol_Cap()
            self.systemSized = True

            #Check for a temp maint system
            if self.tempmaintSystem :
                self.tempmaintSystem.sizeVol_Cap()
                return self.primarySystem.getSizingResults() + self.tempmaintSystem.getSizingResults()
            else:
                return self.primarySystem.getSizingResults()
        else:
            raise Exception("The system can not be sized without a valid build")

    def build_size(self):
        """
        One function to build and size the HPWH system after initalization, that returns minimum results
        Returns
        -------
        list
            [PVol_G_atStorageT, PCap_kBTUhr, TMVol_G_atStorageT, TMCap_kBTUhr]
        """
        self.buildSystem()
        return self.sizeSystem()

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
        if not self.systemSized:
            raise Exception("System must be sized first")

        fig = Figure()

        hovertext = 'Storage Volume: %{x:.1f} gallons \nHeating Capacity: %{y:.1f}'

        [x_data, y_data] = self.primarySystem.primaryCurve()
        fig.add_trace(Scatter(x=x_data, y=y_data,
                              mode='lines', name='Primary Sizing Curve',
                              hovertemplate = hovertext,
                              opacity=0.8, marker_color='green'))

        [x_ash, y_ash] = self.ashraeSize.primaryCurve()
        fig.add_trace(Scatter(x=x_ash[:-1], y=y_ash[:-1], #Drops the last point
                              mode='lines', name='ASHRAE Sizing Curve',
                              hovertemplate = hovertext,
                              opacity=0.8, marker_color='red'))

        # [xlow, ylow] = self.ashraeSize.getLowCurve()
        # fig.add_trace(Scatter(x=xlow[:-1], y=ylow[:-1], #Drops the last point
        #               mode='lines',   opacity=0.4,  marker_color='crimson',
        #               hovertemplate = hovertext,
        #               name='ASHRAE Low Curve' ))
        

        fig.add_trace(Scatter(x=(0,max(x_data[-1],x_ash[-2])),
                              y=(self.primarySystem.PCap_kBTUhr,self.primarySystem.PCap_kBTUhr),
                              mode='lines', name='Minimum Size',
                              opacity=0.8, marker_color='grey'))

        fig.update_layout(title="Primary Sizing Curve",
                          xaxis_title="Primary Tank Volume (Gallons)",
                          yaxis_title="Primary Heating Capacity (kBTU/hr)")

        if return_as_div:
            plot_div = plot(fig,  output_type='div', show_link=False, link_text="",
                        include_plotlyjs = False)
            return plot_div
        else:
            return fig

    def plotPrimaryStorageLoadSim(self, return_as_div = True):
        """
        Returns a plot of the of the simulation for the minimum sized primary system

        Parameters
        ----------
        return_as_div
            A logical on the output, as a div (true) or as a figure (false)
        Returns
        -------
        div/fig
            plot_div
        """
        if not self.systemSized:
            raise Exception("System must be sized first")
        if self.inputs.schematic == "swingtank":
            raise Exception("Simulation does not support swing tanks at the moment")

        fig = Figure()

        [ V, G_hw, D_hw, run ] = self.primarySystem.runStorage_Load_Sim();

        nameG_hw = "HW Generation - Compressor hrs/day: %.1f " % (sum(run[24:])/max(G_hw)/2)
        x_data = list(range(len(V)))
        fig.add_trace(Scatter(x=x_data, y=V, name='Useful Storage Volume',
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='green'))
        fig.add_trace(Scatter(x=x_data, y=run, name = nameG_hw,
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='red'))
        fig.add_trace(Scatter(x=x_data, y=D_hw, name='Hot Water Demand',
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='blue'))
        fig.add_trace(Scatter(x=x_data, y=G_hw, name='Generation Volume per Hour',
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='grey'))

        fig.update_layout(title="Hot Water Psuedo-Simulation",
                          xaxis_title="Hour",
                          yaxis_title="Gallons at Supply Temperature",
                          legend_orientation="h")

        if return_as_div:
            plot_div = plot(fig,  output_type='div', show_link=False, link_text="",
                        include_plotlyjs = False)
            return plot_div
        else:
            return fig


    def plotParallelTankCurve(self, return_as_div = True):
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
        if not self.systemSized:
            raise Exception("System must be sized first")
        if self.inputs.schematic != "paralleltank":
            raise Exception("No parallel tank detected in the system")
        fig = Figure()

        hovertext = 'Storage Volume: %{x:.1f} gallons \nHeating Capacity: %{y:.1f}'

        [x_data, y_data] = self.tempmaintSystem.tempMaintCurve()
        [x_data2, y_data2] = self.tempmaintSystem.tempMaintCurve(2 * self.tempmaintSystem.minimumRunTime)

        fig.add_trace(Scatter(x=x_data, y=y_data,
                              mode='lines', name='Maximum Capacity',
                              hovertemplate = hovertext,
                              opacity=0.8, marker_color='red'))


        fig.add_trace(Scatter(x=(x_data[0],x_data[-1]),
                              y=(self.tempmaintSystem.TMCap_kBTUhr,self.tempmaintSystem.TMCap_kBTUhr),
                              mode='lines', name='Capacity',
                              opacity=0.8, marker_color='grey',
                              fill='tonexty' # fill area between trace0 and trace1
                              ))

        fig.add_trace(Scatter(x=x_data2, y=y_data2,
                              mode='lines', name='Recommended Curve',
                              hovertemplate = hovertext,
                              opacity=0.8, marker_color='green'))


        fig.update_layout(title="Parallel Loop Tank Sizing Curve, with a minimum runtime of %i minutes"% (self.tempmaintSystem.minimumRunTime *60) ,
                          xaxis_title="Parallel Loop Tank Volume (Gallons)",
                          yaxis_title="Parallel Loop Heating Capacity (kBTU/hr)")
        fig.update_xaxes(range=[0, x_data[-1]])
        fig.update_yaxes(range=[0, y_data[-1]])

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
        primaryWriter.writeLine('primaryCurve_heatCap_kBTUhr, ' +np.array2string(pCurve[1], precision = 2, separator=",", max_line_width = 300.))
        if self.tempmaintSystem is not None:
            TMWriter = writeClassAtts(self.tempmaintSystem, fileName, 'a')
            TMWriter.writeLine('\ntemperatureMaintenanceSystem:')
            TMWriter.writeLine('schematic, '+ self.inputs.schematic)
            TMWriter.writeToFile()
            if self.inputs.schematic == "paralleltank":
                TMCurve = self.tempmaintSystem.tempMaintCurve()
                TMWriter.writeLine('TMCurve_vol, ' +np.array2string(TMCurve[0], precision = 2, separator=",", max_line_width = 300.))
                TMWriter.writeLine('TMCurve_heatCap_kBTUhr, ' +np.array2string(TMCurve[1], precision = 2, separator=",", max_line_width = 300.))


##############################################################################
##############################################################################
##############################################################################
class HPWHsizerRead:
    """
    Class for gathering hpwh sizing inputs and checking them. Will gather inputs be manual entry or from a file.


    """
    schematicNames = ["primary", "swingtank", "paralleltank", "trimtank"]

    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""
        self.nBR            = np.zeros(6) # Number of bedrooms 0Br, 1Br...
        self.rBR            = np.zeros(6) # Ratio of people bedrooms 0Br, 1Br...
        self.nPeople        = 0. # Nnumber of people
        self.nApt           = 0. # The number of apartments

        self.gpdpp          = 0. # Gallons per day per person
        self.gpdpp_BR       = np.zeros(6) # Gallons per day per person by bedrooms

        self.loadShapeNorm  = np.zeros(24) # The normalized load shape
        self.supplyT_F      = 0. # The supply temperature to the occupants
        self.incomingT_F    = 0. # The incoming cold water temperature for the city
        self.storageT_F     = 0. # The primary hot water storage temperature
        self.compRuntime_hr = 0. # The runtime?
        self.percentUseable = 0 # The  percent of useable storage

        self.aquaFract      = 0 # The aquatstat fractrion
        self.defrostFactor  = 1. # The defrost factor. Derates the output power for defrost cycles.
        self.totalHWLoad_G  = 0. #Total hot water load to calculated

        self.schematic      = "" # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.Wapt           = 0. # The recirculation loop losses in terms of W/apt

        self.setpointTM_F   = 0. # The setpoint of the temperature maintenance tank.
        self.TMonTemp_F     = 0. # The temperature the temperature maintenance heat pump or resistance element turns on

        self.loadshift      = np.ones(24) # The load shift array

        self.singlePass     = True # Single pass or multipass

    def initPrimaryByUnits(self, nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, defrostFactor, aquastatFract,
                    schematic, singlePass = True):
        self.nBR            = np.array(nBR) # Number of bedrooms 0Br, 1Br...
        self.rBR            = np.array(rBR) # Ratio of people bedrooms 0Br, 1Br...
        self.gpdpp_BR       = np.array(gpdpp_BR) # Gallons per day per person by bedrooms
        self.loadShapeNorm  = np.array(loadShapeNorm) # The normalized load shape
        self.supplyT_F      = supplyT_F # The supply temperature to the occupants
        self.incomingT_F    = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F     = storageT_F # The primary hot water storage temperature
        self.compRuntime_hr = compRuntime_hr # The runtime?
        self.percentUseable = percentUseable #The  percent of useable storage

        self.defrostFactor  = defrostFactor # The defrost factor. Derates the output power for defrost cycles.
        self.aquaFract      = aquastatFract # The aquatstat fractrion

        self.schematic      = schematic # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.singlePass     = singlePass # Single pass or multipass

        self.__checkInputs()
        self.__calcedVariables()

    def initPrimaryByPeople(self, nPeople, nApt, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, defrostFactor, aquastatFract,
                    schematic,  singlePass = True):
        self.nPeople        = nPeople
        self.gpdpp          = gpdpp # Gallons per day per person
        self.loadShapeNorm  = np.array(loadShapeNorm) # The normalized load shape
        self.supplyT_F        = supplyT_F # The supply temperature to the occupants
        self.incomingT_F      = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F       = storageT_F # The primary hot water storage temperature
        self.compRuntime_hr    = compRuntime_hr # The runtime?
        self.percentUseable = percentUseable #The  percent of useable storage

        self.defrostFactor  = defrostFactor # The defrost factor. Derates the output power for defrost cycles.
        self.aquaFract      = aquastatFract # The aquatstat fractrion

        self.schematic      = schematic # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.singlePass     = singlePass # Single pass or multipass

        self.nApt           = nApt

        self.__checkInputs()
        self.__calcedVariables()

    def initTempMaint(self, Wapt, setpointTM_F = 0, TMonTemp_F = 0):
        """
        Assign temperature maintenance variables with either "swingtank" or "paralleltank"
        """
        self.Wapt = Wapt

        if self.schematic == "swingtank":
            pass
        elif self.schematic == "paralleltank":
            if any(x==0 for x in [setpointTM_F,TMonTemp_F]):
                raise Exception("Error in initTempMaint, paralleltank needs inputs != 0")
            else:
                self.setpointTM_F     = setpointTM_F
                self.TMonTemp_F       = TMonTemp_F

    def setLoadShift(self, ls_arr):
        """
        Checks and initilize the load shift variable.

        Args:
            ls_arr (TYPE): array of 0's and 1's or Boolean where 1 or True is .

        Raises:
            Exception: Loadshift input array not on length 24.

        Returns:
            None.

        """
        ls_arr = np.array(ls_arr, dtype = bool) # Coerce to numpy array of data type boolean
        # Check
        if len(ls_arr) != 24 :
            raise Exception("loadshift is not of length 24 but instead has length of "+str(len(self.loadShapeNorm))+".")
        if sum(ls_arr) == 0 :
            raise Exception("When using Load shift the HPWH's must run for at least 1 hour each day.")
        if sum(ls_arr) == 24 :
            raise Exception("If the HPWH's are free to run 24 hours a day, you aren't really loadshifting")
        self.loadshift = np.array(ls_arr, dtype = float)# Coerce to numpy array of data type float


    def __checkInputs(self):
        """Checks inputs are all valid"""
        if sum(self.loadShapeNorm) > 1 + 1e3 or sum(self.loadShapeNorm) < 1 - 1e3:
            raise Exception("Sum of the loadShapeNorm does not equal 1 but "+str(sum(self.loadShapeNorm))+".")
        if self.schematic not in self.schematicNames:
            raise Exception('Invalid input given for the schematic: "'+ self.schematic +'".\n')
        if self.percentUseable > 1 or self.percentUseable < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for percentUseable, it must be between 0 and 1.\n')
        if self.defrostFactor > 1 or self.defrostFactor < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for defrostFactor, it must be between 0 and 1.\n')
        if self.aquaFract > 1 or self.aquaFract < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for aquaFract, it must be between 0 and 1.\n')
        if self.aquaFract < (1-self.percentUseable): # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for aquaFract, it must be greater than (1 - percentUseable) otherwise the aquastat is in the cold part of the storage tank.\n')

        # Check temperature inputs
        if not self.__checkLiqudWater(self.supplyT_F):
            raise Exception('Invalid input given for supplyT_F, it must be between 32 and 212F.\n')
        if not self.__checkLiqudWater(self.incomingT_F):
            raise Exception('Invalid input given for incomingT_F, it must be between 32 and 212F.\n')
        if not self.__checkLiqudWater(self.storageT_F):
            raise Exception('Invalid input given for storageT_F, it must be between 32 and 212F.\n')
        if self.supplyT_F <= self.incomingT_F:
            raise Exception('Invalid input given for supplyT_F, supplyT_F must be greater than incomingT_F\n')
        if self.storageT_F <= self.incomingT_F:
            raise Exception('Invalid input given for storageT_F, storageT_F must be greater than incomingT_F\n')
        if self.storageT_F <= self.supplyT_F:
            raise Exception('Invalid input given for storageT_F, storageT_F must be greater than supplyT_F\n')

    def __checkLiqudWater(self,var_F):
        """
        Checks if the variable has a temperuter with in the range of liquid water at atm pressure

        Args:
            var_F (float): Temperature of water.

        Returns:
            bool: True if liquid, False if solid or gas.

        """
        if var_F < 32 or var_F > 212:
            return False
        else:
            return True

    def __calcedVariables(self):
        """ Calculate other variables needed."""
        if sum(self.nBR + self.nApt) == 0:
            raise Exception("Need input given for number of bedrooms by size or number of apartments")
        if self.nApt == 0:
            self.nApt = sum(self.nBR)
        if self.nPeople == 0:
            self.nPeople = sum(self.nBR * self.rBR)
        if self.gpdpp == 0:
            self.totalHWLoad_G = sum(self.gpdpp_BR * self.nBR * self.rBR)
        else:
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
            elif temp[0] == "gpdpp_br":
                self.gpdpp_br      = float(temp[1])
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

            elif temp[0] == "aquafract":
                temp[1] = float(temp[1])
                if temp[1] > 1: # Check to make sure the percent is stored as anumber 0 to 1.
                    temp[1] = temp[1]/100.
                self.aquaFract = temp[1]

            elif temp[0] == "schematic":
                self.schematic  = temp[1]
            elif temp[0] == "singlepass":
                self.singlePass  = temp[1] in ['true','1','t','y']

            elif temp[0] == "napt":
                self.nApt       = float(temp[1])

            elif temp[0] == "setpointtm_f":
                self.setpointTM_F  = float(temp[1])
            elif temp[0] == "tmontemp_f":
                self.TMonTemp_F   = float(temp[1])
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
