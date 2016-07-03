# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import os.path

import logging

import mysql.connector

from scrapy.exceptions import DropItem
from newscrawler.config import CrawlerConfig

################
#
# Handles reponses to HTML responses other than 200 (accept).
# As of 22.06.16 not active, but serves as an example of new
#     functionality
#
################


class HTMLCodeHandling(object):

    def process_item(self, item, spider):
        # For the case where something goes wrong
        if item['spiderResponse'].status != 200:
            # Item is no longer processed in the pipeline
            raise DropItem("%s: Non-200 response" % item['url'])
        else:
            return item

################
#
# Compares the item's age to the current version in the DB.
# If the difference is greater than delta_time, then save the newer version.
#
###############


class RSSCrawlCompare(object):

    def __init__(self):
        self.cfg = CrawlerConfig.get_instance()
        self.delta_time = self.cfg.section("Crawler")["deltatime"]
        self.database = self.cfg.section("Database")

        # Establish DB connection
        # Closing of the connection is handled once the spider closes
        self.conn = mysql.connector.connect(host=self.database["host"],
                                            port=self.database["port"],
                                            db=self.database["db"],
                                            user=self.database["username"],
                                            passwd=self.database["password"],
                                            buffered=True)
        self.cursor = self.conn.cursor()

        # Defined DB query to retrieve the last version of the article
        self.compare_versions = ("SELECT * FROM CurrentVersions WHERE url=%s")

    def process_item(self, item, spider):
        if spider.name == 'rssCrawler':
            # Search the CurrentVersion table for a version of the article
            try:
                self.cursor.execute(self.compare_versions, (item['url'],))
            except mysql.connector.Error as err:
                print "Something went wrong in rss query: {}".format(err)

            # Save the result of the query. Must be done before the add,
            #   otherwise the result will be overwritten in the buffer
            old_version = self.cursor.fetchone()

            if old_version is not None:
                # Compare the two download dates. index 3 of old_version
                #   corresponds to the downloadDate attribute in the DB
                if (datetime.datetime.strptime(
                        item['downloadDate'], "%y-%m-%d %H:%M:%S") -
                        old_version[3]) \
                        < datetime.timedelta(hours=self.delta_time):
                    raise DropItem("Article in DB too recent. Not saving.")

        return item

    def close_spider(self, spider):
        # Close DB connection - garbage collection
        self.conn.close()

################
#
# Handles remote storage of the meta data in the DB
#
################


class DatabaseStorage(object):

    # init database connection
    def __init__(self):
        self.cfg = CrawlerConfig.get_instance()
        self.database = self.cfg.section("Database")
        # Establish DB connection
        # Closing of the connection is handled once the spider closes
        self.conn = mysql.connector.connect(host=self.database["host"],
                                            port=self.database["port"],
                                            db=self.database["db"],
                                            user=self.database["username"],
                                            passwd=self.database["password"],
                                            buffered=True)
        self.cursor = self.conn.cursor()

        # initialize necessary DB queries for this pipe
        self.compare_versions = ("SELECT * FROM CurrentVersions WHERE url=%s")

        self.insert_current = ("INSERT INTO CurrentVersions(local_path,\
                              modified_date,download_date,source_domain,url,\
                              html_title, ancestor, descendant, version,\
                              rss_title) VALUES (%(local_path)s,\
                              %(modified_date)s, %(download_date)s,\
                              %(source_domain)s, %(url)s, %(html_title)s,\
                              %(ancestor)s, %(descendant)s, %(version)s,\
                              %(rss_title)s)")

        self.insert_archive = ("INSERT INTO ArchiveVersions(id, local_path,\
                              modified_date,download_date,source_domain,url,\
                              html_title, ancestor, descendant, version,\
                              rss_title) VALUES (%(dbID)s, %(local_path)s,\
                              %(modified_date)s, %(download_date)s,\
                              %(source_domain)s, %(url)s, %(html_title)s,\
                              %(ancestor)s, %(descendant)s, %(version)s,\
                              %(rss_title)s)")

        self.delete_from_current = (
            "DELETE FROM CurrentVersions WHERE url = %s")

    # Store item data in DB.
    # First determine if a version of the article already exists,
    #   if so then 'migrate' the older version to the archive table.
    # Second store the new article in the current version table
    def process_item(self, item, spider):

        # Search the CurrentVersion table for a version of the article
        try:
            self.cursor.execute(self.compare_versions, (item['url'],))
        except mysql.connector.Error as err:
            print "Something went wrong in query: {}".format(err)

        # Save the result of the query. Must be done before the add,
        #   otherwise the result will be overwritten in the buffer
        old_version = self.cursor.fetchone()

        # If there is an existing article with the same URL, then move
        #   it to the ArchiveVersion table, and delete it from the
        #   CurrentVersion table
        if old_version is not None:
            old_version_list = {
                'dbID': old_version[0],
                'local_path': old_version[1],
                'modified_date': old_version[2],
                'download_date': old_version[3],
                'source_domain': old_version[4],
                'url': old_version[5],
                'html_title': old_version[6],
                'ancestor': old_version[7],
                'descendant': old_version[8],
                'version': old_version[9],
                'rss_title': old_version[10], }

            # Update the version number of the new article
            item['version'] = (old_version[9] + 1)

            # Update the ancestor attribute of the new article
            item['ancestor'] = old_version[0]

            # Delete the old version of the article from the
            # CurrentVerion table
            try:
                self.cursor.execute(
                    self.delete_from_current, (old_version[5], )
                    )
                self.conn.commit()
            except mysql.connector.Error as err:
                print "Something went wrong in delete: {}".format(err)

            # Add the old version to the ArchiveVersion table
            try:
                self.cursor.execute(self.insert_archive, old_version_list)
                self.conn.commit()
            except mysql.connector.Error as err:
                print "Something went wrong in archive: {}".format(err)

        current_version_list = {
            'local_path': item['local_path'],
            'modified_date': item['modified_date'],
            'download_date': item['download_date'],
            'source_domain': item['source_domain'],
            'url': item['url'],
            'html_title': item['html_title'],
            'ancestor': item['ancestor'],
            'descendant': item['descendant'],
            'version': item['version'],
            'rss_title': item['rss_title'], }

        # Add the new version of the article to
        # the CurrentVersion table
        try:
            self.cursor.execute(self.insert_current, current_version_list)
            self.conn.commit()

        except mysql.connector.Error as err:
            print "Something went wrong in commit: {}".format(err)

        logging.info("Article inserted into the database.")

        # populate item field with db ID number
        try:
            item['dbID'] = self.cursor.lastrowid
        except mysql.connector.Error as err:
            print "Something went wrong in id query: {}".format(err)

        if old_version is not None:
            # Update the old version's descendant attribute
            try:
                self.cursor.execute(
                    "UPDATE ArchiveVersions SET descendant=%s WHERE\
                    id=%s", (item['dbID'], old_version[0],)
                    )
            except mysql.connector.Error as err:
                print("Something went wrong in version update: {}"
                      .format(err))

        return item

    def close_spider(self, spider):
        # Close DB connection - garbage collection
        self.conn.close()

################
#
# Handles storage of the file on the local system
#
################


class LocalStorage(object):

    # Save the html and filename to the local storage folder
    def process_item(self, item, spider):

        # Add a log entry confirming the save
        logging.info("Saving to {}".format(item['absLocalPath']))

        # Ensure path exists
        dir_ = os.path.dirname(item['absLocalPath'])
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        # Write raw html to local file system
        with open(item['absLocalPath'], 'wb') as file_:
            file_.write(item['spiderResponse'].body)
            file_.close()

        return item
