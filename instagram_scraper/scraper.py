import os
import sys
import json
import random
import time
import argparse
import requests

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from PIL import Image
from tqdm import tqdm
from pprint import pprint

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

parser = argparse.ArgumentParser(description='Videos to images')
parser.add_argument('--hashtag', type=str, help='Hashtag name')
parser.add_argument('--output_dir', type=str, help='Output dir for hashtags data')
parser.add_argument('--chrome_driver_path', type=str, help='Path to geckodriver')
parser.add_argument('--instagram_username', type=str, help='Instagram Username')
parser.add_argument('--instagram_password', type=str, help='Instagram Password')
args = parser.parse_args()

instagram_url = "https://www.instagram.com/"
hashtag_path = "https://www.instagram.com/explore/tags/" + args.hashtag + "/"

options = Options()
options.headless = False

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--mute-audio")

driver = webdriver.Chrome(executable_path=args.chrome_driver_path, options=options, chrome_options=chrome_options)
actionChains = ActionChains(driver)

print("Logging in to Instagram")

driver.get(instagram_url)

try:
    timeout = 5 # The amount of time we should wait for timeout
    username_present = EC.presence_of_element_located((By.NAME, 'username'))
    WebDriverWait(driver, timeout).until(username_present)
except Exception as e:
    print("Error e: ", str(e))

username = driver.find_element_by_name('username')
password = driver.find_element_by_name('password')

username.send_keys(args.instagram_username)
password.send_keys(args.instagram_password)

submit_button = driver.find_element_by_xpath("//button[@type='submit']")
submit_button.click()

print("Getting the webpage")
time.sleep(5)

driver.get(hashtag_path)
final_array = [] # Contains all the links to the posts
visited = {}
for i in range(50):
    a_name_array = (driver.find_elements_by_xpath("//a[@href]"))
    for ele in a_name_array:
        link = ele.get_attribute("href")
        if link not in visited and "/p/" in link:
            visited[link] = True
            print(link)
            final_array.append(link)
    actionChains.send_keys(Keys.END).perform()
    time.sleep(2)

driver.close()
driver.quit()

print("Num posts: {}".format(len(final_array)))

headers = {
    'authority': 'www.instagram.com',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    'dnt': '1',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cookie': 'mcd=3; mid=W6Y23QAEAAFCrQGU-Biy8KQormLH; fbm_124024574287414=base_domain=.instagram.com; csrftoken=EQp2v3VktI8Ukzl1Mdl3qIjw6gYSnVKl; ds_user_id=12609073606; sessionid=12609073606%3ANrq5UW3yZrmCuA%3A14; rur=FRC; urlgen="{\\"14.139.82.6\\": 55824}:1hFf7n:txypGvUAyCDpMJndpYSZ3GGqzdI"',
}

params = (
    ('__a', '1'),
)

text, video, likes, comments = {}, {}, {}, {}
json_data = {}
json_response_dict = {}

for link in tqdm(final_array):
    try:
        if "/p/" in link:
            id_post = link.split('/')[-2]
            response = requests.get(link, headers=headers, params=params)
            json_response = response.json()
            # Num comments
            comm = json_response["graphql"]["shortcode_media"]["edge_media_preview_comment"]["count"]
            # Num likes
            like = json_response["graphql"]["shortcode_media"]["edge_media_preview_like"]["count"]
            # Is video
            is_video = json_response["graphql"]["shortcode_media"]["is_video"]
            # Text Description
            text_des = json_response["graphql"]["shortcode_media"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
            #Video link
            image_link = json_response["graphql"]["shortcode_media"]["display_url"]
            #time of video
            time_image = json_response["graphql"]["shortcode_media"]["taken_at_timestamp"]
            comments[id_post] = comm
            likes[id_post] = like
            video[id_post] = is_video
            text[id_post] = text_des
            json_data[id_post] = {
                "id": id_post,
                "num_likes": like,
                "num_comments": comm,
                "is_video": is_video,
                "text_des":text_des,
                "image_link":image_link,
                "time_stamp":time_image
            }
            json_response_dict[id_post] = json_response
    except Exception as e:
        print("Exception",e)
        pass

os.makedirs(args.output_dir, exist_ok=True)
output_path = os.path.join(args.output_dir, args.hashtag + ".json")

with open(output_path,'w') as f:
    json.dump(json_data, f, indent=4)