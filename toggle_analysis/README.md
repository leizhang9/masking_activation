# Howto

* Open a terminal an change with `cd` into the `tofu` directory
* Execute `make venv` to generate the venv
* Execute `source tofu_python/bin/activate` to activate the venv
* Copy the `settings.json` file into the directory where the `vcd` dumps are located
* Execute `python3 parse.py -s <directory of vcds>/settings.json`
* Execute `python3 synthesize.py -s <directory of vcds>/settings.json`
* Change in the terminal into the `t_test` directory
* Execute `python3 ttest.py -i <directory of vcds>/traces.h5 -p 2 --seg-size 10000`
* To see the result execute `python3 evaluation.py -i <directory of vcds>/traces_result.hdf5`
