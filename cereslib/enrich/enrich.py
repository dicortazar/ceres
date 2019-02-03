#!/usr/bin/python
# Copyright (C) 2016 Bitergia
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
#   Alberto Perez <alpgarcia@bitergia.com>
#


import pandas

import numpy as np

import re


class Enrich(object):
    """ Class that enriches information for a given dataset.

    Its usual way of working consists of providing a new columns
    in the dataframe from a given entry. This allows to keep
    adding extra information to the basics coming from the original
    data source.

    An example of this would be the addition of the affiliation,
    gender, workload adequacy and other metrics for a given commmit.
    """


class PairProgramming(Enrich):
    """ This class splits a commit into 2 of them according to the author name.

    There are cases where two developers have participated in a commit.
    One of the ways to identify those is claiming that commit as author, but
    also as a committer.

    Depending on the process of the organization, this may indicate a review
    process, a peer development process or even nothing.

    This class should be called when committer an author usually participate
    in the development of such commit.
    """

    def __init__(self, commits):
        """ Main constructor of the class

        :param commits: original list of commits
        :type commits: dataframe with commit information
        """

        self.commits = commits

    def enrich(self, column1, column2):
        """ This class splits those commits where column1 and column2
        values are different

        :param column1: column to compare to column2
        :param column2: column to compare to column1
        :type column1: string
        :type column2: string

        :returns: self.commits with duplicated rows where the values at
            columns are different. The original row remains while the second
            row contains in column1 and 2 the value of column2.
        :rtype: pandas.DataFrame
        """

        if column1 not in self.commits.columns or \
           column2 not in self.commits.columns:
            return self.commits

        # Select rows where values in column1 are different from
        # values in column2
        pair_df = self.commits[self.commits[column1] != self.commits[column2]]
        new_values = list(pair_df[column2])
        # Update values from column2
        pair_df[column1] = new_values

        # This adds at the end of the original dataframe those rows duplicating
        # information and updating the values in column1
        return self.commits.append(pair_df)


class FileType(Enrich):
    """ This class creates a new column with the file type
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided

        :param data: original dataframe
        : type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column):
        """ This method adds a new column depending on the extension
        of the file.

        :param column: column where the file path is found
        :type column: string

        :return: returns the original dataframe with a new column named as
                 'filetype' that contains information about its extension
        :rtype: pandas.DataFrame
        """

        if column not in self.data:
            return self.data

        # Insert a new column with default values
        self.data["filetype"] = 'Other'

        # Insert 'Code' only in those rows that are
        # detected as being source code thanks to its extension
        reg = "\.c$|\.h$|\.cc$|\.cpp$|\.cxx$|\.c\+\+$|\.cp$|\.py$|\.js$|\.java$|\.rs$|\.go$"
        self.data.loc[self.data[column].str.contains(reg), 'filetype'] = 'Code'

        return self.data


class FilePath(Enrich):
    """ This class creates new columns with:
            * File extension
            * File path (excluding file name)
            * File name (excluding directories)
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided

        :param data: original dataframe
        : type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column):
        """ This method splits file path in new columns allowing further
        filtering on those particular path parts:
            * File extension
            * File directory name (full path excluding file name)
            * File name (excluding directories)
            * Path list including each directory/file as a separated element

        :param column: column where the file path is found
        :type column: string

        :return: returns the original dataframe with new columns named
                 'file_ext', 'file_dir_name', 'file_name', 'path_list'
        :rtype: pandas.DataFrame
        """

        if column not in self.data:
            return self.data

        # Insert new columns
        self.data['file_name'] = \
            self.data.apply(lambda row: row[column][row[column].rfind('/') + 1:],
                            axis=1)
        self.data['file_ext'] = \
            self.data.apply(lambda row:
                            '' if (row.file_name.rfind('.') == -1)
                            else row.file_name[row.file_name.rfind('.') + 1:],
                            axis=1)
        # To get correct dir name:
        # *  Replace multiple consecutive slashes by just one
        self.data['file_dir_name'] = self.data[column].str.replace('/+', '/')
        self.data['file_dir_name'] = \
            self.data.apply(lambda row:
                            row.file_dir_name if row.file_dir_name.startswith('/')
                            else '/' + row.file_dir_name,
                            axis=1)
        self.data['file_dir_name'] = \
            self.data.apply(lambda row:
                            row.file_dir_name[:row.file_dir_name.rfind('/') + 1],
                            axis=1)

        # Clean filepath for splitting path parts:
        # * Replace multiple consecutive slashes by just one
        # * Remove leading slash if any, to avoid str.split to add an empty
        #   string to the resulting list of slices
        # * Remove trailing slash if any, to avoid str.split to add an empty
        #   string to the resulting list of slices
        self.data['file_path_list'] = self.data[column].str.replace('/+', '/')
        self.data['file_path_list'] = self.data.file_path_list.str.replace('^/', '')
        self.data['file_path_list'] = self.data.file_path_list.str.replace('/$', '')
        self.data['file_path_list'] = self.data.file_path_list.str.split('/')

        return self.data


