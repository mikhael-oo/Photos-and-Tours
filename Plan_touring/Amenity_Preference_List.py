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
If the user is planning a tour of the city (currently only Vancouver is available) by walking/biking/driving, 
we can plan the tour with the most interesting amenities and choose an Airbnb with more chain restaurants nearby.
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
airbnb = airbnb[['listing_url','name', 'neighbourhood_cleansed','latitude', 'longitude', 'property_type', 'room_type', 'price', 'minimum_nights']]
airbnb['price'] = airbnb['price'].replace('[\$,]', '', regex=True).astype(float)
airbnb = airbnb.rename(columns={'latitude': 'lat', 'longitude': 'lon', 'name': 'bnb_name'})
airbnb.loc[airbnb.price > 1000, 'price'] = airbnb.price / airbnb.minimum_nights

neighbor = pd.read_csv('../data/neighbourhoods.csv')

def main_menu():
    '''
    Sub menu processing for option 3 in main.py.
    '''
    # Choose the method of travel
    print("\nWhat is your method of travel:")
    print("1. Walking")
    print("2. Biking")
    print("3. Driving")
    choice = input("Please enter an option number:\n")
    
    folium_map(airbnb, amenities)

    # Choose the neighbourhood
    print("Please choose the neighbourhood you want to stay in:")
    print("---You can check the generated heatmap van_heatmap.html to see the neighbourhoods.")
    print("1. Arbutus Ridge")
    print("2. Downtown")
    print("3. Downtown Eastside")
    print("4. Dunbar Southlands")
    print("5. Fairview")
    print("6. Grandview-Woodland")
    print("7. Hastings-Sunrise")
    print("8. Kensington-Cedar Cottage")
    print("9. Kerrisdale")
    print("10. Killarney")
    print("11. Kitsilano")
    print("12. Marpole")
    print("13. Mount Pleasant")
    print("14. Oakridge")
    print("15. Renfrew-Collingwood")
    print("16. Riley Park")
    print("17. Shaughnessy")
    print("18. South Cambie")
    print("19. Strathcona")
    print("20. Sunset")
    print("21. Victoria-Fraserview")
    print("22. West End")
    print("23. West Point Grey")

    neighbourhoods = input("Please enter an option number: \n")
    exec_menu(int(choice), int(neighbourhoods))
    return

def deg2rad(deg) :
    '''
    Change degree value to radians. (Based on Exercise 3)
    '''
    return deg * (np.pi/180)

def exec_menu(choice, neighbourhoods):    
    if choice < 1 or choice > 3 or neighbourhoods > 23 or neighbourhoods < 1:
        print("\n---Invalid input. Please input a number from 1 to 23.\n")
        main_menu()
    else:
        bnb = get_bnb(neighbourhoods)
        amenities_list = get_amenities(bnb,choice)
        m = planRoute(bnb, amenities_list, choice)
        m.save('planned_route.html')

        print("\n---Printed to planned_route.html.")

        return
    
