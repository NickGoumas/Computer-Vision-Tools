#!/usr/bin/env python3

import pandas as pd
from osgeo import gdal
from osgeo import osr
from math import degrees
import numpy as np
import argparse
import os

from GeoRef_Class import GeoRef

ap = argparse.ArgumentParser()
ap.add_argument('-AUV_VIS', 
	required=True,	
	help='Path to the AUV_VIS_RAWLOG CSV file. Needed for image filenames with timestamps.')

ap.add_argument('-images',
	required=True,
	help='Path to directory of images to georeference.')

ap.add_argument('-GPSD_CLIENT', 
	required=True, 
	help='Path to the GPSD_CLIENT CSV file. Needed for Lat Long wth timestamps.')

ap.add_argument('-UVC_OSI', 
	required=True, 
	help='Path to the UVC_OSI CSV file. Needed for height from bottom with timestamps.')

ap.add_argument('-UVC_RPH', 
	required=True,
	help='Path to the UVC_RPH CSV file. Needed for heading with timestamps')
'''
ap.add_argument('-IVER3_LOG',
	required=True,
	help='Path to the standard OceanServer mission log. Might be needed for height from bottom.')
'''
args = ap.parse_args()

def getTimeFromImage(filename, auv_vis_df):
	index = auv_vis_df.index[auv_vis_df['image_name'] == filename].tolist()
	#print('pair:', filename, index)
	index = index[0]
	utc_time = auv_vis_df.get_value(index, 'utime')
	return utc_time

def getLatLonFromTime(utime, df):
	rows, cols = df.shape
	for i in range(0, rows):
		test_utime = df.loc[i, 'utime']
		if test_utime >= utime:
			index = i
			lat = df.loc[index, 'latitude']
			lon = df.loc[index, 'longitude']
			return lat, lon

def getAltimeterFromTime(utime, uvc_osi_df):
	rows, cols = uvc_osi_df.shape
	for i in range(0, rows):
		test_utime = uvc_osi_df.loc[i, 'utime']
		if test_utime >= utime:
			index = i
			altimeter = uvc_osi_df.loc[index, 'altimeter']
			return altimeter

def getHeadingFromTime(utime, uvc_rph_df):
	rows, cols = uvc_rph_df.shape
	for i in range(0, rows):
		test_utime = uvc_rph_df.loc[i, 'utime']
		if test_utime >= utime:
			index = i
			heading = uvc_rph_df.loc[index, 'heading']
			return heading


# Load the AUV_VIS CSV using the correct delimiter and header row.
# Also only load the two columns we're working with.
auv_vis_df = pd.read_csv(args.AUV_VIS, sep=';', header=1, usecols=['utime', 'image_name'])

# Load the image directory and create a list of image 
# filenames for the compiled dataframe.
image_directory = args.images
image_list = []
for file in os.listdir(image_directory):
	if file.endswith('.tif'):
		image_list.append(file)

# Load the GPSD_CLIENT for the lat lon data.
gpsd_client_df = pd.read_csv(args.GPSD_CLIENT, sep=';', header=1, usecols=['utime', 'latitude', 'longitude'])

#print(gpsd_client_df.loc[0, 'latitude'])
# Load UVC_OSI for the height from bottom data.
uvc_osi_df = pd.read_csv(args.UVC_OSI, sep=';', header=1, usecols=['utime', 'altimeter', 'latitude', 'longitude'])

# Load UVC_RPH for the heading data.
uvc_rph_df = pd.read_csv(args.UVC_RPH, sep=';', header=1, usecols=['utime', 'heading'])

# Create empty dataframe for final data to use for georef class.
compiled_df = pd.DataFrame(columns=['utime', 'image_filename', 'image_filepath', 'lat', 'lon', 'hfb', 'heading'])


print(len(image_list))
# Append data to the final dataframe from CSVs.
for i in range(0, len(image_list)):
	utime = getTimeFromImage(image_list[i], auv_vis_df)
	compiled_df.loc[i, 'utime'] = utime
	compiled_df.loc[i, 'image_filename'] = image_list[i]
	image_filepath = os.path.join(image_directory, image_list[i])
	compiled_df.loc[i, 'image_filepath'] = image_filepath

compiled_df = compiled_df.sort_values('utime').reset_index(drop=True)

for i in range(0, len(image_list)):
	utime = compiled_df.loc[i, 'utime']
	lat, lon = getLatLonFromTime(utime, uvc_osi_df)
	lat = degrees(lat)
	lon = degrees(lon)
	compiled_df.loc[i, 'lat'] = lat
	compiled_df.loc[i, 'lon'] = lon
	height = getAltimeterFromTime(utime, uvc_osi_df)
	compiled_df.loc[i, 'hfb'] = height
	heading = getHeadingFromTime(utime, uvc_rph_df)
	compiled_df.loc[i, 'heading'] = degrees(heading)

output_directory = os.path.join(args.images, 'georeferenced')
if not os.path.exists(output_directory):
	os.makedirs(output_directory)


for i in range(0, 89):
	print('utime:', compiled_df.loc[i, 'utime'])
	line_data = compiled_df.iloc[i].to_dict()
	geotiff = GeoRef(output_directory, line_data)