class Projects(Enrich):
    """ This class adds project info based on a pre-processed dataset
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided.

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column, projects):
        """ This method adds a new column named as 'project'
        that contains information about the associated project
        that the event in 'column' belongs to.

        :param column: column with information related to the project
        :type column: string
        :param projects: information about item - project
        :type projects: pandas.DataFrame

        :returns: original data frame with a new column named 'project'
        :rtype: pandas.DataFrame
        """

        if column not in self.data.columns:
            return self.data

        self.data = pandas.merge(self.data, projects, how='left', on=column)

        return self.data


class MessageLogFlag(Enrich):
    """ This class adds specific events for the
    given message log body
    """

    FLAGS_REGEX = {'Patch by Blink': '\s*Patch by (?P<value>.+)$',
                   'Patch by WebKit': '\s*Patch by (?P<value>.+) on .+$',
                   'Reviewed by WebKit': '\s*Reviewed by (?P<value>.+) on .+$'}

    def __parse_flags(self, body):
        """Parse flags from a message"""
        flags = []
        values = []
        lines = body.split('\n')
        for l in lines:
            for name in self.FLAGS_REGEX:
                m = re.match(self.FLAGS_REGEX[name], l)

                if m:
                    flags.append(name)
                    values.append(m.group("value").strip())

        # TODO: this should be more consistent. Either
        # returning a list of strings or strings
        if flags == []:
            flags = ""
            values = ""

        if len(flags) == 1:
            flags = flags[0]
            values = values[0]

        return flags, values

    def __init__(self, data):

        """ Main constructor of the class where the original dataframe
        is provided.

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column):
        """ This method helps to identify flags in the message log.
        As some communities may use the log message for the code
        authorship, specifig flags/tags are used to determine
        some actions by the authors or reviewers such who is
        the author or the reviewer is.

        The list of supported flags are found in the FLAGS_REGEX
        variable. In addition to this, a flag usually has a
        related developer where her name and email address are
        specified. This is also covered by this flag analysis.

        :param column: column where the text to analyze is found
        :type data: string
        """

        if column not in self.data.columns:
            return self.data

        flags_list = []
        values_list = []
        # Assuming the index of the dataframe is an integer
        for i in list(range(len(self.data))):
            flags, values = self.__parse_flags(self.data[column][i])
            flags_list.append(flags)
            values_list.append(values)

        self.data["flags"] = flags_list
        self.data["values"] = values_list

        return self.data


