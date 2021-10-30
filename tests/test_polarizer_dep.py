from src.polar_dep import Config, Sequence

import numpy as np
from PIL import Image
import yaml
import pytest


class MockCamera:
    def __init__(self, *args, **kwargs):
        self.counter = 1  # For testing the number of for-loop
        self.exposure_time: float = None

    def capture(self, *args, **kwargs):
        image = np.ones((2448, 2048)) * self.counter
        self.counter += 1

        return Image.fromarray(image)

    def change_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time


class MockStage:
    def __init__(self, *args, **kwargs):
        return None

    def wait_while_busy(self, *args, **kwargs):
        return None

    def move(self, *args, **kwargs):
        return None


@pytest.fixture(scope="module")
def seq():
    with open("./tests/sequence_example.yaml", "rb") as f:
        cfg = Config(yaml.safe_load(f))

    return Sequence(cfg, stage=MockStage(), camera=MockCamera())


def test_multi_scan(seq):
    multi_scanned_image = seq.multi_scan(n=10)

    assert type(multi_scanned_image) == np.ndarray
    assert multi_scanned_image.dtype == "int16"
    assert np.all(multi_scanned_image == 5)


def test_cn_scan(seq, tmp_path):
    log_dir = tmp_path / "log"
    output_dir = tmp_path / "output"
    log_dir.mkdir()
    output_dir.mkdir()
    seq.config.output_folder = output_dir
    seq.config.log_folder = log_dir

    output = seq.crossed_nicols_scan()

    assert type(output) == tuple
    assert seq.camera.exposure_time == seq.config.scan_time


def test_domain_capture(seq, tmp_path):
    log_dir = tmp_path / "log"
    output_dir = tmp_path / "output"
    log_dir.mkdir()
    output_dir.mkdir()

    seq.config.output_folder = output_dir
    seq.config.log_folder = log_dir
    seq.cn_params = (0, 0, 100)

    seq.capture_domain()

    assert seq.camera.exposure_time != seq.config.scan_time


# TODO: Remove side-effect of seq.config.cn_info = "tests" on tests_sequence_run()
def test_read_from_file(seq):
    seq.config.cn_info = "tests"
    seq.current_angle = 0

    assert seq.read_from_file() == [4, 173, 523]

    seq.config.cn_info = None


def test_cn_capture(seq, tmp_path):
    log_dir = tmp_path / "log"
    output_dir = tmp_path / "output"
    log_dir.mkdir()
    output_dir.mkdir()

    seq.config.output_folder = output_dir
    seq.config.log_folder = log_dir
    seq.cn_params = (0, 0, 100)

    seq.cn_capture()

    assert seq.camera.exposure_time != seq.config.scan_time


def test_sequence_run(seq, tmp_path):
    log_dir = tmp_path / "log"
    output_dir = tmp_path / "output"
    log_dir.mkdir()
    output_dir.mkdir()

    seq.config.output_folder = output_dir
    seq.config.log_folder = log_dir

    seq.run()

    assert seq.camera.exposure_time != seq.config.scan_time
    assert seq.current_angle == seq.config.angle_end + seq.config.step
