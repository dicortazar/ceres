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

from datetime import datetime as dt

import pandas

from grimoirelab_toolkit.datetime import str_to_datetime
from grimoire_elk.enriched.sortinghat_gelk import SortingHat


class Events(object):
    """ Class that 'eventizes' information for a given dataset.

    This class aims at providing with some granularity all of the events
    of a pre-formatted item. This is expected to help in later steps
    during the visualization platform.
    """

    META_TIMESTAMP = "metadata__timestamp"
    META_UPDATED_ON = "metadata__updated_on"
    META_ENRICHED_ON = "metadata__enriched_on"

    GRIMOIRE_CREATION_DATE = "grimoire_creation_date"
    PROJECT = "project"
    PROJECT_1 = "project_1"
    PERCEVAL_UUID = "perceval_uuid"

    SH_AUTHOR_ID = "author_id"
    SH_AUTHOR_ORG_NAME = "author_org_name"
    SH_AUTHOR_NAME = "author_name"
    SH_AUTHOR_UUID = "author_uuid"
    SH_AUTHOR_DOMAIN = "author_domain"
    SH_AUTHOR_USER_NAME = "author_user_name"
    SH_AUTHOR_BOT = "author_bot"
    SH_AUTHOR_MULTI_ORG_NAMES = "author_multi_org_names"

    UNKNOWN = 'Unknown'

    def __init__(self, items, enrich):
        """ Main constructor of the class

        :param items: original list of JSON that contains all info about a commit
        :type items: list
        :param enrich:
        :type enrich: grimoire_elk.elk.enrich.Enrich
        """

        self.items = items
        self.enrich = enrich

    def _add_metadata(self, df_columns, item):
        metadata__timestamp = item["metadata__timestamp"]
        metadata__updated_on = item["metadata__updated_on"]
        metadata__enriched_on = dt.utcnow().isoformat()

        df_columns[Events.META_TIMESTAMP].append(metadata__timestamp)
        df_columns[Events.META_UPDATED_ON].append(metadata__updated_on)
        df_columns[Events.META_ENRICHED_ON].append(metadata__enriched_on)

        # If called after '__add_sh_info', item will already contain
        # 'grimoire_creation_date'

        if Events.GRIMOIRE_CREATION_DATE in item:
            creation_date = item[Events.GRIMOIRE_CREATION_DATE]
        else:
            creation_date = str_to_datetime(item['data']['AuthorDate'])

        df_columns[Events.GRIMOIRE_CREATION_DATE].append(creation_date)

        # Perceval fields
        df_columns[Events.PERCEVAL_UUID].append(item['uuid'])

        # TODO add other common fields as 'perceval version', 'tag', 'origin'...

    def _add_general_info(self, df_columns, item):

        project_item = self.enrich.get_item_project(item)
        df_columns[Events.PROJECT].append(project_item[Events.PROJECT])
        df_columns[Events.PROJECT_1].append(project_item[Events.PROJECT_1])

    def _add_sh_info(self, df_columns, item, update_sh_db=False):

        # To ensure we have procesed the entity
        if update_sh_db:
            identities = self.enrich.get_identities(item)
            SortingHat.add_identities(self.enrich.sh_db, identities,
                                      self.enrich.get_connector_name())

        # Add the grimoire_creation_date to the raw item
        # It is used for getting the right affiliation
        item.update(self.enrich.get_grimoire_fields(
            item["data"]["AuthorDate"], "commit"))
        sh_identity = self.enrich.get_item_sh(item)

        author_id = sh_identity.get(Events.SH_AUTHOR_ID, Events.UNKNOWN)
        author_org_name = sh_identity.get(Events.SH_AUTHOR_ORG_NAME, Events.UNKNOWN)
        author_name = sh_identity.get(Events.SH_AUTHOR_NAME, Events.UNKNOWN)
        author_uuid = sh_identity.get(Events.SH_AUTHOR_UUID, Events.UNKNOWN)
        author_domain = sh_identity.get(Events.SH_AUTHOR_DOMAIN, Events.UNKNOWN)
        author_username = sh_identity.get(Events.SH_AUTHOR_USER_NAME, Events.UNKNOWN)
        author_bot = sh_identity.get(Events.SH_AUTHOR_BOT, False)
        author_multi_org_names = sh_identity.get(Events.SH_AUTHOR_MULTI_ORG_NAMES, [Events.UNKNOWN])

        df_columns[Events.SH_AUTHOR_ID].append(author_id)
        df_columns[Events.SH_AUTHOR_ORG_NAME].append(author_org_name)
        df_columns[Events.SH_AUTHOR_NAME].append(author_name)
        df_columns[Events.SH_AUTHOR_UUID].append(author_uuid)
        df_columns[Events.SH_AUTHOR_DOMAIN].append(author_domain)
        df_columns[Events.SH_AUTHOR_USER_NAME].append(author_username)
        df_columns[Events.SH_AUTHOR_BOT].append(author_bot)
        df_columns[Events.SH_AUTHOR_MULTI_ORG_NAMES].append(author_multi_org_names)

    def _init_common_fields(self, df_columns):
        # Metadata fields
        df_columns[Events.META_TIMESTAMP] = []
        df_columns[Events.META_UPDATED_ON] = []
        df_columns[Events.META_ENRICHED_ON] = []

        # Common fields
        df_columns[Events.GRIMOIRE_CREATION_DATE] = []
        df_columns[Events.PROJECT] = []
        df_columns[Events.PROJECT_1] = []
        df_columns[Events.PERCEVAL_UUID] = []

        # SortigHat information
        df_columns[Events.SH_AUTHOR_ID] = []
        df_columns[Events.SH_AUTHOR_ORG_NAME] = []
        df_columns[Events.SH_AUTHOR_NAME] = []
        df_columns[Events.SH_AUTHOR_UUID] = []
        df_columns[Events.SH_AUTHOR_DOMAIN] = []
        df_columns[Events.SH_AUTHOR_USER_NAME] = []
        df_columns[Events.SH_AUTHOR_BOT] = []
        df_columns[Events.SH_AUTHOR_MULTI_ORG_NAMES] = []

    def _add_common_fields(self, df_columns, item):
        self._add_metadata(df_columns, item)
        self._add_sh_info(df_columns, item)
        self._add_general_info(df_columns, item)

    @staticmethod
    def _add_common_events(events, df_columns):
        events[Events.META_TIMESTAMP] = df_columns[Events.META_TIMESTAMP]
        events[Events.META_UPDATED_ON] = df_columns[Events.META_UPDATED_ON]
        events[Events.META_ENRICHED_ON] = df_columns[Events.META_ENRICHED_ON]

        events[Events.GRIMOIRE_CREATION_DATE] = df_columns[Events.GRIMOIRE_CREATION_DATE]
        events[Events.PROJECT] = df_columns[Events.PROJECT]
        events[Events.PROJECT_1] = df_columns[Events.PROJECT_1]

        events[Events.PERCEVAL_UUID] = df_columns[Events.PERCEVAL_UUID]

        events[Events.SH_AUTHOR_ID] = df_columns[Events.SH_AUTHOR_ID]
        events[Events.SH_AUTHOR_ORG_NAME] = df_columns[Events.SH_AUTHOR_ORG_NAME]
        events[Events.SH_AUTHOR_NAME] = df_columns[Events.SH_AUTHOR_NAME]
        events[Events.SH_AUTHOR_UUID] = df_columns[Events.SH_AUTHOR_UUID]
        events[Events.SH_AUTHOR_DOMAIN] = df_columns[Events.SH_AUTHOR_DOMAIN]
        events[Events.SH_AUTHOR_USER_NAME] = df_columns[Events.SH_AUTHOR_USER_NAME]
        events[Events.SH_AUTHOR_BOT] = df_columns[Events.SH_AUTHOR_BOT]
        events[Events.SH_AUTHOR_MULTI_ORG_NAMES] = df_columns[Events.SH_AUTHOR_MULTI_ORG_NAMES]


