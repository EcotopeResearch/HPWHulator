import pytest

import filecmp
import numpy as np
import os
import HPWHSizer


def file_regression(fileRef, fileResults):
        return filecmp.cmp(fileRef, fileResults);

@pytest.fixture
def empty_sizer():
    '''Returns a HPWHsizer instance initialized to zeros'''
    return HPWHSizer.HPWHSizer()

@pytest.fixture
def units_sizer():
    '''Returns a HPWHsizer instance initialized to with by units'''
    hpwh = HPWHSizer.HPWHSizer()
    hpwh.initByUnits( [50,50,50,50,0,0], [1.374,1.74,2.567,3.109,4.225,3.769], 20, 
                     [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                      0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                      0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038, 0.],
                    120, 50, 150, 16, 0, 0.8, .33, .9,'tempmaint')
    hpwh.setTMVars(16, 135, 100., 117., 0);
    return hpwh;

@pytest.fixture
def people_sizer():
    '''Returns a HPWHsizer instance initialized by nPeople inputs'''
    hpwh = HPWHSizer.HPWHSizer()

    hpwh.initByPeople(100, 22., 
                      [0.027,0.013,0.008,0.008,0.024,0.04 ,0.074,0.087,\
                       0.082,0.067,0.04 ,0.034, 0.034,0.029,0.027,0.029,\
                       0.035,0.04 ,0.048,0.051,0.055,0.059,0.051,0.038, 0.],
                    120, 50, 150., 18., 0, .8, .3,.9, "swingtank", 36);
    hpwh.setSwingVars(122., 100.);
    return hpwh;
# End of fixtures

# Start of tests
def test_default_initial_amount(empty_sizer):
    assert (empty_sizer.nBR             == np.zeros(6)).all()
    assert (empty_sizer.rBR             == np.zeros(6)).all()
    assert empty_sizer.nPeople          == 0.; # Nnumber of people
    assert empty_sizer.gpdpp            == 0.; # Gallons per day per person
    assert (empty_sizer.loadShapeNorm   == np.zeros(24)).all(); # The normalized load shape
    assert empty_sizer.supplyT          == 0.; # The supply temperature to the occupants
    assert empty_sizer.incomingT        == 0.; # The incoming cold water temperature for the city
    assert empty_sizer.storageT         == 0.; # The primary hot water storage temperature 
    assert empty_sizer.compRuntime      == 0.; # The runtime?
    assert empty_sizer.metered          == 0; # If the building as individual metering on the apartment or not
    assert empty_sizer.percentUseable   == 0; #The  percent of useable storage
    assert empty_sizer.aquaFract        == 0.; # The aquastat fraction
    assert empty_sizer.defrostFactor    == 1.; # The defrost factor. Derates the output power for defrost cycles.

    assert empty_sizer.schematic        == ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
    assert empty_sizer.swingOnT         == 0.; # The temperature the swing tank turns on at
    assert empty_sizer.nApt             == 0.; # The number of apartments
    assert empty_sizer.Wapt             == 0.; # The recirculation loop losses in terms of W/apt
    assert empty_sizer.TMRuntime        == 0.; # The temperature maintenance minimum runtime.
    assert empty_sizer.UAFudge          == 0.;
    assert empty_sizer.totalHWLoad      == 0.;
    assert empty_sizer.offTime          == 0.;
    assert empty_sizer.Wapt             == 0.;
    assert empty_sizer.returnT          == 0.;
    assert empty_sizer.fdotRecirc       == 0.;
    
    with pytest.raises(Exception):
        assert empty_sizer.sizeSystem();
        assert empty_sizer.sizePrimaryTankVolume(-10)
        assert empty_sizer.sizePrimaryTankVolume(100)

def test_people_sizer(people_sizer):
    with pytest.raises(Exception):
        assert people_sizer.sizePrimaryTankVolume(-10)
        assert people_sizer.sizePrimaryTankVolume(100)
    people_sizer.sizeSystem();
    people_sizer.writeOutput("tests/output/people_sizer.txt");
    assert file_regression("tests/ref/people_sizer.txt", 
                           "tests/output/people_sizer.txt");
def test_units_sizer(units_sizer):
    with pytest.raises(Exception):
        assert units_sizer.sizePrimaryTankVolume(-10)
        assert units_sizer.sizePrimaryTankVolume(100)
    units_sizer.sizeSystem();
    units_sizer.writeOutput("tests/output/units_sizer.txt");
    assert file_regression("tests/ref/units_sizer.txt", 
                           "tests/output/units_sizer.txt");

@pytest.mark.parametrize("hrs", [
    20, 16, 12
])
def test_primaryHeatHrs2kBTUHR(empty_sizer, hrs):
    assert empty_sizer.primaryHeatHrs2kBTUHR(hrs) == 0.;


@pytest.mark.parametrize("Wapt, returnT, fdotRecirc", [
    (99.15126, 117, 45), 
    (58.75630029, 110, 8),
    (881.3445044, 40, 15)
])
def test_setRecircVars(units_sizer, Wapt, returnT, fdotRecirc):
    tol = 1e-4;
    units_sizer.setRecircVars(0, returnT, fdotRecirc)
    assert abs(units_sizer.Wapt - Wapt) < tol;
    units_sizer.setRecircVars(Wapt, 0, fdotRecirc)   
    assert abs(units_sizer.returnT - returnT) < tol;
    units_sizer.setRecircVars(Wapt, returnT, 0)      
    assert abs(units_sizer.fdotRecirc - fdotRecirc) < tol;
    
    with pytest.raises(Exception):
        assert units_sizer.setRecircVars(0, returnT, 0)
        assert units_sizer.setRecircVars(-Wapt, -returnT, 0)
        assert units_sizer.setRecircVars(Wapt, units_sizer.supplyTemp, 0)
        assert units_sizer.setRecircVars(Wapt, units_sizer.supplyTemp+10, 0)


    
# File tests!
@pytest.mark.parametrize("file1", [
    "tests/test_60UnitSwing.txt",
    "tests/test_200UnitTM.txt"
])
def test_hpwh_from_file(empty_sizer, file1):
    empty_sizer.initializeFromFile(file1);
    empty_sizer.sizeSystem();
    empty_sizer.writeOutput("tests/output/"+os.path.basename(file1));
    
    assert file_regression("tests/ref/"+os.path.basename(file1), 
                           "tests/output/"+os.path.basename(file1));