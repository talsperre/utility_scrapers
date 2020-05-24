# Scraper Instructions
The code for scraper to collect data from Snapchat Maps using SnapMap API. The data is collected from over 170 cities provided in the file `cities_list.csv`.

### Running scraper
To run the scraper, enter the following line in the terminal:

```
python scraper.py --csv_path cities_list.csv --data_dir ./city_data --dest_dir save_path
```

### City data
The folder contains over 170 geojson files collected from [OpenStreetMap](https://www.openstreetmap.org/) for all the cities in the list provided in `cities_list.csv`.

### Cities List
The list of cities used is given in the `cities_list.csv` file. The columns of the file are as follows:

```
"city_name", "population", "osm_id", "json_file_path", "use_bbox"
```

The `use_bbox` column indicates whether we are using bounding box of the city for data collection or the shapfile of the city provided by official sources. We use the bounding box instead of the shapefile for all the cities where we could not collect relevant boundary data.

`osm_id` refers to the id of the city provided by OpenStreetMaps.