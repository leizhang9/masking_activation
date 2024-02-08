set project "//media/ge36cig/7585AD1A4660599C/ma_zhang_masking_activation_functions_for_nns/project_lut/project_lut.xpr"
set tracked_module "/masked_lut_tb/dut/*"
set vcd_dir "/media/ge36cig/7585AD1A4660599C/ma_zhang_masking_activation_functions_for_nns/project_lut/tmp/vcd_syn"
set num_traces 4000
set input_file "input.txt"
set tb_name masked_lut_tb

# open project and update sources
open_project $project
update_compile_order -fileset sources_1

# make toggle testbench active
set_property top $tb_name [get_filesets sim_1]
set_property top_lib xil_defaultlib [get_filesets sim_1]
update_compile_order -fileset sim_1

# start simulator
# launch_simulation -mode behavioral
# -mode post-synthesis -type timing
launch_simulation -mode post-synthesis -type timing
set offset 0

for {set t 0} {$t < $num_traces} {incr t} {
  restart
  puts "$t of $num_traces"
  # open vcd file
  open_vcd $vcd_dir/dump_$t.vcd

  # signals that are logged
  log_vcd [get_objects -r filter {type == internal_signal} $tracked_module]

  run 100ns

  set fp [open $input_file r]
  set f_data [read $fp]
  set inputs [split $f_data "\n"]
  set tmp 0
  set current_offset 0
  foreach line $inputs {
    if {$current_offset < $offset} {
      incr current_offset
    } else {
      if {$tmp == 0} {
        set_value -radix bin /$tb_name/x $line
      }
      if {$tmp == 1} {
        set_value -radix bin /$tb_name/rnd $line
      }
      if {$tmp == 2} {
        break
      }
      incr tmp
    }
  }
  close $fp
  set offset [expr $offset + 2]
  run 100ns

  # close vcd file
  close_vcd
}

# close simulation and project
close_sim
close_project
