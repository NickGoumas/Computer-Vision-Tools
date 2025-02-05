#!/usr/bin/env python3

from mosaic import Stitcher
import argparse
import imutils
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--first", required=True,
    help="path to the first image")
ap.add_argument("-s", "--second", required=True,
    help="path to the second image")
args = vars(ap.parse_args())

# load the two images and resize them to have a width of 400 pixels
# (for faster processing)
imageA = cv2.imread(args["first"])
imageB = cv2.imread(args["second"])
#imageA = imutils.resize(imageA, width=400)
#imageB = imutils.resize(imageB, width=400)

# stitch the images together to create a panorama
stitcher = Stitcher()
result = stitcher.stitch([imageA, imageB], showMatches=False)

# show the images
#cv2.imshow("Image A", imageA)
#cv2.imshow("Image B", imageB)
#cv2.imshow("Keypoint Matches", vis)
#cv2.imshow("Result", result)
print('Result Size:{}'.format(result.shape))
cv2.imwrite('Left_result.png', result)
#cv2.waitKey(0)