def get_bnb(neighbourhoods):
    select_neighbor = neighbor.iat[neighbourhoods-1, 1]
        
    roomtype = input("\nPlease enter what room type you are interested in:\n1. Entire home/apt\n2. Private room\n3. Shared room\n")
    if roomtype == "1":
        bnb_list = airbnb[airbnb['room_type'] == 'Entire home/apt']
    elif roomtype == "2":
        bnb_list = airbnb[airbnb['room_type'] == 'Private room']
    elif roomtype == "3":
        bnb_list = airbnb[airbnb['room_type'] == 'Shared room']
    else:
        print("---Invalid input. Please input 1, 2 or 3.")
        get_bnb(neighbourhoods)
        
    maxPrice = int(input("\nPlease enter maximum price per day:\n"))
    bnb = bnb_list[bnb_list['price'] < maxPrice]

    bnbs = bnb[bnb['neighbourhood_cleansed']==select_neighbor]
        
    # Choose Airbnb with more restaurants and more bars nearby
    bnb_amenities = amenities[(amenities['amenity'] == 'restaurant') | (amenities['amenity'] == 'cafe') | (amenities['amenity'] == 'fast_food') | (amenities['amenity'] == 'ice_cream') | (amenities['amenity'] == 'bistro') | (amenities['amenity'] == 'food_court') | (amenities['amenity'] == 'marketplace') | (amenities['amenity'] == 'juice_bar')|(amenities['amenity'] == 'bar') | (amenities['amenity'] == 'biergarten') | (amenities['amenity'] == 'pub') | (amenities['amenity'] == 'nightclub') | (amenities['amenity'] == 'lounge') | (amenities['amenity'] == 'stripclub')]

    # Calculate the distance between points in bnbs and points in amenities.
    combined_df = bnb_amenities.assign(key=1).merge(bnbs.assign(key=1), how='outer', on='key')
    combined_df = combined_df.drop(columns=["amenity","tags","neighbourhood_cleansed"])
    combined = distance(combined_df)

    tmp = combined.loc[(combined['distance(m)'] <= 100)] # Includes only amenities within 100m
    tmp.rename(columns={'lat_x': 'am_lat', 'lon_x': 'am_lon', 'lat_y': 'bnb_lat', 'lon_y': 'bnb_lon'}, inplace=True)
    tmp = tmp.drop(columns=["am_lat","am_lon","key", 'listing_url','property_type', 'room_type'])
    choose_bnb = tmp.groupby("bnb_name", as_index=False)['distance(m)'].agg('sum')
    choose_bnb = choose_bnb.sort_values(by = 'distance(m)')

    choosed_bnb = choose_bnb.iat[0,0]
    choosed = bnbs[bnbs['bnb_name'] == choosed_bnb].drop(columns=["minimum_nights","room_type","property_type","neighbourhood_cleansed"])

    return choosed

def get_amenities(bnb, choice):
    
    #filter attractions
    tags = amenities['tags'].apply(pd.Series)
    tag = tags.loc[:, tags.columns == 'tourism']
    new = pd.concat([amenities.drop(['tags'], axis=1), tag], axis=1)
    tourism = new.dropna(subset=['tourism'])

    route_amenities = amenities[(amenities['amenity'] == 'leisure') | (amenities['amenity'] == 'lounge') | (amenities['amenity'] == 'social_centre') | (amenities['amenity'] == 'spa') | (amenities['amenity'] == 'meditation_centre')| (amenities['amenity'] == 'bench') | (amenities['amenity'] == 'playground') | (amenities['amenity'] == 'shelter') |  (amenities['amenity'] == 'park')]

    amenities_df = pd.merge(route_amenities, tourism, how='outer', on=['lat','lon','amenity','name'])
    route_df = amenities_df.assign(key=1).merge(bnb.assign(key=1), how='outer', on='key')

    combined = distance(route_df)
            
    if choice == 1:
        tmp = combined.loc[(combined['distance(m)'] <= 1500)] # Includes only amenities within 1.5km    
    elif choice == 2:
        tmp = combined.loc[(combined['distance(m)'] <= 4500)] # Includes only amenities within 4.5km 
    else:
        tmp = combined.loc[(combined['distance(m)'] <= 20000)] # Includes only amenities within 20km 
   
    tmp.rename(columns={'lat_x': 'lat', 'lon_x': 'lon', 'lat_y': 'bnb_lat', 'lon_y': 'bnb_lon'}, inplace=True)
    tmp = tmp.drop(columns=["bnb_lat","bnb_lon","key", 'listing_url','tags'])
    choose_am = tmp.groupby("amenity", as_index=False)['distance(m)'].agg('min')
    choose_am = choose_am.sort_values(by = 'distance(m)')

    choosed = tmp[tmp['distance(m)'] == choose_am]
    choosed = pd.merge(choose_am, tmp, how='inner', on=['distance(m)'])

    return choosed

