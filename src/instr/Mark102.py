import pyvisa
import time

from instr.interfaces.stage import stages


class Mark102(stages):
    """
    Sigma koki 2-stage controller
    """

    def __init__(self, gpib: int = 8, init_position: bool = False):
        self.gpib = gpib

        resource_manager = pyvisa.ResourceManager()
        try:
            self.instrument = resource_manager.open_resource(f"GPIB0::{gpib}::INSTR")
        except Exception:
            raise ValueError("Instrument is not found")

        if init_position:
            self.initialize()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.instrument.close()

    def initialize(self):
        print("Initialize")
        self.wait_while_busy()
        self.instrument.query("H:W")  # Initialize positions

    def wait_while_busy(self):
        # If the state is "B"(Busy), wait for 1 second
        while self.instrument.query("!:") == "B\r\n":
            time.sleep(1)

    def move(self, angle: int, axis: int):
        query = f"A:{int(axis)}+P{int(angle * 1000 * 4 / 10)}"

        self.instrument.query(query)
        self.instrument.query("G:")  # Move
        self.wait_while_busy()


if __name__ == "__main__":
    with Mark102(init_position=False) as stage:
        # stage.move(6, axis=1)
        stage.move(177.2 - 3.15, axis=2)

        # 116.7 and 115.6  cn = 116.15