class Bugzilla(Events):
    """ Class used to 'eventize' Bugzilla items

    This splits information of each item based on a pre-configured mapping.
    There are several levels of events. These levels were created as a way
    to have more or less time consuming generation of events.
    """

    EVENT_OPEN = "ISSUE_OPEN"

    # Fields supported by this module (when a DataFrame is returned)
    ISSUE_ID = "id"
    ISSUE_EVENT = "eventtype"
    ISSUE_DATE = "date"
    ISSUE_OWNER = "owner"

    def __bug_photo(self, item):
        """ Retrieves basic information about the current status of the bug

        That current status contains the photo of the bug at the moment of
        the analysis. These fields will be used later for create extra
        events
        """

    def __init__(self, items):
        """ Main constructor of the class

        :param items: original list of JSON that contains all info about a bug
        :type items: list
        """

        self.items = items

    def eventize(self, granularity):
        """ This splits the JSON information found at self.events into the
        several events. For this there are three different levels of time
        consuming actions: 1-soft, 2-medium and 3-hard.

        Level 1 provides events about open and closed issues.
        Level 2 provides events about the rest of the status updates.
        Level 3 provides events about the rest of the values in any of the
        fields.

        :param granularity: Levels of time consuming actions to calculate events
        :type granularity: integer

        :returns: Pandas dataframe with splitted events.
        :rtype: pandas.DataFrame
        """

        issue = {}
        issue[Bugzilla.ISSUE_ID] = []
        issue[Bugzilla.ISSUE_EVENT] = []
        issue[Bugzilla.ISSUE_DATE] = []
        issue[Bugzilla.ISSUE_OWNER] = []

        events = pandas.DataFrame()

        for item in self.items:
            bug_data = item["data"]
            if granularity == 1:
                # Open Date: filling a new event
                issue[Bugzilla.ISSUE_ID].append(bug_data['bug_id'][0]['__text__'])
                issue[Bugzilla.ISSUE_EVENT].append(Bugzilla.EVENT_OPEN)
                issue[Bugzilla.ISSUE_DATE].append(str_to_datetime(bug_data['creation_ts'][0]['__text__']))
                issue[Bugzilla.ISSUE_OWNER].append(bug_data['reporter'][0]["__text__"])

                # Adding the rest of the status updates (if there were any)
                if 'activity' in bug_data.keys():
                    activity = bug_data["activity"]
                    for change in activity:
                        # if change["What"] == "Status":
                        # Filling a new event
                        issue[Bugzilla.ISSUE_ID].append(bug_data['bug_id'][0]['__text__'])
                        issue[Bugzilla.ISSUE_EVENT].append("ISSUE_" + change["Added"])
                        issue[Bugzilla.ISSUE_DATE].append(str_to_datetime(change["When"]))
                        issue[Bugzilla.ISSUE_OWNER].append(change["Who"])

            if granularity == 2:
                # TBD Let's produce an index with all of the changes.
                #    Let's have in mind the point about having the changes of initiating
                #    the ticket.
                pass

            if granularity == 3:
                # TDB
                pass

        # Done in this way to have an order (and not a direct cast)
        events[Bugzilla.ISSUE_ID] = issue[Bugzilla.ISSUE_ID]
        events[Bugzilla.ISSUE_EVENT] = issue[Bugzilla.ISSUE_EVENT]
        events[Bugzilla.ISSUE_DATE] = issue[Bugzilla.ISSUE_DATE]
        events[Bugzilla.ISSUE_OWNER] = issue[Bugzilla.ISSUE_OWNER]

        return events