class EmailFlag(Enrich):
    """ This class adds specific events for the given
    email body
    """

    FLAGS_REGEX = {
        'Acked-by': '^Acked-by:(?P<value>.+)$',
        'Cc': '^Cc:(?P<value>.+)',
        'Fixes': '^Fixes:(?P<value>.+)$',
        'From': '^[Ff]rom:(?P<value>.+)$',
        'Reported-by': '^Reported-by:(?P<value>.+)$',
        'Tested-by': '^Tested-by:(?P<value>.+)$',
        'Reviewed-by': '^Reviewed-by:(?P<value>.+)$',
        'Release-Acked-by': '^Release-Acked-by:(?P<value>.+)$',
        'Signed-off-by': '^Signed-off-by:(?P<value>.+)$',
        'Suggested-by': '^Suggested-by:(?P<value>.+)$'}

    def __parse_flags(self, body):
        """Parse flags from a message"""
        flags = []
        values = []
        lines = body.split('\n')
        for l in lines:
            for name in self.FLAGS_REGEX:
                m = re.match(self.FLAGS_REGEX[name], l)

                if m:
                    flags.append(name)
                    values.append(m.group("value").strip())

        if flags == []:
            flags = ""
            values = ""

        return flags, values

    def __init__(self, data):

        """ Main constructor of the class where the original dataframe
        is provided.

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column):
        """ This method helps to identify flags in the emails.
        As some communities may use the mailing list for the code
        review process, specifig flags/tags are used to determine
        some actions by the reviewers such as the moment when a
        patch is approved to merged.

        The list of supported flags are found in the FLAGS_REGEX
        variable where. In addition to this, a flag usually has a
        related developer where her name and email address are
        specified. This is also covered by this flag analysis.

        :param column: column where the text to analyze is found
        :type data: string
        """

        if column not in self.data.columns:
            return self.data

        flags_list = []
        values_list = []
        # Assuming the index of the dataframe is an integer
        for i in list(range(len(self.data))):
            flags, values = self.__parse_flags(self.data[column][i])
            flags_list.append(flags)
            values_list.append(values)

        self.data["flags"] = flags_list
        self.data["values"] = values_list

        return self.data


class SplitEmailDomain(Enrich):
    """ This class returns a new column with the domain of the email
    analyzed
    """

    def __parse_email(self, email):
        """ This function returns the domain of a given email
        """

        try:
            return email.split('@')[1]
        except Exception:
            return "unknown"

    def __init__(self, data):

        """ Main constructor of the class where the original dataframe
        is provided.

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column):
        """ This enricher returns the same dataframe
        with a new column named 'domain'.
        That column is the result of splitting the
        email address of another column. If there is
        not a proper email address an 'unknown'
        domain is returned.

        :param column: column where the text to analyze is found
        :type data: string
        """

        if column not in self.data.columns:
            return self.data

        self.data['domain'] = self.data[column].apply(lambda x: self.__parse_email(x))
        return self.data


class ToUTF8(Enrich):
    """ This class helps to migrate (or ignore) the strings to utf-8
    """

    def __remove_surrogates(self, s, method='replace'):
        """ Remove surrogates in the specified string
        """

        if type(s) == list and len(s) == 1:
            if self.__is_surrogate_escaped(s[0]):
                return s[0].encode('utf-8', method).decode('utf-8')
            else:
                return ""
        if type(s) == list:
            return ""
        if type(s) != str:
            return ""
        if self.__is_surrogate_escaped(s):
            return s.encode('utf-8', method).decode('utf-8')
        return s

    def __is_surrogate_escaped(self, text):
        """ Checks if surrogate is escaped
        """

        try:
            text.encode('utf-8')
        except UnicodeEncodeError as e:
            if e.reason == 'surrogates not allowed':
                return True
        return False

    def __init__(self, data):
        """ Main constructor

        :parama data: Original dataset
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, columns):
        """ This method convert to utf-8 the provided columns

        :param columns: list of columns to convert to
        :type columns: list of strings
        :return: original dataframe with converted strings
        :rtype: pandas.DataFrame
        """

        for column in columns:
            if column not in self.data.columns:
                return self.data

        for column in columns:
            a = self.data[column].apply(self.__remove_surrogates)
            self.data[column] = a

        return self.data


class SplitEmail(Enrich):
    """ This class split the tuple 'name <email>' into 'name' and 'email'.
    This adds two new columns named as 'user' and 'email to the provided
    one
    """

    def __parse_addr(self, addr):
        """ Parse email addresses
        """

        from email.utils import parseaddr

        value = parseaddr(addr)
        return value[0], value[1]

    def __init__(self, data):
        """ Main constructor oft he class

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column):
        """ This method creates two new columns: user and email.
        Those contain the information coming from the usual tuple of
        user <email> found in several places like in the mailing lists
        or the git repositories commit.

        :param column: column to be used for this parser
        :type column: string

        :returns: dataframe with two new columns
        :rtype: pandas.DataFrame
        """

        if column not in self.data.columns:
            return self.data

        self.data["user"], self.data["email"] = zip(*self.data[column].map(self.__parse_addr))

        return self.data