def distance(combined_df):
    R = 6371

    dLat = deg2rad(combined_df['lat_y']-combined_df['lat_x'])
    dLon = deg2rad(combined_df['lon_y']-combined_df['lon_x'])

    a = np.sin(dLat/2) * np.sin(dLat/2) + np.cos(deg2rad(combined_df['lat_x'])) * np.cos(deg2rad(combined_df['lat_y'])) * np.sin(dLon/2) * np.sin(dLon/2)
        
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    d = R * c * 1000 # Distance in m

    combined_df['distance(m)'] = d
    combined_df=combined_df.sort_values(['distance(m)']) # Lat/lon_y are the coordinates from pt
    return combined_df

def folium_points(bnbdata):
    
    # Instantiate a feature group for the bnbs in the dataframe
    bnbs = folium.map.FeatureGroup()

    # Loop through the data and add each to the bnbs feature group
    for lat, lng, in zip(bnbdata.lat, bnbdata.lon):
        bnbs.add_child(
            folium.CircleMarker(
                [lat, lng],
                radius=7, # define how big you want the circle markers to be
                color='dark green',
                fill=True,
                fill_color='green',
                fill_opacity=0.4
            )
        )
    return bnbs  

def folium_markers(data):
    d = folium.map.FeatureGroup()
    #add a marker for each toilet
    for lat, lon, name in zip(data.lat, data.lon, data.name):
        d.add_child(
            folium.Marker(
                [lat,lon], 
                popup=name
            )
        ) 
    return d

def folium_heatmap(amdata):
    '''
    Return heat data.
    '''
    heatdata = amdata[['lat','lon']].values.tolist()
    return heatdata

def folium_map(bnbdata, amdata):
    '''
    Create a heatmap of Vancouver amenities and Airbnbs.
    Reference: https://blog.dominodatalab.com/creating-interactive-crime-maps-with-folium/
    '''
    # Vancouver latitude and longitude values
    latitude = 49.2823254
    longitude = -123.1187994

    # Create map and display it
    van_map = folium.Map(location=[latitude, longitude], zoom_start=12)
    
    # Add points to map
    van_map.add_child(folium_points(bnbdata))
    HeatMap(folium_heatmap(amdata)).add_to(van_map)
    folium.GeoJson(
        '../data/local-area-boundary.geojson',
        style_function=lambda feature: {
            'fillColor': '#ffff00',
            'color': 'black',
            'weight': 2,
            'dashArray': '5, 5'
        }   
    ).add_to(van_map)
    
    # Display the map of Vancouver
    van_map

    van_map.save('van_heatmap.html')  
    
def planRoute(bnb, amenities_list, choice):
    '''
    Reference: https://stackoverflow.com/questions/60578408/is-it-possible-to-draw-paths-in-folium
    '''
    ox.config(log_console=True, use_cache=True)
    if choice == 1:
       G_walk = ox.graph_from_place('Vancouver, British Columbia, Canada', network_type='walk')   
    elif choice == 2:
       G_walk = ox.graph_from_place('Vancouver, British Columbia, Canada', network_type='bike') 
    else:
       G_walk = ox.graph_from_place('Vancouver, British Columbia, Canada',  network_type='drive')
    
    orig_node = ox.get_nearest_node(G_walk, (bnb.iloc[0]['lat'], bnb.iloc[0]['lon']))
    dest_node = orig_node

    nodes = []
    routes = []

    for index, row in amenities_list.iterrows():
        nodes.append(ox.get_nearest_node(G_walk, (row['lat'], row['lon'])))
        if index == 0:
            routes.append(nx.shortest_path(G_walk, orig_node, nodes[index],  weight='length'))
        elif (index == len(amenities_list.index)-1):
            routes.append(nx.shortest_path(G_walk,  nodes[index], dest_node,  weight='length'))
        else:
            routes.append(nx.shortest_path(G_walk,  nodes[index-1], nodes[index],  weight='length'))
        
    for route in routes:
        route_map = ox.plot_route_folium(G_walk, route)
    
    return route_map

if __name__ == '__main__':
    
    main_menu()