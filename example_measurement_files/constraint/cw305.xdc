# Clock signal
set_property PACKAGE_PIN N13 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]

#Reset signal (over switch)
set_property PACKAGE_PIN R1 [get_ports rst]
set_property IOSTANDARD LVCMOS33 [get_ports rst]

#USB-RS232 Interface
set_property PACKAGE_PIN A15 [get_ports uart_rx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_rx]
set_property PACKAGE_PIN C12 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

#Status LEDs
set_property PACKAGE_PIN T2 [get_ports led_idle]
set_property IOSTANDARD LVCMOS33 [get_ports led_idle]

#Trigger
set_property PACKAGE_PIN T14 [get_ports trigger]
set_property IOSTANDARD LVCMOS33 [get_ports trigger]

create_clock -period 10.000 -waveform {0.000 5.000} [get_ports clk]
