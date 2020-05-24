import os
import sys
import requests
import time
import json
import numpy as np
import pandas as pd
import random
import threading
import argparse
import traceback
import csv

from pprint import pprint
from subprocess import call
from shapely.geometry import shape, Point, MultiPolygon
from shapely.geometry.polygon import Polygon

############################################################ Argument Parsing ###################################################################################

parser = argparse.ArgumentParser(description="Script to download dataset")

parser.add_argument("--csv_path", help="Path to the cities csv file")
parser.add_argument("--data_dir", help="Path to the cities data directory")
parser.add_argument("--dest_dir", help="Path to the destination dir")

arguments = parser.parse_args()

csv_path = arguments.csv_path
data_dir = arguments.data_dir
dest_dir = arguments.dest_dir

script_start_time = time.time()

cities_df = pd.read_csv(csv_path, names=["City", "Population", "Id", "Json_file", "use_bbox"], header=None)
print(cities_df.head())

############################################################ Lat-Lon Code #######################################################################################

from math import pi, cos

RADIUS_EARTH = 6378 # in kilometers
TILE_SIZE = 1.000 # the tile size in the grid (in kilometers)

list_of_cities = []
city_lat_lon_dict = {}

for i in range(len(cities_df)):
    try:
        city = cities_df.loc[i]["City"]
        city_json = cities_df.loc[i]["Json_file"]
        city_id = str(int(cities_df.loc[i]["Id"]))
        city_path = os.path.join(data_dir, city_json)
        use_bbox = cities_df.loc[i]["use_bbox"]
        print(city, city_path, city_id)
        with open(city_path) as f:
            data = json.load(f)

        for feature in data["features"]:
            if "osm_id" in feature["properties"]:
                if feature["properties"]["osm_id"] == city_id:
                    polygon = shape(feature['geometry'])
                    lng_start, lat_start, lng_end, lat_end = map(float, feature["bbox"])

                    lat_change = (TILE_SIZE / ((2 * pi/360) * RADIUS_EARTH))
                    lng_change = (TILE_SIZE / ((2 * pi/360) * RADIUS_EARTH)) / cos(((lat_start + lat_end) / 2) * pi/180)

                    city_lats = []
                    ite = 0
                    while((lat_start + (ite * lat_change)) < lat_end):
                        city_lats.append((lat_start + ite * lat_change))
                        ite += 1

                    city_lngs = []
                    ite = 0
                    while((lng_start + (ite * lng_change)) < lng_end):
                        city_lngs.append((lng_start + ite * lng_change))
                        ite += 1

                    list_of_cities.append(city)
                    if city not in city_lat_lon_dict:
                        city_lat_lon_dict[city] = {
                            "latitudes": city_lats,
                            "longitudes": city_lngs,
                            "polygon": polygon,
                            "relevant_tiles": [],
                            "use_bbox": use_bbox
                        }

    except Exception as e:
        print("Exception e: ", str(e))
        traceback.print_exc(file=sys.stdout)

print("List of Cities: ", list_of_cities)
print("Length of Cities: ", len(list_of_cities))

############################################################ Find relevant tiles #################################################################################

occupancy_percentage = []
tiles_count = []
for key, val in city_lat_lon_dict.items():
    print("City: {}, Latitudes: {}, Longitudes: {}".format(key, len(val["latitudes"]), len(val["longitudes"])))
    num_inside, num_total = 0, 0
    for i, lat in enumerate(val["latitudes"]):
        for j, lon in enumerate(val["longitudes"]):
            if val["use_bbox"] == "no":
                val["relevant_tiles"].append((lat, lon))
                num_inside += 1
            else:
                cur_point = Point(lon, lat)
                if val["polygon"].contains(cur_point):
                    val["relevant_tiles"].append((lat, lon))
                    num_inside += 1
            num_total += 1
    occupancy_percentage.append(num_inside * 1.0 / num_total)
    tiles_count.append(num_inside)
    print("Num Inside: {}, Num Total: {}, Relevant Tiles: {}, Percentage: {}".format(num_inside, num_total, len(val["relevant_tiles"]), occupancy_percentage[-1]))
    print("-"*50)

print("Mean occupancy: {}".format(np.mean(occupancy_percentage)))
print("Total Tiles: ", np.sum(tiles_count))

city_list = []
for i in range(len(cities_df)):
    try:
        city = cities_df.loc[i]["City"]
        num_total = len(city_lat_lon_dict[city]["latitudes"]) * len(city_lat_lon_dict[city]["longitudes"])
        num_relevant = len(city_lat_lon_dict[city]["relevant_tiles"])
        percentage_relevant = num_relevant * 1.0 / num_total
        city_list.append([city, num_total, num_relevant, percentage_relevant])
    except Exception as e:
        print("Exception e: ", str(e))
        traceback.print_exc(file=sys.stdout)

