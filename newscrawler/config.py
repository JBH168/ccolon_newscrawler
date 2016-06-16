# -*- coding: utf-8 -*-
"""
This is the config-loading and json-loading module which loads and parses the
config file as well as the json file.

It handles the [General]-Section of the config.

All object-getters create deepcopies.
"""

from copy import deepcopy

import logging
import ConfigParser
import json
from ast import literal_eval
from scrapy.utils.log import configure_logging


class CrawlerConfig(object):
    """
    The actual class. First parameter: config-file.
    This class is a singleton-class,
    Usage:
        First creation and loading of the config-file:
            c = CrawlerConfig.get_instance()
            c.setup(<config_file>)
        Further using:
            c = CrawlerConfig.get_instance()
    """

    # singleton-helper-class
    # Source: http://code.activestate.com/recipes/52558-the-singleton-pattern-implemented-with-python/#c4
    class SingletonHelper(object):
        """The singleton-helper-class"""
        # https://pythontips.com/2013/08/04/args-and-kwargs-in-python-explained/
        def __call__(self, *args, **kw):
            if CrawlerConfig.instance is None:
                CrawlerConfig.instance = CrawlerConfig()

            return CrawlerConfig.instance

    # singleton-helper-variable + function
    get_instance = SingletonHelper()
    instance = None

    # Here starts the actual class!
    log = None
    log_output = []
    __current_section = None
    __logging = None
    __scrapy_options = None

    def __init__(self):
        """The constructor
        (keep in mind: this is a singleton, so just called once)"""

        if CrawlerConfig.instance is not None:
            self.log_output.append(
                {"level": "error",
                 "msg": "Multiple instances of singleton-class"})
            raise RuntimeError('Multiple instances of singleton-class')

    def setup(self, filepath):
        """Setup the actual class.
        Arguments:
            1. filepath: Path to the config-file (including file-name)
        """
        if self.log is not None:
            self.log.warning("Disallowed multiple setup of config.")
            return

        self.log = logging.getLogger(__name__)
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read(filepath)
        self.sections = self.parser.sections()
        self.log_output.append(
            {"level": "info", "msg": "Loading config-file (%s)" % filepath})
        self.load_config()
        self.handle_general()
        self.handle_logging()

    def load_config(self):
        """Load the config to self.config. Recursive dict:
           [section][option] = value"""
        self.__config = {}

        # Parse sections, its options and put it in self.config.
        for section in self.sections:

            self.__config[section] = {}
            options = self.parser.options(section)

            # Parse options of each section
            for option in options:

                try:
                    opt = self.parser \
                        .get(section, option)
                    try:
                        self.__config[section][option] = literal_eval(opt)
                    except (SyntaxError, ValueError) as error:
                        self.__config[section][option] = opt
                        self.log_output.append(
                            {"level": "debug",
                             "msg": "Option not literal_eval-parsable"
                             " (maybe string): %s" % option})

                    if self.__config[section][option] == -1:
                        self.log_output.append(
                            {"level": "debug", "msg": "Skipping: %s" % option})
                except ConfigParser.NoOptionError as exc:
                    self.log_output.append(
                        {"level": "error",
                         "msg": "Exception on %s: %s" % (option, exc)})
                    self.__config[section][option] = None

    def get_logging(self):
        if self.__logging is None:
            self.__logging = {}
            logging_options = self.__config["Logging"]

            for key, value in logging_options.iteritems():
                self.__logging[key.upper()] = value

        return deepcopy(self.__logging)

    def get_scrapy_options(self):
        """
        returns all the options listed in the config section 'Scrapy'
        """
        if self.__scrapy_options is None:
            self.__scrapy_options = {}
            options = self.section("Scrapy")

            for key, value in options.iteritems():
                self.__scrapy_options[key.upper()] = value
        return self.__scrapy_options

    def handle_general(self):
        return

    def handle_logging(self):
        """To allow devs to log as early as possible, logging will already be handled here"""

        configure_logging(self.get_scrapy_options())

        # Disable duplicates
        self.__scrapy_options["LOG_ENABLED"] = False

        # Now, after log-level is correctly set, lets log them.
        for msg in self.log_output:
            if msg["level"] is "error":
                self.log.error(msg["msg"])
            elif msg["level"] is "info":
                self.log.info(msg["msg"])
            elif msg["level"] is "debug":
                self.log.debug(msg["msg"])

    def config(self):
        return deepcopy(self.__config)

    def section(self, section):
        return deepcopy(self.__config[section])

    def set_section(self, section):
        self.__current_section = section

    def option(self, option):
        if self.__current_section is None:
            raise RuntimeError('No section set in option-getting')
        return self.__config[self.__current_section][option]


class JsonConfig(object):
    """
    The actual class. First parameter: config-file.
    This class is a singleton-class,
    Usage:
        First creation and loading of the config-file:
            c = JsonConfig.get_instance()
            c.setup(<config_file>)
        Further using:
            c = JsonConfig.get_instance()
    """

    # singleton-helper-class
    # Source: http://code.activestate.com/recipes/52558-the-singleton-pattern-implemented-with-python/#c4
    class SingletonHelper(object):
        """The singleton-helper-class"""
        def __call__(self, *args, **kw):
            if JsonConfig.instance is None:
                JsonConfig.instance = JsonConfig()

            return JsonConfig.instance

    # singleton-helper-variable + function
    get_instance = SingletonHelper()
    instance = None

    # Here starts the actual class!
    log = None
    __json_object = None

    def __init__(self):
        """The constructor
        (keep in mind: this is a singleton, so just called once),"""
        self.log = logging.getLogger(__name__)
        if JsonConfig.instance is not None:
            self.log.error('Multiple instances of singleton-class')
            raise RuntimeError('Multiple instances of singleton-class')

    def setup(self, filepath):
        """Setup the class at first usage
        Arguments:
            1. filepath: Path to the json-file (including file-name)"""
        self.log.debug("Loading JSON-file (" + filepath + ")")
        self.load_json(filepath)

    def load_json(self, filepath):
        self.__json_object = json.load(open(filepath, 'r'))

    def config(self):
        return deepcopy(self.__json_object)

    def get_site_objects(self):
        return deepcopy(self.__json_object["base_urls"])

    def get_url_array(self):
        urlarray = []
        for urlobjects in self.__json_object["base_urls"]:
            urlarray.append(urlobjects["url"])
        return urlarray