class BugzillaRest(Events):
    """ Class used to eventize Bugzilla Rest items

    This splits each item information based on a pre-existing mapping.
    """

    EVENT_OPEN = "ISSUE_OPEN"

    # Fields supported by this module (when a DataFrame is returned)
    ISSUE_ID = "id"
    ISSUE_EVENT = "eventtype"
    ISSUE_DATE = "date"
    ISSUE_OWNER = "owner"
    ISSUE_ADDED = "added"
    ISSUE_REMOVED = "removed"

    def __init__(self, items):
        """ Main constructor of the class

        :param items: original list of JSON that contains all info about a bug
        :type items: list
        """

        self.items = items

    def eventize(self, granularity):
        """ This splits the JSON information found at self.events into the
        several events. For this there are three different levels of time
        consuming actions: 1-soft, 2-medium and 3-hard.

        Level 1 provides events about open and closed issues.
        Level 2 provides events about the rest of the status updates.
        Level 3 provides events about the rest of the values in any of the
        fields.

        :param granularity: Levels of time consuming actions to calculate events
        :type granularity: integer

        :returns: Pandas dataframe with splitted events.
        :rtype: pandas.DataFrame
        """

        issue = {}
        issue[BugzillaRest.ISSUE_ID] = []
        issue[BugzillaRest.ISSUE_EVENT] = []
        issue[BugzillaRest.ISSUE_DATE] = []
        issue[BugzillaRest.ISSUE_OWNER] = []
        issue[BugzillaRest.ISSUE_ADDED] = []
        issue[BugzillaRest.ISSUE_REMOVED] = []

        events = pandas.DataFrame()

        for item in self.items:
            bug_data = item["data"]
            if granularity == 1:
                # Open Date: filling a new event
                issue[BugzillaRest.ISSUE_ID].append(bug_data['id'])
                issue[BugzillaRest.ISSUE_EVENT].append(BugzillaRest.EVENT_OPEN)
                issue[BugzillaRest.ISSUE_DATE].append(str_to_datetime(bug_data['creation_time']))
                issue[BugzillaRest.ISSUE_OWNER].append(bug_data['creator_detail']["real_name"])
                issue[BugzillaRest.ISSUE_ADDED].append("-")
                issue[BugzillaRest.ISSUE_REMOVED].append("-")

                # Adding the rest of the status updates (if there were any)
                if 'history' in bug_data.keys():
                    history = bug_data["history"]
                    for step in history:
                        # Filling a new event
                        who = step["who"]
                        when = str_to_datetime(step["when"])
                        changes = step["changes"]
                        for change in changes:
                            issue[BugzillaRest.ISSUE_ID].append(bug_data['id'])
                            issue[BugzillaRest.ISSUE_EVENT].append("ISSUE_" + change["field_name"])
                            issue[BugzillaRest.ISSUE_ADDED].append(change["added"])
                            issue[BugzillaRest.ISSUE_REMOVED].append(change["removed"])
                            issue[BugzillaRest.ISSUE_DATE].append(when)
                            issue[BugzillaRest.ISSUE_OWNER].append(who)

            if granularity == 2:
                # TBD Let's produce an index with all of the changes.
                #    Let's have in mind the point about having the changes of initiating
                #    the ticket.
                pass

            if granularity == 3:
                # TDB
                pass

        # Done in this way to have an order (and not a direct cast)
        events[BugzillaRest.ISSUE_ID] = issue[BugzillaRest.ISSUE_ID]
        events[BugzillaRest.ISSUE_EVENT] = issue[BugzillaRest.ISSUE_EVENT]
        events[BugzillaRest.ISSUE_DATE] = issue[BugzillaRest.ISSUE_DATE]
        events[BugzillaRest.ISSUE_OWNER] = issue[BugzillaRest.ISSUE_OWNER]
        events[BugzillaRest.ISSUE_ADDED] = issue[BugzillaRest.ISSUE_ADDED]
        events[BugzillaRest.ISSUE_REMOVED] = issue[BugzillaRest.ISSUE_REMOVED]

        return events


