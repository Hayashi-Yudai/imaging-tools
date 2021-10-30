from serial import Serial
import time

from interfaces.stage import stages


class SHOT702(stages):
    """
    Sigma koki 2-axis stage controller.

    This stage controller has RS232C interface to connect to the computer
    """

    def __init__(self, port="COM3", init_position=False):
        self.instrument = Serial(port, 38400)
        if init_position:
            self.initialize()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.instrument.close()

    def initialize(self):
        self.wait_while_busy()
        self.instrument.write(b"H:W\r\n")
        time.sleep(0.1)
        self.instrument.read_all()

    def wait_while_busy(self):
        while True:
            self.instrument.write(b"!:\r\n")
            time.sleep(0.1)
            status = self.instrument.read_all()

            if status != b"B\r\n" and status != b"NG\r\n":
                break

    def _wait_response(self):
        while True:
            status = self.instrument.read_all()

            if status == b"OK\r\n":
                break
            elif status == b"NG\r\n":
                raise RuntimeError("Invalid command!")
            else:
                time.sleep(0.2)

    def write_query(self, query):
        self.instrument.write(query)
        self._wait_response()

    def move(self, angle, axis=1):
        query = f"A:1+P{int(angle * 1000 * 4 / 10)}\r\n".encode()

        self.wait_while_busy()

        self.write_query(query)
        self.write_query(b"G:\r\n")


if __name__ == "__main__":
    with SHOT702(init_position=True) as stage:
        stage.move(45)
