import pytest

import filecmp
import numpy as np
import HPHWSizer 


def file_regression(fileRef, fileResults):
        return filecmp.cmp(fileRef, fileResults);

@pytest.fixture
def empty_sizer():
    '''Returns a HPWHsizer instance initialized to zeros'''
    return HPWHSizer()

def test_default_initial_amount(empty_sizer):
    assert (empty_sizer.nBR  == np.zeros(6)).all()
    assert (empty_sizer.rBR  == np.zeros(6)).all()
    assert empty_sizer.nPeople    == 0.; # Nnumber of people
    assert empty_sizer.gpdpp      == 0.; # Gallons per day per person
    assert (empty_sizer.loadShapeNorm  == np.zeros(24)).all(); # The normalized load shape
    assert empty_sizer.supplyT    == 0.; # The supply temperature to the occupants
    assert empty_sizer.incomingT  == 0.; # The incoming cold water temperature for the city
    assert empty_sizer.storageT   == 0.; # The primary hot water storage temperature 
    assert empty_sizer.compRuntime  == 0.; # The runtime?
    assert empty_sizer.metered    == 0; # If the building as individual metering on the apartment or not
    assert empty_sizer.percentUseable == 0; #The  percent of useable storage
    
    assert empty_sizer.schematic  == ""; # The schematic for sizing maybe just primary maybe with temperature maintenance.
    assert empty_sizer.swingOnT   == 0.; # The temperature the swing tank turns on at
    assert empty_sizer.nApt       == 0.; # The number of apartments
    assert empty_sizer.Wapt       == 0.; # The recirculation loop losses in terms of W/apt
    assert empty_sizer.TMRuntime  == 0.; # The temperature maintenance minimum runtime.
    
    
@pytest.mark.parametrize("file1", [
    "test_60UnitSwing.txt",
    "test_200UnitSwing.txt"
])
def test_hpwh_from_file(empty_sizer, file1):
    empty_sizer.initializeFromFile(file1);
    empty_sizer.sizeSystem();
    empty_sizer.writeOutput("/output/"+file1);
    
    assert file_regression("/ref/"+file1, "/output/"+file1);


