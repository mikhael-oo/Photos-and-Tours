from exif import Image


'''
This file is about extracting a coordinate from an image in python. 
It makes use of the EXIF library in python, and the process is split into two functions.
The first function below which is "decimal_coords" only works as a converter of the
coordinates into Decimal format. The second function "image_coordinates" accepts the
image path and then opens it up using EXIF library. From there, we check if the image
has an exif data since some images do end up not having them. Then we extract the coordinates if
the image has them. 

These functions were adapted from https://medium.com/spatial-data-science/how-to-extract-gps-coordinates-from-images-in-python-e66e542af354
'''
def decimal_coords(coords, ref):
 decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
 if (ref == "S" or ref == "W"):
     decimal_degrees = -decimal_degrees
 return decimal_degrees


def image_coordinates(img_path):
    with open(img_path, 'rb') as src:
        img = Image(src)
    if img.has_exif:
        try:
            img.gps_longitude
            coords = [decimal_coords(img.gps_latitude,
                      img.gps_latitude_ref),
                      decimal_coords(img.gps_longitude,
                      img.gps_longitude_ref)]
            return coords
        except AttributeError:
            return []
    else:
        return []
    