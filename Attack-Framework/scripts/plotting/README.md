# Plot tools
This folder is a collection of tools for plotting various SCA-related plots. 

### General usage 
The plot scripts differ in their purpose, but show some similiraties regarding their usage.
##### Generic parameters
Some parameters should be generic across scripts (make sure to comly when adding new scripts):
* `-i` (required): input file
* `-o` (optional): output file if `--save-plot` option is used. 
   If `--save-plot` is set, but `-o`is not given, the default file name is the same as the input file with image file extension
* `-c` (optional): `.json` config file for configuring the appearance of the plots, e.g. font sizes, ratios, etc. For 
  details see below (section `plt_config.json`)
* `--save-plot` (optional): use this paraemeter if you want to save the figure, otherwise plots are only displayed

##### Annotating plots
For 1D-plots, annotations can be added:
* `-a` (optional): allows for adding annotations to the plots provided in a `.csv`.
  * `horizontal`: horizontal markers with `|---` and `---|` delimiters, e.g. to mark the region of interest in a trace.
    Each line is a triple of `(LABEL,xmin,xmax)`, where `xmin` and `xmax` are given in SI units (seconds/Hertz).    
    As horizontal mode is the default for annotations, the first line specifying the annotation type is optional.
      ```csv
    # [TYPE] horizontal,,
    $\qquad RoI$,0,0.0000028
    $other\;RoI$,0.000003360 ,0.00000611
    ```
  * `vertical`: vertical dashed bars for annotations, e.g. operations of clock cycles. The Labels are also added vertically.
    Each line is a triple of `(LABEL,x,ymin,ymax)` and the vertical bar is put a `x` from `ymin` to `ymax`.
     ```
     # [TYPE] vertical,,,
    l.42,-0.000005890,0.75,0.85 
    ```
  * `colormarks`: horizontal colorbar with scalable opacity, e.g. to highlight parts of an algorithm in a trace.
    Each line is a triple of `(COLOR,xmin,xmax,ymin,ymax,alpha)` and the colorbar is put a `xmin` to `xmax`and from `ymin` to `ymax`, with a opacitiy of `alpha`.
    Default values are `ymin=0`, `ymax=MAXIMUM y-value` and `alpha=0.1`, in case only three colums are provided.
    ```
    # [TYPE] colormark,,,,
    red,-0.000005890,-0.00000239,0.74,1,0.1
    grey,-0.00000239,-0.000001890,0.74,1,0.1
    ```
  
`LABEL` can make of the LaTeX synthax by using inline math mode.

##### Limiting plotting to time/frequency ranges
For time-vs.-somehing plots there some conventions worth noticing:
* `--time-start` (optional): Start time in seconds (relative to trigger, i.e. negative values possible)
* `--time-stop` (optional): Stop time in seconds (relative to trigger, i.e. negative values possible)  
* `time_scale` (optional): scale of the x-axis can selected to be either second-based (s, ms, us, ns) or in clockcycles 

For further usage details please refer to respective documentation in the arguement parser section of the scripts or run
`python <SCRIPT> -h`, which provides the usage information.

### Configuring your plots - `plt_config.json`
This file contains a dictionary with the [custom configuration of matplotlib via the rcParams](https://matplotlib.org/3.2.1/tutorials/introductory/customizing.html).
You can specify the backend (`Agg`, `pgf`, etc.) as well as the output format of the plot (entry `savefig.format`), font size, legend and axis appearances and the like.

The default backend (if the `backend` entry is not set) is `pgf` to make figures in a nice LaTeX-like way.
[`Pgf` uses `xelatex`as default texsystem](), so make sure you have it installed or change it to `lualatex` or `pdflatex` using the entry `pgf.texsystem`.

Further information (and explanation of the rcParams options) can be found in the matplotlib docs:
* [Customizing Matplotlib with style sheets and rcParams](https://matplotlib.org/3.2.1/tutorials/introductory/customizing.html)
* [Typesetting With XeLaTeX/LuaLaTeX](https://matplotlib.org/tutorials/text/pgf.html)

##### Troubleshooting
Not all backends can handle LaTeX input.
If you are encountering problems with the LaTeX fonts, disable use of Tex by setting `text.usetex: false` to check 
whether is really something Tex-related.
If need be, install required packages.

Per default, if `--save-plot` is not set, `text.usetex: false` is used.