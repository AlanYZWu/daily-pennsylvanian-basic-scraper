"""
Scrapes a headline from The Daily Pennsylvanian website and saves it to a 
JSON file that tracks headlines over time.
"""

import os
import sys
from datetime import datetime

import daily_event_monitor

import bs4
import requests
import loguru


def scrape_data_point():
    """
    Scrapes the main headline from The Daily Pennsylvanian home page.

    Returns:
        str: The headline text if found, otherwise an empty string.
    """
    header= {
        "User-Agent": "cis3500-scraper"
    }
    req = requests.get("https://www.thedp.com", headers=header)
    loguru.logger.info(f"Request URL: {req.url}")
    loguru.logger.info(f"Request status code: {req.status_code}")

    time_stamps = []
    if req.ok:
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        time_stamps_raw = soup.findall("span", class_="post-time")
        
        for stamp in time_stamps_raw:
            time_text = stamp.get_text().strip()
            try:
                dt = datetime.strptime(time_text, "%B %d, %Y at %I:%M %p")
                time_stamps.append(dt.isoformat())
            except ValueError as e:
                loguru.logger.warning(f"Failed to parse '{time_text}': {e}")

if __name__ == "__main__":

    # Setup logger to track runtime
    loguru.logger.add("scrape.log", rotation="1 day")

    # Create data dir if needed
    loguru.logger.info("Creating data directory if it does not exist")
    try:
        os.makedirs("data", exist_ok=True)
    except Exception as e:
        loguru.logger.error(f"Failed to create data directory: {e}")
        sys.exit(1)

    # Load daily event monitor
    loguru.logger.info("Loading daily event monitor")
    dem = daily_event_monitor.DailyEventMonitor(
        "data/daily_pennsylvanian_headlines.json"
    )

    # Run scrape
    loguru.logger.info("Starting scrape")
    try:
        scraped_timestamps = scrape_data_point()
    except Exception as e:
        loguru.logger.error(f"Failed to scrape data point: {e}")
        scraped_timestamps = []

    # Get existing time stamps
    scraped = set()
    for date in dem.data:
        scraped.update(dem.data[date])

    new_stamps = [ts for ts in scraped_timestamps if ts not in scraped]

    # Save data
    if new_stamps:
        for ts in new_stamps:
            dem.add_today(ts)
        dem.save()
        loguru.logger.info("Saved daily event monitor")

    def print_tree(directory, ignore_dirs=[".git", "__pycache__"]):
        loguru.logger.info(f"Printing tree of files/dirs at {directory}")
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(directory, "").count(os.sep)
            indent = " " * 4 * (level)
            loguru.logger.info(f"{indent}+--{os.path.basename(root)}/")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                loguru.logger.info(f"{sub_indent}+--{file}")

    print_tree(os.getcwd())

    loguru.logger.info("Printing contents of data file {}".format(dem.file_path))
    with open(dem.file_path, "r") as f:
        loguru.logger.info(f.read())

    # Finish
    loguru.logger.info("Scrape complete")
    loguru.logger.info("Exiting")
