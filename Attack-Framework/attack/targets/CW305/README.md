# CW305

This is a collection of the minimal requirementes to run the [CW305 target board](https://wiki.newae.com/CW305_Artix_FPGA_Target).
The files contained in this collection were extracted from the [chipwhisperer software](https://github.com/newaetech/chipwhisperer) 
from the `devel` branch and commit `3946ee08bd12ffdf6a6176712ee529521906daba`.

Make sure you follow the developments of chipwhisperer on github in order to get fixes, etc.


### Changelog
The main differences compared to the chipwhisper version are:
* it can be run using `python3` (most changes were obtained by simply running `2to3`, some additional changes such as 
type casts were added manually)
* there is an additional option in the `pll_cdce906.py` file, which allows to directly set the PLL from the EEPROM and 
not from the API
* references to the CWLite or CW1200 are removed as only the CW305 is of interest
* the serial number of the board is passed when configuring the bitstream

### File correspondance

| original file | moved to | 
| -------- | -------- |  
| `software/chipwhisperer/hardware/naeusb/fpga.py`   | `fpga.py`   |
| `software/chipwhisperer/hardware/naeusb/naeusb.py`   | `naeusb.py`   |
| `software/chipwhisperer/hardware/naeusb/pll_cdce906.py`   | `pll_cdce906.py`   |
| `software/chipwhisperer/hardware/firmware/cw035.py`   | import removed by hardcoding in `naeusb.py`  |
| `software/chipwhisperer/common/utils/util.py` | `util.py` |
| `software/chipwhisperer/common/utils/parameter.py` | `parameter.py` |
| `software/chipwhisperer/capture/targets/CW305.py` | `CW305.py` |
| `software/chipwhisperer/capture/targets/_base.py` | `_base.py` |

### Diff from Attack-Framework
You can get an entire diff by running it on the first commit (where the files had just been copied)
```buildoutcfg
git diff 6597cd4ad98485c438a67b802bb548e615efa3b6 6597cd4ad98485c438a67b802bb548e615efa3b6
```
on the `cw305_add` branch of the Attack-Framework.