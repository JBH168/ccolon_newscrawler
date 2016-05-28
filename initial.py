#
# Initial Script
#
# called whenever a crawl should be executed
#
# reads in and parses json file via input.py
# calls the corresponding webcrawler with the input data
#
#
import os
import sys

import logging

import scrapy
from scrapy.crawler import CrawlerProcess

from newscrawler.crawler.spiders.SitemapCrawler import SitemapCrawler
from newscrawler.crawler.spiders.Crawler import Crawler

from newscrawler.config import CrawlerConfig
from newscrawler.config import JsonConfig

from newscrawler.helper import helper


class initial(object):
    cfg = None
    json = None
    log = None
    process = None
    helper = None

    def __init__(self):

        logging.basicConfig(format="[%(pathname)s:%(lineno)d] %(message)s",
                            level="ERROR")
        self.log = logging.getLogger(__name__)

        self.cfg = CrawlerConfig.get_instance()
        self.cfg.setup(self.get_config_file_path())

        self.log.info("Config initalized - Further initialisation.")

        urlinput_file_path = self.cfg.section('Files')['urlinput']
        self.json = JsonConfig.get_instance()
        self.json.setup(self.get_abs_file_path(
                                urlinput_file_path, quit_on_error=True))

        self.helper = helper(self.cfg.section('Heuristics'))

        if self.cfg.section('Crawler')['sitemap'] == "True":
            for url in self.json.get_url_array():
                self.loadCrawler(SitemapCrawler, url)
        else:
            for url in self.json.get_url_array():
                self.loadCrawler(Crawler, url)

        self.process.start()

    def loadCrawler(self, crawler, url):
        if self.process is None:
            self.process = CrawlerProcess()
        self.process.crawl(
            crawler,
            self.helper,
            url=url,
            config=self.cfg)

    def get_config_file_path(self):
        # test if the config file path was passed to this script
        # argv[0] should be this script's name
        # argv[1] should be the config file path
        #   for path names with spaces, use "path"
        if len(sys.argv) > 1:
            input_config_file_path = os.path.abspath(sys.argv[1])

            if not os.path.isabs(input_config_file_path):
                abs_file_path = self.get_abs_file_path(input_config_file_path)
            else:
                abs_file_path = input_config_file_path
            if os.path.exists(abs_file_path) and os.path.splitext(
                            abs_file_path)[1] == ".cfg":
                return abs_file_path
            else:
                self.log.error("First argument passed to initial.py is not"
                               " the config file. Falling back to"
                               " newscrawler.cfg.")

        # Default
        return self.get_abs_file_path("./newscrawler.cfg", quit_on_error=True)

    def get_abs_file_path(self, rel_file_path, quit_on_error=None):
        # for the following three lines of code, see:
        # http://stackoverflow.com/questions/7165749/open-file-in-a-relative-location-in-python
        script_dir = os.path.dirname(__file__)  # absolute dir the script is in
        abs_file_path = os.path.abspath(
                            os.path.join(script_dir, rel_file_path))

        if not os.path.exists(abs_file_path):
            self.log.error(abs_file_path + " does not exist.")
            if quit_on_error is True:
                raise RuntimeError("Importet file not found. Quit.")

        return abs_file_path


if __name__ == "__main__":
    initial()
