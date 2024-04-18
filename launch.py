from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

import time


def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    ############################################## DELETE
    start_time = time.time()
    max_time = 10 # Set timeout to 10 seconds
    while time.time() - start_time < max_time:
        parser = ArgumentParser()
        parser.add_argument("--restart", action = "store_true", default = False)
        parser.add_argument("--config_file", type = str, default = "config.ini")
        args = parser.parse_args()
        main(args.config_file, args.restart)
        pass
    print("The code stopped running after 30 seconds.")
    ############################################## DELETE

    # parser = ArgumentParser()
    # parser.add_argument("--restart", action="store_true", default=False)
    # parser.add_argument("--config_file", type=str, default="config.ini")
    # args = parser.parse_args()
    # main(args.config_file, args.restart)