class Git(Events):
    """ Class used to 'eventize' Git items

    This splits information of each item based on a pre-configured mapping.
    There are several levels of events. These levels were created as a way
    to have more or less time consuming generation of events.
    """

    EVENT_COMMIT = "COMMIT"
    EVENT_FILE = "FILE_"

    # Fields supported by this module (when a DataFrame is returned)
    COMMIT_ID = "id"
    COMMIT_EVENT = "eventtype"
    COMMIT_DATE = "date"
    COMMIT_OWNER = "owner"
    COMMIT_COMMITTER = "committer"
    COMMIT_COMMITTER_DATE = "committer_date"
    COMMIT_REPOSITORY = "repository"
    COMMIT_MESSAGE = "message"
    COMMIT_NUM_FILES = "num_files"
    COMMIT_ADDED_LINES = "num_added_lines"
    COMMIT_REMOVED_LINES = "num_removed_lines"

    COMMIT_HASH = "hash"

    AUTHOR_DOMAIN = "git_author_domain"

    FILE_EVENT = "fileaction"
    FILE_PATH = "filepath"
    FILE_ADDED_LINES = "addedlines"
    FILE_REMOVED_LINES = "removedlines"
    FILE_FILES = "files"

    def __init__(self, items, git_enrich):
        """ Main constructor of the class

        :param items: original list of JSON that contains all info about a commit
        :type items: list
        :param git_enrich:
        :type enrich: grimoire_elk.elk.git.GitEnrich
        """

        super().__init__(items=items, enrich=git_enrich)

    def __add_commit_info(self, df_columns, item):

        commit_data = item["data"]
        repository = item["origin"]

        creation_date = str_to_datetime(commit_data['AuthorDate'])

        df_columns[Git.COMMIT_HASH].append(commit_data['commit'])

        df_columns[Git.COMMIT_ID].append(commit_data['commit'])
        df_columns[Git.COMMIT_EVENT].append(Git.EVENT_COMMIT)
        df_columns[Git.COMMIT_DATE].append(creation_date)
        df_columns[Git.COMMIT_OWNER].append(commit_data['Author'])
        df_columns[Git.COMMIT_COMMITTER].append(commit_data['Commit'])
        df_columns[Git.COMMIT_COMMITTER_DATE].append(str_to_datetime(commit_data['CommitDate']))
        df_columns[Git.COMMIT_REPOSITORY].append(repository)
        if 'message' in commit_data.keys():
            df_columns[Git.COMMIT_MESSAGE].append(commit_data['message'])
        else:
            df_columns[Git.COMMIT_MESSAGE].append('')

        author_domain = self.enrich.get_identity_domain(self.enrich.get_sh_identity(item, 'Author'))
        df_columns[Git.AUTHOR_DOMAIN].append(author_domain)

    def eventize(self, granularity):
        """ This splits the JSON information found at self.events into the
        several events. For this there are three different levels of time
        consuming actions: 1-soft, 2-medium and 3-hard.

        Level 1 provides events about commits
        Level 2 provides events about files
        Level 3 provides other events (not used so far)

        :param granularity: Levels of time consuming actions to calculate events
        :type granularity: integer

        :returns: Pandas dataframe with splitted events.
        :rtype: pandas.DataFrame
        """

        df_columns = {}
        # Init common columns
        self._init_common_fields(df_columns)

        # First level granularity
        df_columns[Git.COMMIT_ID] = []
        df_columns[Git.COMMIT_EVENT] = []
        df_columns[Git.COMMIT_DATE] = []
        df_columns[Git.COMMIT_OWNER] = []
        df_columns[Git.COMMIT_COMMITTER] = []
        df_columns[Git.COMMIT_COMMITTER_DATE] = []
        df_columns[Git.COMMIT_REPOSITORY] = []
        df_columns[Git.COMMIT_MESSAGE] = []
        df_columns[Git.COMMIT_NUM_FILES] = []
        df_columns[Git.COMMIT_ADDED_LINES] = []
        df_columns[Git.COMMIT_REMOVED_LINES] = []
        df_columns[Git.COMMIT_HASH] = []
        df_columns[Git.AUTHOR_DOMAIN] = []

        # Second level of granularity
        df_columns[Git.FILE_FILES] = []
        df_columns[Git.FILE_EVENT] = []
        df_columns[Git.FILE_PATH] = []
        df_columns[Git.FILE_ADDED_LINES] = []
        df_columns[Git.FILE_REMOVED_LINES] = []

        events = pandas.DataFrame()

        for item in self.items:
            commit_data = item["data"]
            if granularity == 1:
                self._add_common_fields(df_columns, item)
                self.__add_commit_info(df_columns, item)

                added_lines = 0
                removed_lines = 0
                files = commit_data["files"]
                df_columns[Git.COMMIT_NUM_FILES] = int(len(files))
                for f in files:
                    if "added" in f.keys() and f["added"] != "-":
                        added_lines = added_lines + int(f["added"])
                    if "removed" in f.keys() and f["removed"] != "-":
                        removed_lines = removed_lines + int(f["removed"])
                df_columns[Git.COMMIT_ADDED_LINES] = added_lines
                df_columns[Git.COMMIT_REMOVED_LINES] = removed_lines

            # TODO: this will fail if no files are found in a commit (eg: merge)
            if granularity == 2:
                # Add extra info about files actions, if there were any
                if "files" in commit_data.keys():
                    files = commit_data["files"]
                    nfiles = 0
                    for f in files:
                        if "action" in f.keys():
                            nfiles += 1

                    for f in files:
                        self._add_common_fields(df_columns, item)
                        self.__add_commit_info(df_columns, item)

                        df_columns[Git.FILE_FILES].append(nfiles)

                        if "action" in f.keys():
                            df_columns[Git.FILE_EVENT].append(Git.EVENT_FILE + f["action"])
                        else:
                            df_columns[Git.FILE_EVENT].append("-")

                        if "file" in f.keys():
                            df_columns[Git.FILE_PATH].append(f["file"])
                        else:
                            df_columns[Git.FILE_PATH].append("-")

                        if "added" in f.keys():
                            if f["added"] == "-":
                                df_columns[Git.FILE_ADDED_LINES].append(0)
                            else:
                                df_columns[Git.FILE_ADDED_LINES].append(int(f["added"]))
                        else:
                            df_columns[Git.FILE_ADDED_LINES].append(0)

                        if "removed" in f.keys():
                            if f["removed"] == "-":
                                df_columns[Git.FILE_REMOVED_LINES].append(0)
                            else:
                                df_columns[Git.FILE_REMOVED_LINES].append(int(f["removed"]))
                        else:
                            df_columns[Git.FILE_REMOVED_LINES].append(0)

                else:
                    print("Merge found, doing nothing...")

            if granularity == 3:
                # TDB
                pass

        # Done in this way to have an order (and not a direct cast)
        self._add_common_events(events, df_columns)

        events[Git.COMMIT_ID] = df_columns[Git.COMMIT_ID]
        events[Git.COMMIT_EVENT] = df_columns[Git.COMMIT_EVENT]
        events[Git.COMMIT_DATE] = df_columns[Git.COMMIT_DATE]
        events[Git.COMMIT_OWNER] = df_columns[Git.COMMIT_OWNER]
        events[Git.COMMIT_COMMITTER] = df_columns[Git.COMMIT_COMMITTER]
        events[Git.COMMIT_COMMITTER_DATE] = df_columns[Git.COMMIT_COMMITTER_DATE]
        events[Git.COMMIT_REPOSITORY] = df_columns[Git.COMMIT_REPOSITORY]
        events[Git.COMMIT_MESSAGE] = df_columns[Git.COMMIT_MESSAGE]
        events[Git.COMMIT_HASH] = df_columns[Git.COMMIT_HASH]
        events[Git.AUTHOR_DOMAIN] = df_columns[Git.AUTHOR_DOMAIN]

        if granularity == 1:
            events[Git.COMMIT_NUM_FILES] = df_columns[Git.COMMIT_NUM_FILES]
            events[Git.COMMIT_ADDED_LINES] = df_columns[Git.COMMIT_ADDED_LINES]
            events[Git.COMMIT_REMOVED_LINES] = df_columns[Git.COMMIT_REMOVED_LINES]
        if granularity == 2:
            events[Git.FILE_FILES] = df_columns[Git.FILE_FILES]
            events[Git.FILE_EVENT] = df_columns[Git.FILE_EVENT]
            events[Git.FILE_PATH] = df_columns[Git.FILE_PATH]
            events[Git.FILE_ADDED_LINES] = df_columns[Git.FILE_ADDED_LINES]
            events[Git.FILE_REMOVED_LINES] = df_columns[Git.FILE_REMOVED_LINES]

        return events


