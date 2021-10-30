from PIL import Image
import numpy as np
import time


class MockCamera:
    def __init__(self, exposure_time: int):
        self.exposure_time = exposure_time

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return None

    def capture(self) -> Image:
        time.sleep(self.exposure_time * 1e-3)
        img = np.random.rand(2048, 2448) * 4096

        return Image.fromarray(img)

    def multi_scan(self, n: int) -> np.ndarray:
        time.sleep(self.exposure_time * 1e-3 * n)

        return (np.random.rand(2048, 2448) * 4096).astype("int16")
