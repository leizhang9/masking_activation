import vxi11
import numpy as np
import random
import serial
import h5py
import os.path

# Name of the oscilloscope
osci_adress = "TCPIP::TUEISEC-AGILENT.sec.ei.tum.de::inst0::INSTR"
inputChannel = 1
nrTraces = 50
n_samples = 21753
formatData = "WORD"  # {ASCii | BINary | BYTE | WORD | FLOat}
uart = "/dev/ttyUSB0"


class HDF5File:
    """
    This class handles the HDF5 dataformat for storing the traces as a HDF5 File
    A created file can not exist on disk and the programm will terminate if file with the same name is found
    """

    def __init__(self, o_file, n_traces, n_samples, datatype, chunksize_traces=None):
        if os.path.isfile(o_file):
            print("File already exists, please remove or delete it!")
            quit()
        else:
            self.fileHandle = h5py.File(o_file, "x")
            self.FH_plainT = self.fileHandle.create_dataset("plaintext", (n_traces, 16), dtype=np.uint8)
            self.FH_cipherT = self.fileHandle.create_dataset("ciphertext", (n_traces, 16), dtype=np.uint8)
            self.FH_traces = self.fileHandle.create_dataset("traces", (n_traces, n_samples), dtype=datatype, chunks=chunksize_traces)

    def addPlaintext(self, plaintext, nrTrace):
        self.FH_plainT[nrTrace, :] = plaintext

    def addCiphertext(self, ciphertext, nrTrace):
        self.FH_cipherT[nrTrace, :] = ciphertext

    def addTrace(self, trace, nrTrace):
        self.FH_traces[nrTrace, :] = trace

    def addData(self, plaintext, ciphertext, trace, nrTrace):
        self.addPlaintext(plaintext, nrTrace)
        self.addCiphertext(ciphertext, nrTrace)
        self.addTrace(trace, nrTrace)

    def close(self):
        self.fileHandle.close()


def captureTrace(format):
    if format == "ASCii":
        data = instr.ask(":WAV:DATA?")
        data = np.array(list(map(float, data.split(",")[:-1])))  # List is needed to call the map object?!
    else:
        # Check the waveform byteorder
        if instr.ask(":WAVeform:BYTeorder?") != "LSBF":
            instr.write(":WAVeform:BYTeorder LSBFirst")

        instr.write(":WAV:DATA?")
        data = instr.read_raw(-1)

        # Strip the data from the first two bytes, which are always '#0' and the trailing newline
        # numpy from buffer : https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.frombuffer.html
        # The datatype has to converted to Big-Endian: '>h' =int16 with big endian
        if format == "BYTE":
            data = np.frombuffer(data[2:-1], dtype=np.int8)
        elif format == "WORD":
            # data = np.frombuffer(data[2:-1], dtype=np.dtype('>h'))
            data = np.frombuffer(data[2:-1], dtype=np.dtype(np.int16))

    return data


def setupOsci():

    # Set the channel to sample
    instr.write(":WAVEFORM:SOURCE CHANNEL{id}".format(id=inputChannel))
    print("The output format is set to {form}".format(form=instr.ask(":WAVeform:FORMat?")))
    instr.write(":WAVeform:FORMat {format}".format(format=formatData))
    instr.write(":ACQuire:COMPlete 100")

    # Set the timeframe to the left of the screen
    instr.write("TIMEBASE:REFERENCE LEFT")
    # We want a little offset to capture something right before the trigger event (offset has to be negative)
    instr.write("TIMEBASE:POSITION -20E-6")
    # Set the range that is displayed on the screen
    instr.write("TIMEBASE:RANGE 175E-6")


if __name__ == "__main__":
    # Check if the connection is working
    # We send the identity command and check if we receive the correct response
    instr = vxi11.Instrument(osci_adress)
    ser = serial.Serial(uart, baudrate=115200, timeout=None)
    try:
        response = instr.ask("*IDN?")
    except BaseException:
        # TO-DO: Find a not so general exception clause
        print("Connection to the oscilloscope could not be established!")
        print("Please check address!")
        print("Addresses look like this: TCPIP::TUEISEC-AGILENT.sec.ei.tum.de::inst0::INSTR")
        quit()

    setupOsci()
    # Create the used hdf5-File for storing the traces
    traces_file = HDF5File("/tmp/test.h5", nrTraces, n_samples, np.int16)

    for i in range(nrTraces):
        instr.write(":SINGle")

        # while instr.ask(":AER?") != 'askdhf':
        #    time.sleep(0.05)

        instr.write(":DIGitize CHANnel1")
        # print(instr.ask(":AER?"))
        while instr.ask("ADER?") != "+1":
            pass
        ciphertext_data = [random.randint(0, 255) for x in range(16)]
        ser.write(ciphertext_data)
        trace = captureTrace(formatData)
        plaintext_data = list(ser.read(16))
        traces_file.addData(plaintext_data, ciphertext_data, trace, i)

    traces_file.close()
