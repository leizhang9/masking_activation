import serial
import numpy as np
import time

import warnings
warnings.filterwarnings("ignore", message="overflow encountered ")

byteorder="little"

class wishbone:
	def __init__(self, port="/dev/ttyUSB1", baudrate=921600):
		self.uart = serial.Serial(port, baudrate, timeout=1, parity="E")
		self.uart.reset_input_buffer()
		self.uart.reset_output_buffer()
		print("The UART on " + self.uart.name + " is open.")
		print("The wishbone bus is ready.\n")

	def read(self,addr):
		cmd = 0x0
		cmd = cmd.to_bytes(1,byteorder)
		self.uart.write(cmd)
		addr = addr.to_bytes(4,byteorder)
		self.uart.write(addr)
		rbytes=self.uart.read(1)
		rbytes=self.uart.read(4)
		drd=int.from_bytes(rbytes,byteorder)
		return drd

	def write(self, addr, data):
		cmd = 0x1
		cmd = cmd.to_bytes(1,byteorder)
		self.uart.write(cmd)
		addr = addr.to_bytes(4,byteorder)
		self.uart.write(addr)
		data = data.to_bytes(4,byteorder)
		self.uart.write(data)
		rbytes=self.uart.read(1)

	def read_multiple_big(self, addr, lenwords):
		cmd = 0x2
		cmd = cmd.to_bytes(1, byteorder)
		self.uart.write(cmd)
		addr = addr.to_bytes(4, byteorder)
		self.uart.write(addr)
		l = lenwords.to_bytes(1, byteorder)
		self.uart.write(l)
		rbytes = self.uart.read(1)
		drd = []
		byteorder1="big"
		for i in range(lenwords):
			rbytes = self.uart.read(4)
			drd.append(int.from_bytes(rbytes, byteorder1))

		return drd
	
	def read_multiple(self, addr, lenwords):
		cmd = 0x2
		cmd = cmd.to_bytes(1, byteorder)
		self.uart.write(cmd)
		addr = addr.to_bytes(4, byteorder)
		self.uart.write(addr)
		l = lenwords.to_bytes(1, byteorder)
		self.uart.write(l)
		rbytes = self.uart.read(1)
		drd = []
		for i in range(lenwords):
			rbytes = self.uart.read(4)
			drd.append(int.from_bytes(rbytes, byteorder))

		return drd

	def write_multiple(self, addr, data):
		cmd = 0x3
		cmd = cmd.to_bytes(1, byteorder)
		self.uart.write(cmd)
		addr = addr.to_bytes(4, byteorder)
		self.uart.write(addr)
		l = len(data).to_bytes(1, byteorder)
		self.uart.write(l)
		for d in data:
			d = d.to_bytes(4, byteorder)
			self.uart.write(d)

		rbytes=self.uart.read(1)

	def close(self):
		self.uart.close()


if __name__ == '__main__':
	wb = wishbone("/dev/ttyUSB1")
	err = 0
	lut_size = 64
	n_tests = lut_size * lut_size
	test_addr = 0x40000000
	
	for x in range(0, lut_size):
		for x0 in range(0, lut_size):
			x1 = x - x0
			# print("x1: ", x1)
			x1 = x1 & (2**8 - 1)
			# print("x1 after converting: ", x1, "\n")
			test_data = [x1, x0]  # [input x1, input rnd]

			# Write data to the FPGA
			wb.write_multiple(test_addr, test_data)
			#print(f"Written data 0x{test_data[0]:X}, 0x{test_data[1]:X} to address 0x{test_addr:X}")

			# Read data back from the same address
			read_data = wb.read_multiple(test_addr, 2)
			#print(f"Read data 0x{read_data[0]:X} from address 0x{test_addr:X}")
			#print(f"Read data 0x{read_data[1]:X} from address 0x{test_addr:X}")
			if (test_data[0] == read_data[0]) and (test_data[1] == read_data[1]):
				print("Success: Read data matches written data.")
			else:
				print("Error: Read data does not match written data.")
			
			# start lut
			wb.write_multiple(0x20000000, [0x00000001])
			# print(f"start lut: Written data 0x01 to address 0x20000000")
			read_data = wb.read_multiple(0x10000000, 4)
			# print(f"Read data 0x{read_data[0]:X}, 0x{read_data[1]:X}, 0x{read_data[2]:X} from address 0x10000000")
			if read_data[0] != x:
				print(f"Error for x:{x} x0:{x0}.")
				err += 1

	# Close the UART connection
	wb.close()
	print("Successfull %.2f %%" %(100 * (n_tests - err) / n_tests))
