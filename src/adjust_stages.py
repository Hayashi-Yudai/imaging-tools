from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from PIL import Image, ImageTk
import tifffile as tiff
import tkinter as tk
import tkinter.font as tkFont
import threading
import queue

from instr.Mark102 import Mark102
from instr.CS505MU import CS505MU
from instr.SHOT702 import SHOT702

# Mock object for development
# from instr_mock.mock_camera import MockCamera as CS505MU
# from instr_mock.mock_stage import MockStage as Mark102
# from instr_mock.mock_qwp import MockQWP as SHOT702

# TODO: 現在のステージ位置を取得して表示する。angle_now = 0 で初期化しなくていいように
# TODO: カメラのライブビューも組み込む


class CameraThread(threading.Thread):
    def __init__(self, camera):
        super(CameraThread, self).__init__()

        self.camera = camera
        self.image_queue = queue.Queue(maxsize=2)
        self.angle_now = 0

        # Stop the thread while stages is moving
        self.is_moving = False
        self.event = threading.Event()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            if self.is_moving:
                self.event.wait()
                self.event.clear()
            try:
                image = np.array(self.camera.capture()).astype("int16")
                self.image_queue.put_nowait(image)
            except queue.Full:
                pass
            except Exception as error:
                print(f"Encountered error: {error}")
                break

        print("Image acquisition has stopped")


class ImageCalcThread(threading.Thread):
    def __init__(self, camera):
        super(ImageCalcThread, self).__init__()

        self.camera = camera
        self.angle_now = 0
        self.angle_queue = queue.Queue(maxsize=4)
        self.intensity_queue = queue.Queue(maxsize=4)

        # Stop the thread while stages is moving
        self.is_moving = False
        self.event = threading.Event()

        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            if self.is_moving:
                self.event.wait()
                self.event.clear()
            try:
                if self.angle_now is not None:
                    intensity = np.mean(camera.capture())
                    self.angle_queue.put_nowait(self.angle_now)
                    self.intensity_queue.put_nowait(intensity)
            except queue.Full:
                pass
            except Exception as error:
                print(f"Encountered error: {error}")
                break

        print("Thread stopped")


class CameraFrame(tk.Frame):
    def __init__(self, thread):
        super(CameraFrame, self).__init__()

        self.thread = thread
        self.canvas = tk.Canvas(self, width=1800, height=1500)
        self.canvas.grid(column=0, row=0)

        self._get_data()

    def _get_data(self):
        global image
        try:
            self.image = self.thread.image_queue.get_nowait()
            self.image = Image.fromarray(self.image)

            image = ImageTk.PhotoImage(master=self.canvas, image=self.image)
            self.canvas.create_image(0, 0, image=image, anchor="nw")
        except queue.Empty:
            pass

        self.after(exposure_time, self._get_data)


class GraphFrame(tk.Frame):
    def __init__(self, thread):
        super(GraphFrame, self).__init__()

        self.thread = thread
        self.fig = plt.figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.log = defaultdict(int)
        self.angles = []
        self.intensities = []
        self.angle_now = 0

        self.graph = FigureCanvasTkAgg(self.fig, master=self)
        self.graph.draw()
        self.graph.get_tk_widget().pack()

        self._get_data()

    def _get_data(self):
        try:
            angle = self.thread.angle_queue.get_nowait()
            intensity = self.thread.intensity_queue.get_nowait()
            self._data_compaction(angle, intensity)
            self._sort_data()

            self.ax.cla()
            self.ax.plot(self.angles, self.intensities, "ro-")
            self.ax.axvline(self.angle_now, c="g", ls="dashed", lw=1)
            self.ax.tick_params(axis="x", labelrotation=45)
            self.fig.tight_layout()
        except queue.Empty:
            pass

        self.graph.draw()
        self.after(exposure_time, self._get_data)

    def _data_compaction(self, angle, intensity):
        if angle not in self.angles:
            self.angles.append(angle)
            self.intensities.append(intensity)
        else:
            num_angle = self.log[angle]
            idx = self.angles.index(angle)

            self.intensities[idx] = (self.intensities[idx] * num_angle + intensity) / (
                num_angle + 1
            )

        self.log[angle] += 1

    def _sort_data(self):
        idx = np.argsort(np.array(self.angles))
        self.angles = np.array(self.angles)[idx].tolist()
        self.intensities = np.array(self.intensities)[idx].tolist()

    def reset_graph(self):
        self.angles = []
        self.intensities = []


class Popup:
    def __init__(self):
        win = tk.Toplevel()
        self.font = tkFont.Font(family="Arial", size=32)

        info = tk.Label(win, text="Output file is saved", font=self.font)
        info.grid(row=0, column=0, sticky=tk.NSEW, padx=100, pady=50)
        btn = tk.Button(win, text="OK", command=win.destroy, font=self.font)
        btn.grid(row=1, column=0, sticky=tk.NSEW, padx=200, pady=50)


