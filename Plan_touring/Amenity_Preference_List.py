import sys
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import MiniBatchKMeans

#TODO ########################################################################
'''
1. Create a function which will classify the 'amenity' column in the air_bnb df which is referenced on line 148. This
    function should create categories such as grocery, restaraunt, entertainment, etc... into which the more specific tags 
    can be bucketed into. This can either be done manually by creating lists or it can be done by using some sort of classifier
    using the tags for the amenity as the input features.

2. Once the above function is done I can then add a section of code to the get_airbnb function which will prompt the user to input their
    top 3 most desired amenities categorized by the above categories. This preference list will then be used to filter only the amenities 
    which the user would like similar to how it is done on line 148.

3. Look into how the 'best' airbnb is chosen. Right now it seems to be using the airbnb which has the min sum of distances between it and all the amenities
    within 100m. This seems like it could select for those airbnbs which are more remote and have less amenities to add to this sum. Maybe a count of the nearby
    amenities would serve to select for better airbnbs.

4. Additional work could be looking into the folium maps that were generated and adding things such as:
    - a start and stop point along the route
    - add popup markers to the folium map where the airbnb we chose is. Reference: https://www.python-graph-gallery.com/312-add-markers-on-folium-map

'''
##############################################################################


"""
If the user is planning a tour of the city (only Vancouver) by walking/biking/driving, 
We can plan the tour with the most interesting amenities and choose an Airbnb with more chain restaurants nearby.
District option 17. Shaughnessy and 22. West End might return an error message.
If it is possible, when choosing the method of travel, please select walking; the API is fragile and cannot handle so many requests.
The Airbnb dataset used in this project is publicly available at:
http://insideairbnb.com/get-the-data.html
Local area boundary used in this project is available at:
https://opendata.vancouver.ca/explore/dataset/local-area-boundary/export/
"""

#read the amenities data and drop the timestamp col
amenities = pd.read_json('../osm/amenities-vancouver.json.gz',lines=True)
amenities = amenities.drop(columns = 'timestamp')


#read in the listings data of the different airbnb locations
airbnb = pd.read_csv('../data/listings.csv.gz', compression='gzip', header=0, sep=',', quotechar='"')
airbnb = airbnb[['listing_url', 'name', 'neighbourhood_cleansed', 'latitude', 'longitude', 
                 'property_type', 'room_type', 'accommodates', 'price', 'minimum_nights', 'maximum_nights']]
#convert the price to a float
airbnb['price'] = airbnb['price'].replace('[\$,]', '', regex=True).astype(float)
airbnb = airbnb.rename(columns={'latitude': 'lat', 'longitude': 'lon', 'name': 'airbnb_name'})
airbnb.loc[airbnb.price > 1000, 'price'] = airbnb.price / airbnb.minimum_nights

#read in the neighbourhood data
neighbor = pd.read_csv('../data/neighbourhoods.csv')

def bens_helper():
    print((amenities.groupby('amenity').count()).index)
    pass

def main_menu():
    '''
    call the classify amenities function
    uncomment the rest of the code in this function when done with it.
    '''
    #my helper function to print stuff
    # bens_helper()


    # Choosing the form of travel from user
    print("\n If you are planning a tour of the city, what is your form of travel? :")
    print("1. Walking")
    print("2. Biking")
    print("3. Driving")
    method_of_travel = input("Please enter an option number provided:\n")
    
    # folium supports both Image, Video, GeoJSON and TopoJSON overlays.
    # From http://python-visualization.github.io/folium/
    folium_map(airbnb, amenities)

    # Choosing the neighbourhood from user interest
    print("Please choose the neighbourhood of Airbnb you want to stay in:")
    print("---You can check the generated heatmap van_heatmap.html to see the neighbourhoods.")
    print("1. Downtown")
    print("2. Downtown Eastside")
    print("3. Dunbar Southlands")
    print("4. Grandview-Woodland")
    print("5. Hastings-Sunrise")
    print("6. Kensington-Cedar Cottage")
    print("7. South Cambie")
    print("8. Strathcona")
    print("9. Sunset")
    print("10. Victoria-Fraserview")
    print("11. West End")
    print("12. West Point Grey")
    print("13. Kerrisdale")
    print("14. Killarney")
    print("15. Kitsilano")
    print("16. Marpole")
    print("17. Mount Pleasant")
    print("18. Oakridge")
    print("19. Renfrew-Collingwood")
    print("20. Riley Park")
    print("21. Arbutus Ridge")
    print("22. Fairview")
    print("23. Shaughnessy")

    neighbourhoods_of_airbnb = input("Please enter an option number provided: \n")

    #call the exec menu function and pass it the method of travel and the neighbourhoods
    exec_menu(int(method_of_travel), int(neighbourhoods_of_airbnb))
    return

