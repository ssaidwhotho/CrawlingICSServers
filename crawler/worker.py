from threading import Thread, RLock

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
import os


def check_ping():
    hostname = "styx.ics.uci.edu"
    response = os.system("ping -c 1 " + hostname)
    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
    else:
        pingstatus = "Network Error"

    return pingstatus


class Worker(Thread):
    def __init__(self, worker_id, config, frontier, counter_object):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.counter_object = counter_object  # make counter object a variable in the worker
        self.lock = RLock()
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {
            -1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {
            -1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)

    def run(self):
        while True:
            # attempt to ping the server to make sure it's not down
            server_status = check_ping()
            while server_status == "Network Error":
                print("Network Error, waiting 60 seconds to try again.")
                time.sleep(60)
                server_status = check_ping()
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            # lock here if multi-threading
            with self.lock:
                similar = scraper.too_similar(resp, self.counter_object)
            while similar:
                tbd_url = self.frontier.get_tbd_url()
                if not tbd_url:
                    self.logger.info("Frontier is empty. Stopping Crawler.")
                    break
                resp = download(tbd_url, self.config, self.logger)
                with self.lock:
                    similar = scraper.too_similar(resp, self.counter_object)
            self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            if len(scraped_urls) > 0:
                with self.lock:
                    self.counter_object.increment_unique_pages()
                    scraper.save_page_data(resp, self.counter_object)
                # lock here if multi-threading
                # with self.lock:
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
                self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)