class App:
    def __init__(self, camera, stage, qwp):
        self.thread = ImageCalcThread(camera)

        self.root = tk.Tk()
        self.fig = plt.figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.camera = camera
        self.stage = stage
        self.qwp = qwp

        self.font = tkFont.Font(family="Arial", size=24)
        self._configure()

    def _configure(self):
        stage_area = self._stage_frame()
        self.graph_area = GraphFrame(thread=self.thread)
        scan_area = self._image_capture_frame()

        graph_reset_button = tk.Button(
            self.root,
            text="Reset graph",
            command=self.reset_graph,
            font=self.font,
        )

        stage_area.grid(column=0, row=0)
        graph_reset_button.grid(column=0, row=1)
        scan_area.grid(column=0, row=2)
        self.graph_area.grid(column=1, row=0, rowspan=3)

    def _stage_frame(self):
        frame = tk.Frame(self.root)
        pol_text = tk.Label(frame, text="Polarizer: ", font=self.font)
        ana_text = tk.Label(frame, text="Analyzer: ", font=self.font)
        qwp_text = tk.Label(frame, text="QWP: ", font=self.font)
        exposure_text = tk.Label(frame, text="Exposure: ", font=self.font)

        pol_setter = tk.Entry(frame, width=20, font=self.font)
        ana_setter = tk.Entry(frame, width=20, font=self.font)
        qwp_setter = tk.Entry(frame, width=20, font=self.font)
        exposure_setter = tk.Entry(frame, width=5, font=self.font)

        pol_but = tk.Button(
            frame,
            text="Set",
            command=lambda: self.move_stage(float(pol_setter.get()), axis=1),
            font=self.font,
        )
        ana_but = tk.Button(
            frame,
            text="Set",
            command=lambda: self.move_stage(float(ana_setter.get()), axis=2),
            font=self.font,
        )
        qwp_but = tk.Button(
            frame,
            text="Set",
            command=lambda: self.move_qwp(float(qwp_setter.get())),
            font=self.font,
        )
        exposure_btn = tk.Button(
            frame,
            text="Set",
            command=lambda: self.change_exposure_time(int(exposure_setter.get())),
            font=self.font,
        )

        pol_text.grid(column=0, row=0)
        pol_setter.grid(column=1, row=0)
        pol_but.grid(column=2, row=0)
        ana_text.grid(column=0, row=1)
        ana_setter.grid(column=1, row=1)
        ana_but.grid(column=2, row=1)
        qwp_text.grid(column=0, row=2)
        qwp_setter.grid(column=1, row=2)
        qwp_but.grid(column=2, row=2)
        exposure_text.grid(column=0, row=3)
        exposure_setter.grid(column=1, row=3)
        exposure_btn.grid(column=2, row=3)

        return frame

    def _image_capture_frame(self):
        frame = tk.Frame(self.root)
        self.path_entry = tk.Entry(frame, width=25, font=self.font)
        self.scan_num_entry = tk.Entry(frame, width=3, font=self.font)
        scan_btn = tk.Button(
            frame, text="Start", font=self.font, command=self.capture_image
        )

        self.path_entry.grid(column=0, row=0)
        self.scan_num_entry.grid(column=1, row=0)
        scan_btn.grid(column=2, row=0)

        return frame

    def reset_graph(self):
        self.graph_area.reset_graph()

    def move_stage(self, angle, axis):
        self.thread.is_moving = True
        self.stage.move(angle, axis)

        if axis == 2:
            self.thread.angle_now = angle
            self.graph_area.angle_now = angle

        self.thread.is_moving = False
        self.thread.event.set()

    def move_qwp(self, angle):
        self.qwp.move(angle)
        self.qwp.wait_while_busy()

        self.thread.angle_now = angle
        self.graph_area.angle_now = angle

    def capture_image(self):
        num = int(self.scan_num_entry.get())
        path = self.path_entry.get()

        if not path.endswith(".tif") or not path.endswith(".tiff"):
            path += ".tif"

        image = self.camera.multi_scan(num)
        tiff.imsave(path, image)

        Popup()

    def change_exposure_time(self, t):
        camera.change_exposure_time(t)

    def run(self):
        self.thread.start()

        self.root.update()
        self.root.deiconify()
        self.root.mainloop()

        self.thread.stop()
        self.thread.join()


if __name__ == "__main__":
    exposure_time = 300
    with CS505MU(
        exposure_time=exposure_time
    ) as camera, Mark102() as stage, SHOT702() as qwp:
        app = App(camera=camera, stage=stage, qwp=qwp)
        app.run()