def deg2rad(deg) :
    ''' Change degree value to radians. (Based on Exercise 3)'''
    return deg * (np.pi/180)

def exec_menu(method_of_travel, neighbourhoods_of_airbnb):   
    #enforce contraints on the inputs the user can give 
    if method_of_travel < 1 or method_of_travel > 3 or neighbourhoods_of_airbnb > 23 or neighbourhoods_of_airbnb < 1:
        print("\nInvalid input. Please input a number from 1 to 23.\n")
        main_menu()
    else:
        # getting the user preferred airbnb based on room type and maximum price with amenities of most restaurants and bars nearby
        airbnb = get_airbnb(neighbourhoods_of_airbnb)
        amenities_list = get_amenities(airbnb, method_of_travel)
        planed_route = plan_Route(airbnb, amenities_list, method_of_travel)
        planed_route.save('planned_route.html')

        print("We have provided you a planned_route.html based on your demands!")
        return
    
def get_airbnb(neighbourhoods_of_airbnb):
    # neighbourhoods_of_airbnb = user input of provided neighbourhood from neighbourhoods.csv
    # getting a single value at specified row = neighbourhoods_of_airbnb - 1 and column = 1 pair by integer position
    select_neighbor = neighbor.iat[neighbourhoods_of_airbnb - 1, 1]
        
    #ask for user input on which room type they would like
    roomtype = input("\nPlease enter what room type you are interested in:\n1. Entire home/apt\n2. Private room\n3. Shared room\n")
    #restrict the airbnb df to only those of the specified roomtype
    if roomtype == "1":
        airbnb_list = airbnb[airbnb['room_type'] == 'Entire home/apt']
    elif roomtype == "2":
        airbnb_list = airbnb[airbnb['room_type'] == 'Private room']
    elif roomtype == "3":
        airbnb_list = airbnb[airbnb['room_type'] == 'Shared room']
    else:
        print("Invalid input. Please input 1, 2 or 3.")
        # Recursion when user typed wrong input
        get_airbnb(neighbourhoods_of_airbnb)
        
    #take the max price input
    maxPrice = int(input("\nPlease enter maximum price per day of your planning for tour:\n"))
    # Extracting airbnbs less then value of the user input
    bnb = airbnb_list[airbnb_list['price'] < maxPrice]
    # From extracted airbnb lists, change the neighborhood
    bnbs = bnb[bnb['neighbourhood_cleansed']==select_neighbor]
        
    
    # Choose Airbnb with more restaurants and more bars nearby
    # bnb_amenities = amenities[(amenities['amenity'] == 'restaurant') | (amenities['amenity'] == 'cafe') | 
    #                           (amenities['amenity'] == 'fast_food') | (amenities['amenity'] == 'ice_cream') | 
    #                           (amenities['amenity'] == 'bistro') | (amenities['amenity'] == 'food_court') | 
    #                           (amenities['amenity'] == 'marketplace') | (amenities['amenity'] == 'juice_bar')|
    #                           (amenities['amenity'] == 'bar') | (amenities['amenity'] == 'biergarten') | 
    #                           (amenities['amenity'] == 'pub') | (amenities['amenity'] == 'nightclub') | 
    #                           (amenities['amenity'] == 'lounge')]
    bnb_amenities = limit_amenity()

    # Calculate the distance between points in extracted airbnb lists based on the maximum value and points in amenities
    combined_df = bnb_amenities.assign(key=1).merge(bnbs.assign(key=1), how='outer', on='key')
    combined_df = combined_df.drop(columns=["amenity", "tags", "neighbourhood_cleansed"])
    combined = distance(combined_df)
    
    
    tmp = combined.loc[(combined['distance(m)'] <= 100)] # Includes only amenities within 100m
    tmp.rename(columns={'lat_x': 'am_lat', 'lon_x': 'am_lon', 'lat_y': 'bnb_lat', 'lon_y': 'bnb_lon'}, inplace=True)
    tmp = tmp.drop(columns=["am_lat","am_lon","key", 'listing_url','property_type', 'room_type'])
    print(tmp)
    #choose_bnb sums the distances from all the amenities within its range of 100km and then selects the ones with the smallest summed distance
    #a problem I could see with this would be that the ones with the smallest distances could have the least amount of amenities
    choose_bnb = tmp.groupby("airbnb_name", as_index=False)['distance(m)'].agg('sum')
    choose_bnb = choose_bnb.sort_values(by = 'distance(m)')
    print(choose_bnb)

    choosed_bnb = choose_bnb.iat[0,0]
    choosed_final = bnbs[bnbs['airbnb_name'] == choosed_bnb].drop(columns=["minimum_nights", "room_type", 
                                                                     "property_type", "neighbourhood_cleansed"])
    print(choosed_final)
    return choosed_final