class SplitLists(Enrich):
    """ This class looks for lists in the given columns and append at the
    end of the dataframe a row for each entry in those lists.
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, columns):
        """ This method appends at the end of the dataframe as many
        rows as items are found in the list of elemnents in the
        provided columns.

        This assumes that the length of the lists for the several
        specified columns is the same. As an example, for the row A
        {"C1":"V1", "C2":field1, "C3":field2, "C4":field3}
        we have three cells with a list of four elements each of them:
        * field1: [1,2,3,4]
        * field2: ["a", "b", "c", "d"]
        * field3: [1.1, 2.2, 3.3, 4.4]

        This method converts each of the elements of each cell in a new
        row keeping the columns name:

        {"C1":"V1", "C2":1, "C3":"a", "C4":1.1}
        {"C1":"V1", "C2":2, "C3":"b", "C4":2.2}
        {"C1":"V1", "C2":3, "C3":"c", "C4":3.3}
        {"C1":"V1", "C2":4, "C3":"d", "C4":4.4}

        :param columns: list of strings
        :rtype pandas.DataFrame
        """

        for column in columns:
            if column not in self.data.columns:
                return self.data

        # Looking for the rows with columns with lists of more
        # than one element
        first_column = list(self.data[columns[0]])
        count = 0
        append_df = pandas.DataFrame()
        for cell in first_column:
            if len(cell) >= 1:
                # Interested in those lists with more
                # than one element
                df = pandas.DataFrame()
                # Create a dataframe of N rows from the list
                for column in columns:
                    df[column] = self.data.loc[count, column]
                # Repeat the original rows N times
                extra_df = pandas.DataFrame([self.data.loc[count]] * len(df))
                for column in columns:
                    extra_df[column] = list(df[column])
                append_df = append_df.append(extra_df, ignore_index=True)
                extra_df = pandas.DataFrame()

            count = count + 1

        self.data = self.data.append(append_df, ignore_index=True)

        return self.data


class MaxMin(Enrich):
    """ This class creates two new columns with the maximum and
    minimum value of the given column
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided.

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, columns, groupby):
        """ This method calculates the maximum and minimum value
        of a given set of columns depending on another column.
        This is the usual group by clause in SQL.

        :param columns: list of columns to apply the max and min values
        :param groupby: column use to calculate the max/min values
        :type columns: list of strings
        """

        for column in columns:
            if column not in self.data.columns:
                return self.data

        for column in columns:
            df_grouped = self.data.groupby([groupby]).agg({column: 'max'})
            df_grouped = df_grouped.reset_index()
            df_grouped.rename(columns={column: 'max_' + column}, inplace=True)
            self.data = pandas.merge(self.data, df_grouped, how='left', on=[groupby])

            df_grouped = self.data.groupby([groupby]).agg({column: 'min'})
            df_grouped = df_grouped.reset_index()
            df_grouped.rename(columns={column: 'min_' + column}, inplace=True)
            self.data = pandas.merge(self.data, df_grouped, how='left', on=[groupby])

        return self.data


