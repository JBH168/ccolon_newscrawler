"""
This file's only purpose is to bundle all helper classes in ./helper_classes
so they can be passed to other classes easily
"""

from helper_classes.heuristics import heuristics
from helper_classes.url_extractor import url_extractor
from helper_classes.savepath_parser import savepath_parser
from helper_classes.parse_crawler import parse_crawler


class helper(object):
    """
    This class contains helper classes from ./helper_classes
    This class and its helper-classes is passed to all crawlers
    """
    heuristics = None
    url_extractor = None
    savepath_parser = None
    parse_crawler = None

    def __init__(
            self,
            cfg_heuristics,
            cfg_savepath,
            cfg_file_path,
            sites_object,
            crawler_class
    ):
        self.heuristics = heuristics(cfg_heuristics, sites_object, crawler_class)
        self.url_extractor = url_extractor()
        self.savepath_parser = savepath_parser(cfg_savepath,
                                               cfg_file_path, self)
        self.parse_crawler = parse_crawler(self)
