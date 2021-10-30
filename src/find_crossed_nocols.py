import numpy as np
import time

from instr.Mark102 import Mark102
from instr.SHOT702 import SHOT702
from instr.CS505MU import CS505MU


def suggested_optimum(pol_angle) -> tuple[int]:
    # Read yaml
    return 167, 310


def optimize(
    suggestion_angle: int, stage, camera, threshold: float = 0.5
) -> tuple[int, bool]:
    min_intensity = np.mean(np.array(camera.capture()))
    tmp_angle = suggestion_angle
    updated = False

    tmp_angle += 1
    stage.move(tmp_angle, axis=2)
    time.sleep(0.5)
    p_intensity = np.mean(np.array(camera.capture()))

    if min_intensity < p_intensity - threshold:
        direction = -1
        stage.move(tmp_angle - 1, axis=2)
    elif p_intensity < min_intensity - threshold:
        direction = 1
        min_intensity = p_intensity
    else:
        direction = 0

    while direction != 0:
        tmp_angle += direction
        stage.move(tmp_angle, axis=2)
        time.sleep(0.5)
        intensity_tmp = np.mean(np.array(camera.capture()))

        if intensity_tmp > min_intensity - threshold:
            direction = 0
        else:
            min_intensity = intensity_tmp
            updated = True

    return tmp_angle, updated


def find_optimum_angle(
    pol_angle: int, stage: Mark102, qwp: SHOT702, camera: CS505MU
) -> tuple[float]:
    stage.move(pol_angle, axis=1)
    time.sleep(0.5)
    ana_tmp, qwp_tmp = suggested_optimum(pol_angle)

    updated = True
    while updated:
        # Analyzer の最適化
        ana_tmp, updated = optimize(ana_tmp, stage, camera)

        # Quarter wave plate の最適化
        qwp_tmp, updated = optimize(qwp_tmp, qwp, camera)

    return ana_tmp, qwp_tmp


if __name__ == "__main__":
    with Mark102() as stage, SHOT702() as qwp, CS505MU(exposure_time=300) as camera:
        # Polarizer angle = 6 deg. の時を考える
        ana_angle, qwp_angle = find_optimum_angle(6, stage, qwp, camera)
