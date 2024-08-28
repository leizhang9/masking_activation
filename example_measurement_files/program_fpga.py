import serial
from attack.targets.CW305 import CW305
import numpy as np
import argparse
import time
parser = argparse.ArgumentParser(description='Argument parser')
parser.add_argument('-f', '--filename', type=str, help='File to program FPGA (*.bit)', required=True)

args = parser.parse_args()

cw = CW305.CW305()
cw.con(bsfile=args.filename, force=True)

# clock fpga

# f_out = (12MHz * N) / (M * P1)
# for 100MHz: N = 25, M = 3, P1 = 1
#
# Register 4: Divider M (1 Byte)
cw.pll.cdce906write(4, 3)

# Register 5: Divider N (lower 8 bit)
cw.pll.cdce906write(5, 25)

# Register 6: Divider N and some other configs
# Bit 7: PLL1 fvco selection
# Bit 6: PLL2 fvco selection
# Bit 5: PLL3 fvco selection
# Bit 4-1: upper 4 bit of divider N
# Bit 0: PLL2 Ref Dev M
cw.pll.cdce906write(6, 0)

# Register 10: PLL selection for divider P1 and some other config that is not needed
# Bit 7-5: PLL selection -> 010 connect PLL2 with P1
# Bit 4-0: Set to default values 0
cw.pll.cdce906write(10, 64)

# Register 14: divider P1
# Bit 7: Reserved
# Bit 6-0: value
cw.pll.cdce906write(14, 1)

# Register 20: Output config Y1 (provide PLL2 frequency to FPGA Pin N13)
# Bit 7: Reserved
# Bit 6: invert output
# Bit 5-4: Slew rate -> 11 (default)
# Bit 3: Enable/Disable output  -> 1 (enable)
# Bit 2-0: Output divider slection -> 001 (P1 = output divider of PLL2)
cw.pll.cdce906write(20, 57)


# Register 16: divider P3
# Bit 7: Reserved
# Bit 6-0: value
cw.pll.cdce906write(16, 1)

# Register 23: Output config Y1 (provide PLL2 frequency to FPGA Pin E12)
# Bit 7: Reserved
# Bit 6: invert output
# Bit 5-4: Slew rate -> 11 (default)
# Bit 3: Enable/Disable output  -> 1 (enable)
# Bit 2-0: Output divider slection -> 011 (P3 = output divider of PLL2)
cw.pll.cdce906write(23, 59)

# clock sma x6

# Register 11: PLL selection for divider P2 + P3 and some other config that is not needed
# Bit 7-6: input signal source -> 00
# Bit 5-3: P3 PLL Selection -> 010
# Bit 2-0: P2 PLL Selection -> 010
cw.pll.cdce906write(11, 18)

# Register 15: divider P2
# Bit 7: Reserved
# Bit 6-0: value
cw.pll.cdce906write(15, 1)

# Register 19: Output config Y0 (provide PLL2 frequency to X6 SMA)
# Bit 7: Reserved
# Bit 6: invert output
# Bit 5-4: Slew rate -> 11 (default)
# Bit 3: Enable/Disable output  -> 1 (enable)
# Bit 2-0: Output divider slection -> 010 (P2 = output divider of PLL2)
cw.pll.cdce906write(19, 58)


cw.dis()
cw.close()
