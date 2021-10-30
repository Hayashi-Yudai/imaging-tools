from instr.Mark102 import Mark102  # polarizer and analyzer controller
from instr.SHOT702 import SHOT702  # quarter wave plate controller
from instr.CS505MU import CS505MU  # CCD camera

import numpy as np
import time


def adjust_stage(average_intensity, camera, stage, angle) -> tuple[float]:
    """
    1 dimensional の Newton 法で解く
    """
    angle_now = angle

    while True:
        tmp = angle_now

        stage.move(angle_now + 0.1, axis=2)
        stage.wait_while_busy()
        intensity1 = np.mean(camera.multi_scan(4))
        stage.move(angle_now + 0.2, axis=2)
        stage.wait_while_busy()
        intensity2 = np.mean(camera.multi_scan(4))

        deriv1 = (intensity1 - average_intensity) / 0.1
        deriv2 = (intensity2 - 2 * intensity1 + average_intensity) / 0.1 ** 2

        angle_now -= deriv1 / deriv2
        print("New angle: ", angle_now)

        stage.move(angle_now, axis=2)
        stage.wait_while_busy()
        print("New intensity: ", np.mean(camera.multi_scan(4)))

        if abs(tmp - angle_now) < 0.05:
            break

    intensity = np.mean(camera.multi_scan(4))

    return intensity, angle_now


if __name__ == "__main__":
    with Mark102(init_position=False) as stage, SHOT702(
        init_position=False
    ) as qwp, CS505MU(exposure_time=300) as camera:
        stage.move(6, axis=1)
        stage.wait_while_busy()

        # analyzer を動かしつつ波長板を動かして最小となる場所を探す
        # polarizer = 6 deg のときで実装してみる

        suggest_analyzer = 178
        suggest_qwp = 44

        diff = 100
        threshold = 1

        stage.move(suggest_analyzer, axis=2)
        stage.wait_while_busy()

        qwp.move(suggest_qwp)
        qwp.wait_while_busy()

        average_intensity = np.mean(np.array(camera.capture()))
        print("Average intensity", average_intensity)
        time.sleep(3)

        while diff > threshold:
            tmp = average_intensity

            average_intensity, suggest_analyzer = adjust_stage(
                average_intensity, camera, stage, suggest_analyzer
            )
            average_intensity, suggest_qwp = adjust_stage(
                average_intensity, camera, qwp, suggest_qwp
            )

            print(f"Average intensity: {average_intensity}")

            diff = tmp - average_intensity

        print("Finished!")