class Gerrit(Events):
    """ Class used to 'eventize' Gerrit items

    This splits information of each item based on a pre-configured mapping.
    There are several levels of events. These levels were created as a way
    to have more or less time consuming generation of events.
    """

    EVENT_OPEN = "CHANGESET_SENT"
    EVENT_ = "CHANGESET_"

    # Fields supported by this module (when a DataFrame is returned)
    CHANGESET_ID = "id"
    CHANGESET_EVENT = "eventtype"
    CHANGESET_DATE = "date"
    CHANGESET_OWNER = "owner"
    CHANGESET_EMAIL = "email"
    CHANGESET_VALUE = "value"
    CHANGESET_REPO = "repository"

    def __init__(self, items):
        """ Main constructor of the class

        :param items: original list of JSON that contains all info about a commit
        :type items: list
        """

        self.items = items

    def eventize(self, granularity):
        """ This splits the JSON information found at self.events into the
        several events. For this there are three different levels of time
        consuming actions: 1-soft, 2-medium and 3-hard.

        Level 1 provides events about commits
        Level 2 provides events about files
        Level 3 provides other events (not used so far)

        :param granularity: Levels of time consuming actions to calculate events
        :type granularity: integer

        :returns: Pandas dataframe with splitted events.
        :rtype: pandas.DataFrame
        """

        changeset = {}
        # First level granularity
        changeset[Gerrit.CHANGESET_ID] = []
        changeset[Gerrit.CHANGESET_EVENT] = []
        changeset[Gerrit.CHANGESET_DATE] = []
        changeset[Gerrit.CHANGESET_OWNER] = []
        changeset[Gerrit.CHANGESET_EMAIL] = []
        changeset[Gerrit.CHANGESET_VALUE] = []
        changeset[Gerrit.CHANGESET_REPO] = []

        events = pandas.DataFrame()

        for item in self.items:
            changeset_data = item["data"]
            if granularity >= 1:
                # Changeset submission date: filling a new event
                changeset[Gerrit.CHANGESET_ID].append(changeset_data["number"])
                changeset[Gerrit.CHANGESET_EVENT].append(Gerrit.EVENT_OPEN)
                changeset[Gerrit.CHANGESET_DATE].append(dt.fromtimestamp(int(changeset_data["createdOn"])))
                changeset[Gerrit.CHANGESET_REPO].append(changeset_data["project"])
                value = email = "notknown"
                if "name" in changeset_data["owner"].keys():
                    value = changeset_data["owner"]["name"]
                elif "username" in changeset_data["owner"].keys():
                    value = changeset_data["owner"]["username"]
                elif "email" in changeset_data["owner"].keys():
                    value = changeset_data["owner"]["email"]
                    email = changeset_data["owner"]["email"]
                changeset[Gerrit.CHANGESET_OWNER].append(value)
                changeset[Gerrit.CHANGESET_EMAIL].append(email)
                changeset[Gerrit.CHANGESET_VALUE].append(-10)

                # Adding the closing status updates (if there was any)
                if changeset_data["status"] == 'ABANDONED' or \
                   changeset_data["status"] == 'MERGED':
                    closing_date = dt.fromtimestamp(int(changeset_data["lastUpdated"]))
                    changeset[Gerrit.CHANGESET_ID].append(changeset_data["number"])
                    changeset[Gerrit.CHANGESET_EVENT].append(Gerrit.EVENT_ +
                                                             changeset_data["status"])
                    changeset[Gerrit.CHANGESET_DATE].append(closing_date)
                    changeset[Gerrit.CHANGESET_REPO].append(changeset_data["project"])
                    value = email = "notknown"
                    if "name" in changeset_data["owner"].keys():
                        value = changeset_data["owner"]["name"]
                    if "username" in changeset_data["owner"].keys():
                        value = changeset_data["owner"]["username"]
                    if "email" in changeset_data["owner"].keys():
                        value = changeset_data["owner"]["email"]
                        email = changeset_data["owner"]["email"]
                    changeset[Gerrit.CHANGESET_OWNER].append(value)
                    changeset[Gerrit.CHANGESET_EMAIL].append(email)
                    changeset[Gerrit.CHANGESET_VALUE].append(-10)

            if granularity >= 2:
                # Adding extra info about the patchsets
                for patchset in changeset_data["patchSets"]:
                    changeset[Gerrit.CHANGESET_ID].append(changeset_data["number"])
                    changeset[Gerrit.CHANGESET_EVENT].append(Gerrit.EVENT_ + "PATCHSET_SENT")
                    changeset[Gerrit.CHANGESET_DATE].append(
                        dt.fromtimestamp(int(patchset["createdOn"])))
                    changeset[Gerrit.CHANGESET_REPO].append(changeset_data["project"])
                    try:
                        email = "patchset_noname"
                        if "name" in patchset["author"].keys():
                            value = patchset["author"]["name"]
                        if "username" in patchset["author"].keys():
                            value = patchset["author"]["username"]
                        if "email" in patchset["author"].keys():
                            value = patchset["author"]["email"]
                            email = patchset["author"]["email"]
                    except KeyError:
                        value = "patchset_noname"
                    changeset[Gerrit.CHANGESET_OWNER].append(value)
                    changeset[Gerrit.CHANGESET_EMAIL].append(email)
                    changeset[Gerrit.CHANGESET_VALUE].append(-10)
                    # print (patchset)
                    if "approvals" in patchset.keys():
                        for approval in patchset["approvals"]:
                            if approval["type"] != "Code-Review":
                                continue
                            changeset[Gerrit.CHANGESET_ID].append(changeset_data["number"])
                            changeset[Gerrit.CHANGESET_EVENT].append(
                                Gerrit.EVENT_ +
                                "PATCHSET_APPROVAL_" + approval["type"])
                            changeset[Gerrit.CHANGESET_DATE].append(
                                dt.fromtimestamp(int(approval["grantedOn"])))
                            changeset[Gerrit.CHANGESET_REPO].append(changeset_data["project"])
                            email = "approval_noname"
                            if "name" in approval["by"].keys():
                                value = approval["by"]["name"]
                            elif "username" in approval["by"].keys():
                                value = approval["by"]["username"]
                            elif "email" in approval["by"].keys():
                                value = approval["by"]["email"]
                                email = approval["by"]["email"]
                            changeset[Gerrit.CHANGESET_OWNER].append(value)
                            changeset[Gerrit.CHANGESET_EMAIL].append(email)
                            changeset[Gerrit.CHANGESET_VALUE].append(int(approval["value"]))

            if granularity >= 3:
                # TDB
                pass

        # Done in this way to have an order (and not a direct cast)
        events[Gerrit.CHANGESET_ID] = changeset[Gerrit.CHANGESET_ID]
        events[Gerrit.CHANGESET_EVENT] = changeset[Gerrit.CHANGESET_EVENT]
        events[Gerrit.CHANGESET_DATE] = changeset[Gerrit.CHANGESET_DATE]
        events[Gerrit.CHANGESET_OWNER] = changeset[Gerrit.CHANGESET_OWNER]
        events[Gerrit.CHANGESET_EMAIL] = changeset[Gerrit.CHANGESET_EMAIL]
        events[Gerrit.CHANGESET_VALUE] = changeset[Gerrit.CHANGESET_VALUE]
        events[Gerrit.CHANGESET_REPO] = changeset[Gerrit.CHANGESET_REPO]

        return events


