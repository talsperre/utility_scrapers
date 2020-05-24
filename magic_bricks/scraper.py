import csv
import time
import argparse

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="Debug mode", default=False)
parser.add_argument("--city_link", help="Link to the city that you want to scrape", \
    default='https://www.magicbricks.com/localities-in-new-delhi')
# Use - separated city names such as new-delhi or the latest city names: e.g. chennai instead of madras, kolkata instead of calcutta
parser.add_argument("--city_name", help="Name of the city that you want to scrape", default='new-delhi')
parser.add_argument("--use_link", help="True if you want to use link else false", type=bool, default=False)
parser.add_argument("--chrome_driver_path", help="Number of times to scroll", default="./chromedriver")
parser.add_argument("--save_path", help="Path where location names are saved", default="results.csv")
parser.add_argument("--num_iters", help="Number of times to scroll", default=10, type=int)
args = parser.parse_args()

opts = Options()
driver = Chrome(options=opts, executable_path=args.chrome_driver_path)
if args.use_link:
    driver.get(args.city_link)
else:
    city_link = "https://www.magicbricks.com/localities-in-{}".format(args.city_name)
    driver.get(city_link)

def num_iters_scroll(num_iters, scroll_pause_time=1):
    count = 0
    while True:

        # Get scroll height
        ### This is the difference. Moving this *inside* the loop
        ### means that it checks if scrollTo is still scrolling
        last_height = driver.execute_script("return document.body.scrollHeight")

        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        count += 1
        if args.debug:
            print("Iteration: {}".format(count))
        if count >= num_iters:
            break

        if new_height == last_height:

            # try again (can be removed)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")

            # check if the page height has remained the same
            if new_height == last_height:
                # if so, you are done
                break
            # if not, move on to the next loop
            else:
                last_height = new_height
    return count

num_iters = num_iters_scroll(num_iters=args.num_iters)
location_names_object = driver.find_elements_by_class_name("loc-card__title")
location_name_list = []

for loc_object in location_names_object:
    if args.debug:
        print(loc_object.text)
    location_name_list.append([loc_object.text])

with open(args.save_path, "w") as f:
    writer = csv.writer(f)
    writer.writerows(location_name_list)

driver.close()