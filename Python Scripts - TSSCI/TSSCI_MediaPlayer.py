import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button
from matplotlib.animation import FuncAnimation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.widgets import TextBox
import os
from pathlib import Path
import tkinter as tk
from tkinter import Listbox, END, Frame
import matplotlib

matplotlib.use('TkAgg')

rate = 9
# Get the current working directory
current_directory = Path.cwd()

class MediaPlayer:
    def __init__(self, parent, rate=1.0):
        self.parent = parent
        self.rate = rate
        self.index = 0
        self.forward = True  # To track the direction of playback
        self.fig, self.ax = plt.subplots(figsize=(14, 7))  # Adjusted figure size
        self.fig.subplots_adjust(left=0.05, right=0.65, top=0.95, bottom=0.2)  # Adjusted subplot positions

        # Create existing buttons
        axprev = plt.axes([0.05, 0.1, 0.05, 0.075])
        axnext = plt.axes([0.10, 0.1, 0.05, 0.075])
        axpause = plt.axes([0.15, 0.1, 0.05, 0.075])
        axresume = plt.axes([0.20, 0.1, 0.05, 0.075])
        ax_rotate_90 = plt.axes([0.25, 0.1, 0.05, 0.075])
        ax_rotate_neg_90 = plt.axes([0.30, 0.1, 0.05, 0.075])
        ax_change_direction = plt.axes([0.35, 0.1, 0.05, 0.075])
        ax_change_speed = plt.axes([0.40, 0.1, 0.05, 0.075])
        ax_decrease_speed = plt.axes([0.45, 0.1, 0.05, 0.075])

        # Position for the rate window and export button
        self.ax_rate = plt.axes([0.15, 0.02, 0.1, 0.05])
        ax_export = plt.axes([0.28, 0.02, 0.1, 0.05])

        self.bprev = self.create_image_button(axprev, os.path.join(current_directory, "icons", "prev.png"), self.prev)
        self.bnext = self.create_image_button(axnext, os.path.join(current_directory, "icons", "next.png"), self.next)
        self.bpause = self.create_image_button(axpause, os.path.join(current_directory, "icons", "pause.png"),
                                               self.pause)
        self.bresume = self.create_image_button(axresume, os.path.join(current_directory, "icons", "play.png"),
                                                self.resume)
        self.b_rotate_90 = self.create_image_button(ax_rotate_90, os.path.join(current_directory, "icons", "Rot.png"),
                                                    self.rotate_90)
        self.b_rotate_neg_90 = self.create_image_button(ax_rotate_neg_90,
                                                        os.path.join(current_directory, "icons", "negRot.png"),
                                                        self.rotate_neg_90)
        self.b_change_direction = self.create_image_button(ax_change_direction,
                                                           os.path.join(current_directory, "icons", "reverse.png"),
                                                           self.change_direction)
        self.b_change_speed = self.create_image_button(ax_change_speed,
                                                       os.path.join(current_directory, "icons", "speed.png"),
                                                       self.change_speed)
        self.b_decrease_speed = self.create_image_button(ax_decrease_speed,
                                                         os.path.join(current_directory, "icons", "slow.png"),
                                                         self.decrease_speed)

        self.b_export = Button(ax_export, 'Export')
        self.b_export.on_clicked(self.export_animation)

        # Create rate display
        self.rate_display = TextBox(self.ax_rate, 'Rate', initial=f'{self.rate:.1f}')
        self.rate_display.set_active(False)  # Make the TextBox read-only
        self.scatter = None
        self.lines = []
        self.paused = False
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=1000 / self.rate, repeat=True)

        # Embed the matplotlib figure into the tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

        # Bind the window close event
        self.parent.protocol("WM_DELETE_WINDOW", self.on_close)

        # Load the TSSCI image and display it on the right side
        self.tssci_image_ax = self.fig.add_axes([0.7, 0.1, 0.25, 0.8])  # Adjusted position and size
        self.tssci_image_ax.axis('off')
        self.tssci_image = None
        self.red_line = None

        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def create_image_button(self, ax, image_path, callback):
        img = plt.imread(image_path)
        imagebox = OffsetImage(img, zoom=0.05)  # Adjust zoom to make the icons smaller
        ab = AnnotationBbox(imagebox, (0.5, 0.5), frameon=False)
        ax.add_artist(ab)
        button = Button(ax, '', color='none', hovercolor='none')
        button.on_clicked(callback)
        return button

    def detect_gaps(self, x_values, y_values):
        # Detect missing points based on whether consecutive points are identical
        missing_indices = [i for i in range(1, len(x_values)) if x_values[i] == x_values[i-1] and y_values[i] == y_values[i-1]]
        gaps = []
        start_idx = None

        for i in range(len(missing_indices) - 1):
            if missing_indices[i+1] == missing_indices[i] + 1:
                if start_idx is None:
                    start_idx = missing_indices[i]
            else:
                if start_idx is not None:
                    gaps.append((start_idx, missing_indices[i]))
                    start_idx = None

        if start_idx is not None:
            gaps.append((start_idx, missing_indices[-1]))

        return gaps

    def draw_lines(self, x_values, y_values, segments, gaps):
        for segment in segments:
            for i in range(len(segment) - 1):
                if not any(gap[0] <= segment[i] <= gap[1] or gap[0] <= segment[i+1] <= gap[1] for gap in gaps):
                    self.ax.plot([x_values[segment[i]], x_values[segment[i+1]]],
                                 [y_values[segment[i]], y_values[segment[i+1]]],
                                 color='gray', alpha=0.5)

    def update_plot(self, *args):
        if not self.paused and hasattr(self, 'data'):
            self.ax.clear()
            row = self.data[self.index]
            x_values = [point[0] for point in row]
            y_values = [1 - point[1] for point in row]  # Flip the y-values
            c_values = [point[2] for point in row]

            self.scatter = self.ax.scatter(x_values, y_values, c=c_values, cmap='viridis', edgecolors='none')

            # Annotate each point with its index
            for i, (x, y) in enumerate(zip(x_values, y_values)):
                self.ax.annotate(str(i), (x, y), textcoords="offset points", xytext=(0, 5), ha='center')

            # Detect gaps
            gaps = self.detect_gaps(x_values, y_values)

            # Define segments to connect
            segments = [
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],  # Jawline
                [17, 18, 19, 20, 21],  # Right eyebrow (closed loop)
                [22, 23, 24, 25, 26],  # Left eyebrow (closed loop)
                [27, 28, 29, 30],  # Nose line (closed loop)
                [31, 32, 33, 34, 35],  # Nose holes (closed loop)
                [36, 37, 38, 39, 40, 41, 36],  # Right eye (closed loop)
                [42, 43, 44, 45, 46, 47, 42],  # Left eye (closed loop)
                [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 48],  # Outer lip (closed loop)
                [60, 61, 62, 63, 64, 65, 66, 67, 60]  # Inner lip (closed loop)
            ]
            self.draw_lines(x_values, y_values, segments, gaps)

            self.ax.set_title(f'Graph for Line {self.index}')
            self.ax.set_xlabel('x')
            self.ax.set_ylabel('y')
            self.canvas.draw()

            if self.forward:
                self.index = (self.index + 1) % len(self.data)
            else:
                self.index = (self.index - 1) % len(self.data)
                if self.index < 0:
                    self.index = len(self.data) - 1

            # Display the TSSCI image if it is loaded
            if self.tssci_image is not None:
                self.tssci_image_ax.clear()
                self.tssci_image_ax.imshow(self.tssci_image)
                if self.red_line is not None:
                    self.red_line.remove()
                self.red_line = self.tssci_image_ax.axhline(y=self.index, color='red', linestyle='-', linewidth=3)
                self.tssci_image_ax.axis('off')
                self.canvas.draw()

    def next(self, event):
        if self.paused:
            self.index = (self.index + 1) % len(self.data)
            self.update_plot_immediate()

    def prev(self, event):
        if self.paused:
            self.index = (self.index - 1) % len(self.data)
            if self.index < 0:
                self.index = len(self.data) - 1
            self.update_plot_immediate()

    def update_plot_immediate(self):
        if hasattr(self, 'data'):
            self.ax.clear()
            row = self.data[self.index]
            x_values = [point[0] for point in row]
            y_values = [1 - point[1] for point in row]  # Flip the y-values
            c_values = [point[2] for point in row]

            self.scatter = self.ax.scatter(x_values, y_values, c=c_values, cmap='viridis', edgecolors='none')

            # Annotate each point with its index
            for i, (x, y) in enumerate(zip(x_values, y_values)):
                self.ax.annotate(str(i), (x, y), textcoords="offset points", xytext=(0, 5), ha='center')

            # Detect gaps
            gaps = self.detect_gaps(x_values, y_values)

            # Define segments to connect
            segments = [
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],  # Jawline
                [17, 18, 19, 20, 21],  # Right eyebrow (closed loop)
                [22, 23, 24, 25, 26],  # Left eyebrow (closed loop)
                [27, 28, 29, 30],  # Nose line (closed loop)
                [31, 32, 33, 34, 35],  # Nose holes (closed loop)
                [36, 37, 38, 39, 40, 41, 36],  # Right eye (closed loop)
                [42, 43, 44, 45, 46, 47, 42],  # Left eye (closed loop)
                [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 48],  # Outer lip (closed loop)
                [60, 61, 62, 63, 64, 65, 66, 67, 60]  # Inner lip (closed loop)
            ]
            self.draw_lines(x_values, y_values, segments, gaps)

            self.ax.set_title(f'Graph for Line {self.index}')
            self.ax.set_xlabel('x')
            self.ax.set_ylabel('y')
            self.canvas.draw()

            # Display the TSSCI image if it is loaded
            if self.tssci_image is not None:
                self.tssci_image_ax.clear()
                self.tssci_image_ax.imshow(self.tssci_image)
                if self.red_line is not None:
                    self.red_line.remove()
                self.red_line = self.tssci_image_ax.axhline(y=self.index, color='red', linestyle='-', linewidth=3)
                self.tssci_image_ax.axis('off')
                self.canvas.draw()

    def rotate_90(self, event):
        for i in range(len(self.data)):
            self.data[i] = [(1 - y, x, c) for x, y, c in self.data[i]]
        self.update_plot_immediate()

    def rotate_neg_90(self, event):
        for i in range(len(self.data)):
            self.data[i] = [(y, 1 - x, c) for x, y, c in self.data[i]]
        self.update_plot_immediate()

    def change_direction(self, event):
        self.forward = not self.forward

    def change_speed(self, event):
        self.rate += 1
        self.rate_display.set_val(f'{self.rate:.1f}')
        self.reset_animation()

    def decrease_speed(self, event):
        if self.rate > 1:  # Ensure the rate does not go below 1
            self.rate -= 1
            self.rate_display.set_val(f'{self.rate:.1f}')
            self.reset_animation()

    def reset_animation(self):
        self.anim.event_source.stop()
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=1000 / self.rate, repeat=True)
        self.anim.event_source.start()

    def pause(self, event):
        self.paused = True

    def resume(self, event):
        self.paused = False

    def on_close(self):
        self.anim.event_source.stop()
        self.parent.destroy()

    def load_data(self, image_path):
        # Load the image
        image = Image.open(image_path)
        self.image_name = os.path.splitext(os.path.basename(image_path))[0]

        # Get the image dimensions
        width, height = image.size

        # Read the image data and rescale it
        data = []
        for y in range(height):
            row = []
            for x in range(width):
                r, g, b = image.getpixel((x, y))
                x_val, y_val, c_val = r / 255.0, g / 255.0, b / 255.0
                row.append((x_val, y_val, c_val))
            data.append(row)

        self.data = data
        self.index = 0  # Reset index for new data
        self.update_plot_immediate()

        # Load the TSSCI image
        self.tssci_image = plt.imread(image_path)

    def export_animation(self, event):
        anim = FuncAnimation(self.fig, self.update_plot, frames=len(self.data), repeat=False)
        anim_folder = os.path.join(current_directory, "animation")
        os.makedirs(anim_folder, exist_ok=True)
        anim.save(os.path.join(anim_folder, f'{self.image_name}_animation.gif'), writer='pillow', fps=10)
        print(f"Animation exported as {self.image_name}_animation.gif")

    def on_click(self, event):
        if event.inaxes == self.tssci_image_ax:
            self.update_index_from_mouse(event.ydata)

    def on_mouse_move(self, event):
        if event.inaxes == self.tssci_image_ax and event.button:
            self.update_index_from_mouse(event.ydata)

    def update_index_from_mouse(self, ydata):
        if ydata is not None:
            self.index = int(ydata)
            self.update_plot_immediate()

def update_listbox(folder, listbox):
    listbox.delete(0, END)
    for file in os.listdir(folder):
        if file.endswith(".png"):
            listbox.insert(END, file)

def on_select(evt, media_player):
    TSSCI_folder = os.path.join(current_directory, "TSSCI")
    widget = evt.widget
    selection = widget.curselection()
    if selection:
        file_path = os.path.join(TSSCI_folder, widget.get(selection[0]))
        media_player.load_data(file_path)

def loadImage():
    root = tk.Tk()
    root.title("TSSCI Image Viewer")

    left_frame = Frame(root)
    left_frame.pack(side="left", fill="y")

    listbox = Listbox(left_frame)
    listbox.pack(side="left", fill="y")

    TSSCI_folder = os.path.join(current_directory, "TSSCI")
    update_listbox(TSSCI_folder, listbox)

    media_player = MediaPlayer(parent=root, rate=rate)
    listbox.bind('<<ListboxSelect>>', lambda evt: on_select(evt, media_player))

    root.mainloop()

def main():
    loadImage()

if __name__ == "__main__":
    main()
