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

import numpy as np

from HPWHComponents import PrimarySystem_SP, ParallelLoopTank, SwingTank, mixVolume # TrimTank, PrimarySystem_MP_NR, PrimarySystem_MP_R
from ashraesizer import ASHRAEsizer
from cfg import compMinimumRunTime, rhoCp, W_TO_BTUHR
from dataFetch import hpwhDataFetch

from plotly.graph_objs import Figure, Scatter
from plotly.offline import plot
from plotly.subplots import make_subplots


##############################################################################
class HPWHsizer:
    """
    The main class to organize a primary and temperature maintenance HPWH system and size it using the Ecotope Modified ASHRAE Method.

    The class uses the initialization functions, initializeFromFile(), initPrimaryByUnits(), and initPrimaryByPeople() to pass the variables
    to a HPWHsizerRead class. The HPWHsizerRead object proccesses the inputs by checking the variables and calculates extra variables. The
    loadshift array is also defined and check with setLoadShiftforPrimary(). The system is sized with the function build_size(), and further
    information is availalbe by pulling the size following the ASHRAE "more accurate" method with getASHRAEResult(). Plots for the sizing curves
    can be pulled from the sized system with plotSizingCurve(). Additionally, a plot simulating the design day can be created with plotPrimaryStorageLoadSim().

    Attributes
    ----------
    validbuild : boolean
        Initialized as false, is true if the system is created susccesfully on a call to buildSystem()

    systemSized : boolean
        Initialized as false, is true if the system is successfully sized.

    doLoadShift : boolean
        Set to true if doing loadshift with a call to setLoadShiftforPrimary()

    inputs : HPWHsizerRead()
        The input handler that checks for valid inputs

    primarySystem : PrimarySystem_SP
        The primary component of the HPWH system of class PrimarySystem_SP

    tempmaintSystem : ParallelLoopTank/SwingTank
        The temperature maintenance component of the HPWH system of class ParallelLoopTank or SwingTank

    ashraeSize : ASHRAEsizer
        The primary component of the HPWH system, which is sized using the ASHRAE method of class ASHRAEsizer

    swingTankLoad_W : float
        The fraction of the distrubution losses that the primary HPWH has to cover when using a swing tank schematic.

    Methods
    -------
    initializeFromFile(fileName)
        Function to initialize a HPWHsystem from a file.

    initPrimaryByUnits(nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, aquaFract,
                    schematic, defrostFactor=1, singlePass=True)
        Function to initialize the primary component of a HPWH system from the list of inputs using a list of the number of apartments and a ratio of people per apartment. This is what users should use to align with CA Title24, see example 2.


    initPrimaryByPeople(nPeople, nApt, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor = 1, singlePass=True)
        Function to initialize the primary component of a HPWH system from the list of inputs using the full number of people and apartments.

    initTempMaint( Wapt, setpointTM_F = 135, TMonTemp_F = 0 )
        Function to initialize the temperature maintenence component of a HPWH system from the list of inputs.

    setLoadShiftforPrimary(ls_arr)
        Adds a specified load shifting scenario to the HPWH system.

    buildSystem()
        Organizes the HPWH system inputs around the schematic to put together the primary and temperature maintenance system

    sizeSystem()
        Sizes the built HPWH system and returns the minimum sizing results, volume and capacity for the primary and temperature maintence systems

    build_size()
         Builds and sizes the system.

    getASHRAEResult()
         Returns just the minimum result for the primary component of the HPWH system from the sized system following the "more accurate" method from ASHRAE

    plotSizingCurve( return_as_div = True)
         Returns the primary sizing curve, storage volume vs. heating capacity for the

    plotPrimaryStorageLoadSim(return_as_div = True)
         Runs and returns a plot for the primary system simulating storage volume with HPWH heating agains the design load shape

    writeToFile(fileName)
        Writes the results of sizing the primary and temperature maintenance systems to a file.

    Examples
    --------
    Example 1:
    An example usage to find the recommended size is:

    To inialize the system:

    >>> from HPWHsizer import HPWHsizer
    >>> hpwh = HPWHsizer()
    >>> hpwh.initPrimaryByPeople(nPeople = 100,
                                 nApt = 36,
                                 gpdpp = 22.,
                                 loadShapeNorm = "stream",
                                 supplyT_F = 120,
                                 incomingT_F = 50,
                                 storageT_F = 150.,
                                 compRuntime_hr = 16.,
                                 percentUseable = .9,
                                 aquaFract = 0.4,
                                 schematic = "paralleltank")
    >>> hpwh.initTempMaint(Wapt = 100,
                           setpointTM_F = 135,
                           TMonTemp_F = 125)

    And then in order to find proper for the system in the order of primary storage volume, primary heating capacity, temperature maintenance storage volume, temperature maintenance heating capacity:

    >>> hpwh.build_size()
    [346.1021666666667, 114.86110625, 48.15823981105004, 32.244741899999994]

    To get the primary sizing curve to find solutions for the primary system at higher heating capacities and lower storage:

    >>> fig = hpwh.plotSizingCurve(return_as_div=False)
    >>> fig.show()

    And to see the how the system performs in a simple simulation:

    >>> fig = hpwh.plotPrimaryStorageLoadSim(return_as_div=False)
    >>> fig.show()

    Plotly figures can also be saved as html with write_html():

    >>> fig.write_html("output.html")


    Example 2:

    If a user wants to align their sizing with the CA Title24 software use the initPrimaryByUnits() function follow:

    >>> from HPWHsizer import HPWHsizer
    >>> hpwh = HPWHsizer()
    >>> hpwh.initPrimaryByUnits(nBR = [6,12,12,6,0,0],
                                rBR = "CA",
                                gpdpp_BR = "CA",
                                loadShapeNorm = "stream",
                                supplyT_F = 125,
                                incomingT_F = 50,
                                storageT_F= 150.,
                                compRuntime_hr = 16.,
                                percentUseable = .8,
                                aquaFract = 0.4,
                                schematic = "swingtank")

    Which will use the California occupancy ratios and the California daily hot water draws. Then create the temperature maintenance load with:

    >>> hpwh.initTempMaint( Wapt = 100 )

    Construct the system by building the connections between the components and size it. To find proper sizing for the system in the order of primary storage volume, primary heating capacity, temperature maintenance storage volume, temperature maintenance heating capacity:

    >>> hpwh.build_size()
    [275.08088575585305, 87.32317975282498, '80', 21.4964946]

    To get the primary sizing curve to find solutions for the primary system at higher heating capacities and lower storage:

    >>> fig = hpwh.plotSizingCurve(return_as_div=False)
    >>> fig.show()

    Unfortunately the simulation of the primary system is yet built out for the swing tank.

    """
    def __init__(self):
        
        print( " HPWHulator Copyright (C) 2020  Ecotope Inc. ")
        print("This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are welcome to redistribute under certain conditions; details check GNU AFFERO GENERAL PUBLIC LICENSE_08102020.docx.")

        self.validbuild     = False
        self.systemSized    = False
        self.doLoadShift    = False
        self.inputs = HPWHsizerRead()

        self.primarySystem = None
        self.tempmaintSystem = None
        self.ashraeSize = None

        self.swingTankLoad_W = 0.
		
		


    def initializeFromFile(self, fileName):
        """
        Initilizes a system from a file

        Attributes
        ----------
        fileName : str
            Name of file to open. File should have lines for each variable with format: \
                <name of variable> <value> i.e. compRuntime_hr 16, or for list: nBR 10 10 10 0 0
        """
        self.inputs.initializeFromFile(fileName)

    def initPrimaryByUnits(self, nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, aquaFract,
                    schematic, defrostFactor = 1, singlePass=True):
        """
        Initializes the primary system by the number of units by number of bedrooms and number of people per unit.
        If aligning the sizing requriements with CA this is the method that should be used.

        Attributes
        ----------
        nBR : array_like
            A list of the number of units by size in the order 0 bedroom units, 1 bedroom units, 2 bedroom units, 3 bedroom units, 4 bedroom units, 5 bedroom units.
        rBR : array_like
            A list of the average number people in each unit by size in the order 0 bedroom units, 1 bedroom units, 2 bedroom units, 3 bedroom units, 4 bedroom units, 5 bedroom units.
        gpdpp_BR : array_like
            A list of the design gallons used per unit by each unit by size in the order 0 bedroom units, 1 bedroom units, 2 bedroom units, 3 bedroom units, 4 bedroom units, 5 bedroom units. .
        loadShapeNorm : array_like or str
            A one dimensional array with length 24 that describes the hot water usage for each hour of the day as a fraction of the total daily load. If string will lookup the loadshape data
        incomingT_F : float
            Incoming city water temperature (design temperature in winter). [°F]
        storageT_F: float
            Storage temperature of the primary hot water storage tanks. [°F]
        supplyT_F : float
            Supply hot water temperature to occupants, typically 120°F. [°F]
        percentUsable : float
            Percent of primary hot water storage that is usable due to sufficient thermal stratification.
        compRuntime_hr : float
            Hour per day central heat pump equipment can run, duty cycle [hrs/day]
        percentUseable : float
            Percent of primary hot water storage that is usable due to sufficient thermal stratification.
        aquaFract  : float
            The fraction of the total hieght of the primary hot water tanks at which the Aquastat is located.
        schematic  : float
            The schematic used, options are "primary", "paralleltank", or "swingtank"
        defrostFactor: float
            A factor that reduces heating capacity at low temperatures based on need for defrost cycles to remove ice from evaporator coils. Defaults to 1.
        singlePass  : float
            Whether sizing a single pass or multipass system. There is no support for multipass primary sytems right now. Defaults to True.

        """
        self.inputs.initPrimaryByUnits(nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, aquaFract,
                     schematic, defrostFactor, singlePass)

    def initPrimaryByPeople(self,  nPeople, nApt,  gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor = 1, singlePass=True):
        """
        Initializes the primary system by the number of total units and number of total people

        Attributes
        ----------
        nPeople : flaot
            The estimated total number of people that will occupy the building
        nApt : flaot
            The total number of apartment units in the project
        gpdpp : flaot
            The design gallons per day per person at  120°F, or can be given as a string key to lookup values from ASHRAE low or medium or Ecotope design value
        loadShapeNorm : array_like or str
            A one dimensional array with length 24 that describes the hot water usage for each hour of the day as a fraction of the total daily load. If string will lookup the loadshape data
        incomingT_F : float
            Incoming city water temperature (design temperature in winter). [°F]
        storageT_F: float
            Storage temperature of the primary hot water storage tanks. [°F]
        supplyT_F : float
            Supply hot water temperature to occupants, typically 120°F. [°F]
        percentUsable : float
            Percent of primary hot water storage that is usable due to sufficient thermal stratification.
        compRuntime_hr : float
            Hour per day central heat pump equipment can run, duty cycle [hrs/day]
        percentUseable : float
            Percent of primary hot water storage that is usable due to sufficient thermal stratification.
        defrostFactor : float
            A factor that reduces heating capacity at low temperatures based on need for defrost cycles to remove ice from evaporator coils.
        aquaFract  : float
            The fraction of the total hieght of the primary hot water tanks at which the Aquastat is located.
        schematic  : float
            The schematic used, options are "primary", "paralleltank", or "swingtank"
        defrostFactor: float
            A factor that reduces heating capacity at low temperatures based on need for defrost cycles to remove ice from evaporator coils. Defaults to 1.
        singlePass  : float
            Whether sizing a single pass or multipass system. There is no support for multipass primary sytems right now. Defaults to True.
        """
        self.inputs.initPrimaryByPeople(nPeople, nApt, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable, aquaFract,
                    schematic, defrostFactor, singlePass )

    def initTempMaint(self, Wapt, setpointTM_F = 130, TMonTemp_F = 120, offTime_hr = 0.333, TMRuntime_hr = 0.333 ):
    #def initTempMaint(self, Wapt, setpointTM_F = 135, TMonTemp_F = 0 ):
        """

        Initializes the temperature maintanence system after the primary system
        with either "swingtank" or "paralleltank". Recommend to leave offtime_hr
        and TMRuntime_hr as defaulted, since they're setup for a minimum runtime of
        10 minutes at the lower end of the design criteria for loop losses.

        Attributes
        ----------
            Wapt : float
                The recicuplation loop losses in terms of Watts per apartment.
            setpointTM_F : float
                The setpoint of the temprature maintence tank. Defaults to 130 °F.
            TMonTemp_F :float
                The temperature where parallel loop tank will turn on. Defaults to 120 °F.

        Raises
        ----------
            Exception: Error if primary system hasn't been sized yet.

        """
        if self.inputs.totalHWLoad_G is None or self.inputs.totalHWLoad_G == 0:
            raise Exception("must initialize the primary system first")

        if self.inputs.schematic == "swingtank" or self.inputs.schematic == "paralleltank":
            if TMonTemp_F == 0:
                TMonTemp_F = self.inputs.supplyT_F + 2;
            #self.inputs.initTempMaintInputs(Wapt, setpointTM_F, TMonTemp_F)
            self.inputs.initTempMaintInputs(Wapt, setpointTM_F, TMonTemp_F, offTime_hr, TMRuntime_hr)


    def setLoadShiftforPrimary(self, ls_arr, cdf_shift=1):
        """
        Sets the load shift to user defined list of 0s of false for force HPWH not to run, and 1s or true for run.


        Attributes
        ----------
        ls_arr : array_like
            Array of zeros and ones of length 24 for each hour of the day to define when HPWH's are allowed to run during a day for load shift.

        """
        self.inputs.setLoadShift(ls_arr, cdf_shift)
        self.doLoadShift    = True

    def buildSystem(self):
        """
        Builds a single pass centralized HPWH plant. Organizes the inputs to the relevant classes and passes important constants between the classes.

        Raises
        ----------
            Exception: If schematic is trim tank throws erros
            Exception: If am invalid schematic string is passed here throws error
            Exception: If trying to use multipass heat pumps for the primary system throws erros
            Exception: If the system does not build correctly.


        """

        self.validbuild = False

        self.ashraeSize = ASHRAEsizer(self.inputs.nPeople,
                                        self.inputs.gpdpp,
                                        self.inputs.incomingT_F,
                                        self.inputs.supplyT_F,
                                        self.inputs.storageT_F,
                                        self.inputs.percentUseable,
                                        self.inputs.compRuntime_hr,
                                        self.inputs.defrostFactor)

        if self.inputs.schematic == "primary":
            pass
        elif self.inputs.schematic == "paralleltank":
            self.tempmaintSystem = ParallelLoopTank(self.inputs.nApt,
                                     self.inputs.Wapt,
                                     self.inputs.setpointTM_F,
                                     self.inputs.TMonTemp_F,
                                     self.inputs.offTime_hr,
                                     self.inputs.TMRuntime_hr)
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
                                                 self.inputs.percentUseable,
                                                 self.inputs.compRuntime_hr,
                                                 self.inputs.aquaFract,
                                                 self.inputs.defrostFactor,
                                                 self.swingTankLoad_W)
            if self.doLoadShift:
                self.primarySystem.setLoadShift(self.inputs.loadshift, self.inputs.cdf_shift)

        elif not self.inputs.singlePass:
            # Multipass systems not yet supported
            raise Exception("Multipass is yet supported")


        if self.primarySystem is not None:
            self.validbuild = True
        else:
            raise Exception ("The HPWH system did not build properly")

    def sizeSystem(self):
        """
        Sizes the system after building with buildSystem()

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
            [PVol_G_atStorageT, PCap_kBTUhr, TMVol_G, TMCap_kBTUhr]
        """
        self.buildSystem()
        return self.sizeSystem()

    def getASHRAEResult(self):
        """
        Gets the results from the system using the "more accurate method" from ASHRAE after building the system.

        Returns
        -------
        list
            [PVol_G_atStorageT, PCap_kBTUhr]
        """

        if self.validbuild:
            return self.ashraeSize.sizeVol_Cap()
        else:
            raise Exception("The system can not be sized without a valid build")

    def plotSizingCurve(self, return_as_div = True):
        """
        Returns a plot of the sizing curve as a div or as a plotly fig

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

        # [x_ash, y_ash] = self.ashraeSize.primaryCurve()
        # fig.add_trace(Scatter(x=x_ash[:-1], y=y_ash[:-1], #Drops the last point
        #                       mode='lines', name='ASHRAE Sizing Curve',
        #                       hovertemplate = hovertext,
        #                       opacity=0.8, marker_color='red'))

        # [xlow, ylow] = self.ashraeSize.getLowCurve()
        # fig.add_trace(Scatter(x=xlow[:-1], y=ylow[:-1], #Drops the last point
        #               mode='lines',   opacity=0.4,  marker_color='crimson',
        #               hovertemplate = hovertext,
        #               name='ASHRAE Low Curve' ))

        [x_data, y_data] = self.primarySystem.primaryCurve()
        fig.add_trace(Scatter(x=x_data, y=y_data,
                              mode='lines', name='Primary Sizing Curve',
                              hovertemplate = hovertext,
                              opacity=0.8, marker_color='green'))

        # fig.add_trace(Scatter(x=(0,max(x_data[-1],x_data[-2], x_data[0])),
        #                       y=(self.primarySystem.PCap_kBTUhr,self.primarySystem.PCap_kBTUhr),
        #                       mode='lines', name='Recommended Minimum Size',
        #                       opacity=0.8, marker_color='grey'))

        fig.add_trace(Scatter(x=[self.primarySystem.PVol_G_atStorageT],
                              y=[self.primarySystem.PCap_kBTUhr],
                              mode='markers', marker_symbol="diamond",marker_size=10,
                              name='Recommended Size',
                              opacity=0.8, marker_color='blue'))

        fig.update_layout(title="Primary Sizing Curve",
                          xaxis_title="Primary Tank Volume (Gallons) at Storage Temperature",
                          yaxis_title="Primary Heating Capacity (kBTU/hr)")

        if return_as_div:
            plot_div = plot(fig,  output_type='div', show_link=False, link_text="",
                        include_plotlyjs = False)
            return plot_div
        else:
            return fig

    def plotPrimaryStorageLoadSim(self, return_as_div = True):
        """
        Returns a plot of the of the simulation for the minimum sized primary system as a div or plotly figure. Can plot the minute level simulation

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

        
        [ V, G_hw, D_hw, run, swingT, srun ] = self.runStorage_Load_Sim();
        
        hrind_fromback = 24 # Look at the last 24 hours of the simulation not the whole thing
        run = np.array(run[-(60*hrind_fromback):])*60
        G_hw = np.array(G_hw[-(60*hrind_fromback):])*60
        D_hw = np.array(D_hw[-(60*hrind_fromback):])*60
        V = np.array(V[-(60*hrind_fromback):])

        if swingT:
            fig = make_subplots(rows=2, cols=1,
                                specs=[[{"secondary_y": False}],
                                        [{"secondary_y": True}]])
        else:
            fig = Figure()

            
        # Do primary components
        x_data = list(range(len(V)))
        
        if self.doLoadShift:
            ls_off = [ int(not x)* max(V)*2 for x in G_hw] 
            fig.add_trace(Scatter(x=x_data, y=ls_off, name='Load Shift Off Period',
                                  mode = 'lines', line_shape='hv',
                                  opacity=0.5, marker_color='grey',
                                  fill='tonexty'))
        
        fig.add_trace(Scatter(x=x_data, y=V, name='Useful Storage Volume at Storage Temperature',
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='green'))
        fig.add_trace(Scatter(x=x_data, y=run, name = "Hot Water Generation at Storage Temperature",
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='red'))
        fig.add_trace(Scatter(x=x_data, y=D_hw, name='Hot Water Demand at Supply Temperature',
                              mode = 'lines', line_shape='hv',
                              opacity=0.8, marker_color='blue'))
        fig.update_yaxes(range=[0, np.ceil(max(V)/100)*100])

        fig.update_layout(title="Hot Water Simulation",
                          xaxis_title= "Minute of Day",
                          yaxis_title="Gallons or\nGallons per Hour",
                          width=900,
                          height=700)
                          
        # Do Swing Tank components:
        if swingT:
            swingT = np.array(swingT[-(60*hrind_fromback):])
            srun = np.array(srun[-(60*hrind_fromback):]) * self.tempmaintSystem.TMCap_kBTUhr/W_TO_BTUHR #srun is logical so convert to kW
            
            # heatin_kWh = sum(srun)/60*self.tempmaintSystem.TMCap_kBTUhr/W_TO_BTUHR 
            # recircLoss = self.tempmaintSystem.Wapt*self.tempmaintSystem.nApt/1000 * 48
            
            # strname = "Swing Temp,\nEnergy in Swing: " + str(round(heatin_kWh)) + \
            #     "\nRecircL: " + str(round(recircLoss)) + "\nRatio: " + str(round(heatin_kWh/recircLoss*100)) + \
            #         "\n Comp Run Time: " +str(round(np.count_nonzero(run)/60/2,2))
            
            fig.add_trace(Scatter(x=x_data, y=swingT, 
                                  name= 'Swing Tank Temperature',
                                  mode = 'lines', line_shape='hv',
                                  opacity=0.8, marker_color='purple',yaxis="y2"), 
                          row=2,col=1,
                         secondary_y=False )
            
            fig.add_trace(Scatter(x=x_data, y=srun, 
                                  name= 'Swing Tank Resistance Element',
                                  mode = 'lines', line_shape='hv',
                                  opacity=0.8, marker_color='goldenrod'), 
                         row=2,col=1,
                         secondary_y=True)

            fig.update_yaxes(title_text="Swing Tank\nTemperature (\N{DEGREE SIGN}F)", 
                             showgrid=False, row=2, col=1,
                             secondary_y=False, range=[self.inputs.supplyT_F-5, self.inputs.storageT_F])

            fig.update_yaxes(title_text="Resistance Element\nOutput (kW)", 
                             showgrid=False, row=2, col=1,
                             secondary_y=True, range=[0,np.ceil(max(srun)/10)*10])

            
        if return_as_div:
            plot_div = plot(fig,  output_type='div', show_link=False, link_text="",
                        include_plotlyjs = False)
            return plot_div
        else:
            return fig


    def plotParallelTankCurve(self, return_as_div = True):
        """
        Returns a plot of the sizing curve as a div or a plotly figure

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

        fig.add_trace(Scatter(x=[self.tempmaintSystem.TMVol_G],
                              y=[self.tempmaintSystem.TMCap_kBTUhr],
                              mode='markers', marker_symbol="diamond",marker_size=10,
                              name='System Size',
                              opacity=0.8, marker_color='blue'))

        fig.update_layout(title="Parallel Loop Tank Sizing Curve, with a minimum runtime of %i minutes"% (compMinimumRunTime*60),
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

    def runStorage_Load_Sim(self, Pcapacity = None, Pvolume = None):
        """
        Returns sizing storage depletion and load results for water volumes at the supply temperature

        Parameters
        ----------
        Pcapacity (float) : The primary heating capacity in kBTUhr to use for the simulation, default is the sized system
        Pvolume (float) : The primary storage volume in gallons to  to use for the simulation, default is the sized system

        Returns
        -------
        list [ V, G_hw, D_hw, run ]
        V - Volume of HW in the tank with time at the strorage temperature. 
        G_hw - The generation of HW with time at the supply temperature
        D_hw - The hot water demand with time at the tsupply temperature
        run - The actual output in gallons of the HPWH with time
        """
        if not Pcapacity:
            if self.primarySystem.PCap_kBTUhr:
                Pcapacity =  self.primarySystem.PCap_kBTUhr
            else:
                raise Exception("The system hasn't been sized yet! Either specify capacity AND volume or size the system.")

        if not Pvolume:
            if self.primarySystem.PVol_G_atStorageT:
                Pvolume =  self.primarySystem.PVol_G_atStorageT
            else:
                raise Exception("The system hasn't been sized yet! Either specify capacity AND volume or size the system.")
            

        # Get the generation rate from the primary capacity
        G_hw = 1000 * Pcapacity / rhoCp / (self.primarySystem.supplyT_F - self.primarySystem.incomingT_F) \
               * self.primarySystem.defrostFactor * np.tile(self.primarySystem.LS_on_off,3)
               
        # Define the use of DHW with the normalized load shape
        D_hw = self.primarySystem.totalHWLoad * np.tile(self.primarySystem.loadShapeNorm,3)

        G_hw = np.array(HRLIST_to_MINLIST(G_hw)) / 60
        D_hw = np.array(HRLIST_to_MINLIST(D_hw)) / 60

        # Init the "simulation"
        V0 = Pvolume* self.primarySystem.percentUseable
        Vtrig = Pvolume* (1 - self.primarySystem.aquaFract)
        
        if self.inputs.schematic == "swingtank" : 
            hpwhsim = Simulator(G_hw, D_hw, V0, Vtrig,                                
                                Tcw = self.primarySystem.incomingT_F,
                                Tstorage = self.primarySystem.storageT_F,
                                Tsupply = self.primarySystem.supplyT_F,
                                schematic = self.inputs.schematic,
                                swing_V0 = int(self.tempmaintSystem.TMVol_G.split()[0]),
                                swing_Ttrig = self.primarySystem.supplyT_F,
                                Qrecirc_W = self.tempmaintSystem.Wapt*self.tempmaintSystem.nApt,
                                Swing_Elem_kW = self.tempmaintSystem.TMCap_kBTUhr/W_TO_BTUHR )

        else:
           # hpwhsim = Simulator(G_hw, D_hw, V0, Vtrig) 
           hpwhsim = Simulator(G_hw, D_hw, V0, Vtrig,
                               Tcw = self.primarySystem.incomingT_F,
                               Tstorage = self.primarySystem.storageT_F,
                               Tsupply = self.primarySystem.supplyT_F)

        return hpwhsim.simulate()

###############################################################################
class Simulator:
    """
    Simulator class to check the primary and swing tank systems.
    The Simulator class to run a simple simulation .

    This class will run the primary simulation (schematic = "primary") or primary with swing tank simulation (schematic = "swingtank"). Both are run
    on a minute timestep to approximate the available storage volume in the primary system
    and the average tank temperature in the swing tank, if applicable. 
    
    The primary system is run assuming the system is perfectly stratified and all of the hot water above the
    cold temperature line is at the storage temperature. Each time step some hot water is removed 
    and some added according to the inputs.
    
    The swing tank is run assuming that the swing tank is well mixed and can be tracked by the average tank temperature 
    and that the system loses the recirculation loop losses as a constant Watts. 
    Since the swing tank is in series with the primary system the temperature needs
    to be tracked to inform inputs for primary step, unlike the parallel loop tank
    which is seperated from the primary system.
    
    The swing tank is also assumed to have an 8 °F deadband from the swing heating trigger temperature.
    
    
    Examples
    --------
    An example usage to simulate a swing tank system:

    First make sure the hot water draws are in gpm. For examples starting with gph for each hour of the day, 
    a list can be converted to gpm for each minute oof the day following:
        
    
    >>> D_hw_gph = [ 27, 12, 8, 8, 24, 40, 74, 87, 82, 67, 40, 34, 29, 27, 
                    29, 34, 40, 48, 51, 55, 59, 51, 38, 36]
    
    >>> D_hw_gpm = np.array(HRLIST_to_MINLIST(D_hw_gph)) / 60
    
    
    Then the simulator can be imported and initilized, with the desired inputs.
    
    
    >>> from HPWHsizer import Simulator
    >>> hpwhsim = Simulator(G_hw = [64]*24*60,
                            D_hw = D_hw_gpm,
                            V0 = 300,
                            Vtrig = 180,     
                            Tcw = 50,
                            Tstorage = 150,
                            Tsupply = 120,
                            schematic = "swingtank",
                            swing_V0 = 80,
                            swing_Ttrig = 121,
                            Qrecirc_W = 2700,
                            Swing_Elem_kW = 5 )

    And then in order to find proper for the system in the order of primary storage volume, primary heating capacity, temperature maintenance storage volume, temperature maintenance heating capacity:

    >>> primaryVol, G_hw, D_hw, primaryGen, swingTemp, swingHeat = hpwhsim.simulate()

    
    """
    pheating = False
    swingheating = False

    def __init__(self, G_hw, D_hw, V0, Vtrig, 
                 Tcw, Tstorage, Tsupply,
                 schematic = "primary",
                 swing_V0 = None,
                 swing_Ttrig = None,
                 Qrecirc_W = None,
                 Swing_Elem_kW = None,
                 ):
        """
        Initialize the simulation to run. Default is the "primary" schematic.
        Parameters
        ----------
        G_hw : list
            The primary hot water generation rate in gallons per minute .
            
        D_hw : list
            The hot water draw rate at the supply temperature.
            
        V0 : float
            The storage volume of the primary system at the storage temperature
            
        Vtrig : float
            The remaining volume of the primary storage volume when heating is triggered, note this equals V0*(1 - aquaFract)
            
        Tcw : float
            The cold makeup water temperature
            
        Tstorage : float
            The hot water storage temperature 
            
        Tsupply : float
            The hot water supply temperature to occupants.
            
        schematic : string
            The schematic string, either "primary", "paralleltank", or "swingtank". Controls the model run. Defaults to "primary".
            
        swing_V0 : float
            The storage volume of the swing tank. Is not need unless schematic is set to "swingtank". Defaults to None.
            
        swing_Ttrig : float
            The swing tank tempeature when the swing tank resistance elements turn on. Is not need unless schematic is set to "swingtank". Defaults to None.

        Qrecirc_W : float
            The recirculation loop losses in Watts. Is not need unless schematic is set to "swingtank". Defaults to None.

        Swing_Elem_kW : float
            The swing tank resistance elements power output in kWatts. Is not need unless schematic is set to "swingtank". Defaults to None.
    
        """

        self.__checkInputs(G_hw, D_hw, V0, Vtrig)
        
        self.Tsupply = Tsupply
        self.Tcw = Tcw
        self.Tstorage = Tstorage
            
        self.N = len(G_hw)
        self.G_hw = G_hw
        self.D_hw = D_hw
        self.prun = [0] * (self.N)

        self.V0 = V0
        self.pV = [V0] + [0] * (self.N - 1)
        self.Vtrig = Vtrig # For the primary system
      
        self.schematic = schematic

        self.swingT = None
        self.srun = None
        
        # If swing tank gather all of the swing tank inputs.
        if self.schematic == "swingtank":
            self.swing_V0 = swing_V0
            self.swing_Ttrig = swing_Ttrig

            self.recircLoss_dT = Qrecirc_W * W_TO_BTUHR / 60 / rhoCp / self.swing_V0  #1/60 to get timestep of 1 minute
            self.element_dT = Swing_Elem_kW * 1000 * W_TO_BTUHR / 60 / rhoCp / self.swing_V0  #1/60 to get timestep of 1 minute
            self.element_deadband_F = 8.
            
            self.swingT = [self.Tstorage] + [0] * (self.N - 1)
            self.srun = [0] * (self.N)
                                    
        
    def __checkInputs(self, G_hw, D_hw, V0, Vtrig):
        if len(G_hw) != len(D_hw):
            raise Exception( "Hot water generation and domestic hot water use must have the same length, i.e. time")
        if V0 <= Vtrig:
            raise Exception( "The initial storage volume can't be greater than the volume to trigger heating.")

    def simulate(self):
        # Run the "simulation"
        for ii in range(1,self.N):
            
            if self.schematic == "swingtank":
                hw_outSwing = mixVolume(self.D_hw[ii], self.swingT[ii-1], self.Tcw, self.Tsupply)

                self.swingT[ii], self.srun[ii] = self.runOneSwingStep(self.swingT[ii-1], hw_outSwing)
                
                mixedGHW = mixVolume(self.G_hw[ii], self.Tstorage, self.Tcw, self.Tsupply)
                #mixedGHW = self.G_hw[ii]
                self.pV[ii], self.prun[ii] = self.runOnePrimaryStep(self.pV[ii-1], hw_outSwing, mixedGHW )
                
            elif self.schematic == "primary" or self.schematic == "paralleltank":
                mixedDHW = mixVolume(self.D_hw[ii], self.Tstorage, self.Tcw, self.Tsupply)
                mixedGHW = mixVolume(self.G_hw[ii], self.Tstorage, self.Tcw, self.Tsupply)
                self.pV[ii], self.prun[ii] = self.runOnePrimaryStep(self.pV[ii-1], mixedDHW, mixedGHW)
       
            else:
                raise Exception(self.schematic + " is not a valid schematic")
                
        return [roundList(self.pV,3),
                roundList(self.G_hw,3),
                roundList(self.D_hw,3),
                roundList(self.prun,3),
                roundList(self.swingT,3) if self.swingT else None,
                roundList(self.srun,3) if self.srun else None ]


    def runOnePrimaryStep(self, Vcurr, hw_out, hw_in):
        """
        Runs one step on the primary system. This changes the volume of the primary system
        by assuming there is hot water removed at a volume of hw_out and hot water
        generated or added at a volume of hw_in. This is assuming the system is perfectly
        stratified and all of the hot water above the cold temperature is at the storage temperature. 

        Parameters
        ----------
        Vcurr (float) : The primary volume at the timestep.
        hw_out (float) : The volume of DHW removed from the primary system, assumed that 100% of what of what is removed is replaced 
        hw_in (float) : The volume of hot water generated in a time step
        
        Returns
        -------
        Vnew (float) : The new primary volume at the timestep.
        did_run (float) : The volume of hot water generated during the time step. 
        
        """
        did_run = 0
        Vnew = 0
        if self.pheating:
                Vnew = Vcurr + hw_in - hw_out # If heating, generate HW and lose HW
                did_run = hw_in

        else:  # Else not heating,
            Vnew = Vcurr - hw_out # So lose HW
            if Vnew < self.Vtrig: # If should heat
                time_missed = (self.Vtrig - Vnew)/hw_out#Volume below turn on / rate of draw gives time below tigger
                Vnew += hw_in * time_missed # Start heating
                did_run = hw_in*time_missed
                self.pheating = True

        if Vnew > self.V0: # If overflow
            time_over = (Vnew - self.V0) / (hw_in - hw_out) # Volume over generated / rate of generation gives time above full
            Vnew = self.V0 - hw_out * time_over # Make full with miss volume
            did_run = hw_in * (1-time_over)
            self.pheating = False # Stop heating
        
        # if Vnew < 0:
        #     raise Exception ( "Primary storage ran out of Volume!")
        
        return Vnew, did_run

    def runOneSwingStep(self, Tcurr, hw_out):
        """
        Runs one step on the swing tank step. Since the swing tank is in series with the primary system
        the temperature needs to be tracked to inform inputs for primary step. The driving assumptions here
        are that the swing tank is well mixed and can be tracked by the average tank temperature 
        and that the system loses the recirculation loop losses as a constant Watts and thus the 
        actual flow rate and return temperature from the loop do not matter. 
        
        Parameters
        ----------
        Tcurr (float) : The current temperature at the timestep.
        hw_out (float) : The volume of DHW removed from the swing tank system.
        hw_in (float) : The volume of DHW added to the system.
        
        Returns
        -------
        Tnew (float) : The new swing tank tempeature the timestep assuming the tank is well mixed.
        did_run (float) : Logic if heated during time step (1) or not (0) 
        
        """
        did_run = 0
        
        # Take out the recirc losses 
        Tnew = Tcurr - self.recircLoss_dT

        # Add in heat for a draw
        if hw_out:
            Tnew += hw_out * (self.Tstorage - Tcurr) / self.swing_V0
       
        # Check if the element is heating
        if self.swingheating:
            Tnew += self.element_dT #If heating, generate HW and lose HW
            did_run = 1
            
            # Check if the should be off
            if Tnew >= self.swing_Ttrig + self.element_deadband_F: # If should heat
                self.swingheating = False

        if Tnew <= self.swing_Ttrig: # If the element should turn on
            self.swingheating = True # Stop heating
            
       # if Tnew < self.Tsupply: # Check for errors
        #    raise Exception("The swing tank dropped below the supply temperature! The system is undersized")
        
        #print(Tnew, Tcurr, hw_out, hw_outSwing, hw_outSwing * (self.Tstorage - Tcurr),self.swing_Ttrig, self.swingheating, did_run )

        return Tnew, did_run 


##############################################################################
##############################################################################
##############################################################################
class HPWHsizerRead:
    """
    Class for gathering hpwh sizing inputs and checking them. Will gather inputs by manual entry or from a file. A pulls data from string inputs.


    """
    schematicNames = ["primary", "swingtank", "paralleltank"]
    hpwhData = hpwhDataFetch()

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

        self.offTime_hr         = 0.
        self.TMRuntime_hr       = 0.

        self.loadshift      = np.ones(24) # The load shift array

        self.singlePass     = True # Single pass or multipass

    def initPrimaryByUnits(self, nBR, rBR, gpdpp_BR, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor, singlePass = True):

        self.nBR            = np.array(nBR) # Number of bedrooms 0Br, 1Br...
        # Calc the number of apartments
        nApt = sum(self.nBR)


        # Check if rBR is a string input
        if type(rBR) is str: # if the input here is a string get the loadshape.
            self.rBR = self.hpwhData.getRPepperBR(rBR)
        else:
            self.rBR = np.array(rBR) # Ratio of people bedrooms 0Br, 1Br...
        #Now get the number of people
        nPeople = sum(self.nBR * self.rBR)


        # Check if gpdpp_BR is a string input and get the gpdpp
        if type(gpdpp_BR) is str: # if the input here is a string get the loadshape.
            self.gpdpp_BR = loadgpdpp(gpdpp_BR, self.nBR)
            gpdpp = self.gpdpp_BR
        else:
           self.gpdpp_BR = np.array(gpdpp_BR) # Gallons per day per person by bedrooms
           gpdpp = sum(self.gpdpp_BR * self.nBR * self.rBR) / nPeople


        self.initPrimaryByPeople(nPeople, nApt, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor, singlePass)


    def initPrimaryByPeople(self, nPeople, nApt, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor, singlePass = True):

        loadShapeNorm = np.array(loadShapeNorm)
        # loadShapeNorm have been coeerced to np.arrays so check these for string inputs
        if loadShapeNorm.dtype.type is np.str_: # if the input here is a any string get the loadshape.
            loadShapeNorm = self.hpwhData.getLoadshape()

        gpdpp =  loadgpdpp(gpdpp)

        self.checkInputs(gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor, singlePass)

        self.nPeople        = nPeople
        self.gpdpp          = gpdpp # Gallons per day per person

        self.loadShapeNorm  = loadShapeNorm # The normalized load shape
        self.supplyT_F        = supplyT_F # The supply temperature to the occupants
        self.incomingT_F      = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F       = storageT_F # The primary hot water storage temperature
        self.compRuntime_hr    = compRuntime_hr # The runtime?
        self.percentUseable = percentUseable #The  percent of useable storage

        self.defrostFactor  = defrostFactor # The defrost factor. Derates the output power for defrost cycles.
        self.aquaFract      = aquaFract # The aquatstat fractrion

        self.schematic      = schematic # The schematic for sizing maybe just primary maybe with temperature maintenance.
        self.singlePass     = singlePass # Single pass or multipass

        self.nApt           = nApt

        self.calcedVariables()

    def initTempMaintInputs(self, Wapt, setpointTM_F = 0, TMonTemp_F = 0, offTime_hr = 0, TMRuntime_hr = 0):
        """
        Assign temperature maintenance variables with either "swingtank" or "paralleltank"
        """
        self.Wapt = Wapt

        if self.schematic == "swingtank":
            pass
        elif self.schematic == "paralleltank":
            if any(x==0 for x in [setpointTM_F,TMonTemp_F]):
                raise Exception("Error in initTempMaintInputs, paralleltank needs inputs != 0")
            elif TMRuntime_hr < compMinimumRunTime:
                raise Exception("TMRuntime_hr is less time the minimum runtime for a HPWH of " + str(compMinimumRunTime*60)+ "minutes.")
            else:
                # Quick Check the inputs makes sense
                if not self.__checkLiqudWater(setpointTM_F):
                    raise Exception('Invalid input given for setpointTM_F, it must be between 32 and 212F.\n')
                if not self.__checkLiqudWater(TMonTemp_F):
                    raise Exception('Invalid input given for TMonTemp_F, it must be between 32 and 212F.\n')
                if setpointTM_F <= TMonTemp_F:
                    raise Exception("The temperature maintenance setpoint temperature must be greater than the turn on temperature")
                if setpointTM_F <= self.incomingT_F:
                    raise Exception("The temperature maintenance setpoint temperature must be greater than the city cold water temperature ")
                if TMonTemp_F <= self.incomingT_F:
                    raise Exception("The temperature maintenance turn on temperature must be greater than the city cold water temperature ")

                self.setpointTM_F     = setpointTM_F
                self.TMonTemp_F       = TMonTemp_F
                self.offTime_hr       = offTime_hr
                self.TMRuntime_hr     = TMRuntime_hr


    def setLoadShift(self, ls_arr, cdf_shift):
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
        if cdf_shift < 0.25 :
            raise Exception("Load shift only available for above 25 percent of days.")
        if cdf_shift > 1 :
            raise Exception("Cannot load shift for more than 100 percent of days")
       # if sum(ls_arr) == 24 :
        #    raise Exception("If the HPWH's are free to run 24 hours a day, you aren't really loadshifting")
        self.loadshift = np.array(ls_arr, dtype = float)# Coerce to numpy array of data type float
        self.cdf_shift = cdf_shift # percent of days for load shifting

    def checkInputs(self, gpdpp, loadShapeNorm, supplyT_F, incomingT_F,
                    storageT_F, compRuntime_hr, percentUseable,  aquaFract,
                    schematic, defrostFactor, singlePass):
        """Checks inputs are all valid"""
        if sum(loadShapeNorm) > 1 + 1e3 or sum(loadShapeNorm) < 1 - 1e3:
            raise Exception("Sum of the loadShapeNorm does not equal 1 but "+str(sum(loadShapeNorm))+".")
        if schematic not in self.schematicNames:
            raise Exception('Invalid input given for the schematic: "'+ schematic +'".\n')
        if percentUseable > 1 or percentUseable < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for percentUseable, must be between 0 and 1.\n')
        if aquaFract > 1 or aquaFract < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for aquaFract, it must be between 0 and 1.\n')
        if aquaFract < (1-percentUseable): # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for aquaFract, it must be greater than (1 - percentUseable) otherwise the aquastat is in the cold part of the storage tank.\n')
        if gpdpp > 49: # or self.gpdpp < 20:
            raise Exception('\nERROR: Please ensure your gallons per day per person is less than 49, the recommend max volume used per day\n')

        # Check temperature inputs
        if not self.__checkLiqudWater(supplyT_F):
            raise Exception('Invalid input given for supplyT_F, it must be between 32 and 212F.\n')
        if not self.__checkLiqudWater(incomingT_F):
            raise Exception('Invalid input given for incomingT_F, it must be between 32 and 212F.\n')
        if not self.__checkLiqudWater(storageT_F):
            raise Exception('Invalid input given for storageT_F, it must be between 32 and 212F.\n')
        if supplyT_F > storageT_F:
            raise Exception("The hot water supply temperature must be less than or equal to the primary storage temperature")
        if incomingT_F >= storageT_F:
            raise Exception("The city cold water temperature must be less than the primary storage temperature")
        if incomingT_F >= supplyT_F:
            raise Exception("The city cold water temperature must be less than the supply hot water temperature")
        if type(singlePass) != bool:
            raise Exception(" The singlePass variable must be of type boolean, True or False.")
        if defrostFactor > 1 or defrostFactor < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('Invalid input given for defrostFactor, it must be between 0 and 1.\n')


    def __checkLiqudWater(self,var_F):
        """
        Checks if the variable has a temperuter with in the range of liquid water at atm pressure

        Args:
            var_F (float): Temperature of water.

        Returns:
            bool: True if liquid, False if solid or gas.

        """
        if var_F < 32. or var_F > 212.:
            return False
        else:
            return True

    def calcedVariables(self):
        """ Calculate other variables needed."""
        self.totalHWLoad_G = self.gpdpp * self.nPeople
        # Covert hw load to gallons at the given supply temperature using 120 F and cold water of 40 F
        #self.totalHWLoad_G = mixVolume(self.totalHWLoad_G, self.supplyT_F, self.incomingT_F, 120.)

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
            elif temp[0] == "offtime_hr":
                self.offTime_hr  = float(temp[1])
            elif temp[0] == "tmruntime_hr":
                self.TMRuntime_hr   = float(temp[1])
            elif temp[0] == "wapt":
                self.Wapt      = float(temp[1])
            else:
                raise Exception('\nERROR: Invalid input given: '+ line +'.\n')
        # End for loop reading file lines.

        self.checkInputs(self.gpdpp, self.loadShapeNorm, self.supplyT_F, self.incomingT_F,
                    self.storageT_F, self.compRuntime_hr,self. percentUseable,  self.aquaFract,
                    self.schematic, self.defrostFactor, self.singlePass)
        self.calcedVariables()

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

def loadgpdpp( gpdpp, nBR = None):
    """
    Loads data for the gpdpp inputs if it is of string type, but passes gpdpp thorugh if it's not string and is just a number.
    Valid string keys are 'ashLow', 'ashMed', or 'ecoMark', and for the advanced processing of the California data
    use "CA". If using the "CA" option the number of units by bedrooms (nBR) is needed. The CA data has assumtions about the ratio of people per unit size.

    Attributes
    ----------
        gpdpp : float/ string
            The gallons per day per person value or a string key to lookup, valid keys are: 'ashLow', 'ashMed', or 'ecoMark', and "CA"
        nBR : list
            List of the number of units by bedroom size for 0 bedroom units (studios) to 5+ bedroom units, for example: [ 0, 12, 12, 12, 0, 0]

    Raises
    ----------
    Exception :
        If asking for the "CA" option and the number of units by bedroom size and number of people aren't defined

    """
    # Check if gpdpp is a string and look up by key
    if isinstance(gpdpp, str): # if the input here is a string get the get the gpdpp
        hpwhData = hpwhDataFetch()

        if gpdpp.lower() == "ca" :
            if nBR is None or sum(nBR) == 0:
                raise Exception("Cannot get the gpdpp for the CA data set without knowning the number of units by bedroom size for 0 BR (studios) through 5+ BR, the list must be of length 6 in that order.")
            if len(nBR) != 6:
                raise Exception("Cannot get the gpdpp for the CA data set without knowning the number of units by bedroom size for 0 BR (studios) through 5+ BR, the list must be of length 6 in that order.")

            # Count up the gpdpp for each bedroom type
            daily_totals = np.zeros(365)
            for ii in range(0,6):
                daily_totals += nBR[ii] * np.array(hpwhData.getCAGPDPPYearly(str(ii) + "br")) # daily totals is gpdpp * bedroom

            # Get the 98th percentile day divide by the number of people rounded up to an integer.
            gpdpp = np.ceil(np.percentile(daily_totals,98)/ sum(nBR))

        # Else look up by normal key function
        else:
            gpdpp = hpwhData.getGPDPP(gpdpp)[0]

    return gpdpp

##############################################################################

def HRLIST_to_MINLIST(a_list):
    """
    Repeats each element of a_list 60 times to go from hourly to minute.
    Still may need other unit conversions to get data from per hour to per minute

    Parameters
    ----------
    a_list : list
        A list in of values per hour.

    Returns
    -------
    out_list : list
        A list in of values per minute created by repeating values per hour 60 times.

    """
    out_list = []
    for num in a_list:
        out_list += [num]*60
    return out_list

##############################################################################

def roundList(a_list, n=3):
    """
    Rounds elements in a python list

    Parameters
    ----------
    a_list : float
        list to round values of.
    n : int
        optional, default = 3. Number of digits to round elements to.

    Returns
    -------
    list
        rounded values.

    """
    return [round(num, n) for num in a_list]