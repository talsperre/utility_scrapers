# utility_scrapers
Scripts to scrape data from some common data sources such as Instagram, Snapchat Maps, Magicbricks & Youtube Ads.

### Installation

In order to run these scripts you need to have the latest version of Python on your PC and either chromedriver or geckodriver to use Selenium. For reference, install all the packages given in my virtual environment:

```
pip install -r requirements.txt
```

For additional instructions on downloading the corresponding chromedriver or geckodriver, look at [Chromedriver download](https://chromedriver.chromium.org/downloads) and [Geckodriver Releases](https://github.com/mozilla/geckodriver/releases) respectively.

### Snapchat Maps

A scraper written to scrape public videos from the [Snapchat Maps](http://maps.snapchat.com/) Interface. The user needs to provide a list of
city names in the format given in the csv file. The data for each city in that csv (`cities_list.csv`) was collected using OSM Maps database.

Additional instructions are given in the `README.md` file inside the snapchat_maps folder.

### Instagram Scraper

A selenium based python code written to scrape the posts in explore feed corresponding to a particular hashtag. The data collected consists of fields like `num_likes` & `num_comments` as well.

Additional instructions are given in the `README.md` file inside the instagram_scraper folder.

### Magicbricks Scraper

A simple scraper written to collect region names in different cities of India. Possible applications include collecting a dataset for NER in Indian context.

Additional instructions are given in the `README.md` file inside the magic_bricks folder.

### Youtube Ads Scraper

Youtube does not provide any API as of now to retrieve all the ads being shown in a given city/region. I have implemented a scraper that can search for such advertisements and collected their metadata & links by going through thousands of youtube videos one by one.

Additional instructions are given in the `README.md` file inside the youtube_scraper folder.