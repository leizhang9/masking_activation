import xmlrpc.client
import logging

_logger = logging.getLogger(__name__)

# https://github.com/NativeDesign/python-tmcl
# port to nativce tmcl


class Koordinatentisch:
    def __init__(self, ip="localhost", port=30000):
        self.ip = ip
        self.port = port
        self.client = None

        # Axis numbers.
        self.xAxisNumber = 0  # X-axis
        self.yAxisNumber = 1  # Y-axis
        self.zAxisNumber = 2  # Z-axis
        self.rAxisNumber = 3  # R-axis (rotation axis)

        # units
        self.oneMeter = 1.0
        self.oneCentiMeter = self.oneMeter / 100.0
        self.oneMilliMeter = self.oneCentiMeter / 10.0
        self.oneMicroMeter = self.oneMilliMeter / 10.0

        # Create the XMLRPC client and connect it to the XMLRPC server.
        # Use your PCs IP address or use the hostname of your PC for the variable 'ip' below.
        # ip  # IP or hostname
        # port = "30000" # ChipScan menu 'Settings' -> 'Set RPC port...' and displayed in status bar.
        self.client = xmlrpc.client.ServerProxy("http://%s:%d" % (self.ip, self.port))
        _logger.info("XMLRPC client created successfully at ip=" + ip + " and port=" + str(port))

    def getZ(self):
        """
        returns the current z position in millimeters
        """
        return self.client.GetScannerPosition(self.zAxisNumber) * 1000

    def getPos(self):
        """
        returns the position tuple (x,y,z,r)
        """
        x_coordinate = self.client.GetScannerPosition(self.xAxisNumber) * 1000
        y_coordinate = self.client.GetScannerPosition(self.yAxisNumber) * 1000
        z_coordinate = self.client.GetScannerPosition(self.zAxisNumber) * 1000
        r_coordinate = self.client.GetScannerPosition(self.rAxisNumber)

        return (x_coordinate, y_coordinate, z_coordinate, r_coordinate)

    def moveAbsPos(self, x=None, y=None, z=None, r=None):
        """
        drives absolut to the position x,y,z,r (all are optional) in mm
        """
        # get current z-position
        z_cur = self.getZ()

        if z is not None and z > z_cur:
            # if target position is higher than current z-position, move in z-direction
            # first in order to prevent damaging the probe by lateral movements
            self.client.MoveScannerAbsolute(self.zAxisNumber, z * self.oneMilliMeter, False)
        if x is not None:
            self.client.MoveScannerAbsolute(self.xAxisNumber, x * self.oneMilliMeter, False)
        if y is not None:
            self.client.MoveScannerAbsolute(self.yAxisNumber, y * self.oneMilliMeter, False)
        if z is not None and z < z_cur:
            # if target position is lower than current z-position, move in x and y-direction
            # first in order to prevent damaging the probe by lateral movements
            self.client.MoveScannerAbsolute(self.zAxisNumber, z * self.oneMilliMeter, False)
        # if r is not  None: self.client.MoveScannerAbsolute(self.rAxisNumber, r*oneMilliMeter, False)

    def moveRelPos(self, x, y, z=None, r=None):
        """
        drives relativ to the current position x,y,z,r (z,r are optional) in mm
        """

        # get current height
        z_cur = self.getZ()
        if z + z_cur > 0:
            # if range would be exceeded by movement, move back to 0
            z = -z_cur
            _logger.warning("Relative movement of result in exceeded z-range: return to 0.")

        self.client.MoveScannerRelative(self.xAxisNumber, x * self.oneMilliMeter, False)
        self.client.MoveScannerRelative(self.yAxisNumber, y * self.oneMilliMeter, False)
        if z is not None:
            self.client.MoveScannerRelative(self.zAxisNumber, z * self.oneMilliMeter, False)
        # if r is not  None: self.client.MoveScannerRelative(self.rAxisNumber, r*oneMilliMeter, False)

    def calibratePos(self):
        """
        calibrate all axis
        """
        print("!!!WARNING!!! z axis needs to be lifted type YES")
        response = input()
        if response != "YES":
            return
        self.client.CalibrateScanner()

        print("Calibration finished")

    def isCalibrated(self):
        """
        check if langer table is calibrated returns True if so
        """

        return self.client.IsScannerCalibrated()

    def getLimitsAxis(self, axis):
        """
        returns the aboslut maximums of each axis input the axis like x y z r
        """

        if axis == "x":
            Min = self.client.GetScannerPositionMinimum(self.xAxisNumber)
            Max = self.client.GetScannerPositionMaximum(self.xAxisNumber)
        elif axis == "y":
            Min = self.client.GetScannerPositionMinimum(self.yAxisNumber)
            Max = self.client.GetScannerPositionMaximum(self.yAxisNumber)
        elif axis == "z":
            Min = self.client.GetScannerPositionMinimum(self.zAxisNumber)
            Max = self.client.GetScannerPositionMaximum(self.zAxisNumber)
        elif axis == "r":
            Min = self.client.GetScannerPositionMinimum(self.rAxisNumber)
            Max = self.client.GetScannerPositionMaximum(self.rAxisNumber)
        else:
            print("No vaid axis")
            raise NameError("Oops!  That was no valid axis.  Try again...")

        return (Min * 1e3, Max * 1e3)

    def moveIdlePos(self):
        """
        drive to the idle position dont move z,r
        """
        print("!!!WARNING!!! x-y plane needs to be cleared type YES")
        response = input()
        if response != "YES":
            return
        self.moveAbsPos(0.0, 0.0)

    def moveCenterPosXY(self):
        print("!!!WARNING!!! x-y plane needs to be cleared type YES")
        response = input()
        if response != "YES":
            return
        self.moveAbsPos(-52.5 / 2.0, -52.5 / 2.0)

    def HasScannerLimitTrigger(self):
        """
        check if the 'depth test' of the langer table is activated.
        returns True if so
        """
        return self.client.HasScannerLimitTrigger()

    def IsScannerLimitTriggered(self):
        """
        checks if the 'depth test' of the langer table is triggered,
        i.e. the probe is touching s.t. in z-direction.
        returns True if so
        """
        return self.client.IsScannerLimitTriggered()


def main():
    print("koordinatentisch")
    t = Koordinatentisch("localhost")
    print(t.getPos())


if __name__ == "__main__":
    main()
