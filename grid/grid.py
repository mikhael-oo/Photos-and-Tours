import pandas as pd
import gzip
import json
import numpy as np
from matplotlib import pyplot as plt



def read_data():
    data = pd.read_json('amenities-vancouver.json.gz',lines=True)
    df = pd.DataFrame(data)
    return df

def find_grid_corners(df):
    top_left = (df['lat'].max(),df['lon'].min())
    bottom_right = (df['lat'].min(),df['lon'].max())
    return list([top_left,bottom_right])

def create_grid(corners):
    lat_1km = 0.00904371732
    lon_1km = 0.01855700018
    lat_range = np.arange(corners[0][0],corners[1][0],-lat_1km)
    lon_range = np.arange(corners[0][1],corners[1][1],lon_1km)
    gridxx, gridyy = np.meshgrid(lat_range,lon_range)
    grid_df = pd.DataFrame(np.vstack([gridxx.reshape(-1),gridyy.reshape(-1)])).T
    grid_df.columns = ['lat','lon']
    return grid_df

def in_radius(center_lat,center_lon,point_lat,point_lon,radius):
    '''
    check if the point specified by point_lat and point_lon are within
    the specified radius of the center point
    the circle has a closed interval so edge points are included
    '''
    if (point_lon - center_lon)**2 + (point_lat - center_lat)**2 <= radius**2:
        return True
    else:
        return False

def get_possible_points(amenities,center_lat,center_lon):
    '''
    create a function to get a smaller subset of amenities around the center point
    this will allow us to not have to check points that are clearly not in the radius
    '''
    pass

    
data = read_data()
corners = find_grid_corners(data)
grid = create_grid(corners)
print(grid)