#ask the user to input their 3 most prefered amenities and limit the amenities df to contain only those types
def limit_amenity():
    '''
        ask the user to input their most prefered amenities and limit the amenities df to contain only those types
    '''

    #this is the dict containing the groupings for each type of amenity
    amenity_groups  = {'Grocery':['Pharmacy','marketplace','pharmacy'],
                        'Shopping':['shop|clothes','social_centre'],
                        'Dine-In':['bar','bistro','cafe','internet_cafe','lounge','pub','restaurant'],
                        'Fast Food':['fast_food','food_court','ice_cream','juice_bar','vending_machine'],
                        'Bank & Post':['atm','atm;bank','bank','letter_box','office|financial','post_office','post_box','post_depot'],
                        'Education':['childcare','college','cram_school','driving_school','language_school','kindergarten','music_school','research_institute','school','university'],
                        'Transportation':['bicycle_parking','bicycle_rental','bicycle_repair_station','boat_rental',
                                        'bus_station','car_rental','car_sharing','charging_station','motorcycle_rental','ferry_terminal'],
                        'Entertainment':['arts_centre','casino','cinema','events_venue','gambling','leisure','nightclub','playground','spa','theatre'],
                        'Parking':['parking','parking_entrance','parking_space']
                        }

    #this is a list to change the user input into a key so it can index the dictionary
    input_to_key = ['None','Grocery','Shopping','Dine-In','Fast Food','Bank & Post','Education','Transportation','Entertainment','Parking']

    #prompt the user for their preferred amenities and take it as input
    print("Please select the top 3 amenities that are the most important to you when looking for a location for your airbnb.")
    print("1. Grocery")
    print("2. Shopping")
    print("3. Dine-In")
    print("4. Fast Food")
    print("5. Bank & Post")
    print("6. Education")
    print("7. Transportation")
    print("8. Entertainment")
    print("9. Parking")
    #split the input into a list of ints which can be used to index the groups dictionary using the input_to_key list
    input_amenities = input("Enter the number corresponding to your preferred amenities. Please select 3 and separate your numbers with a space.")
    input_list = input_amenities.split()
    input_list = [int(i) for i in input_list]
    
    #limit the amenities df based on what the user selected

    limited_amenities = amenities[amenities['amenity'].isin(amenity_groups[input_to_key[input_list[0]]]) |
                                   amenities['amenity'].isin(amenity_groups[input_to_key[input_list[1]]]) |
                                   amenities['amenity'].isin(amenity_groups[input_to_key[input_list[2]]])]
    

    return limited_amenities


def get_amenities(airbnb, method_of_travel):
    
    #filtering attractions with tourism (tag)
    tags = amenities['tags'].apply(pd.Series)
    tag = tags.loc[:, tags.columns == 'tourism']
    new = pd.concat([amenities.drop(['tags'], axis=1), tag], axis=1)
    tourism = new.dropna(subset=['tourism'])

    route_amenities = amenities[(amenities['amenity'] == 'leisure') | (amenities['amenity'] == 'lounge') | 
                                (amenities['amenity'] == 'social_centre') | (amenities['amenity'] == 'spa') | 
                                (amenities['amenity'] == 'meditation_centre')| (amenities['amenity'] == 'bench') | 
                                (amenities['amenity'] == 'playground') | (amenities['amenity'] == 'shelter') |  
                                (amenities['amenity'] == 'park')]

    amenities_df = pd.merge(route_amenities, tourism, how='outer', on=['lat','lon','amenity','name'])
    route_df = amenities_df.assign(key=1).merge(airbnb.assign(key=1), how='outer', on='key')
    combined = distance(route_df)
    
    # Includes only amenities within 1.5km if users chose to walk        
    if method_of_travel == 1:
        len = combined.loc[(combined['distance(m)'] <= 1500)]   
    # Includes only amenities within 4.5km if user chose to bike
    elif method_of_travel == 2:
        len = combined.loc[(combined['distance(m)'] <= 4500)]
    # Includes only amenities within 20km  if user chose to drive
    else:
        len = combined.loc[(combined['distance(m)'] <= 20000)]
   
    len.rename(columns={'lat_x': 'lat', 'lon_x': 'lon', 'lat_y': 'bnb_lat', 'lon_y': 'bnb_lon'}, inplace=True)
    len = len.drop(columns=["bnb_lat", "bnb_lon", "key", 'listing_url', 'tags'])
    # grouping by the "amenity column" with corresponding distance(m) based on the users method of travel
    # starting from min value on distance
    choose_amenity = len.groupby("amenity", as_index=False)['distance(m)'].agg('min')
    choose_amenity = choose_amenity.sort_values(by = 'distance(m)')

    # Based on sorted values of distance, we choose the amenity
    choosed_amenity = len[len['distance(m)'] == choose_amenity]
    choosed_amenity = pd.merge(choose_amenity, len, how='inner', on=['distance(m)'])

    return choosed_amenity

