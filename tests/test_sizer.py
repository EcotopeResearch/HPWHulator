import pytest

import filecmp
import numpy as np

import os
import HPWHsizer
import dataFetch
from HPWHComponents import getPeakIndices, mixVolume


def file_regression(fileRef, fileResults):
        return filecmp.cmp(fileRef, fileResults)

@pytest.fixture
def empty_sizer():
    '''Returns a HPWHsizer instance initialized to zeros'''
    return HPWHsizer.HPWHsizer()

@pytest.fixture
def units_sizer():
    '''Returns a HPWHsizer instance initialized to with by units'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByUnits( [50,50,50,50,0,0], [1.374,1.74,2.567,3.109,4.225,3.769], [20,20,20,20,20,20],
                     [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                      0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                      0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                     120, 50, 150, 16, 0.8, .9, 0.4,
                     'paralleltank' )
    hpwh.initTempMaint(100)
    return hpwh

@pytest.fixture
def people_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByPeople(100, 36, 22.,
                      [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                       0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                       0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                    120, 50, 150., 18., 0.9, 0.9, 0.4,
                    "swingtank" )
    hpwh.initTempMaint(100)

    return hpwh

@pytest.fixture
def primary_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByPeople(100, 36, 22., "stream",
                    120, 50, 150., 16., .9, .9, 0.4,
                    "primary")
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
                    120, 50, 150., 16., .9, .9, 111,
                    "primary")
    with pytest.raises(Exception): # Get get to match text for some weird reason
        empty_sizer.initPrimaryByPeople(100, 22.,  36,
                      [0.0158,0.0053,0.0029,0.0012,0.0018,0.0170,0.0674,0.1267,
                        0.0915,0.0856,0.0452,0.0282,0.0287,0.0223,0.0299,0.0287,
                        0.0276,0.0328,0.0463,0.0587,0.0856,0.0663,0.0487,0.0358],
                    120, 50, 150., 16., .9, .9, 0.05,
                    "primary")

def test_AF_sizing_error(empty_sizer):
    empty_sizer.initPrimaryByPeople(100, 22., 36,
                  [0.0158,0.0053,0.0029,0.0012,0.0018,0.0170,0.0674,0.1267,
                    0.0915,0.0856,0.0452,0.0282,0.0287,0.0223,0.0299,0.0287,
                    0.0276,0.0328,0.0463,0.0587,0.0856,0.0663,0.0487,0.0358],
                120, 50, 150., 16., .9, .9, 0.11,
                "primary")
    with pytest.raises(Exception, match="The aquastat fraction is too low in the storge system recommend increasing to a minimum of: 0.21"):
        empty_sizer.build_size()

# Test the Fetcher
def test_getLoadshape(fetcher):
    assert fetcher.getLoadshape() == [0.008915,0.004458,0.001486,0.001486,0.001486,0.014859,
                    0.069837,0.13373,0.104012,0.077266,0.035067,0.031204,
                    0.020802,0.022288,0.024071,0.024071,0.020802,0.043388,
                    0.047251,0.07578,0.092125,0.059435,0.053492,0.032689]
def test_getGPDPP(fetcher):
    with pytest.raises(Exception):
        assert fetcher.getGPDPP("wrong")
def test_getRPepperBR(fetcher):
    assert fetcher.getRPepperBR("CA") == [1.374, 1.74, 2.567, 3.109, 4.225, 3.769] 
    assert fetcher.getRPepperBR("ASHSTD") == [1.49, 1.94, 2.39, 2.84, 3.29, 3.74] 
    assert fetcher.getRPepperBR("ASHLOW") == [1.69, 2.26, 2.83, 3.4, 3.97, 4.54] 
    with pytest.raises(Exception):
        assert fetcher.getRPepperBR("wrong")

@pytest.mark.parametrize("x, s, expected", [ 
    (1,0, 9.367514819547965e-15),
    (19,0, 0.40480748655575766),
    (25,0, 0.9859985113759763),
    (19,19, 3.3521114861106406e-16),
    (30,5,.9859985113759763),
    ])
def test_getCDF(fetcher, x, s, expected):
    assert fetcher.getCDF(x, s) == expected
    
@pytest.mark.parametrize("x, s, expected", [
    ([1,19,22,25,28],0,[0.0, 0.405, 0.837, 0.986, 1.0]),
    ([1,19,22,25,28],3,[0.0, 0.071, 0.405, 0.837, 0.986]),
    ])    
def test_getCDF_array(fetcher, x, s, expected):
    temp = [round(n, 3) for n in fetcher.getCDF(x, s)]
    assert temp == expected


@pytest.mark.parametrize("nSupplyT, nStorageT_F", [
    (120, 120),
    (125, 125),
    (150, 150),
    (120, 150),
    (120, 125)
    ])
@pytest.mark.parametrize("nPercentUseable, nAF", [
    (.8, .4),
    (1., .8),
    (.5, .55),
    (.02, .99),
    ])
@pytest.mark.parametrize('ngpdpp',[(10.),(20.),(40.)])
@pytest.mark.parametrize("LS", [
   ([1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
   ([0,0,0,0,0,0,0,0,0, 1,1,1,1,1,1,1,1, 0,0,0,0,0,0,0])
])
def test_primary_sim_positive(primary_sizer, nSupplyT, nStorageT_F, ngpdpp,
                              nPercentUseable, nAF, LS):
    # Reset inputs
    primary_sizer.inputs.supplyT_F = nSupplyT
    primary_sizer.inputs.storageT_F = nStorageT_F
    primary_sizer.inputs.percentUseable = nPercentUseable
    primary_sizer.inputs.aquaFract = nAF
    primary_sizer.inputs.gpdpp = ngpdpp
    # Recheck and recalc inputs
    primary_sizer.inputs.checkInputs()
    primary_sizer.inputs.calcedVariables()
    primary_sizer.setLoadShiftforPrimary(LS)
    # Size the system
    primary_sizer.build_size()
    # Check the simulation plot is all >= 0
    [ V, G_hw, D_hw, run ] = primary_sizer.primarySystem.runStorage_Load_Sim()
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

def test_trimtank(people_sizer):
    people_sizer.inputs.schematic = 'trimtank'
    with pytest.raises(Exception, match="Trim tanks are not supported yet"):
        assert people_sizer.build_size()

##############################################################################
# Full model and file tests!
@pytest.mark.parametrize("file1", [
    "tests/test_60UnitSwing.txt",
    "tests/test_200UnitTM.txt"
])
def test_hpwh_from_file(empty_sizer, file1):
    empty_sizer.initializeFromFile(file1)
    results = empty_sizer.build_size()
    assert len(results) == 4
    empty_sizer.writeToFile("tests/output/"+os.path.basename(file1))

    assert file_regression("tests/ref/"+os.path.basename(file1),
                           "tests/output/"+os.path.basename(file1))

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

##############################################################################
## Test ploting outputs stay same
def test_plot_primaryCurve(primary_sizer):
    primary_sizer.build_size()
    fig = primary_sizer.plotSizingCurve(return_as_div=False)
    fig.write_html("tests/output/test_plot_primaryCurve.html")
    with open('tests/output/test_plot_primaryCurve.txt', 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/test_plot_primaryCurve.txt",
                           "tests/output/test_plot_primaryCurve.txt")

def test_parallel_curve(units_sizer):
    units_sizer.build_size()
    fig = units_sizer.plotParallelTankCurve(return_as_div=False)
    with open('tests/output/test_plot_parallelCurve.txt', 'w') as file:
        file.write(str(fig))
    fig.write_html("tests/output/test_plot_parallelCurve.html")
    assert file_regression("tests/ref/test_plot_parallelCurve.txt",
                           "tests/output/test_plot_parallelCurve.txt")

def test_plot_simPrimary(primary_sizer):
    primary_sizer.build_size()
    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/test_plot_simPrimary.html")
    with open('tests/output/test_plot_simPrimary.txt', 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/test_plot_simPrimary.txt",
                           "tests/output/test_plot_simPrimary.txt")

@pytest.mark.parametrize("file1, LS", [
   ( "test_plot_simLS8.txt", [1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
   ( "test_plot_simLS4.txt", [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1]),
   ( "test_plot_simLSTOU.txt",[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1]),
   ( "test_plot_simLSSolarDream.txt", [0,0,0,0,0,0,0,0,0, 1,1,1,1,1,1,1,1, 0,0,0,0,0,0,0])
])
def test_plot_LS(primary_sizer, file1, LS):
    primary_sizer.setLoadShiftforPrimary(LS)
    primary_sizer.build_size()

    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/" + os.path.splitext(file1)[0] +".html")
    with open("tests/output/"+os.path.basename(file1), 'w') as file:
        file.write(str(fig))
    assert file_regression("tests/ref/"+os.path.basename(file1),
                           "tests/output/"+os.path.basename(file1))
