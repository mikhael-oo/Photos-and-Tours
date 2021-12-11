# CMPT 353 Project

## OSM, Photos, and Tours
The OpenStreetMap project collects community-provided map data that is free to use. The full data dump, known as planet.osm, provides all of the data from their maps in a slightly ugly XML format, ready for analysis. The main goal of this project is to write a program which would allow tourists to find Airbnbs that meet their needs quickly and easily. The final result solved this exact problem with the generated output of planned_route.html and bnb_map.html. 

## Dataset
Provided dataset : 
The data set is in JSON format, with fields for latitude, longitude, timestamp (when the node was edited), the amenity type (like “restaurant”, “bench”, “pharmacy”, etc), the name (like “White Spot”, often missing), and a dictionary of any other tags in the entry. This data can be found in "osm" directory. The provided data of “amenities-vancouver.jason.gz” contains a total of 17,718 unique amenities with 6 different columns which included amenity characteristics, geographic information and tags associated with WikiData.

In this project, the provided data was narrowed down to the city of Vancouver. The data provided by the instructor included locations in Vancouver and the amenities they hold. After a detailed cleaning and analysis, we employed two other external datasets to complement what we already have. We got a dataset containing the Airbnb listings in the city and a local boundary dataset in order to make recommendations to meet users’ preferences and provide them with a planned route based on their preferences. In addition to these datasets, the geographical data outlining Vancouver’s local area boundaries was acquired to enable a feature via which users can search for Airbnbs throughout several districts in Vancouver. (several districts are collected from Inside Airbnbs which is named as neighbourhoods.csv)


Additional dataset : 
The Airbnb dataset used in this project is publicly available at http://insideairbnb.com/get-the-data.html.
Local area boundary used in this project is available at https://opendata.vancouver.ca/explore/dataset/local-area-boundary/export/ which can be found in the "data" directory.

### Set up the environment:
For a list of all modules/packages needed to run the code you can simply run:
###
        $ pip3 install -r requirements.txt

We have found that both folium and osmnx have some issues being installed on Windows systems without a virtual environment. We would strongly recommend running this code on a bash based terminal (OSX/Linux) to avoid any potential issue.

### if you get an error message when attempting to install osmnx, try:
        $ sudo apt-get update -y
        $ sudo apt-get install -y libspatialindex-dev
        $ pip3 install Rtree

### and then:
        $ pip3 install osmnx

### To run the system, use main.py in the directory Plan_touring with the following command:
        $ python3 main.py ../osm

### By running main.py, the outputs are available in Plan_touring directory namely:
        bnb_map.html
        planned_route.html
    
### Contributer :
        Jeongwoon Suh (301313489)
        Ben Ledingham (301372106)
        Mikhael Opeyemi-Olatunji (301438457)
