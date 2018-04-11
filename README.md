# Computer-Vision-Tools
Personally developed python tools for manipulating images.


## Bayer-Converter
Debayer/demosaic raw tif images. Creates a 'debayered' directory in with the raw images.
Usage: bayer2RGB.py /directory_to_convert.

## Image-Georeferencing
Convert tif images into geotifs. Currently setup to accept lcm generated csv files. Need to refactor to accept clean lists of iamges and gps coordinates.

## Mosaic-Stitching
Stitch two images together.
Usage: stitch.py -f /first_image -s /second_image