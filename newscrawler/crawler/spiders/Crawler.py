# -*- coding: utf-8 -*-
import scrapy


class Crawler(scrapy.Spider):
    name = "Crawler"
    allowed_domains = None
    start_urls = None
    original_url = None

    config = None
    helper = None

    def __init__(self, helper, url, config, *args, **kwargs):
        self.config = config
        self.helper = helper
        self.original_url = url

        self.allowed_domains = [self.helper.url_extractor
                                .get_allowed_domains(url)]
        self.start_urls = [self.helper.url_extractor.get_start_urls(url)]

        super(Crawler, self).__init__(*args, **kwargs)

    def parse(self, response):
        # Recursivly crawl all URLs on the current page
        for href in response.css("a::attr('href')"):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse)

        # heuristics
        if self.helper.heuristics.is_article(response, self.original_url):
            self.helper.download.save_webpage(response)
