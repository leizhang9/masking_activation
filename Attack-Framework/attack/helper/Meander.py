import numpy as np


class Meander:
    @staticmethod
    def horMeander(xOrigin, yOrigin, xLen, yLen, resolution):

        pointsX = np.empty([1, 0])
        pointsY = np.empty([1, 0])

        stepsX = int(xLen / resolution) + 1
        stepsY = int(yLen / resolution) + 1

        xRow = [xOrigin + i * resolution for i in range(0, stepsX)]

        for i in range(0, stepsY):
            if not (i % 2):
                pointsX = np.append(pointsX, xRow)
                tmp = np.ones([1, stepsX]) * resolution * i + yOrigin
                # print np.shape(tmp)
                pointsY = np.append(pointsY, tmp)
                # print 'A'
            else:
                pointsX = np.append(pointsX, xRow[::-1])
                tmp = np.ones([1, stepsX]) * resolution * i + yOrigin
                # print np.shape(tmp)
                pointsY = np.append(pointsY, tmp)
                # print 'B'

        points = np.vstack((pointsX, pointsY))
        return points

    @staticmethod
    def verMeander(xOrigin, yOrigin, xLen, yLen, resolution):
        pointsX = np.empty([1, 0])
        pointsY = np.empty([1, 0])

        stepsX = int(xLen / resolution) + 1
        stepsY = int(yLen / resolution) + 1

        yRow = [yOrigin + i * resolution for i in range(0, stepsY)]

        for i in range(0, stepsX):
            if not (i % 2):
                pointsY = np.append(pointsY, yRow)
                tmp = np.ones([1, stepsY]) * resolution * i + xOrigin
                # print np.shape(tmp)
                pointsX = np.append(pointsX, tmp)
                # print 'A'
            else:
                pointsY = np.append(pointsY, yRow[::-1])
                tmp = np.ones([1, stepsY]) * resolution * i + xOrigin
                # print np.shape(tmp)
                pointsX = np.append(pointsX, tmp)
                # print 'B'

        points = np.vstack((pointsX, pointsY))
        return points


def main():
    from Meander import Meander
    import matplotlib.pyplot as plt

    points = Meander.horMeander(1.0, 1.0, 1.0, 1.0, 0.1)
    # points = Meander.verMeander(1.0,1.0,1.0,1.0,0.1)
    plt.plot(points[0, :], points[1, :])
    plt.show()


if __name__ == "__main__":
    main()
