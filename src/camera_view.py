import queue
import threading

import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

from instr.CS505MU import CS505MU
from instr.Mark102 import Mark102


class LiveViewCanvas(tk.Canvas):
    def __init__(self, parent, image_queue, text):
        self.image_queue = image_queue
        self.now_img = None
        self.image = None
        self.crossed_nicols = None
        self.text = text
        tk.Canvas.__init__(self, parent)
        self.pack()
        self._get_image()

    def _get_image(self):
        try:
            self.image = self.image_queue.get_nowait()
            self.resized_image = self.image.resize((600, 500), resample=Image.NEAREST)
            self.now_img = self.resized_image

            if self.crossed_nicols is not None:
                self.resized_image = Image.fromarray(
                    np.array(self.resized_image) - np.array(self.crossed_nicols)
                )

            self.text.set(f"{np.mean(np.array(self.image)):.3f}")

            self._image = ImageTk.PhotoImage(master=self, image=self.resized_image)
            self.config(width=600, height=500)
            self.create_image(0, 0, image=self._image, anchor="nw")
        except queue.Empty:
            pass

        self.after(10, self._get_image)

    def set_crossed_nicols(self):
        self.crossed_nicols = self.now_img

    def reset_image(self):
        self.crossed_nicols = None


class ImageAcquisitionThread(threading.Thread):
    def __init__(self, camera):
        super(ImageAcquisitionThread, self).__init__()
        self._camera = camera
        self._previous_timestamp = 0

        self._bit_depth = camera.bit_depth
        self._camera.image_poll_timeout_ms = 0
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()

    def get_output_queue(self):
        return self._image_queue

    def stop(self):
        self._stop_event.set()

    def _get_image(self) -> Image:
        image = np.array(self._camera.capture())
        image = image >> (self._bit_depth - 8)
        image = Image.fromarray(image)

        return image

    def run(self):
        while not self._stop_event.is_set():
            try:
                pil_image = np.array(self._camera.capture()) >> 4
                pil_image = Image.fromarray(pil_image)
                self._image_queue.put_nowait(pil_image)
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print(f"Encountered error: {error}, image acquisition will stop.")
                break
        print("Image acquisition has stopped")


class App:
    def __init__(self, camera, stage, waveplate):
        self.camera = camera
        self.stage = stage
        self.waveplate = waveplate

        self.root = tk.Tk()
        self.averaged_intensity = tk.StringVar()
        self.averaged_intensity.set("0.000")
        self.image_acquisition_thread = ImageAcquisitionThread(self.camera)

        self.configure_widgets()

        self.camera.frames_per_trigger_zero_for_unlimited = 0

    def configure_widgets(self):
        intensity_frame = self.intensity_frame()
        intensity_frame.grid(row=0, column=0, sticky=tk.W + tk.E)

        camera_frame = tk.Frame(self.root, width=200, height=200, padx=10, pady=5)
        self.canvas = LiveViewCanvas(
            parent=camera_frame,
            image_queue=self.image_acquisition_thread.get_output_queue(),
            text=self.averaged_intensity,
        )
        camera_frame.grid(row=1, column=0, columnspan=3)

        memorize_btn = tk.Button(
            self.root, text="Memorize", command=self.set_crossed_nicols
        )
        memorize_btn.grid(row=0, column=1)
        reset_btn = tk.Button(self.root, text="Reset", command=self.reset_image)
        reset_btn.grid(row=0, column=2)

        exposure_time_controller = self.exposure_time_controller_frame()
        exposure_time_controller.grid(row=2, column=0, sticky=tk.W + tk.E)

        stage_controller = self.stage_frame()
        stage_controller.grid(row=3, column=0, sticky=tk.W + tk.E)

    def intensity_frame(self):
        frame = tk.Frame(self.root)
        text = tk.Label(frame, text="Average intensity: ")
        text.grid(row=0, column=0)
        label = tk.Label(frame, textvariable=self.averaged_intensity)
        label.grid(row=0, column=1)

        return frame

    def exposure_time_controller_frame(self):
        frame = tk.Frame(self.root)
        exposure_time_label = tk.Label(frame, text="Exposure time (ms): ")
        exposure_time_label.grid(row=0, column=0)
        self.exposure_time_setter = tk.Entry(frame, width=20)
        self.exposure_time_setter.grid(row=0, column=1)
        exposure_time_button = tk.Button(
            frame, text="Set", command=self.set_exposure_time
        )
        exposure_time_button.grid(row=0, column=2)

        return frame

    def stage_frame(self):
        frame = tk.Frame(self.root, pady=10)

        stage_label1 = tk.Label(frame, text="stage 1:")
        stage_label2 = tk.Label(frame, text="stage 2:")
        stage_label1.grid(row=0, column=0)
        stage_label2.grid(row=1, column=0)

        angle_text_area1 = tk.Entry(frame, width=20)
        angle_text_area2 = tk.Entry(frame, width=20)
        angle_text_area1.grid(row=0, column=1)
        angle_text_area2.grid(row=1, column=1)

        set_button1 = tk.Button(
            frame,
            text="Set",
            command=lambda: self.move_stage(float(angle_text_area1.get()), axis=1),
        )
        set_button2 = tk.Button(
            frame,
            text="Set",
            command=lambda: self.move_stage(float(angle_text_area2.get()), axis=2),
        )
        set_button1.grid(row=0, column=2)
        set_button2.grid(row=1, column=2)

        return frame

    def set_crossed_nicols(self):
        self.canvas.set_crossed_nicols()

    def reset_image(self):
        self.canvas.reset_image()

    def set_exposure_time(self):
        self.camera.change_exposure_time(int(self.exposure_time_setter.get()))

    def move_stage(self, angle, axis):
        if angle > 360:
            return

        self.stage.move(angle, axis=axis)

    def rotate_waveplate(self, angle):
        if angle > 360:
            return

        self.waveplate.move(angle)

    def run(self):
        self.image_acquisition_thread.start()

        self.root.mainloop()

        self.image_acquisition_thread.stop()
        self.image_acquisition_thread.join()


if __name__ == "__main__":
    with CS505MU(exposure_time=40) as camera:
        App(camera=camera, stage=None, waveplate=None).run()
