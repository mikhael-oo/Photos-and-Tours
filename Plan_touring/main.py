import numpy as np
import pandas as pd
import sys
import time

import Amenity_Preference_List
from Amenity_Preference_List import folium_markers

def main(dataset):
    Amenity_Preference_List.main_menu()
       
if __name__ == '__main__':
    dataset = sys.argv[1]
    main(dataset)