from instr.CS505MU import CS505MU
import pyvisa as visa
import tifffile as tiff

import threading
import time


def capture(camera, image):
    image.append(camera.capture())


def read_temperature(lakeshore, exposure_time, temp):
    time.sleep(exposure_time / 2)

    temperature = lakeshore.query("KRDG?A").replace("\r\n", "")
    temp.append(temperature)


if __name__ == "__main__":
    path = "./image_test/"
    exposure_time = 500  # ms

    rm = visa.ResourceManager("@py")

    with rm.open_resources("GPIB0::13::instr") as lakeshore, CS505MU(
        exposure_time=exposure_time
    ) as camera:

        print("Start captureing")

        while True:
            image_list = []
            temp_list = []
            t1 = threading.Thread(target=capture, args=(camera, image_list))
            t2 = threading.Thread(
                target=read_temperature, args=(lakeshore, exposure_time, temp_list)
            )

            t1.start()
            t2.start()

            t1.join()
            t2.join()

            tiff.imsave(f"{path}/{temp_list[0].tif}", image_list[0])
            break
