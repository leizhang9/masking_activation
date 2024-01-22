# General configuration
## Sources and directories
set SRC_DIR                 "sources"
set ADD_DIR                 "sources/addition"

set SIM_DIR                 "simulation"
set VIVADO_MAJOR_VERSION    "2020"

set ORIGIN_DIR              "."

# Defaults from argument parser
set PROJECT_NAME            "Masked_Compare"
set TARGET_BOARD            "cw305"
set CREATEBITSTREAM         false


#################################################
# Argument parser
#################################################
variable script_file
set script_file             "setup_project.tcl"

# Help information for this script
proc print_help {} {
  variable script_file
  puts "\nDescription:"
  puts "Script for setting up a the project for the TPU with a TDC"
  puts "The script contains commands for creating a project, filesets, runs,"
  puts "adding/importing sources and setting properties on various objects.\n"
  puts "Syntax:"
  puts "$script_file"
  puts "$script_file -tclargs \[--board <name>\]"
  puts "$script_file -tclargs \[--create-bitstream\]"
  puts "$script_file -tclargs \[--help\]\n"
  puts "Usage:"
  puts "Name                   Description"
  puts "-------------------------------------------------------------------------"
  puts "\[--board <name>\]       Create project either for Basys3 or CW305 board,"
  puts "                       by specifiying name ('basys3'/'cw305'). Default is"
  puts "                       'basys3'. If using the CW305 board, do not forget"
  puts "                       to specify active low reset in rtl/framework_pkg.vhd!\n"
  puts "\[--create-bitstream\]    Runs synthesis, implementation and bitstream"
  puts "                       generation. Default is to only set up the project.\n"
  puts "\[--project-name\]        Name of the project folder. Default: 'tdc_and_tpu'\n"
  puts "\[--help\]               Print help information for this script"
  puts "-------------------------------------------------------------------------\n"
  exit 0
}

# Parse the argument values to the respective variables
if { $::argc > 0 } {
  for {set i 0} {$i < $::argc} {incr i} {
    set option [string trim [lindex $::argv $i]]
    switch -regexp -- $option {
      "--board"                 { incr i; set TARGET_BOARD [lindex $::argv $i] }
      "--create-bitstream"      { set CREATEBITSTREAM true }
      "--project-name"          { incr i; set PROJECT_NAME [lindex $::argv $i] }
      "--help"                  { print_help }
      default {
        if { [regexp {^-} $option] } {
          puts "ERROR: Unknown option '$option' specified, please type '$script_file -tclargs --help' for usage info.\n"
          return 1
        }
      }
    }
  }
}

# Select the correct device and constraint for the different target boards
if {[string match "basys3" ${TARGET_BOARD}]} {
    set DEVICE                  "xc7a35tcpg236-1"
    set BOARD_CONSTR            "basys3"
} elseif {[string match "cw305" ${TARGET_BOARD}]} {
    set DEVICE                  "xc7a100tftg256-2"
    set BOARD_CONSTR            "CW305"
} else {
    puts "ERROR: Unknown target board '${TARGET_BOARD}'. Only 'basys3' and 'cw305' are supported"
    exit 1
}

#################################################
# Create the project
#################################################
# force to overwrite old project
create_project $PROJECT_NAME ./$PROJECT_NAME/ -part $DEVICE -force
set proj_dir [get_property directory [current_project]]

# Some standard properties
set tmp [current_project]
set_property -name "default_lib"        -value "xil_defaultlib" -objects $tmp
set_property -name "enable_vhdl_2008"   -value "1"              -objects $tmp
set_property -name "part"               -value $DEVICE          -objects $tmp
set_property -name "simulator_language" -value "Mixed"          -objects $tmp
set_property -name "target_language"    -value "VHDL"           -objects $tmp


#################################################
# Add sources to list
#################################################
set obj [get_filesets sources_1]

set files [glob $ORIGIN_DIR/$SRC_DIR/*.vhd]
append files " " [glob $ORIGIN_DIR/$ADD_DIR/*.vhd]
add_files -norecurse -fileset $obj $files

# Adding the files to project and set them to VHDL-2008
if {[string equal [get_filesets -quiet sources_1] ""]} {
    create_fileset -srcset sources_1
}
set source_set [get_filesets sources_1]

add_files -norecurse -fileset $source_set $files
set_property file_type {VHDL 2008} [get_files -of_objects $source_set]


# #################################################
# # Set simulation set
# #################################################
if {[string equal [get_filesets -quiet sim_1] ""]} {
   create_fileset -simset sim_1
}
set sim_set [get_filesets sim_1]

set files [glob "$ORIGIN_DIR/$SIM_DIR/*.vhd"]

add_files -norecurse -fileset $sim_set $files
set_property file_type {VHDL 2008} [get_files -of_objects $sim_set]

# Set Top module
# set_property top wrapper_mlp_fsm [current_fileset]
# update_compile_order -fileset sources_1
set_property top masked_cmp_trn_tb [get_filesets sim_1]
set_property top_lib xil_defaultlib [get_filesets sim_1]
update_compile_order -fileset sim_1

#################################################
# Default synthesis parameters
#################################################
if {[string equal [get_runs -quiet synth_1] ""]} {
    create_run  -name               synth_1 \
                -part               $DEVICE \
                -flow               "Vivado Synthesis $VIVADO_MAJOR_VERSION" \
                -strategy           "Vivado Synthesis Defaults" \
                -report_strategy    {No Reports} \
                -constrset          constrs_1
} else {
    set_property strategy   "Vivado Synthesis Defaults" [get_runs synth_1]
    set_property flow       "Vivado Synthesis $VIVADO_MAJOR_VERSION"     [get_runs synth_1]
    set_property STEPS.SYNTH_DESIGN.ARGS.FSM_EXTRACTION off [get_runs synth_1]
}

#################################################
# Default implementation parameters
#################################################
if {[string equal [get_runs -quiet impl_1] ""]} {
    create_run  -name               impl_1 \
                -part               $DEVICE \
                -flow               "Vivado Implementation $VIVADO_MAJOR_VERSION" \
                -strategy           "Vivado Implementation Defaults" \
                -report_strategy    {No Reports} \
                -constrset          constrs_1 \
                -parent_run         synth_1
} else {
   set_property strategy   "Vivado Implementation Defaults"                     [get_runs impl_1]
   set_property flow       "Vivado Implementation $VIVADO_MAJOR_VERSION"        [get_runs impl_1]
}


#################################################
# Synthesis, Implementation and Bitstream
#################################################
if { $CREATEBITSTREAM } {
    update_compile_order -fileset sources_1
    update_compile_order -fileset sim_1
    update_compile_order -fileset sim_1
    set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]
    set_property STEPS.SYNTH_DESIGN.ARGS.FSM_EXTRACTION off [get_runs synth_1]
    set_property STEPS.SYNTH_DESIGN.ARGS.KEEP_EQUIVALENT_REGISTERS true [get_runs synth_1]
    set_property STEPS.SYNTH_DESIGN.ARGS.RESOURCE_SHARING off [get_runs synth_1]
    set_property STEPS.SYNTH_DESIGN.ARGS.NO_LC true [get_runs synth_1]
    set_property STEPS.OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
    set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
    set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
    update_compile_order -fileset sources_1
    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1
}
puts "Successful project setup"
