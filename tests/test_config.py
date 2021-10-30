from src.polar_dep import Config

import yaml


def test_instantiate_config():
    with open("./tests/sequence_example.yaml", "rb") as f:
        cfg = Config(yaml.safe_load(f))

    assert type(cfg) == Config


def test_config_attrs():
    with open("./tests/sequence_example.yaml", "rb") as f:
        cfg = Config(yaml.safe_load(f))

    assert cfg.scan_num == 4
    assert cfg.domain_capture_num == 16
    assert cfg.roi == [500, 1000, 1000, 1500]
    assert cfg.intensity == 3000
    assert cfg.scan_time == 300
    assert cfg.angle == 3.15
    assert cfg.angle_start == 0
    assert cfg.angle_end == 10
    assert cfg.step == 10
    assert cfg.cn_info == None
    assert cfg.output_folder == "./outputs/output"
    assert cfg.log_folder == "./outputs/log"
