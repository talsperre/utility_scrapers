# Running scraper
To run the scraper, enter the following line in the terminal:

```
python scraper.py --chrome_driver_path CHROMEDRIVER_PATH --hashtag YOUR_HASHTAG --output_dir OUTPUT_DIRECTORY --instagram_username YOUR_USERNAME --instagram_password YOUR_PASSWORD
```

Once the scraper runs, it will save a file called `YOUR_HASHTAG.json` in the `OUTPUT_DIRECTORY` provided in the command earlier.

If the `OUTPUT_DIRECTORY` does not exist, then the script will create the same on its own.