def distance(combined_df):
    """Haversine formula: calculate distance between two points on a globe"""
    # Adaopted from http://www.codecodex.com/wiki/Calculate_distance_between_two_points_on_a_globe
    # Radius of earth in Kilometers default
    R = 6371

    dLat = deg2rad(combined_df['lat_y']-combined_df['lat_x'])
    dLon = deg2rad(combined_df['lon_y']-combined_df['lon_x'])

    a = (np.sin(dLat/2) * np.sin(dLat/2) 
         + np.cos(deg2rad(combined_df['lat_x'])) * np.cos(deg2rad(combined_df['lat_y'])) * np.sin(dLon/2) * np.sin(dLon/2))
        
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    # converting distance in m
    d = R * c * 1000 

    combined_df['distance(m)'] = d
    # Lat/lon_y are the coordinates from points
    combined_df=combined_df.sort_values(['distance(m)'])
    return combined_df

def folium_map(airbnb_data, amenities_data):
    '''
    Create a heatmap of Vancouver amenities from "amenities-vancouver.jason.gz" and airbnbs from "listings.csv.gz"
    Reference: https://blog.dominodatalab.com/creating-interactive-crime-maps-with-folium/
    '''
    # Vancouver latitude and longitude values
    latitude = 49.2823254
    longitude = -123.1187994

    # Create map and display it
    vancouver_map = folium.Map(location=[latitude, longitude], zoom_start=12)
    
    # Add points to map
    vancouver_map.add_child(folium_points(airbnb_data))
    HeatMap(folium_heatmap(amenities_data)).add_to(vancouver_map)
    folium.GeoJson(
        '../data/local-area-boundary.geojson',
        style_function=lambda feature: {
            'fillColor': '#ffff00',
            'color': 'black',
            'weight': 2,
            'dashArray': '5, 5'
        }   
    ).add_to(vancouver_map)
    
    # Display the map of Vancouver
    vancouver_map

    vancouver_map.save('van_heatmap.html')  
    
def folium_heatmap(amdata):
    '''Return heat data'''
    heatdata = amdata[['lat','lon']].values.tolist()
    return heatdata

def folium_points(bnbdata):
    
    # Instantiate a feature group for the bnbs in the dataframe
    airbnbs = folium.map.FeatureGroup()

    # Loop through the data and add each to the airbnbs feature group
    for lat, lng, in zip(bnbdata.lat, bnbdata.lon):
        airbnbs.add_child(
            folium.CircleMarker(
                [lat, lng],
                radius = 10, # define how big you want the circle markers to be
                color = 'dark green',
                fill = True,
                fill_color = 'green',
                fill_opacity = 0.4
            )
        )
    return airbnbs  

def folium_markers(data):
    d = folium.map.FeatureGroup()
    for lat, lon, name in zip(data.lat, data.lon, data.name):
        d.add_child(
            folium.Marker(
                [lat,lon], 
                popup = name
            )
        ) 
    return d
    
def plan_Route(airbnb, amenities_list, method_of_travel):
    ''' Reference: https://stackoverflow.com/questions/60578408/is-it-possible-to-draw-paths-in-folium'''
    """ This function plots walking/biking/driving paths between two points using data of airbnbs, amenities list which 
    depends on method of travel
    data of airbnbs: based on users preference : room type; max price; bar& resturants amenities specifically
    amenities list: amenities based on the tag "tourism"
    """
    
    ox.config(log_console=True, use_cache=True)
    if method_of_travel == 1:
       G_walk = ox.graph_from_place('Vancouver, British Columbia, Canada', network_type='walk')   
    elif method_of_travel == 2:
       G_walk = ox.graph_from_place('Vancouver, British Columbia, Canada', network_type='bike') 
    else:
       G_walk = ox.graph_from_place('Vancouver, British Columbia, Canada',  network_type='drive')
    
    orig_node = ox.get_nearest_node(G_walk, (airbnb.iloc[0]['lat'], airbnb.iloc[0]['lon']))
    dest_node = orig_node

    nodes = []
    routes = []

    for index, row in amenities_list.iterrows():
        nodes.append(ox.get_nearest_node(G_walk, (row['lat'], row['lon'])))
        if index == 0:
            routes.append(nx.shortest_path(G_walk, orig_node, nodes[index],  weight='length'))
        elif (index == len(amenities_list.index) - 1):
            routes.append(nx.shortest_path(G_walk,  nodes[index], dest_node,  weight='length'))
        else:
            routes.append(nx.shortest_path(G_walk,  nodes[index-1], nodes[index],  weight='length'))
        
    for route in routes:
        route_map = ox.plot_route_folium(G_walk, route)
    
    return route_map

if __name__ == '__main__':
    main_menu()