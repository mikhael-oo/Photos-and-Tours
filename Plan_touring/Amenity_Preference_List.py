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

amenities = pd.read_json('../osm/amenities-vancouver.json.gz',lines=True)
amenities = amenities.drop(columns = 'timestamp')

airbnb = pd.read_csv('../data/listings.csv.gz', compression='gzip', header=0, sep=',', quotechar='"')
airbnb = airbnb[['listing_url', 'name', 'neighbourhood_cleansed', 'latitude', 'longitude', 
                 'property_type', 'room_type', 'accommodates', 'price', 'minimum_nights', 'maximum_nights']]
airbnb['price'] = airbnb['price'].replace('[\$,]', '', regex=True).astype(float)
airbnb = airbnb.rename(columns={'latitude': 'lat', 'longitude': 'lon', 'name': 'airbnb_name'})
airbnb.loc[airbnb.price > 1000, 'price'] = airbnb.price / airbnb.minimum_nights

neighbor = pd.read_csv('../data/neighbourhoods.csv')

def main_menu():
    
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
    exec_menu(int(method_of_travel), int(neighbourhoods_of_airbnb))
    return

def deg2rad(deg) :
    ''' Change degree value to radians. (Based on Exercise 3)'''
    return deg * (np.pi/180)

def exec_menu(method_of_travel, neighbourhoods_of_airbnb):    
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
        
    roomtype = input("\nPlease enter what room type you are interested in:\n1. Entire home/apt\n2. Private room\n3. Shared room\n")
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
        
    maxPrice = int(input("\nPlease enter maximum price per day of your planning for tour:\n"))
    # Extracting airbnbs less then value of the user input
    bnb = airbnb_list[airbnb_list['price'] < maxPrice]
    # From extracted airbnb lists, change the neighborhood
    bnbs = bnb[bnb['neighbourhood_cleansed']==select_neighbor]
        
    # Choose Airbnb with more restaurants and more bars nearby
    bnb_amenities = amenities[(amenities['amenity'] == 'restaurant') | (amenities['amenity'] == 'cafe') | 
                              (amenities['amenity'] == 'fast_food') | (amenities['amenity'] == 'ice_cream') | 
                              (amenities['amenity'] == 'bistro') | (amenities['amenity'] == 'food_court') | 
                              (amenities['amenity'] == 'marketplace') | (amenities['amenity'] == 'juice_bar')|
                              (amenities['amenity'] == 'bar') | (amenities['amenity'] == 'biergarten') | 
                              (amenities['amenity'] == 'pub') | (amenities['amenity'] == 'nightclub') | 
                              (amenities['amenity'] == 'lounge')]

    # Calculate the distance between points in extracted airbnb lists based on the maximum value and points in amenities
    combined_df = bnb_amenities.assign(key=1).merge(bnbs.assign(key=1), how='outer', on='key')
    combined_df = combined_df.drop(columns=["amenity", "tags", "neighbourhood_cleansed"])
    combined = distance(combined_df)

    tmp = combined.loc[(combined['distance(m)'] <= 100)] # Includes only amenities within 100m
    tmp.rename(columns={'lat_x': 'am_lat', 'lon_x': 'am_lon', 'lat_y': 'bnb_lat', 'lon_y': 'bnb_lon'}, inplace=True)
    tmp = tmp.drop(columns=["am_lat","am_lon","key", 'listing_url','property_type', 'room_type'])
    choose_bnb = tmp.groupby("airbnb_name", as_index=False)['distance(m)'].agg('sum')
    choose_bnb = choose_bnb.sort_values(by = 'distance(m)')

    choosed_bnb = choose_bnb.iat[0,0]
    choosed_final = bnbs[bnbs['airbnb_name'] == choosed_bnb].drop(columns=["minimum_nights", "room_type", 
                                                                     "property_type", "neighbourhood_cleansed"])

    return choosed_final

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