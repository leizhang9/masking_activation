import logging


class CameraUtilities:
    """
    Class that allows access to the camera, e.g. mounted on the Langer table. If other camera is present, this can also
    be used.
    """

    def __init__(self):
        # empty
        pass

    @staticmethod
    def make_screenshot(cam_id=0, file_path=None, frame_width=1e6):
        """
        Initializes a camera instance and takes a screenshot from the desired camera. If a file path is given, the image
        it stored. You can adjust the framewidth (i.e. resoluation) - per default the maximum resolution is enforced by
        setting the value to an insanely high value.

        inspired from
        https://stackoverflow.com/questions/11094481/capturing-a-single-image-from-my-webcam-in-java-or-python
        for a decent documentation see also
        https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture-get

        :param cam_id: ID of the camera. Default is 0, higher number in case you are using more than one.
        :param file_path: file path for saving the screenshot, if None screenshot is not saved
        :param frame_width: width
        :return: img: image
        """

        from cv2 import VideoCapture
        from cv2 import VideoWriter

        # initialize the camera
        cam = VideoCapture(cam_id)

        # assume a 3:4 format of the camera and adapt  height and width accordingly
        cam.set(CAP_PROP_FRAME_WIDTH, frame_width)
        cam.set(CAP_PROP_FRAME_HEIGHT, round(frame_width * 3 / 4))

        # take a screenshot
        s, img = cam.read()

        # check whether screenshot was successful
        if s:
            logging.info("Image from camera %s succesfully captured." % cam_id)
            if file_path is not None:
                # if reading succeeded, save the image
                imwrite(file_path, img)
                logging.info("Image written to %s." % file_path)

            # return the image for further use, e.g. savin in HDF5 files
            return img
        else:
            return None


def main():
    cam_utils = CameraUtilities()
    img = cam_utils.make_screenshot()

    # display the image for test purposes
    if img is not None:
        namedWindow("cam-test", WND_PROP_AUTOSIZE)
        imshow("cam-test", img)
        waitKey(0)
        destroyWindow("cam-test")
    else:
        logging.error("Screenshot was not successful.")


if __name__ == "__main__":
    main()
