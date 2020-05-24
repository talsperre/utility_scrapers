import sys
import time
import random
import dataset
import sqlite3
import argparse
import traceback

import numpy as np

from urllib import parse
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


parser = argparse.ArgumentParser(description="Script to collect youtube ads data")
parser.add_argument("--batch_idx", help="Which batch of trending videos to download", type=int, default=0)
parser.add_argument("--num_batches", \
    help="Num of batches in which to split data collection. Can use it to parallelize the script", type=int, default=5)
parser.add_argument('--chrome_driver_path', type=str, help='Path to geckodriver')
parser.add_argument('--database_name', type=str, help=\
    'Name of the DB where data will be saved. Will always create a new DB')
args = parser.parse_args()

###################################################### Scraper Code ####################################################

def get_youtube_ads_data(youtube_url):
    # Get Youtube Video with given url and time
    driver.get(youtube_url)
    try:
        element_present = EC.presence_of_element_located((By.ID, 'movie_player'))
        WebDriverWait(driver, timeout).until(element_present)
        elem = driver.find_element_by_id("movie_player")
    except Exception as e:
        print("Error e: ", str(e))

    # Right click on the video player
    actionChains.context_click(elem).perform()
    elem_menu_items = driver.find_elements_by_class_name("ytp-menuitem-label")

    # Iterate over all the options available after right click
    for elem in elem_menu_items:
        content = elem.get_attribute("innerHTML")
        first_word = content.split()[0]
        # We need to activate stats for ners in each video
        # If the option has Stats written in it, then click that button
        if first_word == "Stats":
            elem.click()
            try:
                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'html5-video-info-panel-content'))
                WebDriverWait(driver, timeout).until(element_present)
                print("Got element after WebDriverWait")
                stat_nerd_div = driver.find_element_by_class_name("html5-video-info-panel-content")
            except Exception as e:
                print("Error e: ", str(e))
            stat_nerd_child_divs = stat_nerd_div.find_elements_by_tag_name("div")
            nerd_span_elem = stat_nerd_child_divs[0].find_element_by_tag_name("span")
            video_id_text = nerd_span_elem.get_attribute("innerHTML")
            # Get the video id of video being currently played (Ad or actual video)
            video_id = video_id_text.split()[0]
            # Get the video id of the video that was suppoed to be played
            original_url = driver.current_url
            # Get the params of the current url
            original_url_params = dict(parse.parse_qsl(parse.urlsplit(original_url).query))
            print("current_video_id : ", video_id)
            print("original_video_id: ", original_url_params["v"])
            is_advert = "no"
            if video_id != original_url_params["v"]:
                print("ADVERTISEMENT")
                is_advert = "yes"

            # Insert into Database
            table = db['youtube_ads']
            try:
                table.insert(dict(
                    original_id=original_url_params["v"],
                    current_id=video_id,
                    is_advert=is_advert,
                    scraped_time=time.strftime("%Y_%m_%d_%H_%M_%S")
                ))
            except Exception as e:
                print("DB Exception")
                print("Error e: {}".format(str(e)))
                traceback.print_exc(file=sys.stdout)

            # Get next video url
            next_video_url = youtube_url
            try:
                element_present = EC.presence_of_element_located((By.XPATH, '//*[@class="yt-simple-endpoint style-scope ytd-compact-video-renderer"]'))
                WebDriverWait(driver, timeout).until(element_present)
                print("Got element after WebDriverWait")
                next_video_href_tags = driver.find_elements_by_xpath('//*[@class="yt-simple-endpoint style-scope ytd-compact-video-renderer"]')
                next_video_href_tag = random.choice(next_video_href_tags)
                next_video_url = next_video_href_tag.get_attribute("href")
            except Exception as e:
                print("Error e: ", e)
            return next_video_url
    return None

###################################################### Initilizations Code ####################################################

options = Options()
options.headless = True
conn = sqlite3.connect(args.database_name)
#  "sqlite:///youtube.db"
db = dataset.connect("sqlite:///{}".format(args.database_name))

batch_idx = args.batch_idx
timeout = 5 # The amount of time we should wait for timeout

###################################################### Popular Videos Listing ##################################################

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--incognito")

driver = webdriver.Chrome(executable_path=args.chrome_driver_path, options=options, chrome_options=chrome_options)
actionChains = ActionChains(driver)

driver.get("https://www.youtube.com/feed/trending")
trending_hrefs = driver.find_elements_by_xpath('//*[@class="yt-simple-endpoint style-scope ytd-video-renderer"]')
links_list = []

print("-"*100)
print("Top trending videos today")

for elem in trending_hrefs:
    link = elem.get_attribute("href")
    links_list.append(link)
    print(link)

num_links = len(links_list)
total_recursion = int(60000 / num_links) # Magic Number - feel free to change it
print("Num Links: {}, Total Recursion: {}".format(num_links, total_recursion))
driver.quit()

###################################################### Data Collection Code ###################################################

link_split_list = np.array_split(links_list, args.num_batches)
cur_link_list = link_split_list[batch_idx]

for link_num, link in enumerate(cur_link_list):
    current_url = link
    try:
        for i in range(total_recursion):
            print("-"*100)
            print("Initial URL in main loop: {}, Link Num: {}".format(link, link_num))
            start_time = time.time()
            # Start new webdriver
            options = Options()
            options.headless = True
            driver = webdriver.Chrome(executable_path=args.chrome_driver_path, options=options, chrome_options=chrome_options)
            actionChains = ActionChains(driver)
            new_url = get_youtube_ads_data(current_url)
            if new_url == current_url:
                print("Same as the old URL")
            else:
                print("Not the same url, we have a new URL")
            driver.quit()
            total_time = time.time() - start_time
            print("Video no. : {}, Time taken: {}, new_url: {}".format(i, total_time, new_url))
            if new_url is None:
                break
            else:
                current_url = new_url
    except Exception as e:
        print("Last Exception")
        print("Error e: {}".format(str(e)))
        traceback.print_exc(file=sys.stdout)
