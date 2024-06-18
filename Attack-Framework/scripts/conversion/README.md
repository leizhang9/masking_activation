# Conversion to AISEC format

In order to use the [attacktool from AISEC](#LINK to gitlab), conversion scripts are needed.

### tueisec_to_aisec

Allows for conversion of the TUEISEC data format (hdf5 files) into the AISEC dataformat (sqlite database), c.f. the help

```buildoutcfg
python3 tueisec_to_aisec.py --help
```
for information  on the usage.

### ascad_to_aisec

Allows for conversion of the [ASCAD data](https://github.com/prouff/ASCAD_data) format (hdf5 files) into the AISEC 
dataformat (sqlite database). The ASCAD database can be used to evaluate machine learning techniques for side-channel 
analysis. However, for comparison classical SCA attacks can be evaluated using the AISEC attacktool.