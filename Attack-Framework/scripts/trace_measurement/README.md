# Trace measurement

The main script to acquire measurements is `trace_measurement.py`. It should not be necessary to touch this script, but 
all changes are made by an external configuration file (for which `config_template.json` provides a maximum template)
and the communication with the target (for which `leakres_setkey.py` in conjunction with `target_STMF2.py` provides an) 
example.

### trace_measurement.py
There is a help for usage of the script
```
python3 trace_measurement.py -h
```

### Target control

You need to write the communication with the DUT in a class that inherits from `attack.targets.TargetBase` with the
following functions (an example is provided in `leakres_setkey.py`):

* `configure_device`: configures the device, e.g., by programming it. This is different for each hardware plattform you 
use
* `provide_info`: reads out information from the device such as serial number, device type, etc. If no read out is 
possible, you can of course pass a string manually. The returned string is written to the HDF5 file.
* `load_data`: loads data onto the device before starting a measurement (may be redundant, e.g., if data is loaded to
 trigger an event)
* `execute_trigger`: activates the trigger, additional data can be loaded or read back after the execution
* `read_data`: reads data from the device after the measurement (may be redundant, e.g., if data is automatically 
returned by triggered event)

The functions `configure_device`, `load_data`, `read_data`, `execute_trigger` are provided with the values specified in
the config, i.e., the config can be used to modify the functions or define cases. **#TODO**: Add an examples

Furthermore, the index of the measurement and the index of repetition can be provided, e.g., in order keep the input
 constant for several measurements or read back the output every 100 measurement.

> **IMPORTANT NOTE:** The outputs of `load_data`, `read_data` and `execute_trigger` have be a list of numpy arrays. 
Otherwise (e.g., if the output is a list of lists) the hand over of the data does work!

### configuration
The configuration file determines the setting of the target, scope and establishes a link between the recorded channels
and the datasets.

##### target
Here, the UART communication settings are defined, the path to the configuration file (e.g., `.elf` or `.bit`) as well
 as further information about the target are provided. The entry `description` allows to describe in some words what the 
 device does and what the experiment is all about. Make sure you write something meaningful here to know lateron what you did...

##### scope

Here, parameters for the scope are provided. Currently, the PicoScope 6000 and the Keysight 254A are supported. 

> **Important Note**: For PicoScope the channel numbers are {0,1,2,3} while for Keysight 254A, the channel numbers are
 {1,2,3,4}! Make sure to adapt the `config_template.json` accordingly if you work with the Keysight!

It is not necessarry to provide all fields and all channels, e.g., if you only want to measure on the first channel,
 you could leave the field `channel2`
and `channel3` empty or leave them out completely from your config file. Per default, a channel is deactivated. For further default settings have a look at the script `trace_measurement.py`.

##### msmt

Here, parameters related to the measurement are provided. `number of traces` specifies the number of measurement (e.g, 
with different inputs), while `repetitions` are the repetitions for a measurement with the same input, i.e., to enhance 
the SNR by averaging.

If measurements are taken too fast after another, it is a known issue that the oscilloscopes may miss a trigger event.
In order to mitigiate this problem, a `delay [s]` between consecutive measurements can be specified. Depending on the
duration of data transfer in between measurements, values from tens to hundreds of microseconds have been shown to be a
good trade-off.

Another known issue (at least with the PicoScope and also confirmed by other research groups) is that sometimes the 
first measurements of a measurement campaign are different/unsuitable for an attack. The reasons are yet to be 
determined, but heating up of device/measurement and/or transient effects of ADCs in the scopes could be the reason.
Anyhow, to avoid working on bad data, it is possible to specify a `number of dummy traces` that will be recorded 
before the actual measurements are taken. Alternatively, a `dummy time [s]` can be specified for which meaurement are 
taken. If `number of dummy traces > 0`, this parameter will be preferred over `dummy time [s]`.

> Currently, dummy measurements are only supported for the PicoScope as data retrieval differs on the scopes.
TODO: Evaluate for Keysight.

##### HDF5
This is a crucial part of the config as the datasets for storing as well as their relation to the outputs of the target
control function (see below) is specified

###### datasets

When creating the HDF5 (c.f. `attack.helper.utils.HDF5utils`), a dataset is created with the specified dimension, 
datatype and name if the `create` entry is true.

Example:

```
...
"k": {
    "datatype": "uint16",
    "dim": 16,
    "create": true
},
"ptxt": {
    "datatype": "uint16",
    "dim": 16,
    "create": true
},
"ctxt": {
    "datatype": "uint16",
    "dim": 16,
    "create": true
},
"mask": {
    "datatype": "uint16",
    "dim": 16,
    "create": true
},
"iv": {
    "datatype": "uint8",
    "dim": 8,
    "create": false
}
...
"samples":{
    "datatype": "uint8",
    "dim": null,
    "create": true,
    "record channel": 1
```
would create datasets `k`, `ctxt`, `ptxt` and `mask` with 16 entries of datatyoe `uint16` while `iv` would not be created.

All datasets that use `"dim": null` are interpreted as measurement datasets. Their datasize is set depending on the chosen
sampling rate and sampling duration.
 > **Attention:** The number `record channel` refers to the order used in the config file
and not that of the scope. I.e., while the scopes first channel may be `0`, the first channel in the config notation is alway
`1`!
###### saving
This part establishes the relation ship between the datasets and the outputs of the target control functions

> Example:
>
>```
>"input_data":{
>    "0": "ptxt",
>    "1": "k",
>    "2": "mask"
>},
>"trigger_data":{
>},
>"output_data":{
>    "0": "ctxt"
>}
>```
>In this case, the first output of `load_data` would be written to `ptxt`, the second to `k`, etc. The output from 
>`execute_trigger` is discarded. The output from `read_data` is written to `ctxt`.

Note that the names of the datasets, the number of outputs from the target control functions and the relationship for 
saving must be consistent and match each other.

> If there is an error when storing data, most likely you messed something up with the expected and the actual datatype.


##### table

If you are working with the Langer ICS105 x-y-z table, you can automatically scan over different positions, e.g., of a 
package or a die.
> **IMPORTANT:** When you are working with the table double-check any parameters in the config regarding positioning. 
In particular, `active` is set to `false`, if you do not want to move the table.
If you screw something up this may lead to severe damage of probes, table and target device!!!

The Langer ICS105 can move in all three directions by 52mm, i.e., make sure the centre of the target is placed more or 
less at `x=26mm, y=26mm` to have enough space in both direction in order to reach all points. 

To systematically move over different positions, the function `attack.helper.Meander.horMeander` generates a meander 
pattern, where you need to specify the first position by `"xOrigin [mm]`/`yOrigin [mm]`, the length in both dimensions 
by `xLen [mm]`/`yLen [mm]`, and the resolution, i.e., the distance between consecutive measurement points, by 
`resolution [mm]`.

> If you have any doubts about the use of the table turn to Lars Tebelmann or Michael Gruber.

##### experiment

Here you can specify entries that can be used to configure your target, e.g., in the functions `configure_device`, 
`load_data`, `read_data` or `execute_trigger`.