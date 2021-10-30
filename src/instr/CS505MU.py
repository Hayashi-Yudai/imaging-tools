from PIL import Image
import os
import time
import numpy as np
from tqdm import tqdm

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK


class CS505MU:
    def __init__(
        self,
        dll_path: str = "../../dlls",  # relative path to the dll files
        bits: str = "64_lib",  # dll folder name
        camera_number: int = 0,
        exposure_time: int = 100,  # milliseconds
    ):
        """
        CCD camera of Thorlabs

        This program assumes the structure of dll files is
        like the following,

        dlls
        ├── 32_lib
        │   └── Copy 32-bit native libraries here
        └── 64_lib
            ├── thorlabs_tsi_LUT.dll
            ├── thorlabs_tsi_camera_sdk.dll
            ├── thorlabs_tsi_color_processing.dll
            ├── thorlabs_tsi_color_processing_vector_avx2.dll
            ├── thorlabs_tsi_cs_camera_device.dll
            ...
        """
        self.configure_path(dll_path, bits)

        self.sdk = TLCameraSDK()

        camera_list = self.sdk.discover_available_cameras()
        if len(camera_list) > 0:
            self.camera = self.sdk.open_camera(camera_list[camera_number])
        else:
            raise ValueError("No camera is found!")

        # if zero, camera will self-trigger infinitely, allowing a continuous vide feed
        self.camera.frames_per_trigger_zero_for_unlimited = 1
        self.camera.arm(2)
        self.exposure_time = exposure_time
        self.camera.exposure_time_us = int(exposure_time * 1e3)

        # self.sleeping_time = sleeping_time
        self.bit_depth = self.camera.bit_depth

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.camera.dispose()
        self.sdk.dispose()

    @staticmethod
    def configure_path(dll_path, bits):
        relative_path_to_dlls = dll_path + os.sep + bits
        absolute_path_to_file_directory = os.path.dirname(os.path.abspath(__file__))
        absolute_path_to_dlls = os.path.abspath(
            absolute_path_to_file_directory + os.sep + relative_path_to_dlls
        )
        os.environ["PATH"] = absolute_path_to_dlls + os.pathsep + os.environ["PATH"]
        try:
            # Python 3.8 introduces a new method to specify dll directory
            os.add_dll_directory(absolute_path_to_dlls)
        except AttributeError:
            pass

    def capture(self, dispose=False) -> Image:
        counter = 0
        while True:
            time.sleep(self.exposure_time / 1000)
            self.camera.issue_software_trigger()
            frame = self.get_pending_frame_or_null()
            if frame is not None:
                if dispose:
                    if counter > 1:
                        break
                    counter += 1
                else:
                    break

        image = Image.fromarray(frame.image_buffer)

        return image

    def multi_scan(self, n: int) -> np.ndarray:
        image_avg = np.array(self.capture(dispose=True)).astype("float64")

        for i in tqdm(range(1, n)):
            image = np.array(self.capture(dispose=False))
            image_avg = (image_avg * i + image) / (i + 1)

        return image_avg.astype("int16")

    def get_pending_frame_or_null(self):
        return self.camera.get_pending_frame_or_null()

    def change_exposure_time(self, exposure_time):
        """Change the exposure time of the CCD camera
        exposure time: millisecond
        """
        self.camera.exposure_time_us = int(exposure_time * 1e3)
        self.exposure_time = int(exposure_time)


if __name__ == "__main__":
    frames = []
    with CS505MU(exposure_time=1) as camera:
        start = time.time()
        for i in range(100):
            image = camera.capture(dispose=False)
            frames.append(image)
        print((time.time() - start) / 100)