with open("cities-count.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(city_list)

############################################################ Scraper Initializtions #############################################################################

radius = 500.00 # Radius in m from the centre of the grid cell till the edge
radius_large = 708.00 # Larger radius in m from the centre of the grid cell till the vertice
radius_list = [radius, radius_large]
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US',
    'Referer': 'https://map.snapchat.com/@28.632713,77.183984,11.77z',
    'content-type': 'application/json',
    'origin': 'https://map.snapchat.com',
    'Connection': 'keep-alive',
    'TE': 'Trailers',
}
city_dict = {}
city_dict_large = {}
cur_tile_count = 0

############################################################ Epoch Time Code ####################################################################################

epoch_headers = {
    'Referer': 'https://map.snapchat.com/@17.382284,78.462814,12.00z',
    'Origin': 'https://map.snapchat.com',
    'Accept-Language': 'en-GB',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    'DNT': '1',
    'Content-Type': 'application/json',
}

epoch_data = '{}'

def getSnapchatEpochTime():
    for i in range(5):
        try:
            epoch_response = requests.post('https://ms.sc-jpl.com/web/getLatestTileSet', headers=epoch_headers, data=epoch_data)
            json_epoch = epoch_response.json()
            return json_epoch["tileSetInfos"][0]["id"]["epoch"]
        except Exception as e:
            print("Exception e: ", str(e))
            traceback.print_exc(file=sys.stdout)
    return -1

############################################################ Scraper Code #######################################################################################

def getVideos(city, relevant_tiles, epoch_time):
    print("-"*100)
    print("City: {}".format(city))
    print("Num Tiles: {}".format(len(relevant_tiles)))

    if city not in city_dict:
        city_dict[city] = {}

    if city not in city_dict_large:
        city_dict_large[city] = {}

    radius_type = "normal"
    for i, cur_radius in enumerate(radius_list):
        if i == 1:
            radius_type = "large"

        for j, (lat, lon) in enumerate(relevant_tiles):
            try:
                try:
                    grid_num = j + 1
                    str_data = '{"requestGeoPoint":{"lat":' + str(lat) + ',"lon":' + str(lon)+ '},"zoomLevel":15.587275736039764,"tileSetId":{"flavor":"default","epoch":' + epoch_time + ',"type":1},"radiusMeters":' + str(cur_radius) + ',"maximumFuzzRadius":0}'
                    response = requests.post('https://ms.sc-jpl.com/web/getPlaylist', headers=headers, data=str_data)
                except Exception as e:
                    print("Exception e1: {}".format(e))
                    traceback.print_exc(file=sys.stdout)

                if response.status_code != 200:
                    epoch_time = getSnapchatEpochTime()
                    try:
                        str_data = '{"requestGeoPoint":{"lat":' + str(lat) + ',"lon":' + str(lon)+ '},"zoomLevel":15.587275736039764,"tileSetId":{"flavor":"default","epoch":' + epoch_time + ',"type":1},"radiusMeters":' + str(cur_radius) + ',"maximumFuzzRadius":0}'
                        response = requests.post('https://ms.sc-jpl.com/web/getPlaylist', headers=headers, data=str_data)
                    except Exception as e:
                        print("Exception e2: {}".format(e))
                        traceback.print_exc(file=sys.stdout)

                json_response = response.json()

                if json_response['manifest']:
                    print("city: {}, grid_num: {}, Num videos: {}, response: {}, lat: {}, lon: {}, radius_type: {}, time: {}".format(city, grid_num, json_response['manifest']['totalCount'], response.status_code, lat, lon, radius_type, time.strftime("%Y_%m_%d_%H_%M_%S")))
                    for idx, elem in enumerate(json_response['manifest']['elements']):
                        elem_id = elem['id']
                        elem["lat"], elem["lon"], elem["city"], elem["scraped_time"] = lat, lon, city, time.strftime("%d_%m_%Y_%H_%M")
                        elem["grid_num"] = grid_num
                        elem["radius_type"] = radius_type

                        if elem_id not in city_dict[city]:
                            if radius_type == "normal":
                                city_dict[city][elem_id] = elem
                        if elem_id not in city_dict_large[city]:
                            if radius_type == "large":
                                city_dict_large[city][elem_id] = elem
                else:
                    print("city: {}, grid_num: {}, Num videos: {}, response: {}, lat: {}, lon: {}, radius_type: {}, time: {}".format(city, grid_num, 0, response.status_code, lat, lon, radius_type, time.strftime("%Y_%m_%d_%H_%M_%S")))
            except Exception as e:
                print("city: {}, grid_num: {}, Caught Exception e: {}, Epoch Time: {}, response: {}, lat: {}, lon: {}, radius_type: {}, time: {}".format(city, grid_num, str(e), epoch_time, response.status_code, lat, lon, radius_type, time.strftime("%Y_%m_%d_%H_%M_%S")))
                print("Exception e_outer: {}".format(e))
                traceback.print_exc(file=sys.stdout)
                epoch_time = getSnapchatEpochTime()

