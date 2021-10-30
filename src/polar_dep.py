"""
polarizerの角度依存性を測定するプログラム
"""
from instr.Mark102 import Mark102  # stage controller
from instr.CS505MU import CS505MU  # CCD camera

import numpy as np
from scipy.optimize import minimize
import tifffile as tiff
from tqdm import tqdm
import yaml


class Config:
    """
    Set measurement configuration
    """

    def __init__(self, config: dict):
        self.config = config

        # How many images the camera capture for crossed nicols scan and domain capturing
        self.scan_num: int = self.config["capture"]["scan_num"]
        self.domain_capture_num: int = self.config["capture"]["domain_capture_num"]

        # Camera settings
        self.roi: list[int] = self.config["camera"]["roi"]
        self.intensity: float = self.config["camera"]["intensity"]
        self.scan_time: float = self.config["camera"]["scan_time"]

        # How far the analyzer angle is from the crossed nicols position
        # when capturing domain images
        self.angle: float = self.config["analyzer"]["angle"]

        # Polarizer setting
        self.angle_start: float = self.config["polarizer"]["angle_start"]
        self.angle_end: float = self.config["polarizer"]["angle_end"]
        self.step: float = self.config["polarizer"]["step"]

        # Directory settings
        self.cn_info: str = self.config["cn_info"]
        self.output_folder: str = self.config["output_folder"]
        self.log_folder: str = self.config["log_folder"]


class Sequence:
    """
    Sequence runner
    """

    def __init__(self, config: Config, stage: Mark102, camera: CS505MU):
        self.config = config
        self.stage = stage
        self.camera = camera

        self.current_angle: float = self.config.angle_start
        self.cn_params: tuple[float] = None

    def multi_scan(self, n: int, adjust=False) -> np.ndarray:
        image_avg = np.array(self.camera.capture(dispose=True)).astype("float64")

        if adjust and self.camera.exposure_time < 2000:
            n *= 4
        elif adjust and self.camera.exposure_time < 4000:
            n *= 2

        for i in tqdm(range(1, n)):
            image = np.array(self.camera.capture(dispose=False))
            image_avg = (image_avg * i + image) / (i + 1)

        return image_avg.astype("int16")

    def crossed_nicols_scan(self) -> tuple[float]:
        start = -self.current_angle + 173 - 2
        start = start if start > 0 else 360 + start
        end = start + 4

        angles = np.arange(start, end, 0.2)
        average_intensities = []

        self.camera.change_exposure_time(self.config.scan_time)

        for angle in angles:
            self.stage.move(angle, axis=2)
            self.stage.wait_while_busy()

            print(f"analyzer angle: {angle:.2f}")
            image_avg = self.multi_scan(self.config.scan_num)
            roi = self.config.roi
            image_roi = image_avg[roi[0] : roi[1], roi[2] : roi[3]]

            average_intensities.append(np.mean(image_roi))

        average_intensities = np.array(average_intensities)

        def error(x):
            def fitting_func(x):
                return x[0] * (angles - x[1]) ** 2 + x[2]

            return np.sum((average_intensities - fitting_func(x)) ** 2)

        slope, cn_angle, cn_intensity = minimize(
            error, [1, start + 2, min(average_intensities)]
        ).x

        log = {
            "angles": angles.tolist(),
            "intensities": average_intensities.tolist(),
            "fit_params": [float(slope), float(cn_angle), float(cn_intensity)],
        }
        with open(
            f"{self.config.log_folder}/{self.current_angle}_scan_info.yaml", "w"
        ) as f:
            yaml.dump(log, f)

        return slope, cn_angle, cn_intensity

    def adjust_exposure_time(self):
        """
        Adjust the exposure time of the camera so that the average intensity
        in the ROI of the image becomes the target intensity specified in the
        configuration file.

        If the calculated exposure time is longer than 15 seconds, which is the
        maximum exposure time of the camera, set it to 15 seconds.
        """
        target_intensity = self.config.intensity

        base_intensity = self.cn_params[0] * self.config.angle ** 2 + self.cn_params[2]
        exposure_time = target_intensity // base_intensity * self.config.scan_time
        exposure_time = min(15000, exposure_time)
        self.camera.change_exposure_time(exposure_time)

    def capture_domain(self) -> None:
        self.adjust_exposure_time()

        self.stage.move(self.cn_params[1] + self.config.angle, axis=2)
        self.stage.wait_while_busy()

        save_folder = self.config.output_folder

        image_pos = self.multi_scan(self.config.domain_capture_num, adjust=True)

        tiff.imsave(f"{save_folder}/pos_{self.current_angle}.tif", image_pos)

        negative_angle = self.cn_params[1] - self.config.angle
        negative_angle = negative_angle if negative_angle > 0 else 360 + negative_angle
        self.stage.move(negative_angle, axis=2)
        self.stage.wait_while_busy()

        image_neg = self.multi_scan(self.config.domain_capture_num, adjust=True)

        tiff.imsave(f"{save_folder}/neg_{self.current_angle}.tif", image_neg)

    def read_from_file(self) -> list[float]:
        with open(
            f"{self.config.cn_info}/{self.current_angle}_scan_info.yaml", "rb"
        ) as f:
            data = yaml.safe_load(f)

        return data["fit_params"]

    def cn_capture(self) -> None:
        self.adjust_exposure_time()

        self.stage.move(self.cn_params[1], axis=2)
        self.stage.wait_while_busy()

        cn_image = self.multi_scan(self.config.domain_capture_num, adjust=True)

        tiff.imsave(
            f"{self.config.output_folder}/cn_{self.current_angle}.tif", cn_image
        )

    def run(self) -> None:
        scan_exposure_time = self.config.scan_time

        while self.current_angle <= self.config.angle_end:
            print(f"Measuring {self.current_angle} deg.")
            self.stage.move(self.current_angle, axis=1)
            self.stage.wait_while_busy()

            # Crossed Nicols scan
            if self.config.cn_info is None:
                print("Start crossed nicols scan")
                self.cn_params = self.crossed_nicols_scan()
                print("Done.\n")
            else:
                self.cn_params = self.read_from_file()

            self.cn_capture()

            # Domain measurement
            print("Start domain capturing")
            self.capture_domain()
            print("Done. \n")

            self.current_angle += self.config.step


if __name__ == "__main__":
    config_file = "./outputs/conbs_210702/sequence_10k.yaml"

    with open(config_file, "rb") as f:
        config = Config(yaml.safe_load(f))

    with Mark102(init_position=True) as stage, CS505MU(exposure_time=100) as camera:
        sequence = Sequence(config, stage=stage, camera=camera)
        sequence.run()
