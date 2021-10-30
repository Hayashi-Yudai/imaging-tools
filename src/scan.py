from instr.CS505MU import CS505MU
from instr.Mark102 import Mark102

import numpy as np
import tifffile as tiff

if __name__ == "__main__":
    with Mark102(init_position=True) as stage, CS505MU(exposure_time=15000) as camera:
        pol = 51
        cn = 121
        stage.move(pol, axis=1)

        for angle in np.arange(cn - 1.5, cn + 1.5, 0.05):
            stage.move(angle, axis=2)
            stage.wait_while_busy()

            image = camera.multi_scan(4)
            tiff.imsave(
                f"./outputs/conbs_210629/test-scan/51deg/{angle:.2f}.tif", image
            )
