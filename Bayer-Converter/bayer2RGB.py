#!/usr/bin/env python2

# Debayering tool using opencv.
# Agreement to pep8 checked using flake8.
from __future__ import print_function
import os
import cv2
import argparse
import sys


parser = argparse.ArgumentParser(
    description='A python 2.7 script to debayer a directory of raw .tif images. '+
    			'The debayered directory is created inside the input directory',
    epilog='Created by Nick Goumas')
parser.add_argument(
    'input_directory',
    help='Directory of raw .tif images to debayer.')
args = parser.parse_args()


# If the output directory doesn't exist, create it.
def create_output_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print('Directory *{}* created.'.format(path))


def convert_bayer(filepath):
    image = cv2.imread(filepath)
    image = image[0:, 0:, 1]
    image = cv2.cvtColor(image, cv2.COLOR_BAYER_BG2BGR)
    return image


# Create list of full paths for each .tif file.
def list_dir_tifs(path):
    files = os.listdir(path)
    bayer_filenames = [i for i in files if i.endswith('.tif')]
    bayer_fullpaths = [os.path.join(path, j) for j in bayer_filenames]
    bayer_names_paths = list(zip(bayer_filenames, bayer_fullpaths))
    return bayer_names_paths


# Print progress bar to terminal.
def print_percent_complete(complete, total):
    percent = float(complete) / float(total) * 100.
    print('\r {}% complete '.format(round(percent, 1)), end='')
    sys.stdout.flush()



output_dir_name = 'Debayered'

input_dir_path = os.path.abspath(args.input_directory)
output_dir_path = os.path.abspath(args.input_directory + output_dir_name)

create_output_dir(output_dir_path)

file_list = list_dir_tifs(input_dir_path)
total_imgs = len(file_list)
img_count = 1

for filename, fullpath in file_list:
    try:
        image = convert_bayer(fullpath)
        cv2.imwrite(os.path.join(output_dir_path, filename), image)
    except TypeError:
        print('')
        print('\r Error, possible bad file:', filename)

    print_percent_complete(img_count, total_imgs)
    img_count += 1