class Gender(Enrich):
    """ This class creates three new columns with the gender of
    the name provided
    """

    def __init__(self, data, key=None, gender_file=None):
        """ Main constructor of the class where the original dataframe
        is provided.

        :param data: original dataframe
        :param key: genderize key (optional)
        :param gender_file: file with gender info, used as cache
        :type data: pandas.DataFrame
        :type key: string
        :type gender_file: string (as filepath)
        """

        from genderize import Genderize

        self.data = data
        self.gender = {}  # init the name-gender dictionary
        self.key = key
        self.gender_file = gender_file

        # Init the genderize connection
        self.connection = Genderize()
        if self.key:
            self.connection = Genderize(api_key=self.key)

        if self.gender_file:
            # This file is used as cache for the gender info
            # This helps to avoid calling once and again to the API
            fd = open(gender_file, "r")
            lines = fd.readlines()
            fd.close()
            # TODO: fix hardcoded code when reading columns and using
            #      separators
            for line in lines:
                gender_data = line.split("\t")
                self.gender[gender_data[1]] = {"gender_analyzed_name": gender_data[1],
                                               "gender": gender_data[2]}

    def enrich(self, column):
        """ This method calculates thanks to the genderize.io API the gender
        of a given name.

        This method initially assumes that for the given
        string, only the first word is the one containing the name
        eg: Daniel Izquierdo <dizquierdo@bitergia.com>, Daniel would be the name.

        If the same class instance is used in later gender searches, this stores
        in memory a list of names and associated gender and probability. This is
        intended to have faster identifications of the gender and less number of
        API accesses.

        :param column: column where the name is found
        :type column: string

        :return: original dataframe with four new columns:
         * gender: male, female or unknown
         * gender_probability: value between 0 and 1
         * gender_count: number of names found in the Genderized DB
         * gender_analyzed_name: name that was sent to the API for analysis
        :rtype: pandas.DataFrame
        """

        if column not in self.data.columns:
            return self.data

        splits = self.data[column].str.split(" ")
        splits = splits.str[0]
        self.data["gender_analyzed_name"] = splits.fillna("noname")
        self.data["gender_probability"] = 0
        self.data["gender"] = "Unknown"
        self.data["gender_count"] = 0

        names = list(self.data["gender_analyzed_name"].unique())

        for name in names:
            if name in self.gender.keys():
                gender_result = self.gender[name]
            else:
                try:
                    # TODO: some errors found due to encode utf-8 issues.
                    # Adding a try-except in the meantime.
                    gender_result = self.connection.get([name])[0]
                except Exception:
                    continue

                # Store info in the list of users
                self.gender[name] = gender_result

            # Update current dataset
            if gender_result["gender"] is None:
                gender_result["gender"] = "NotKnown"
            self.data.loc[self.data["gender_analyzed_name"] == name, 'gender'] =\
                gender_result["gender"]
            if "probability" in gender_result.keys():
                self.data.loc[self.data["gender_analyzed_name"] == name,
                              'gender_probability'] = gender_result["probability"]
                self.data.loc[self.data["gender_analyzed_name"] == name,
                              'gender_count'] = gender_result["count"]

        self.data.fillna("noname")
        return self.data


class TimeDifference(Enrich):
    """ This class creates a new column with the difference in seconds
    between two dates.
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided

        :param data: original dataframe
        :type data: pandas.DataFrame
        """

        self.data = data

    def enrich(self, column1, column2):
        """ This method calculates the difference in seconds between
            the 2 columns (column2 - column1)

        The final result may provided negative values depending on the values
        from column1 and column2.

        :param column1: first column. Values in column1 must be datetime type
        :param column2: second column. Values in column2 must be datetime type
        :type column1: string
        :type column2: string

        :return: original dataframe with a new column with the difference
            between column2 - column1
        :rtype: pandas.DataFrame
        """

        if column1 not in self.data.columns or \
           column2 not in self.data.columns:
            return self.data

        self.data["timedifference"] = (self.data[column2] - self.data[column1]) / np.timedelta64(1, 's')
        return self.data


