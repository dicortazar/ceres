# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   Daniel Izquierdo Cortazar <dizquierdo@bitergia.com>
#

from collections import namedtuple
from dateutil import parser as date_parser

import configparser
import logging
import sys

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Search

from grimoire_elk.enriched.git import GitEnrich

from cereslib.dfutils.filter import FilterRows
from cereslib.enrich.enrich import FileType, FilePath, ToUTF8
from cereslib.events.events import Git, Events

import certifi

# TODO read this from a file
MAPPING_GIT = \
    {
        "mappings": {
            "item": {
                "properties": {
                    "addedlines": {
                        "type": "long"
                    },
                    "author_bot": {
                        "type": "boolean"
                    },
                    "author_domain": {
                        "type": "keyword"
                    },
                    "author_id": {
                        "type": "keyword"
                    },
                    "author_name": {
                        "type": "keyword"
                    },
                    "author_org_name": {
                        "type": "keyword"
                    },
                    "author_user_name": {
                        "type": "keyword"
                    },
                    "author_uuid": {
                        "type": "keyword"
                    },
                    "committer": {
                        "type": "keyword"
                    },
                    "committer_date": {
                        "type": "date"
                    },
                    "date": {
                        "type": "date"
                    },
                    "eventtype": {
                        "type": "keyword"
                    },
                    "fileaction": {
                        "type": "keyword"
                    },
                    "filepath": {
                        "type": "keyword"
                    },
                    "files": {
                        "type": "long"
                    },
                    "filetype": {
                        "type": "keyword"
                    },
                    "file_name": {
                        "type": "keyword"
                    },
                    "file_ext": {
                        "type": "keyword"
                    },
                    "file_dir_name": {
                        "type": "keyword"
                    },
                    "file_path_list": {
                        "type": "keyword"
                    },
                    "grimoire_creation_date": {
                        "type": "date"
                    },
                    "hash": {
                        "type": "keyword"
                    },
                    "id": {
                        "type": "keyword"
                    },
                    "message": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "metadata__enriched_on": {
                        "type": "date"
                    },
                    "metadata__timestamp": {
                        "type": "date"
                    },
                    "metadata__updated_on": {
                        "type": "date"
                    },
                    "owner": {
                        "type": "keyword"
                    },
                    "perceval_uuid": {
                        "type": "keyword"
                    },
                    "project": {
                        "type": "keyword"
                    },
                    "project_1": {
                        "type": "keyword"
                    },
                    "removedlines": {
                        "type": "long"
                    },
                    "repository": {
                        "type": "keyword"
                    }
                }
            }
        }
    }

# Logging formats
LOG_FORMAT = "[%(asctime)s - %(levelname)s] - %(message)s"
DEBUG_LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s] - %(message)s"


def parse_es_section(parser, es_section):

    ES_config = namedtuple('ES_config',
                           ['es_read', 'es_write', 'es_read_git_index',
                            'es_write_git_index'])

    user = parser.get(es_section, 'user')
    password = parser.get(es_section, 'password')
    host = parser.get(es_section, 'host')
    port = parser.get(es_section, 'port')
    path = parser.get(es_section, 'path')
    es_read_git_index = parser.get(es_section, 'index_git_raw')

    host_output = parser.get(es_section, 'host_output')
    port_output = parser.get(es_section, 'port_output')
    user_output = parser.get(es_section, 'user_output')
    password_output = parser.get(es_section, 'password_output')
    path_output = parser.get(es_section, 'path_output')
    es_write_git_index = parser.get(es_section, 'index_git_output')

    connection_input = "https://" + user + ":" + password + "@" + host + ":"\
                       + port + "/" + path
    print("Input ES:", connection_input)
    # es_read = Elasticsearch([connection_input], use_ssl=True, verity_certs=False,
    #                         ca_cert=certifi.where(), timeout=100)
    es_read = Elasticsearch(['https://admin:admin@localhost:9200/'], verify_certs=False)
    credentials = ""
    if user_output:
        credentials = user_output + ":" + password_output + "@"

    connection_output = "https://" + credentials + host_output + ":"\
                        + port_output + "/" + path_output
    # es_write = Elasticsearch([connection_output], use_ssl=False,
    #                           verity_certs=False, ca_cert=certifi.where(),
    #                           scroll='300m', timeout=100)
    es_write = Elasticsearch(['https://admin:admin@localhost:9200/'], verify_certs=False)
    print("Output ES:", connection_output)

    return ES_config(es_read=es_read, es_write=es_write,
                     es_read_git_index=es_read_git_index,
                     es_write_git_index=es_write_git_index)


def parse_sh_section(parser, sh_section, general_section):

    sh_user = parser.get(sh_section, 'db_user')
    sh_password = parser.get(sh_section, 'password')
    sh_name = parser.get(sh_section, 'db_name')
    sh_host = parser.get(sh_section, 'host')
    sh_port = parser.get(sh_section, 'port')

    projects_file_path = parser.get(general_section, 'projects')

    # TODO add port when parameter is available
    return GitEnrich(db_sortinghat=sh_name, db_user=sh_user,
                     db_password=sh_password, db_host=sh_host,
                     json_projects_map=projects_file_path)


def parse_config(general_section='General', sh_section='SortingHat',
                 es_section='ElasticSearch'):

    Config = namedtuple('Config', ['es_config', 'git_enrich', 'log_level', 'size',
                                   'inc'])

    parser = configparser.ConfigParser()
    conf_file = '.settings'
    fd = open(conf_file, 'r')
    parser.read_file(fd)
    fd.close()

    es_config = parse_es_section(parser, es_section=es_section)
    git_enrich = parse_sh_section(parser, general_section=general_section,
                                  sh_section=sh_section)

    log_level = parser.get(general_section, 'log_level')
    size = parser.get(general_section, 'size')
    inc = parser.get(general_section, 'inc')

    return Config(es_config=es_config,
                  git_enrich=git_enrich,
                  log_level=log_level,
                  size=size,
                  inc=inc)


