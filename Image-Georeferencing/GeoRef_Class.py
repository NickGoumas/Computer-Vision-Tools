#!/usr/bin/env python3

import cv2
import math
import numpy as np
import LatLonUTMconversion as LLUTM
from osgeo import gdal
from osgeo import osr
import os

class GeoRef:
    def __init__(self, output_dir, list_dicts):
        self.output_dir = output_dir
        self.heading  = list_dicts['heading']
        self.lat      = list_dicts['lat']
        self.lon      = list_dicts['lon']
        self.hfb      = list_dicts['hfb']
        self.filename = list_dicts['image_filename']
        self.filepath = list_dicts['image_filepath']
        self.utime    = list_dicts['utime']
        self.runPipeline()

    def runPipeline(self):
        print('lat/lon:', self.lat, self.lon)
        img = self.loadImage(self.filepath)
        res = self.findPixelResolution(img)
        img = self.rotateImage(img)
        point1, point2 = self.findCornerPoints(img, self.lat, self.lon, res)
        self.geotransformImage(img, point1, point2)
        #self.previewImage(self.filename, img)


    def loadImage(self, filepath):
        img = cv2.imread(filepath)
        return img

    def previewImage(sefl, filename, img):
        resized_img = cv2.resize(img, (0,0), fx=0.25, fy=0.25)
        cv2.imshow(filename, resized_img)
        cv2.waitKey(0)

    def rotateImage(self, image):
        angle = -self.heading
        diagonal = int(math.sqrt(pow(image.shape[0], 2) + pow(image.shape[1], 2)))
        offset_x = int((diagonal - image.shape[0])/2)
        offset_y = int((diagonal - image.shape[1])/2)
        dst_image = np.zeros((diagonal, diagonal, 3), dtype='uint8')
        image_center = (diagonal/2, diagonal/2)

        # Get rot matrix. Point of rot, angle of rot and image scale.
        R = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        dst_image[offset_x:(offset_x + image.shape[0]), \
                  offset_y:(offset_y + image.shape[1]), \
                  :] = image

        dst_image = cv2.warpAffine(dst_image, R, (diagonal, diagonal), flags=cv2.INTER_LINEAR)

        # Calculate the rotated bounding rect
        x0 = offset_x
        x1 = offset_x + image.shape[0]
        x2 = offset_x
        x3 = offset_x + image.shape[0]

        y0 = offset_y
        y1 = offset_y
        y2 = offset_y + image.shape[1]
        y3 = offset_y + image.shape[1]

        corners = np.zeros((3,4))
        corners[0,0] = x0
        corners[0,1] = x1
        corners[0,2] = x2
        corners[0,3] = x3
        corners[1,0] = y0
        corners[1,1] = y1
        corners[1,2] = y2
        corners[1,3] = y3
        corners[2:] = 1

        c = np.dot(R, corners)

        x = int(c[0,0])
        y = int(c[1,0])
        left  = x
        right = x
        up    = y
        down  = y

        for i in range(4):
            x = int(c[0,i])
            y = int(c[1,i])
            if (x < left): left = x
            if (x > right): right = x
            if (y < up): up = y
            if (y > down): down = y
        h = down - up
        w = right - left

        cropped = np.zeros((w, h, 3), dtype='uint8')
        cropped[:, :, :] = dst_image[left:(left+w), up:(up+h), :]
        return cropped

    def findPixelResolution(self, img):
        # IMX267 Pregius 14.158mm x 7.500mm
        # 4112 x 2176
        # Image shape = (1088, 2056), binning 2x2.
        # 14.158mm / 2 = 7.079
        # 7.5mm / 2 = 3.75mm
        # 10mm focal length
        # Horizontal angle = 70
        # Vertical angle = 40
        hor_angle_rad = math.radians(35)
        ver_angle_rad = math.radians(20)
        adj_leg       = self.hfb

        # tan(ang of view) * adj = opp
        hor_opp_leg = math.tan(hor_angle_rad) * adj_leg
        meters_hor  = hor_opp_leg * 2

        ver_opp_leg = math.tan(ver_angle_rad) * adj_leg
        meters_ver  = ver_opp_leg *2

        #print('height m:', meters_ver)
        #print('width m:', meters_hor)

        hor_res = meters_hor / img.shape[1]
        ver_res = meters_ver / img.shape[0]

        res = round((hor_res + ver_res) / 2, 5)
        return res

    def findCornerPoints(self, img, center_lat, center_lon, res):
        center_UTM = LLUTM.LLtoUTM(23, center_lat, center_lon)
        UTM_zone, center_UTM_e, center_UTM_n = center_UTM
        #print('easting', center_UTM_e)
        #print('northing', center_UTM_n)

        ver_pixels, hor_pixels = img.shape[0], img.shape[1]
        ver_meters, hor_meters = ver_pixels*res, hor_pixels*res
        ver_offset, hor_offset = ver_meters/2, hor_meters/2

        upper_northing_bound = center_UTM_n + ver_offset
        lower_northing_bound = center_UTM_n - ver_offset

        left_easting_bound  = center_UTM_e - hor_offset
        right_easting_bound = center_UTM_e + hor_offset

        upper_left_LL  = LLUTM.UTMtoLL(23, upper_northing_bound, left_easting_bound, UTM_zone)
        lower_right_LL = LLUTM.UTMtoLL(23, lower_northing_bound, right_easting_bound, UTM_zone)
        return upper_left_LL, lower_right_LL

    def addAlphaChannel(self, image):
        # Create a one channel image with same XY.
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Create the alpha and b, g, r channels.
        retval, alpha = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
        b, g, r = cv2.split(image)

        # Merge the channels back to an image.
        bgra = [b, g, r, alpha]
        result = cv2.merge(bgra)
        return result

    def geotransformImage(self, img, point1, point2):
        lat = [point1[0], point2[0]]
        lon = [point1[1], point2[1]]

        filename = 'Geo_' + self.filename
        filepath = os.path.join(self.output_dir, filename)

        img = self.addAlphaChannel(img)

        # Lat -> NS, Lon -> EW
        nx, ny, chan = img.shape
        xmin, ymin, xmax, ymax = min(lon), min(lat), max(lon), max(lat)

        x_lat_res = (xmax - xmin) / float(nx)
        y_lon_res = (ymax - ymin) / float(ny)

        # Top left x, west-east pixel resolution, 0, top left y, 0, north-south pixel resolution(neg val).
        geotransform = (xmin, x_lat_res, 0, ymax, 0, -y_lon_res)
        
        # create the 3-band raster file
        # .Create method inputs (filename, x pixels, y pixels, channels, GDAL raster type)
        dst_ds = gdal.GetDriverByName('GTiff').Create(filepath, ny, nx, 4, gdal.GDT_Byte)
        dst_ds.SetGeoTransform(geotransform)            # specify coords
        srs = osr.SpatialReference()                    # establish encoding
        #srs.ImportFromEPSG(3857)                       # WGS84, meters/meters
        srs.ImportFromEPSG(4326)                        # WGS84, lat/long
        dst_ds.SetProjection(srs.ExportToWkt())         # export coords to file
        dst_ds.GetRasterBand(1).WriteArray(img[:,:,2])  # Blue channel
        dst_ds.GetRasterBand(2).WriteArray(img[:,:,1])  # Green channel
        dst_ds.GetRasterBand(3).WriteArray(img[:,:,0])  # Red channel
        dst_ds.GetRasterBand(4).WriteArray(img[:,:,3])  # Alpha channel
        dst_ds.FlushCache()                             # write to disk
        dst_ds = None



        
        