class Uuid(Enrich):
    """ This class adds new columns with the uuid of a given identity. If more
    not common columns (those not used to decide how to merge rows) are
    provided together with the uuid within the CSV file, all of them will also
    be merged in the resulting dataframe.
    """

    def __init__(self, data, file_path='data/uuids.csv',
                 drop_columns=[], drop_duplicates=[]):
        """ Main constructor of the class where the original dataframe
        is provided and the dataframe containing identities and their
        uuids is loaded from CSV file.

        :param data: original dataframe
        :param file_path: uuids file path (optional)
        :param drop_columns: columns to remove from the csv
        :param drop_duplicates: columns to use to remove duplicates
        :type data: pandas.DataFrame
        :type file_path: string
        """

        self.data = data

        # Read csv to data frame, read '\N' (null in MySQL export format) also
        # as NaN (this is the way pandas deal with null values)
        self.uuids_df = pandas.read_csv(filepath_or_buffer=file_path, na_values='\\N', sep=',')
        # Remove required columns to later merge
        for column in drop_columns:
            self.uuids_df.drop(column, 1)

        if len(drop_duplicates) > 0:
            self.uuids_df.drop_duplicates(subset=drop_duplicates, inplace=True)
        else:
            self.uuids_df.drop_duplicates(inplace=True)

    def enrich(self, columns):
        """ Merges the original dataframe with corresponding entity uuids based
        on the given columns. Also merges other additional information
        associated to uuids provided in the uuids dataframe, if any.

        :param columns: columns to match for merging
        :type column: string array

        :return: original dataframe with at least one new column:
         * uuid: identity unique identifier
        :rtype: pandas.DataFrame
        """

        for column in columns:
            if column not in self.data.columns:
                return self.data

        self.data = pandas.merge(self.data, self.uuids_df, how='left', on=columns)
        self.data = self.data.fillna("notavailable")

        return self.data


class Onion(Enrich):
    """ This class adds a new column with the role of the author with respect
    to the amount of work in a given column. The onion model is based on the
    analysis of the community where the 80% of the work is done by membe
    """

    def __init__(self, data):
        """ Main constructor of the class where the original dataframe
        is provided and the dataframe containing identities and their
        uuids is loaded from CSV file.

        :param data: original dataframe
        :param file_path: uuids file path (optional)
        :param drop_columns: columns to remove from the csv
        :param drop_duplicates: columns to use to remove duplicates
        :type data: pandas.DataFrame
        :type file_path: string
        """

        self.data = data

    def enrich(self, member_column, events_column):
        """ Calculates the onion model for the given set of columns.
        This expects two columns as input (typically the author and
        the amount of events) and returns a third column with the
        role (core, regular, casual) of such community member.

        :param columns: columns to match for calculating the onion model
        :type column: string array

        :return: original dataframe with three new columns and ordered by role
                 importance:
         * onion_role: "core", "regular", or "casual"
         * percent_cum_net_sum: percentage of the activity up to such developer
         * cum_net_sum: accumulated activity up to such developer
        :rtype: pandas.DataFrame
        """

        if member_column not in self.data.columns or \
           events_column not in self.data.columns:
            return self.data

        # Order the data... just in case
        self.data.sort_values(by=events_column, ascending=False, inplace=True)
        # Reset the index to properly work with other methods
        self.data.reset_index(inplace=True)
        # Remove resultant new 'index' column
        self.data.drop(["index"], axis=1, inplace=True)

        # Calculate onion limits and accumulative sum and percentage
        self.data["cum_net_sum"] = self.data[events_column].cumsum()
        self.data["percent_cum_net_sum"] = (self.data.cum_net_sum/self.data[events_column].sum())*100

        # Assign roles based on the percentage
        self.data["onion_role"] = pandas.cut(self.data["percent_cum_net_sum"],
                                               [0.0, 80.0, 95.0, 100.0],
                                               labels=["core", "regular", "casual"])

        return self.data
