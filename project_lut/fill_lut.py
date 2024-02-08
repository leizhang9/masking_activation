# generate vhdl codes for lut.vhd, data width = 8
for i in range(256):
    binary_string = format(i, '08b')  # Convert integer to 8-bit binary string
    print(f'\t\t\twhen "{binary_string}" => output <= "{binary_string}";')
