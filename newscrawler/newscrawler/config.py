# -*- coding: utf-8 -*-
"""
This is the config-loading module which loads by default the config in the
root-folder of the project.
It handles the [General]-Section of the config.

It loads the newscrawler.cfg and parses it with the config-parser-module.
"""

from copy import deepcopy

import logging
import ConfigParser


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
    class SingletonHelper:
        """The singleton-helper-class"""
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

    def __init__(self):
        """The constructor (keep in mind: this is a singleton, so just called once),
        Arguments:
            1. self
            2. filepath: Path to the config-file (including file-name)
        """

        if CrawlerConfig.instance is not None:
            self.log_output.append(
                {"level": "error",
                 "msg": "Multiple instances of singleton-class"})
            raise RuntimeError('Multiple instances of singleton-class')

    def setup(self, filepath):
        if CrawlerConfig.instance is not None:
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
                    self.__config[section][option] = self.parser \
                        .get(section, option)
                    if self.__config[section][option] == -1:
                        self.log_output.append(
                            {"level": "debug", "msg": "Skipping: %s" % option})
                except ConfigParser.NoOptionError as exc:
                    self.log_output.append(
                        {"level": "error",
                         "msg": "Exception on %s: %s" % (option, exc)})
                    self.__config[section][option] = None

    def handle_general(self):
        """Handle the General-section of the config."""
        logging.basicConfig(format=self.__config["General"]["logformat"],
                            level=self.__config["General"]["loglevel"])

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
