import sys
import pandas as pd 

# this file displays the process of cleaning the data


data = pd.read_json("../cmpt353_finalproject/osm/amenities-vancouver.json.gz", lines=True)
print(data.head(20))


# the function below removes all rows with empty dictionaries

def not_empty_dict(input):
    if (input):
        return True
    else:
        return False

data_clone = data.copy()
data_clone = data_clone[data_clone["tags"].apply(not_empty_dict)]
print(data_clone.head(20))

# the list below showcases the amenities we do not care about and will not need
unnecessary_amenities = ["waste_basket", "bench", "vending_machine", "gambling", "juice_bar", "toilets",
                         "bicycle_repair_station", "luggage_locker", "waste_disposal", "compressed_air"]

def dispose_amenities(input):
    if (input not in unnecessary_amenities):
        return True
    else:
        return False
    
data_cleaned = data_clone[data_clone["amenity"].apply(dispose_amenities)]

# data_cleaned represents the cleaned_data

# the function below highlights the complete steps into one function 

def clean_data(data):
    copy_data = data.copy()
    copy_data = copy_data[copy_data["tags"].apply(not_empty_dict)]
    copy_data = copy_data[copy_data["amenity"].apply(dispose_amenities)]
    return copy_data

