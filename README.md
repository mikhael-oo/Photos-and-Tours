# CMPT 353 Project

## OSM, Photos, and Tours
The OpenStreetMap project collects community-provided map data that is free to use. The full data dump, known as planet.osm, provides all of the data from their maps in a slightly ugly XML format, ready for analysis.

## Dataset
Provided dataset : 
The data set is in JSON format, with fields for latitude, longitude, timestamp (when the node was edited), the amenity type (like “restaurant”, “bench”, “pharmacy”, etc), the name (like “White Spot”, often missing), and a dictionary of any other tags in the entry. This data can be found in "osm" directory.

Additional dataset : 
The Airbnb dataset used in this project is publicly available at http://insideairbnb.com/get-the-data.html.
Local area boundary used in this project is available at https://opendata.vancouver.ca/explore/dataset/local-area-boundary/export/ which can be found in the "data" directory.

### Set up the environment:
For a list of all modules/packages needed to run the code you can simply run:
###
        $ pip3 install -r requirements.txt

### To run the system, use main.py in the directory Plan_touring with the following arguments:
        $ python3 main.py ../osm
    
### Contributer :
        Jeongwoon Suh (301313489)
        Ben Ledingham (301372106)
        Mikhael Opeyemi-Olatunji (301438457)