class Email(Events):
    """ Class used to 'eventize' mailing list items

    This splits information of each item based on a pre-configured mapping.
    There are several levels of events. These levels were created as a way
    to have more or less time consuming generation of events.
    """

    EVENT_OPEN = "EMAIL_SENT"

    # Fields supported by this module (when a DataFrame is returned)
    EMAIL_ID = "id"
    EMAIL_EVENT = "eventtype"
    EMAIL_DATE = "date"
    EMAIL_OWNER = "owner"
    EMAIL_SUBJECT = "subject"
    EMAIL_BODY = "body"
    EMAIL_ORIGIN = "mailinglist"

    def __init__(self, items):
        """ Main constructor of the class

        :param items: original list of JSON that contains all info about a commit
        :type items: list
        """

        self.items = items

    def eventize(self, granularity):
        """ This splits the JSON information found at self.events into the
        several events. For this there are three different levels of time
        consuming actions: 1-soft, 2-medium and 3-hard.

        Level 1 provides events about emails
        Level 2 not implemented
        Level 3 not implemented

        :param granularity: Levels of time consuming actions to calculate events
        :type granularity: integer

        :returns: Pandas dataframe with splitted events.
        :rtype: pandas.DataFrame
        """

        email = {}
        # First level granularity
        email[Email.EMAIL_ID] = []
        email[Email.EMAIL_EVENT] = []
        email[Email.EMAIL_DATE] = []
        email[Email.EMAIL_OWNER] = []
        email[Email.EMAIL_SUBJECT] = []
        email[Email.EMAIL_BODY] = []
        email[Email.EMAIL_ORIGIN] = []

        events = pandas.DataFrame()

        for item in self.items:
            origin = item["origin"]
            email_data = item["data"]
            if granularity == 1:
                # Changeset submission date: filling a new event
                email[Email.EMAIL_ID].append(email_data["Message-ID"])
                email[Email.EMAIL_EVENT].append(Email.EVENT_OPEN)
                try:
                    email[Email.EMAIL_DATE].append(str_to_datetime(email_data["Date"], ignoretz=True))
                except KeyError:
                    email[Email.EMAIL_DATE].append(str_to_datetime("1970-01-01"))
                email[Email.EMAIL_OWNER].append(email_data["From"])
                email[Email.EMAIL_SUBJECT].append(email_data["Subject"])
                try:
                    email[Email.EMAIL_BODY].append(email_data["body"]["plain"])
                except KeyError:
                    email[Email.EMAIL_BODY].append("None")
                email[Email.EMAIL_ORIGIN].append(origin)

            if granularity == 2:
                # TDB
                pass

            if granularity == 3:
                # TDB
                pass

        # Done in this way to have an order (and not a direct cast)
        events[Email.EMAIL_ID] = email[Email.EMAIL_ID]
        events[Email.EMAIL_EVENT] = email[Email.EMAIL_EVENT]
        events[Email.EMAIL_DATE] = email[Email.EMAIL_DATE]
        events[Email.EMAIL_OWNER] = email[Email.EMAIL_OWNER]
        events[Email.EMAIL_SUBJECT] = email[Email.EMAIL_SUBJECT]
        events[Email.EMAIL_BODY] = email[Email.EMAIL_BODY]
        events[Email.EMAIL_ORIGIN] = email[Email.EMAIL_ORIGIN]

        return events
