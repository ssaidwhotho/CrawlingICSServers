import os
import shelve
import random

from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize, similarity_score
from scraper import is_valid


class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        self.previously_visited = set()

        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        try:
            random_file = random.choice(self.to_be_downloaded)
            self.to_be_downloaded.remove(random_file)
            return random_file
        except IndexError:
            return None

    def add_url(self, url):
        url = normalize(url)
        # check similarity of url to previously visited urls via levenstein distance
        for prev_url in self.to_be_downloaded:
            similarity = similarity_score(url, prev_url)
            if similarity >= 0.8:
                print(f"\n\n URL SIMILARITY DETECTED {url} \n\n") # delete soon
                return
        urlhash = get_urlhash(url)
        if urlhash not in self.save and urlhash not in self.previously_visited:  # don't put in if seen before
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.previously_visited.add(urlhash)  # adds the urlhash to mark it as visited
        self.save.sync()
