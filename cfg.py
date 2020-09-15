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

# Declaring variables with a global scope

rhoCp = 8.353535
W_TO_BTUHR = 3.412142
W_TO_BTUMIN = W_TO_BTUHR/60.
W_TO_TONS = 0.000284345
TONS_TO_KBTUHR = 12.

pCompMinimumRunTime = 10./60.
tmCompMinimumRunTime  = 20./60.

def mixVolume(vol, hotT, coldT, outT):
    """
    Adjusts the volume of water such that the hotT water and outT water have the
    same amount of energy, meaning different volumes.

    Parameters
    ----------
    vol : float
        The reference volume to convert.
    hotT : float
        The hot water temperature used for mixing.
    coldT : float
        The cold water tempeature used for mixing.
    outT : float
        The out water temperature from mixing.

    Returns
    -------
    float
        Temperature adjusted volume.

    """
    fraction = (outT - coldT) / (hotT - coldT)

    return vol * fraction


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
