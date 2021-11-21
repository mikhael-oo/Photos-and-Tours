import numpy as np
import pandas as pd
import sys
import time

import Amenity_Preference_List
from Amenity_Preference_List import folium_markers

def main(dataset):
    print("\nWelcome to our OSM Project! What would you like to do:")
    invalid_option = True
    while(invalid_option):
        try:
            print("1. Find amenities within 100m of a given set of photos\n2. Create a smoothed tour given a set of photos\n3. Vancouver Airbnb tour")
            option = input("Please enter an option number:\n")
            option = int(option)
            if option == 3:
                Amenity_Preference_List.main_menu()
                invalid_option = False
        
        except ValueError:
            print("\n---Invalid input. Please input 1, 2 or 3.\n")
            time.sleep(1)
       
if __name__ == '__main__':
    dataset = sys.argv[1]
    main(dataset)