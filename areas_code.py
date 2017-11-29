#!/usr/bin/python
# Copyright (C) 2017 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Daniel Izquierdo Cortazar <dizquierdo@bitergia.com>
#

from collections import namedtuple

import configparser
import logging

from elasticsearch import Elasticsearch, helpers

from grimoire_elk.elk.git import GitEnrich

from df_utils.filter import FilterRows
from enrich.enrich import FileType, FilePath, ToUTF8
from events.events import Git

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
    es_read = Elasticsearch([connection_input], use_ssl=True, verity_certs=True,
                            ca_cert=certifi.where(), timeout=100)

    credentials = ""
    if user_output:
        credentials = user_output + ":" + password_output + "@"

    connection_output = "http://" + credentials + host_output + ":"\
                        + port_output + "/" + path_output
    # es_write = Elasticsearch([connection_output], use_ssl=True,
    #                           verity_certs=True, ca_cert=certifi.where(),
    #                           scroll='300m', timeout=100)
    print("Output ES:", connection_output)
    es_write = Elasticsearch([connection_output])

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

    #TODO add port when parameter is available
    return GitEnrich(db_sortinghat=sh_name, db_user=sh_user,
                     db_password=sh_password, db_host=sh_host,
                     json_projects_map=projects_file_path)

def parse_config(general_section='General', sh_section='SortingHat',
                 es_section='ElasticSearch'):

    Config = namedtuple('Config', ['es_config', 'git_enrich', 'log_level', 'size'])

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

    return Config(es_config=es_config,
                  git_enrich=git_enrich,
                  log_level=log_level,
                  size=size)


def upload_data(events_df, es_write_index, es_write, uniq_id):
    # Uploading info to the new ES
    test = events_df.to_dict("index")
    docs = []
    for i in test.keys():
        header = {
            "_index": es_write_index,
            "_type": "item",
            "_id": int(uniq_id),
            "_source": test[i]
        }
        docs.append(header)
        uniq_id = uniq_id + 1
    logging.info("Written: " + str(len(docs)))
    helpers.bulk(es_write, docs)

    return uniq_id

# def add_sh_info(git_enrich, item):
#     # To ensure we have procesed the entity, uncomment following lines
#     # identities = git_enrich.get_identities(item)
#     # SortingHat.add_identities(git_enrich.sh_db, identities, git_enrich.get_connector_name())
#
#     # Add the grimoire_creation_date to the raw item
#     # It is used for getting the right affiliation
#     item.update(git_enrich.get_grimoire_fields(item["data"]["AuthorDate"], "commit"))
#     sh_identity = git_enrich.get_item_sh(item)
#
#     item['data']['author_id'] = sh_identity['author_id']
#     item['data']['author_org_name'] = sh_identity['author_org_name']
#     item['data']['author_name'] = sh_identity['author_name']
#     item['data']['author_uuid'] = sh_identity['author_uuid']
#     item['data']['author_domain'] = sh_identity['author_domain']
#     item['data']['author_user_name'] = sh_identity['author_user_name']
#     item['data']['author_bot'] = sh_identity['author_bot']
#
#     return item

# def add_project_info(git_enrich, item):
#     project_item = git_enrich.get_item_project(item)
#     item['data']['project'] = sh_identity['author_bot']


def analyze_git(es_read, es_write, es_read_index, es_write_index, git_enrich,
                size):

    es_write.indices.delete(es_write_index, ignore=[400, 404])
    es_write.indices.create(es_write_index, body=MAPPING_GIT)

    logging.info("Start reading items...")

    query = {"query": {"match_all" :{}}}

    # s = Search(using=es_read, index=es_read_index)
    # s.params(scroll=1)
    # s.extra(size=10)

    #s.execute()

    commits = []
    cont = 1
    uniq_id = 1

    #for hit in s.scan():
    for hit in helpers.scan(es_read, query, scroll='300m', index=es_read_index):
        item = hit["_source"]

        # SH information, this should be done while eventizing
        #item = add_sh_info(git_enrich, item)
        #logging.info("SH info  a +dstr(ed to ite)m " + str(cont))

        # TODO Project enrichment should be done in proper pandas style
        #add_project_info(git_enrich, item)

        commits.append(item)

        if cont % size == 0:
            logging.info("Total Items read: " + str(cont))
            logging.info("New commits: " + str(len(commits)))

            # Create events from commits
            # TODO add tests for eventize method
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

            #logging.info(events_df)
            logging.info("New Filetype events: " + str(len(events_df)))

            # Split filepath info
            enriched_filepath = FilePath(events_df)
            events_df = enriched_filepath.enrich('filepath')

            #logging.info(events_df)
            logging.info("New Filepath events: " + str(len(events_df)))

            # Deal with surrogates
            convert = ToUTF8(events_df)
            events_df = convert.enrich(["owner"])

            logging.info("Final new events: " + str(len(events_df)))

            commits = []

            uniq_id = upload_data(events_df, es_write_index, es_write, uniq_id)

        cont = cont + 1
    upload_data(events_df, es_write_index, es_write, uniq_id)

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
        logging.getLogger('elasticsearch').setLevel(logging.INFO)
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
                int(config.size))


if __name__ == "__main__":
    main()
