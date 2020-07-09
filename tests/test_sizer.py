import pytest

import filecmp
import numpy as np

import os
import HPWHsizer
import dataFetch

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
    hpwh.initPrimaryByUnits( [50,50,50,50,0,0], [1.374,1.74,2.567,3.109,4.225,3.769], 20,
                     [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                      0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                      0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                     120, 50, 150, 16, 0, 0.8, .9,
                     'paralleltank',True )
    hpwh.initTempMaint(100)
    return hpwh

@pytest.fixture
def people_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByPeople(100, 22.,
                      [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                       0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                       0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                    120, 50, 150., 18., 0, .9, .9,
                    "swingtank", True, 36)
    hpwh.initTempMaint(100)

    return hpwh

@pytest.fixture
def primary_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initPrimaryByPeople(100, 22.,
                      [0.0158,0.0053,0.0029,0.0012,0.0018,0.0170,0.0674,0.1267,
                       0.0915,0.0856,0.0452,0.0282,0.0287,0.0223,0.0299,0.0287,
                       0.0276,0.0328,0.0463,0.0587,0.0856,0.0663,0.0487,0.0358],
                    120, 50, 150., 16., 0, .9, .9,
                    "primary", True, 36)
    return hpwh

@pytest.fixture
def fetcher():
    fetch = dataFetch.hpwhDataFetch()
    return fetch
# End of fixtures
###############################################################################
###############################################################################
# Start of tests

#Init Tests
def test_default_init(empty_sizer):
    assert empty_sizer.validbuild  == False
    assert empty_sizer.primarySystem            == None
    assert empty_sizer.tempmaintSystem          == None
    assert empty_sizer.ashraeSize               == None
    
    assert (empty_sizer.translate.nBR             == np.zeros(6)).all()
    assert (empty_sizer.translate.rBR             == np.zeros(6)).all()
    assert empty_sizer.translate.nPeople          == 0. # Nnumber of people
    assert empty_sizer.translate.gpdpp            == 0. # Gallons per day per person
    assert (empty_sizer.translate.loadShapeNorm   == np.zeros(24)).all() # The normalized load shape
    assert empty_sizer.translate.supplyT_F        == 0. # The supply temperature to the occupants
    assert empty_sizer.translate.incomingT_F      == 0. # The incoming cold water temperature for the city
    assert empty_sizer.translate.storageT_F       == 0. # The primary hot water storage temperature
    assert empty_sizer.translate.compRuntime_hr   == 0. # The runtime?
    assert empty_sizer.translate.percentUseable   == 0 #The  percent of useable storage
    assert empty_sizer.translate.defrostFactor    == 1. # The defrost factor. Derates the output power for defrost cycles.
    assert empty_sizer.translate.totalHWLoad_G    == 0

    assert empty_sizer.translate.schematic        == "" # The schematic for sizing maybe just primary maybe with temperature maintenance.
    assert empty_sizer.translate.TMonTemp_F       == 0. # The temperature the swing tank turns on at
    assert empty_sizer.translate.nApt             == 0. # The number of apartments
    assert empty_sizer.translate.Wapt             == 0. # The recirculation loop losses in terms of W/apt
    assert empty_sizer.translate.TMRuntime_hr     == 0. # The temperature maintenance minimum runtime.
    assert empty_sizer.translate.offTime_hr       == 0.
    assert empty_sizer.translate.Wapt             == 0.
    assert empty_sizer.translate.returnT_F        == 0.
    assert empty_sizer.translate.fdotRecirc_gpm   == 0.

    with pytest.raises(Exception):
        assert empty_sizer.sizeSystem()
    with pytest.raises(Exception):
        assert empty_sizer.primarySystem.sizeVol_Cap()
        
def test_multipass(people_sizer):
    people_sizer.translate.singlePass = False
    with pytest.raises(Exception, match="Multipass is yet supported"):
        assert people_sizer.build_size()
    
def test_trimtank(people_sizer):
    people_sizer.translate.schematic = 'trimtank'
    with pytest.raises(Exception, match="Trim tanks are not supported yet"):
        assert people_sizer.build_size()   

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


@pytest.mark.parametrize("arr, expected", [
    ([1, 2, 1, 1, -3, -4, 7, 8, 9, 10, -2, 1, -3, 5, 6, 7, -10], [4,10,12,16]),
    ([1.3, 100.2, -500.5, 1e9, -1e-9, -5.5, 1,7,8,9,10, -1], [2,4,11]),
    ([-1, 0, 0, -5, 0, 0, 1, 7, 8, 9, 10, -1], [0,3,11])
])
def test_getPeakIndices(units_sizer, arr, expected):
    units_sizer.buildSystem()
    assert all(units_sizer.primarySystem.getPeakIndices(arr) == np.array(expected))






###############################################################################
# Full model and file tests!
def test_primarySizer(primary_sizer):
    with pytest.raises(Exception, match="The system can not be sized without a valid build"):
        assert primary_sizer.sizeSystem()
    
    results = primary_sizer.build_size()
    assert len(results) == 3
    
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
    assert len(results) == 5    
    
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
    assert len(results) == 5
    
    with pytest.raises(Exception):
        assert units_sizer.sizePrimaryTankVolume(-10)
    with pytest.raises(Exception):
        assert units_sizer.sizePrimaryTankVolume(100)
    units_sizer.writeToFile("tests/output/units_sizer.txt")
    assert file_regression("tests/ref/units_sizer.txt",
                           "tests/output/units_sizer.txt")

@pytest.mark.parametrize("file1", [
    "tests/test_60UnitSwing.txt",
    "tests/test_200UnitTM.txt"
])
def test_hpwh_from_file(empty_sizer, file1):
    empty_sizer.initializeFromFile(file1)
    results = empty_sizer.build_size()
    assert len(results) == 5
    empty_sizer.writeToFile("tests/output/"+os.path.basename(file1))

    assert file_regression("tests/ref/"+os.path.basename(file1),
                           "tests/output/"+os.path.basename(file1))


def test_primaryPlot(primary_sizer):    
    primary_sizer.build_size()
    fig = primary_sizer.plotSizingCurve(return_as_div=False)
    fig.write_html("tests/output/primarytest.html")
    
def test_simPlot(primary_sizer):    
    primary_sizer.build_size()
    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/simtest.html")
    
def test_simLSP_8hr(primary_sizer): 
    primary_sizer.buildSystem()
    primary_sizer.primarySystem.setLoadShift([1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,1,1])
    primary_sizer.sizeSystem()
    primary_sizer.writeToFile("tests/output/test_primaryLS8.txt")

    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/simLS8test.html")
    
    assert file_regression("tests/ref/test_primaryLS8.txt",
                           "tests/output/test_primaryLS8.txt")
    
def test_simLSP_4hr(primary_sizer): 
    primary_sizer.buildSystem()
    primary_sizer.primarySystem.setLoadShift([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1])
    primary_sizer.sizeSystem()
    primary_sizer.writeToFile("tests/output/test_primaryLS4.txt")

    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/simLS4test.html")
    
    assert file_regression("tests/ref/test_primaryLS4.txt",
                           "tests/output/test_primaryLS4.txt")

def test_simLS_TOU(primary_sizer): 
    primary_sizer.buildSystem()
    primary_sizer.primarySystem.setLoadShift([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1])
    primary_sizer.sizeSystem()
    primary_sizer.writeToFile("tests/output/test_primaryLSTOU.txt")

    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/simLSTOUtest.html")
    
    assert file_regression("tests/ref/test_primaryLSTOU.txt",
                           "tests/output/test_primaryLSTOU.txt")
    
def test_simLS_SolarDream(primary_sizer): 
    primary_sizer.buildSystem()
    primary_sizer.primarySystem.setLoadShift([0,0,0,0,0,0,0,0,0, 1,1,1,1,1,1,1,1, 0,0,0,0,0,0,0])
    primary_sizer.sizeSystem()
    primary_sizer.writeToFile("tests/output/test_primaryLSSolarDream.txt")

    fig = primary_sizer.plotPrimaryStorageLoadSim(return_as_div=False)
    fig.write_html("tests/output/simLSSolarDreamtest.html")
    
    assert file_regression("tests/ref/test_primaryLSSolarDream.txt",
                           "tests/output/test_primaryLSSolarDream.txt")