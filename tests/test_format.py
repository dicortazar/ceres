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
#     Daniel Izquierdo <dizquierdo@bitergia.com>
#

import sys
import unittest

import pandas
import scipy

if '..' not in sys.path:
    sys.path.insert(0, '..')

from cereslib.dfutils.format import Format


class TestFormat(unittest.TestCase):
    """ Unit tests for Format class
    """

    def test_fill_missing_fields(self):
        """ Test several cases for the fill_missing_fields method
        """

        empty_columns = []
        columns = ["test1"]
        empty_df = pandas.DataFrame()
        # With empty dataframe and any columns, this always returns empty dataframe
        # A DataFrame with columns but not data is an empty DataFrame
        self.assertTrue(Format().fill_missing_fields(empty_df, empty_columns).empty)
        self.assertTrue(Format().fill_missing_fields(empty_df, columns).empty)
        self.assertEqual(columns, Format().fill_missing_fields(empty_df, columns).columns)

        # With a dataframe with some data, this returns a non-empty dataframe
        df = empty_df.copy()
        df["test"] = scipy.zeros(10)

        self.assertFalse(Format().fill_missing_fields(df, empty_columns).empty)

    def test_update_field_names(self):
        """Test several cases for the update_field_names method
        """

        columns = ["test1", "test2"]
        new_columns = ["new_test1", "new_test2"]
        matching = dict(zip(columns, new_columns))
        df = pandas.DataFrame()
        for test in columns:
            df[test] = scipy.zeros(10)

        self.assertEqual(new_columns, Format().update_field_names(df, matching).columns.tolist())
        # Expected to return True as the dataframe's columns' names have been renamed
        self.assertNotEqual(columns, Format().update_field_names(df, matching).columns.tolist())


if __name__ == '__main__':
    unittest.main()
