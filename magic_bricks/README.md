# Running scraper
To run the scraper, enter the following line in the terminal:

```
python scrape_loc.py --city_name CITY_NAME --num_iters NUMBER_OF_SCROLLING_ITERATIONS --save_path OUTPUT_FILE_PATH --chrome_driver_path CHROME_DRIVER_PATH
```

A sample command has been provided for reference:
```
python scrape_loc.py --city_name mumbai --num_iters 10 --save_path res1.csv --chrome_driver_path ./chromedriver
```

Once the scraper runs, it will save a file called `OUTPUT_FILE_PATH` provided in the command earlier.

If the city data does not exist on the website, a blank file will be saved.