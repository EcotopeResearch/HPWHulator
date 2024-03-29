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


import pytest

import filecmp
import numpy as np

import os, sys
import HPWHsizer
import dataFetch
from HPWHComponents import getPeakIndices
from cfg import mixVolume


def file_regression(fileRef, fileResults):
    return filecmp.cmp(fileRef, fileResults)

class Shhh:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

@pytest.fixture
def empty_sizer():
    '''Returns a HPWHsizer instance initialized to zeros'''
    with Shhh():
        hpwh = HPWHsizer.HPWHsizer()
    return hpwh

@pytest.fixture
def units_sizer():
    '''Returns a HPWHsizer instance initialized to with by units'''
    with Shhh():
        hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByUnits([50,50,50,50,0,0],
                            [1.374,1.74,2.567,3.109,4.225,3.769],
                            [20,20,20,20,20,20],
                            [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                             0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                             0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                            120, 50, 150, 16, 0.8,  0.4,
                            'paralleltank', .9 )
    hpwh.initTempMaint(100)
    return hpwh

@pytest.fixture
def people_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    with Shhh():
        hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByPeople(100, 36, 22.,
                             "stream",
                             120, 50, 150., 18., 0.9, 0.4,
                             "swingtank", 0.9 )
    hpwh.initTempMaint(100)

    return hpwh

@pytest.fixture
def primary_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    with Shhh():
        hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByPeople(100, 36, 22, "stream",
                             120, 50, 150., 16., .9, 0.4,
                             "primary", .9 )
    return hpwh

@pytest.fixture
def CA_sizer(): # Returns the hpwh sizer object designed for Cali options
    with Shhh():
        hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByUnits([6,12,12,6,0,0], "CA", "CA", "stream",
                            125, 50, 150., 16., .8, 0.4,
                            "swingtank")
    hpwh.initTempMaint(100)
    return hpwh

@pytest.fixture
def fetcher():
    fetch = dataFetch.hpwhDataFetch()
    return fetch
# End of fixtures
###############################################################################
###############################################################################
# Start of tests

# Unit Tests
@pytest.mark.parametrize("arr, expected", [
    ([1, 2, 1, 1, -3, -4, 7, 8, 9, 10, -2, 1, -3, 5, 6, 7, -10], [4,10,12,16]),
    ([1.3, 100.2, -500.5, 1e9, -1e-9, -5.5, 1,7,8,9,10, -1], [2,4,11]),
    ([-1, 0, 0, -5, 0, 0, 1, 7, 8, 9, 10, -1], [0,3,11])
])
def test_getPeakIndices( arr, expected):
    assert all(getPeakIndices(arr) == np.array(expected))

@pytest.mark.parametrize("hotT, coldT, outT, expected", [
   (125, 50, 120, 93.333),
   (120, 40, 120, 100.0),
   (150, 40, 120, 72.727),
   (100, 40, 120, 133.333)
])
def test_mixVolume(hotT, coldT, outT, expected):
    assert round(mixVolume(100, hotT, coldT, outT), 3) == expected

@pytest.mark.parametrize("hrs", [
    -0.1, 0, 24.1, np.array([ 1, 3, 44]), np.array([-1, 2, 3]), np.array([0,2,4,25])
])
def test_checkHeatHours(primary_sizer, hrs):
    primary_sizer.build_size()
    with pytest.raises(Exception, match="Heat hours is not within 1 - 24 hours"):
        primary_sizer.primarySystem.sizePrimaryTankVolume(hrs)

# Check for AF errors
def test_AF_initialize_error(empty_sizer):
    with pytest.raises(Exception, match="Invalid input given for aquaFract, it must be between 0 and 1.\n"):
        empty_sizer.initPrimaryByPeople(100, 22., 36,
                        [0.0158,0.0053,0.0029,0.0012,0.0018,0.0170,0.0674,0.1267,
                       0.0915,0.0856,0.0452,0.0282,0.0287,0.0223,0.0299,0.0287,
                       0.0276,0.0328,0.0463,0.0587,0.0856,0.0663,0.0487,0.0358],
                    120, 50, 150., 16., .9, 111, "primary", .9)

    with pytest.raises(Exception): # Get get to match text for some weird reason
        empty_sizer.initPrimaryByPeople(100, 22.,  36,
                      [0.0158,0.0053,0.0029,0.0012,0.0018,0.0170,0.0674,0.1267,
                        0.0915,0.0856,0.0452,0.0282,0.0287,0.0223,0.0299,0.0287,
                        0.0276,0.0328,0.0463,0.0587,0.0856,0.0663,0.0487,0.0358],
                      120, 50, 150., 16., .9, 0.05,
                      "primary", .9)

def test_AF_sizing_error(empty_sizer):
    empty_sizer.initPrimaryByPeople(100, 22., 36,
                  [0.0158,0.0053,0.0029,0.0012,0.0018,0.0170,0.0674,0.1267,
                    0.0915,0.0856,0.0452,0.0282,0.0287,0.0223,0.0299,0.0287,
                    0.0276,0.0328,0.0463,0.0587,0.0856,0.0663,0.0487,0.0358],
                  120, 50, 150., 16., .9, 0.11,
                  "primary", .9)
    with pytest.raises(Exception, match =
                       "('01', 'The aquastat fraction is too low in the storge system recommend increasing the maximum run hours in the day or increasing to a minimum of: ', 0.209)"):
        empty_sizer.build_size()

def test_primary_AF_over_1_Error(primary_sizer):
    # Reset inputs
    primary_sizer.inputs.supplyT_F = 105
    primary_sizer.inputs.storageT_F = 160
    primary_sizer.inputs.percentUseable = .5
    primary_sizer.inputs.aquaFract = .56
    primary_sizer.inputs.compRuntime_hr = 8.
    # Recalc inputs
    primary_sizer.inputs.calcedVariables()
    # Size the system
    with pytest.raises(Exception, match =
                       "The minimum aquastat fraction is greater than 1. This is due to the storage efficency and/or the maximum run hours in the day may be too low"):
        primary_sizer.build_size()

def test_parallel_min_size(units_sizer):
    with pytest.raises(Exception, match="The expected run time of the parallel tank is less time the minimum runtime for a HPWH of 20.0 minutes."):
        units_sizer.initTempMaint( 100, safetyTM = 1.75, offTime_hr = .1)
    with pytest.raises(Exception, match="The expected run time of the parallel tank is less time the minimum runtime for a HPWH of 20.0 minutes."):
        units_sizer.initTempMaint( 100, safetyTM = 5, offTime_hr = .5)


@pytest.mark.parametrize("loadshape", [
    ([-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ([1/2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1/2]),
    ([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
    ([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1]),
    ([-1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1]),
    ("loadshape"), ([1]), ([-1]), ([1, -1]), ([1000, -1]), ([10]*24)
    ])
class TestParametrizedLoadShapeErrors:
    def test_loadShapeNorm_errors(self, empty_sizer, loadshape):
        # Check the init is bad for the load shape norm
        with pytest.raises(Exception):
            empty_sizer.initPrimaryByPeople(100, 50, 20, loadshape,
                        120, 50, 150., 16., 0.4, 0.11, "primary")
            
    def test_LS_loadshape_errors(self, primary_sizer, loadshape):
        # Check the init is bad for the load shape norm
        with pytest.raises(Exception):
            primary_sizer.setLoadShiftforPrimary([1]*24, avgLoadShape = loadshape)

# Test the Fetcher
def test_getLoadshape(fetcher):
    assert fetcher.getLoadshape() == [0.015197568,
             0.006079027,0.003039514,0.003039514,0.003039514,0.009118541,0.075987842,
             0.151975684,0.100303951,0.082066869,0.021276596,0.024316109, 0.021276596,
             0.024316109,    0.012158055,    0.006079027,    0.009118541,    0.036474164, 0.054711246,
            0.072948328, 0.088145897, 0.09118541 , 0.063829787,0.024316109]
def test_getGPDPP(fetcher):
    with pytest.raises(Exception):
        assert fetcher.getGPDPP("wrong")
def test_getRPepperBR(fetcher):
    assert fetcher.getRPepperBR("CA") == [1.374, 1.74, 2.567, 3.109, 4.225, 3.769]
    assert fetcher.getRPepperBR("ASHSTD") == [1.49, 1.94, 2.39, 2.84, 3.29, 3.74]
    assert fetcher.getRPepperBR("ASHLOW") == [1.69, 2.26, 2.83, 3.4, 3.97, 4.54]
    with pytest.raises(Exception):
        assert fetcher.getRPepperBR("wrong")

@pytest.mark.parametrize("x, expected", [
    (0.25, 0.6497449987474476),
    (0.5, 0.7052988591269841),
    (0.75, 0.7608527195065206),
    (0.99, 0.8969068189975757),
    (0.999999, 1),
    ])
def test_getCDF(fetcher, x, expected):
    assert fetcher.getCDF(x) == expected

def test_CDFShift_error( primary_sizer ):
    with pytest.raises(Exception):
        assert primary_sizer.setLoadShiftforPrimary([1]*24, 1.1)
    with pytest.raises(Exception):
        assert primary_sizer.setLoadShiftforPrimary([1]*24, .24)
    with pytest.raises(Exception):
        assert primary_sizer.setLoadShiftforPrimary([1]*24, -1)
    with pytest.raises(Exception):
        assert primary_sizer.setLoadShiftforPrimary([1]*24, 0)



#@pytest.mark.parametrize("x, s, expected", [
#    ([1,19,22,25,28],0,[0.0, 0.405, 0.837, 0.986, 1.0]),
#    ([1,19,22,25,28],3,[0.0, 0.071, 0.405, 0.837, 0.986]),
#    ])
#def test_getCDF_array(fetcher, x, s, expected):
#    temp = [round(n, 3) for n in fetcher.getCDF(x, s)]
#    assert temp == expected

# Test on the loadgpdpp function utilizing fetcher check it throws errors
def test_loadgpdpp_errs():
    with pytest.raises(Exception):
        assert HPWHsizer.loadgpdpp('CA')
    with pytest.raises(Exception):
        assert HPWHsizer.loadgpdpp('CA',1)
    with pytest.raises(Exception):
        assert HPWHsizer.loadgpdpp('CA',[12,12,12,12])
    with pytest.raises(Exception):
        assert HPWHsizer.loadgpdpp('CA',[12,12,12,12,12,12,12])
        

# Test on the loadgpdpp function utilizing fetcher it operates as expected
@pytest.mark.parametrize("x, nBR, expected", [
    (30 , 0, 30),
    ("ashLow", 0, 20),
    ("CA", [50, 50, 0, 0, 0, 0], 31),
    ("CA", [6, 12, 12, 6, 0, 0], 26),
    ("CA", [10, 10, 10, 10, 10, 10], 24),
    ("CA", [8, 34, 40, 6, 0, 0], 27),
    ])
def test_loadgpdpp(x, nBR, expected):
    assert HPWHsizer.loadgpdpp(x,nBR) == expected


@pytest.mark.parametrize("nSupplyT, nStorageT_F", [
    (120, 120),
    (120, 160),
    (150, 150),
    ])
@pytest.mark.parametrize("nPercentUseable, nAF", [
    (1., .8),
    (.4, .9),
    (.05, .99),
    ])
@pytest.mark.parametrize('ncompRuntime_hr',[(9.6),(14.1)])
def test_primary_sim_positive(primary_sizer, nSupplyT, nStorageT_F, ncompRuntime_hr,
                              nPercentUseable, nAF):
    # Reset inputs
    primary_sizer.inputs.supplyT_F = nSupplyT
    primary_sizer.inputs.storageT_F = nStorageT_F
    primary_sizer.inputs.percentUseable = nPercentUseable
    primary_sizer.inputs.aquaFract = nAF
    primary_sizer.inputs.compRuntime_hr = ncompRuntime_hr
    # Recalc inputs
    primary_sizer.inputs.calcedVariables()
    # Size the system
    primary_sizer.build_size()
    # Check the simulation plot is all >= 0
    [ V, G_hw, D_hw, run, _, _, _ ] = primary_sizer.runStorage_Load_Sim()
    assert all(i >= 0 for i in V + G_hw + D_hw + run)


@pytest.mark.parametrize("nSupplyT, nStorageT_F", [
    (120, 185),
    (130, 150),
    ])
@pytest.mark.parametrize("nPep", [
    20, 1000
    ])
@pytest.mark.parametrize("nApt", [
    12, 1000
    ])
@pytest.mark.parametrize("Wapt", [
    30, 175
    ])
def test_swing_sim_limits(CA_sizer, nSupplyT, nStorageT_F, nPep, nApt, Wapt):
    # Reset inputs
    CA_sizer.inputs.supplyT_F = nSupplyT
    CA_sizer.inputs.storageT_F = nStorageT_F
    CA_sizer.inputs.nPeople = nPep
    CA_sizer.inputs.nApt = nApt
    CA_sizer.inputs.Wapt = Wapt

    # Recalc inputs
    CA_sizer.inputs.calcedVariables()

    # Size the system
    CA_sizer.build_size()
    # Check the simulation plot is all >= 0
    [ V, G_hw, D_hw, run, swingT, _, _ ] = CA_sizer.runStorage_Load_Sim()

    # fig = CA_sizer.plotStorageLoadSim(return_as_div=False)
    # fig.write_html("tests/output/" + str(nSupplyT) + "_"+ str(nStorageT_F)+"_"+str(nPep) +"_"+str(nApt)+ "_"+ str(Wapt)+ "_"  +".html")

    assert all(i >= 0 for i in V + G_hw + D_hw + run)
    assert min(swingT) >= nSupplyT

@pytest.mark.parametrize("loadshape", [
    ([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
    ([1/2, 1/2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ([1/2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1/2]),
    ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1/2, 1/2]),
    ([1/4, 1/4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1/4, 1/4]),
    ([1/4, 1/4, 1/4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1/4]),
    ([1/4, 1/4, 1/4, 1/4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ])
def test_swing_custom_loadshapes(people_sizer, loadshape):
    print((loadshape))
    print(len(loadshape))
    people_sizer.inputs.loadShapeNorm = loadshape
    
    # Recalc inputs
    people_sizer.inputs.calcedVariables()

    # Size the system
    [PV, PV, _, TMC] =people_sizer.build_size()
    assert all(i > 0 for i in [PV, PV, TMC])

    # Check the simulation plot is all >= 0
    [ V, G_hw, D_hw, run, _, _, _ ] = people_sizer.runStorage_Load_Sim()
    # fig = CA_sizer.plotStorageLoadSim(return_as_div=False)
    # fig.write_html("tests/output/" + str(nSupplyT) + "_"+ str(nStorageT_F)+"_"+str(nPep) +"_"+str(nApt)+ "_"+ str(Wapt)+ "_"  +".html")
    assert all(i >= 0 for i in V + G_hw + D_hw + run)

##############################################################################
# Init Tests
def test_default_init(empty_sizer):
    assert empty_sizer.validbuild               == False
    assert empty_sizer.primarySystem            == None
    assert empty_sizer.tempmaintSystem          == None
    assert empty_sizer.ashraeSize               == None

    assert (empty_sizer.inputs.nBR             == np.zeros(6)).all()
    assert (empty_sizer.inputs.rBR             == np.zeros(6)).all()
    assert empty_sizer.inputs.nPeople          == 0. # Nnumber of people
    assert empty_sizer.inputs.gpdpp            == 0. # Gallons per day per person
    assert (empty_sizer.inputs.loadShapeNorm   == np.zeros(24)).all() # The normalized load shape
    assert empty_sizer.inputs.supplyT_F        == 0. # The supply temperature to the occupants
    assert empty_sizer.inputs.incomingT_F      == 0. # The incoming cold water temperature for the city
    assert empty_sizer.inputs.storageT_F       == 0. # The primary hot water storage temperature
    assert empty_sizer.inputs.compRuntime_hr   == 0. # The runtime?
    assert empty_sizer.inputs.percentUseable   == 0  # The  percent of useable storage
    assert empty_sizer.inputs.defrostFactor    == 1. # The defrost factor. Derates the output power for defrost cycles.
    assert empty_sizer.inputs.totalHWLoad_G    == 0
    assert empty_sizer.inputs.aquaFract        == 0

    assert empty_sizer.inputs.schematic        == "" # The schematic for sizing maybe just primary maybe with temperature maintenance.
    assert empty_sizer.inputs.TMonTemp_F       == 0. # The temperature the swing tank turns on at
    assert empty_sizer.inputs.nApt             == 0. # The number of apartments
    assert empty_sizer.inputs.Wapt             == 0. # The recirculation loop losses in terms of W/apt
    assert empty_sizer.inputs.Wapt             == 0.

    with pytest.raises(Exception):
        assert empty_sizer.sizeSystem()
    with pytest.raises(Exception):
        assert empty_sizer.getSizingResults()
    with pytest.raises(Exception):
        assert empty_sizer.primarySystem.sizeVol_Cap()

def test_multipass(people_sizer):
    people_sizer.inputs.singlePass = False
    with pytest.raises(Exception, match="Multipass is yet supported"):
        assert people_sizer.build_size()


#############################################################################
# Full model test! 
def test_primarySizer(primary_sizer):
    with pytest.raises(Exception, match="The system can not be sized without a valid build"):
        assert primary_sizer.sizeSystem()

    results = primary_sizer.build_size()
    assert len(results) == 2

    with pytest.raises(Exception):
        assert primary_sizer.sizePrimaryTankVolume(-10)
    with pytest.raises(Exception):
        assert primary_sizer.sizePrimaryTankVolume(100)
    primary_sizer.writeToFile("tests/output/primary_sizer.txt")
    assert file_regression("tests/ref/primary_sizer.txt",
                            "tests/output/primary_sizer.txt")

def test_initPrimaryByPeople(people_sizer):
    with pytest.raises(Exception, match="The system can not be sized without a valid build"):
        assert people_sizer.sizeSystem()

    results = people_sizer.build_size()
    assert len(results) == 4

    with pytest.raises(Exception):
        assert people_sizer.primarySystem.sizePrimaryTankVolume(-10)
    with pytest.raises(Exception):
        assert people_sizer.primarySystem.sizePrimaryTankVolume(100)

    people_sizer.writeToFile("tests/output/people_sizer.txt")
    assert file_regression("tests/ref/people_sizer.txt",
                            "tests/output/people_sizer.txt")

def test_initPrimaryByUnits(units_sizer):
    with pytest.raises(Exception, match="The system can not be sized without a valid build"):
        assert units_sizer.sizeSystem()

    results = units_sizer.build_size()
    assert len(results) == 4

    with pytest.raises(Exception):
        assert units_sizer.sizePrimaryTankVolume(-10)
    with pytest.raises(Exception):
        assert units_sizer.sizePrimaryTankVolume(100)
    units_sizer.writeToFile("tests/output/units_sizer.txt")
    assert file_regression("tests/ref/units_sizer.txt",
                            "tests/output/units_sizer.txt")

def test_CA_sizing_settings(CA_sizer):
    results = CA_sizer.build_size()
    assert len(results) == 4
    CA_sizer.writeToFile("tests/output/ca_sizer.txt")
    assert file_regression("tests/ref/ca_sizer.txt",
                            "tests/output/ca_sizer.txt")

##############################################################################
# Load Shift tests
@pytest.mark.parametrize("file1, LS", [
    ( "test_primaryLS8.txt", [1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
    ( "test_primaryLS4.txt", [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
    ( "test_primaryLSTOU.txt",[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1]),
    ( "test_primaryLSSolarDream.txt", [0,0,0,0,0,0,0,0,0, 1,1,1,1,1,1,1,1, 0,0,0,0,0,0,0])
])
def test_size_LS(primary_sizer, file1, LS):
    primary_sizer.setLoadShiftforPrimary(LS)
    primary_sizer.build_size()

    primary_sizer.writeToFile("tests/output/"+os.path.basename(file1))
    assert file_regression("tests/ref/"+os.path.basename(file1),
                            "tests/output/"+os.path.basename(file1))
# Load Shift Shapes
@pytest.mark.parametrize("LS", [
    ([0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0]),
])
@pytest.mark.parametrize("file1, loadshape", [
    ("test_primaryLS_CustomShape1.txt", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ("test_primaryLS_CustomShape2.txt", [1/2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1/2]),
    ("test_primaryLS_CustomShape3.txt", [1/10, 1/10, 1/10, 1/10, 1/10, 1/10, 1/10, 1/10, 1/10, 1/10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ])
def test_size_LS(primary_sizer, LS, file1, loadshape):
    primary_sizer.setLoadShiftforPrimary(LS, avgLoadShape = loadshape)
    primary_sizer.build_size()

    fig = primary_sizer.plotStorageLoadSim(return_as_div=False)
    # Print figures for visualizatoin.
    #fig.write_html("tests/output/" + os.path.splitext(file1)[0] +".html")

    primary_sizer.writeToFile("tests/output/"+os.path.basename(file1))
    assert file_regression("tests/ref/"+os.path.basename(file1),
                            "tests/output/"+os.path.basename(file1))

##############################################################################
## Test ploting outputs stay same
def test_plot_primaryCurve(primary_sizer):
    primary_sizer.build_size()
    fig = primary_sizer.plotSizingCurve(return_as_div=False)
    #fig.write_html("tests/output/test_plot_primaryCurve.html") # we don't need to test the we can write to html
    fig.layout = {} #Set figure layout to blank, save's space and we're testing the importand data part.

    with open('tests/output/test_plot_primaryCurve.txt', 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/test_plot_primaryCurve.txt",
                            "tests/output/test_plot_primaryCurve.txt")

def test_parallel_curve(units_sizer):
    units_sizer.build_size()
    fig = units_sizer.plotParallelTankCurve(return_as_div=False)
    fig.layout = {} #Set figure layout to blank, save's space and we're testing the importand data part.

    with open('tests/output/test_plot_parallelCurve.txt', 'w') as file:
        file.write(str(fig))
    #fig.write_html("tests/output/test_plot_parallelCurve.html")
    assert file_regression("tests/ref/test_plot_parallelCurve.txt",
                            "tests/output/test_plot_parallelCurve.txt")

def test_plot_simPrimary(primary_sizer):
    primary_sizer.build_size()
    fig = primary_sizer.plotStorageLoadSim(return_as_div=False)
    #fig.write_html("tests/output/test_plot_simPrimary.html") # we don't need to test the we can write to html
    fig.layout = {} #Set figure layout to blank, save's space and we're testing the importand data part.

    with open('tests/output/test_plot_simPrimary.txt', 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/test_plot_simPrimary.txt",
                            "tests/output/test_plot_simPrimary.txt")

def test_plot_simSwing(CA_sizer):
    CA_sizer.build_size()
    fig = CA_sizer.plotStorageLoadSim(return_as_div=False)
    #fig.write_html("tests/output/test_plot_simSwing.html")  # we don't need to test the we can write to html
    fig.layout = {} #Set figure layout to blank, save's space and we're testing the importand data part.

    with open('tests/output/test_plot_simSwing.txt', 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/test_plot_simSwing.txt",
                            "tests/output/test_plot_simSwing.txt")

@pytest.mark.parametrize("file1, LS", [
    ( "test_plot_simLS8.txt", [1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
    ( "test_plot_simLS4.txt", [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
    ( "test_plot_simLSTOU.txt",[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1]),
    ( "test_plot_simLSSolarDream.txt", [0,0,0,0,0,0,0,0,0, 1,1,1,1,1,1,1,1, 0,0,0,0,0,0,0])
])
def test_plot_LS(primary_sizer, file1, LS):
    primary_sizer.setLoadShiftforPrimary(LS)
    primary_sizer.build_size()

    fig = primary_sizer.plotStorageLoadSim(return_as_div=False)
    #fig.write_html("tests/output/" + os.path.splitext(file1)[0] +".html")
    fig.layout = {} #Set figure layout to blank, save's space and we're testing the importand data part.

    with open("tests/output/"+os.path.basename(file1), 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/"+os.path.basename(file1),
                            "tests/output/"+os.path.basename(file1))

@pytest.mark.parametrize("file1, LS", [
    ( "test_plot_swingLS8.txt", [1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
    ( "test_plot_swingLS4.txt", [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
])
def test_swing_LS(CA_sizer, file1, LS):
    CA_sizer.setLoadShiftforPrimary(LS)
    CA_sizer.build_size()

    fig = CA_sizer.plotStorageLoadSim(return_as_div=False)
    #fig.write_html("tests/output/" + os.path.splitext(file1)[0] + ".html")
    fig.layout = {} #Set figure layout to blank, save's space and we're testing the importand data part.

    with open("tests/output/"+os.path.basename(file1), 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/"+os.path.basename(file1),
                            "tests/output/"+os.path.basename(file1))
