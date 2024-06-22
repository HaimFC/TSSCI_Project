"""
Title:        plotFacedFromJson
Description:  This script make graph faces from JSON files.
              this is not used in the CreateTSSCI project, only for debug uses
Author:       Haim Fellner Cohen and Gal Zohar
Date:         2024-06-22
Version:      1.0
"""

# Example script content starts here
import argparse
import os

# Assume these are defined elsewhere
current_directory = '/path/to/current_directory'
fileName = 'default_image.jpg'

# Create an ArgumentParser object
parser = argparse.ArgumentParser()

# Construct the frame folder path
frame_folder = os.path.join(current_directory, "frames")

# Add the --image_path argument
parser.add_argument("--image_path",
                    default=os.path.join(frame_folder, fileName),
                    help="Process an image. Read all standard formats (jpg, png, bmp, etc.).")

# Parse the arguments
args = parser.parse_known_args()[0]  # Only interested in known args

# Access the image_path argument
image_path = args.image_path
print(f"Image path: {image_path}")

# Example functions and further code can follow


import os
import json
import matplotlib.pyplot as plt
from pathlib import Path

# Get the current working directory
current_directory = Path.cwd()


def extract_keypoints(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
        keypoints = []
        for person in data['people']:
            if 'face_keypoints_2d' in person:
                keypoints.extend(person['face_keypoints_2d'])
    return keypoints


def plot_keypoints(keypoints, filename, directory):
    x_values = [keypoints[i] for i in range(0, len(keypoints), 3)]
    y_values = [keypoints[i + 1] for i in range(0, len(keypoints), 3)]

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

    plt.figure()
    plt.scatter(x_values, y_values)

    # Connect points based on segments
    for segment in segments:
        plt.plot([x_values[i] for i in segment], [y_values[i] for i in segment], 'b-')

    plt.title(f'Face Keypoints for {filename}')
    plt.xlabel('X values')
    plt.ylabel('Y values')
    plt.gca().invert_yaxis()  # Invert y-axis to match image coordinates
    plt.savefig(os.path.join(directory, "graphsPlot", f'{filename}_face_keypoints_plot.png'))
    plt.close()


def plot_face_keypoints_from_json(directory):
    # Ensure the directory for plots exists
    plot_dir = os.path.join(directory, "graphsPlot")
    os.makedirs(plot_dir, exist_ok=True)

    # Plot keypoints for each JSON file in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            keypoints = extract_keypoints(filepath)
            plot_keypoints(keypoints, filename, directory)


# Example usage

directory = os.path.join(current_directory, "jsons")
plot_face_keypoints_from_json(directory)