############################################################ Threading Code #####################################################################################
thread_count = 100

cities_split_list = np.array_split(list_of_cities, thread_count)
print("Num of city splits: {}".format(len(cities_split_list)))

def scrapeData(city_list):
    for i, city in enumerate(city_list):
        try:
            print("-"*100)
            estimated_time = getSnapchatEpochTime()
            print("Estimated Time: {}".format(estimated_time))
            getVideos(city, city_lat_lon_dict[city]["relevant_tiles"], estimated_time)
        except Exception as e:
            print("Exception e: {}".format(e))
            traceback.print_exc(file=sys.stdout)

t = []
for x in range(thread_count):
    try:
        t.append(threading.Thread(target=scrapeData, args=(cities_split_list[x],)))
    except Exception as e:
        print("Exception e: {}".format(e))
        traceback.print_exc(file=sys.stdout)

for x in range(thread_count):
    try:
        t[x].start()
    except Exception as e:
        print("Exception e: {}".format(e))
        traceback.print_exc(file=sys.stdout)

for x in range(thread_count):
    try:
        t[x].join()
    except Exception as e:
        print("Exception e: {}".format(e))
        traceback.print_exc(file=sys.stdout)

# both threads completely executed
print("Done!")

############################################################ Final Download Code ################################################################################
for city, videos_dict in city_dict.items():
    try:
        metadata_path = os.path.join(dest_dir, "metadata", "normal", time.strftime("%Y_%m_%d"))
        os.makedirs(metadata_path, exist_ok=True)

        for elem_id, elem in videos_dict.items():
            try:
                metadata_name = os.path.join(metadata_path, elem_id + ".json")
                with open(metadata_name, "w") as out_file:
                    json.dump(elem, out_file, indent=4, sort_keys=True)
            except Exception as e:
                print("Exception e: {}".format(e))
                traceback.print_exc(file=sys.stdout)

    except Exception as e:
        print("Exception e: {}".format(e))
        traceback.print_exc(file=sys.stdout)

for city, videos_dict in city_dict_large.items():
    try:
        metadata_path = os.path.join(dest_dir, "metadata", "large", time.strftime("%Y_%m_%d"))
        os.makedirs(metadata_path, exist_ok=True)

        for elem_id, elem in videos_dict.items():
            try:
                metadata_name = os.path.join(metadata_path, elem_id + ".json")
                with open(metadata_name, "w") as out_file:
                    json.dump(elem, out_file, indent=4, sort_keys=True)
            except Exception as e:
                print("Exception e: {}".format(e))
                traceback.print_exc(file=sys.stdout)

    except Exception as e:
        print("Exception e: {}".format(e))
        traceback.print_exc(file=sys.stdout)

city_list = []
total_snaps = 0

for i in range(len(cities_df)):
    try:
        city = cities_df.loc[i]["City"]
        num_total = len(city_lat_lon_dict[city]["latitudes"]) * len(city_lat_lon_dict[city]["longitudes"])
        num_relevant = len(city_lat_lon_dict[city]["relevant_tiles"])
        percentage_relevant = num_relevant * 1.0 / num_total
        num_snaps = 0
        if city in city_dict_large:
            num_snaps = len(city_dict_large[city])
            total_snaps += num_snaps
        city_list.append([city, num_total, num_relevant, percentage_relevant, num_snaps])
    except Exception as e:
        print("Exception e: ", str(e))
        traceback.print_exc(file=sys.stdout)

cities_count_dir = os.path.join(dest_dir, "logs")
os.makedirs(cities_count_dir, exist_ok=True)

cities_count_path = os.path.join(cities_count_dir, time.strftime("%Y_%m_%d_%H_%M") + ".csv")
with open(cities_count_path, "w") as f:
    writer = csv.writer(f)
    writer.writerows(city_list)

script_end_time = time.time()
time_list = [[script_end_time - script_start_time, total_snaps]]

cities_time_dir = os.path.join(dest_dir, "time_logs")
os.makedirs(cities_time_dir, exist_ok=True)

cities_time_path = os.path.join(cities_time_dir, time.strftime("%Y_%m_%d_%H_%M") + ".csv")
with open(cities_time_path, "w") as f:
    writer = csv.writer(f)
    writer.writerows(time_list)