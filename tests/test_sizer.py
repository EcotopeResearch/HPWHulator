import pytest

import filecmp
import numpy as np
import os
import HPWHsizer


def file_regression(fileRef, fileResults):
        return filecmp.cmp(fileRef, fileResults);

@pytest.fixture
def empty_sizer():
    '''Returns a HPWHsizer instance initialized to zeros'''
    return HPWHsizer.HPWHsizer()

@pytest.fixture
def units_sizer():
    '''Returns a HPWHsizer instance initialized to with by units'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initByUnits( [50,50,50,50,0,0], [1.374,1.74,2.567,3.109,4.225,3.769], 20, 
                     [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                      0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                      0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                     120, 50, 150, 16, 0, 0.8, .9,
                     'paralleltank',True, 
                     100., 115., 0. )
    return hpwh;

@pytest.fixture
def people_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    hpwh = HPWHsizer.HPWHsizer()
    hpwh.initByPeople(100, 22., 
                      [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                       0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                       0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038],
                    120, 50, 150., 18., 0, .9, .9, 
                    "swingtank", True, 36,
                    100., 115., 0.);
    return hpwh;
# End of fixtures

# Start of tests

#Init Tests
def test_default_init(empty_sizer):
    assert (empty_sizer.translate.nBR             == np.zeros(6)).all()
    assert (empty_sizer.translate.rBR             == np.zeros(6)).all()
    assert empty_sizer.translate.nPeople          == 0.; # Nnumber of people
    assert empty_sizer.translate.gpdpp            == 0.; # Gallons per day per person
    assert (empty_sizer.translate.loadShapeNorm   == np.zeros(24)).all(); # The normalized load shape
    assert empty_sizer.translate.supplyT_F        == 0.; # The supply temperature to the occupants
    assert empty_sizer.translate.incomingT_F      == 0.; # The incoming cold water temperature for the city
    assert empty_sizer.translate.storageT_F       == 0.; # The primary hot water storage temperature 
    assert empty_sizer.translate.compRuntime_hr   == 0.; # The runtime?
    assert empty_sizer.translate.metered          == 0; # If the building as individual metering on the apartment or not
    assert empty_sizer.translate.percentUseable   == 0; #The  percent of useable storage
    assert empty_sizer.translate.defrostFactor    == 1.; # The defrost factor. Derates the output power for defrost cycles.
    assert empty_sizer.translate.totalHWLoad_G    == 0;

    assert empty_sizer.translate.schematic        == ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
    assert empty_sizer.translate.TMonTemp_F       == 0.; # The temperature the swing tank turns on at
    assert empty_sizer.translate.nApt             == 0.; # The number of apartments
    assert empty_sizer.translate.Wapt             == 0.; # The recirculation loop losses in terms of W/apt
    assert empty_sizer.translate.TMRuntime_hr     == 0.; # The temperature maintenance minimum runtime.
    assert empty_sizer.translate.UAFudge          == 0.;
    assert empty_sizer.translate.offTime_hr       == 0.;
    assert empty_sizer.translate.Wapt             == 0.;
    assert empty_sizer.translate.returnT_F        == 0.;
    assert empty_sizer.translate.fdotRecirc_gpm   == 0.;
    
    with pytest.raises(Exception):
        assert empty_sizer.sizeSystem();
        assert empty_sizer.primarySystem.sizeVol_Cap();
        assert empty_sizer.primarySystem.sizePrimaryTankVolume(-10)
        assert empty_sizer.primarySystem.sizePrimaryTankVolume(100)

@pytest.mark.parametrize("arr, expected", [
    ([1, 2, 1, 1, -3, -4, 7, 8, 9, 10, -2, 1, -3, 5, 6, 7, -10], [4,10,12,16]), 
    ([1.3, 100.2, -500.5, 1e9, -1e-9, -5.5, 1,7,8,9,10, -1], [2,4,11])
])
def test_getPeakIndices(units_sizer, arr, expected):
    units_sizer.buildSystem();
    assert all(units_sizer.primarySystem.getPeakIndices(arr) == expected);

@pytest.mark.parametrize("Wapt, returnT, fdotRecirc", [
    (99.15126, 117, 45), 
    (58.75630029, 110, 8),
    (881.3445044, 40, 15)
])
def test_setRecircVars(units_sizer, Wapt, returnT, fdotRecirc):
    tol = 1e-4;
    units_sizer.translate.setRecircVars(0, returnT, fdotRecirc)
    assert abs(units_sizer.translate.Wapt - Wapt) < tol;
    units_sizer.translate.setRecircVars(Wapt, 0, fdotRecirc)   
    assert abs(units_sizer.translate.returnT_F - returnT) < tol;
    units_sizer.translate.setRecircVars(Wapt, returnT, 0)      
    assert abs(units_sizer.translate.fdotRecirc_gpm - fdotRecirc) < tol;
    
    with pytest.raises(Exception):
        assert units_sizer.translate.setRecircVars(0, returnT, 0)
        assert units_sizer.translate.setRecircVars(-Wapt, -returnT, 0)
        assert units_sizer.translate.setRecircVars(Wapt, units_sizer.supplyTemp, 0)
        assert units_sizer.translate.setRecircVars(Wapt, units_sizer.supplyTemp+10, 0)

# Full model and file tests!
def test_initByPeople(people_sizer):
    with pytest.raises(Exception):
        assert people_sizer.sizeSystem();
    people_sizer.buildSystem();
    people_sizer.sizeSystem();
    with pytest.raises(Exception):
        assert people_sizer.primarySystem.sizePrimaryTankVolume(-10)
        assert people_sizer.primarySystem.sizePrimaryTankVolume(100)
        
    people_sizer.writeToFile("tests/output/people_sizer.txt");
    assert file_regression("tests/ref/people_sizer.txt", 
                           "tests/output/people_sizer.txt");
    
def test_initByUnits(units_sizer):
    with pytest.raises(Exception):
        assert units_sizer.sizeSystem();
    units_sizer.buildSystem();
    units_sizer.sizeSystem();
    with pytest.raises(Exception):
        assert units_sizer.sizePrimaryTankVolume(-10)
        assert units_sizer.sizePrimaryTankVolume(100)
    units_sizer.writeToFile("tests/output/units_sizer.txt");
    assert file_regression("tests/ref/units_sizer.txt", 
                           "tests/output/units_sizer.txt");

@pytest.mark.parametrize("file1", [
    "tests/test_60UnitSwing.txt",
    "tests/test_200UnitTM.txt"
])
def test_hpwh_from_file(empty_sizer, file1):
    empty_sizer.initializeFromFile(file1);
    empty_sizer.buildSystem();
    empty_sizer.sizeSystem();
    empty_sizer.writeToFile("tests/output/"+os.path.basename(file1));
    
    assert file_regression("tests/ref/"+os.path.basename(file1), 
                           "tests/output/"+os.path.basename(file1));