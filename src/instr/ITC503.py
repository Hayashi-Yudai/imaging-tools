from serial import Serial
import time


class ITC503:
    """
    Oxford instruments temperature controller
    """

    def __init__(self, port: int = "COM3"):
        self.instrument = Serial(port, 9600)

    def __enter__(self):
        self._set_remote()
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self._set_local()
        self.instrument.close()

    def _set_local(self, locked: bool = True):
        if locked:
            # Default state
            self.instrument.write(b"C0\r\n")
        else:
            self.instrument.write(b"C2\r\n")

        time.sleep(0.5)
        self.instrument.read_all()

    def _set_remote(self, locked: bool = True):
        if locked:
            # Front panel disabled
            self.instrument.write(b"C1\r\n")
        else:
            # Front panel active
            self.instrument.write(b"C3\r\n")

        time.sleep(0.5)
        self.instrument.read_all()

    def set_heater_channel(self, ch: int):
        self.instrument.write(f"H{ch}\r\n".encode())
        time.sleep(0.5)
        self.instrument.read_all()

    def set_heater_gasflow_mode(
        self, heater_mode: str = "manual", gas_mode: str = "manual"
    ):
        if heater_mode == "manual" and gas_mode == "manual":
            self.instrument.write(b"A0\r\n")
        elif heater_mode == "auto" and gas_mode == "manual":
            self.instrument.write(b"A1\r\n")
        elif heater_mode == "manual" and gas_mode == "auto":
            self.instrument.write(b"A2\r\n")
        elif heater_mode == "auto" and gas_mode == "auto":
            self.instrument.write(b"A3\r\n")
        else:
            print("Invalid argument. Mode should be 'manual' or 'auto'")

        time.sleep(0.5)
        self.instrument.read_all()

    def set_temperature(self, target_temp: float):
        self.instrument.write(f"T{target_temp}\r\n".encode())

        time.sleep(0.5)
        self.instrument.read_all()

    def read_temperature(self, ch: int):
        self.instrument.write(f"R{ch}\r\n".encode())
        time.sleep(0.5)
        temp = self.instrument.read_all().decode()

        return temp[1:].replace("\r", "")


if __name__ == "__main__":
    with ITC503() as controller:
        # controller.set_heater_gasflow_mode(heater_mode="auto")
        controller.set_temperature(20)
