import serial
import numpy as np
import time

import warnings
warnings.filterwarnings("ignore", message="overflow encountered ")

byteorder="little"

class wishbone:
	def __init__(self, port="/dev/ttyUSB1", baudrate=9216):
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
	rng = np.random.default_rng()

	err = 0
	n_tests = 100
	n_data = 8
	for i in range(0, n_tests):
		data = rng.integers(0, 2**32-1, n_data, dtype=np.uint32)

		write_data = []
		dr = []
		for i in range(0, len(data)):
			write_data.append(data[i].item())
			wb.write_multiple(0x50000000 + i, [write_data[i]])

		data = rng.integers(0, 2**32-1, n_data, dtype=np.uint32)

		write_data = []
		dr = []
		for i in range(0, len(data)):
			write_data.append(data[i].item())
			wb.write_multiple(0x60000000 + i, [write_data[i]])
			dr.append(wb.read_multiple_big(0x60000000 + i, 1)[0])

		if not np.allclose(write_data, dr):
			err += 1

		d = wb.read_multiple(0x40000000, 2)
		wb.write(0x40000000, n_data)
		d = wb.read_multiple(0x40000000, 1)
		wb.write(0x40000001, n_data)
		d = wb.read_multiple(0x40000000, 2)

		if not np.allclose([n_data, n_data], d):
			err += 1

		data = np.array([4, 88, 10, 98, 1, 0, 0, 0], dtype=np.uint32)
		write_data = []
		for i in range(0, len(data)):
			write_data.append(data[i].item())
		wb.write_multiple(0x40000002, write_data)
		d = wb.read_multiple(0x40000002, 8)
		print(data)
		print(d)

		wb.write(0x70000000, 1)
		wb.write(0x80000000, 1)

		
		wb.write(0x20000000, 1)

		dr = []
		for i in range(0, n_data):
			dr.append(wb.read_multiple_big(0x60000000 + i, 1)[0])
		for i in dr:
			print(i & 0x000000ff)
			print((i >> 8) & 0x000000ff)
			print((i >> 16) & 0x000000ff)
			print((i >> 24) & 0x000000ff)
			print("###################")

		wb.write(0x20000000, 1)


		dr = []
		for i in range(0, n_data):
			dr.append(wb.read_multiple_big(0x60000000 + i, 1)[0])
		for i in dr:
			print(i & 0x000000ff)
			print((i >> 8) & 0x000000ff)
			print((i >> 16) & 0x000000ff)
			print((i >> 24) & 0x000000ff)
			print("###################")


	print("Successfull %.2f %%" %(100 * (n_tests - err) / n_tests))
