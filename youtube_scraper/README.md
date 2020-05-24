# Running scraper
To run the scraper, enter the following line in the terminal:

```
python scraper.py --chrome_driver_path CHROMEDRIVER_PATH --database_name YOUR_DB_NAME
```

Once the scraper runs, it will save the data/links to a DB called `YOUR_DB_NAME.db`, which is a `sqlite3` database.

The script takes two more arguements:
- `num_batches`: To divide data collection into batches - script can be extended to run parallely using threads
- `batch_idx`: The batch index for which data needs to be collected

To look at how to parallelize the data collection, see the code in the snapchat_scraper folder of the same repository