def upload_data(events_df, es_write_index, es_write):
    # Uploading info to the new ES
    rows = events_df.to_dict("index")
    docs = []
    for row_index in rows.keys():
        row = rows[row_index]
        item_id = row[Events.PERCEVAL_UUID] + "_" + row[Git.FILE_PATH] +\
            "_" + row[Git.FILE_EVENT]
        header = {
            "_index": es_write_index,
            "_type": "item",
            "_id": item_id,
            "_source": row
        }
        docs.append(header)
    helpers.bulk(es_write, docs)
    logging.info("Written: " + str(len(docs)))


def init_write_index(es_write, es_write_index):
    """Initializes ES write index
    """
    logging.info("Initializing index: " + es_write_index)
    es_write.indices.delete(es_write_index, ignore=[400, 404])
    es_write.indices.create(es_write_index, body=MAPPING_GIT)


def eventize_and_enrich(commits, git_enrich):
    logging.info("New commits: " + str(len(commits)))

    # Create events from commits
    git_events = Git(commits, git_enrich)
    events_df = git_events.eventize(2)

    logging.info("New events: " + str(len(events_df)))

    # Filter information
    data_filtered = FilterRows(events_df)
    events_df = data_filtered.filter_(["filepath"], "-")

    logging.info("New events filtered: " + str(len(events_df)))

    # Add filetype info
    enriched_filetype = FileType(events_df)
    events_df = enriched_filetype.enrich('filepath')

    logging.info("New Filetype events: " + str(len(events_df)))

    # Split filepath info
    enriched_filepath = FilePath(events_df)
    events_df = enriched_filepath.enrich('filepath')

    logging.info("New Filepath events: " + str(len(events_df)))

    # Deal with surrogates
    convert = ToUTF8(events_df)
    events_df = convert.enrich(["owner"])

    logging.info("Final new events: " + str(len(events_df)))

    return events_df


def analyze_git(es_read, es_write, es_read_index, es_write_index, git_enrich,
                size, incremental):

    query = {"match_all": {}}
    sort = [{"metadata__timestamp": {"order": "asc"}}]

    if incremental.lower() == 'true':
        search = Search(using=es_write, index=es_write_index)
        # from:to parameters (=> from: 0, size: 0)
        search = search[0:0]
        search = search.aggs.metric('max_date', 'max', field='metadata__timestamp')

        try:
            response = search.execute()

            if response.to_dict()['aggregations']['max_date']['value'] is None:
                msg = "No data for 'metadata__timestamp' field found in "
                msg += es_write_index + " index"
                logging.warning(msg)
                init_write_index(es_write, es_write_index)

            else:
                # Incremental case: retrieve items from last item in ES write index
                max_date = response.to_dict()['aggregations']['max_date']['value_as_string']
                max_date = date_parser.parse(max_date).isoformat()

                logging.info("Starting retrieval from: " + max_date)
                query = {"range": {"metadata__timestamp": {"gte": max_date}}}

        except NotFoundError:
            logging.warning("Index not found: " + es_write_index)
            init_write_index(es_write, es_write_index)

    else:
        init_write_index(es_write, es_write_index)

    search_query = {
        "query": query,
        "sort": sort
    }

    logging.info(search_query)

    logging.info("Start reading items...")

    commits = []
    cont = 0

    for hit in helpers.scan(es_read, search_query, scroll='300m', index=es_read_index,
                            preserve_order=True):

        cont = cont + 1

        item = hit["_source"]
        commits.append(item)
        logging.debug("[Hit] metadata__timestamp: " + item['metadata__timestamp'])

        if cont % size == 0:
            logging.info("Total Items read: " + str(cont))

            events_df = eventize_and_enrich(commits, git_enrich)
            upload_data(events_df, es_write_index, es_write)

            commits = []
            events_df = None

    # In case we have some commits pending, process them
    if len(commits) > 0:
        logging.info("Total Items read: " + str(cont))
        events_df = eventize_and_enrich(commits, git_enrich)
        upload_data(events_df, es_write_index, es_write)


def configure_logging(info=False, debug=False):
    """Configure logging
    The function configures log messages. By default, log messages
    are sent to stderr. Set the parameter `debug` to activate the
    debug mode.
    :param debug: set the debug mode
    """
    if info:
        logging.basicConfig(level=logging.INFO,
                            format=LOG_FORMAT)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urrlib3').setLevel(logging.WARNING)
        logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    elif debug:
        logging.basicConfig(level=logging.DEBUG,
                            format=DEBUG_LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.WARNING,
                            format=LOG_FORMAT)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urrlib3').setLevel(logging.WARNING)
        logging.getLogger('elasticsearch').setLevel(logging.WARNING)


def main():

    config = parse_config()

    if config.log_level == 'info':
        configure_logging(info=True)
    elif config.log_level == 'debug':
        configure_logging(debug=True)
    else:
        configure_logging()

    es_config = config.es_config

    analyze_git(es_config.es_read,
                es_config.es_write,
                es_config.es_read_git_index,
                es_config.es_write_git_index,
                config.git_enrich,
                int(config.size),
                incremental=config.inc)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        s = "\n\nReceived Ctrl-C or other break signal. Exiting.\n"
        sys.stdout.write(s)
        sys.exit(0)
    except RuntimeError as e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
