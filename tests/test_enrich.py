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
#     Daniel Izquierdo <dizquierdo@bitergia.com>
#     Alberto Perez <alpgarcia@bitergia.com>
#

import os
import pandas
import scipy
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from enrich.enrich import PairProgramming, TimeDifference, Uuid, FilePath

from df_utils.format import Format

class TestEnrich(unittest.TestCase):
    """ Unit tests for Enrich classes
    """

    def setUp(self):
        self.__tests_dir = os.path.dirname(os.path.realpath(__file__))
        self.__enrich_dir = os.path.join(self.__tests_dir, "data/enrich/")

    def test_PairProgramming(self):
        """ Test several cases for the PairProgramming class
        """

        empty_df = pandas.DataFrame()
        # With empty dataframe and any columns, this always returns empty dataframe
        # A DataFrame with columns but not data is an empty DataFrame
        pair = PairProgramming(empty_df)
        self.assertTrue(pair.enrich("test1","test2").empty)
        # With a dataframe with some data, this returns a non-empty dataframe

        csv_df = pandas.read_csv(os.path.join(self.__enrich_dir,
                                              "pairprogramming.csv"))
        pair = PairProgramming(csv_df)
        enriched_df = pair.enrich("test1","test2")
        self.assertFalse(enriched_df.empty)
        # Expected to return the same df as test1 and test2 do not exist
        self.assertEqual(len(enriched_df), 7)

        enriched_df = pair.enrich("author", "committer")
        self.assertFalse(enriched_df.empty)
        # Expected to add a new entry at the end of the dataframe
        self.assertEqual(len(enriched_df), 8)

        enriched_df = pair.enrich("committer", "author")
        self.assertFalse(enriched_df.empty)
        # Expected to add a new entry at the end of the dataframe
        self.assertEqual(len(enriched_df), 8)


    def test_TimeDifference(self):
        """ Several test cases for the TimeDifference class
        """

        empty_df = pandas.DataFrame()
        # With empty dataframe and any columns this always returns emtpy datafram
        # A DataFrame with columns but no data is an empty DataFrame
        time = TimeDifference(empty_df)
        self.assertTrue(time.enrich("fake_column1", "fake_column2").empty)

        # A dataframe with some data, this returns a non-empty dataframe
        csv_df = pandas.read_csv(os.path.join(self.__enrich_dir,
                                              "timedifference.csv"))
        time = TimeDifference(csv_df)
        format_ = Format()
        time.data = format_.format_dates(time.data, ["date_author", "date_committer"])

        enriched_df = time.enrich("fake_column1", "fake_column2")
        self.assertFalse(enriched_df.empty)
        # Expected to return the same df as fake columns do not exist
        self.assertEqual(len(enriched_df), 7)

        enriched_df = time.enrich("date_author", "date_committer")

        self.assertEqual(len(enriched_df[enriched_df["timedifference"] > 0]), 4)

    def test_FilePath(self):
        """ Test FilePath enricher"""

        # Empty test
        empty_df = pandas.DataFrame()
        filepath = FilePath(empty_df)
        enriched_df = filepath.enrich('filepath')
        self.assertTrue(enriched_df.empty)

        #
        test_df = pandas.DataFrame()
        file_1 = {}
        file_2 = {}
        file_3 = {}
        file_1['filepath'] = 'file.txt'
        file_1['file_name'] = 'file.txt'
        file_1['file_ext'] = 'txt'
        file_1['file_dir_name'] = ''
        file_1['path_list'] = ['file.txt']
        file_2['filepath'] = '/foo/bar'
        file_2['file_name'] = 'bar'
        file_2['file_ext'] = ''
        file_2['file_dir_name'] = '/foo/'
        file_2['path_list'] = ['foo', 'bar']
        file_3['filepath'] = '/foo/bar/file.txt'
        file_3['file_name'] = 'file.txt'
        file_3['file_ext'] = 'txt'
        file_3['file_dir_name'] = '/foo/bar/'
        file_3['path_list'] = ['foo', 'bar', 'file.txt']
        test_df['filepath'] = [file_1['filepath'], file_2['filepath'],
                               file_3['filepath']]
        filepath = FilePath(test_df)
        enriched_df = filepath.enrich('filepath')
        self.assertEqual(enriched_df.iloc[[0]]['filepath'].item(), file_1['filepath'])
        self.assertEqual(enriched_df.iloc[[1]]['filepath'].item(), file_2['filepath'])
        self.assertEqual(enriched_df.iloc[[2]]['filepath'].item(), file_3['filepath'])
        self.assertEqual(enriched_df.iloc[[0]]['file_name'].item(), file_1['file_name'])
        self.assertEqual(enriched_df.iloc[[1]]['file_name'].item(), file_2['file_name'])
        self.assertEqual(enriched_df.iloc[[2]]['file_name'].item(), file_3['file_name'])
        self.assertEqual(enriched_df.iloc[[0]]['file_ext'].item(), file_1['file_ext'])
        self.assertEqual(enriched_df.iloc[[1]]['file_ext'].item(), file_2['file_ext'])
        self.assertEqual(enriched_df.iloc[[2]]['file_ext'].item(), file_3['file_ext'])
        self.assertEqual(enriched_df.iloc[[0]]['file_dir_name'].item(), file_1['file_dir_name'])
        self.assertEqual(enriched_df.iloc[[1]]['file_dir_name'].item(), file_2['file_dir_name'])
        self.assertEqual(enriched_df.iloc[[2]]['file_dir_name'].item(), file_3['file_dir_name'])
        self.assertEqual(enriched_df.iloc[[0]]['path_list'].item(), file_1['path_list'])
        self.assertEqual(enriched_df.iloc[[1]]['path_list'].item(), file_2['path_list'])
        self.assertEqual(enriched_df.iloc[[2]]['path_list'].item(), file_3['path_list'])


    def test_Uuid(self):
        """ Test several cases for the Uuid class
        """

        # Empty LEFT dataframe
        empty_df = pandas.DataFrame()
        uuid = Uuid(empty_df,
                    file_path=os.path.join(self.__enrich_dir, "uuids.csv"))

        enriched_df = uuid.enrich(['name', 'email'])

        # If LEFT df is empty, nothing should be merged resulting in an empty df
        self.assertTrue(enriched_df.empty)

        # Load test data from CSV files
        authors_df = pandas.read_csv(os.path.join(self.__enrich_dir,
                                                  "authors.csv"))
        uuid = Uuid(authors_df,
                    file_path=os.path.join(self.__enrich_dir, "uuids.csv"))

        enriched_df = uuid.enrich(['name', 'email'])

        self.assertFalse(enriched_df.empty)
        # Merged len must be equal to LEFT df len
        self.assertEqual(len(enriched_df), len(authors_df))

        # Check rows that should store same uuid, i.e., same author
        self.assertEqual(len(enriched_df[enriched_df['name'] == 'pepe']), 2)
        self.assertEqual(len(enriched_df[enriched_df['name'] == 'John Rambo']), 3)

        pepe_df = enriched_df[enriched_df['name'] == 'pepe']
        pepe_uuid = '0007b2fd4dbb5090a848c50717966a15a1772112'
        self.assertEqual(pepe_df.iloc[[0]]['uuid'].item(), pepe_uuid)
        self.assertEqual(pepe_df.iloc[[1]]['uuid'].item(), pepe_uuid)

        john_df = enriched_df[enriched_df['name'] == 'John Rambo']
        john_uuid = '000eabca391efd736dd8438e4d220b3f00808065'
        self.assertEqual(john_df.iloc[[0]]['uuid'].item(), john_uuid)
        self.assertEqual(john_df.iloc[[1]]['uuid'].item(), john_uuid)
        self.assertEqual(john_df.iloc[[2]]['uuid'].item(), john_uuid)


if __name__ == '__main__':
    unittest.main()
