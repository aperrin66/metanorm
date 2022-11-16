"""Tests for the utils module"""
import re
import unittest
import unittest.mock as mock
from collections import OrderedDict
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc

import metanorm.errors as errors
import metanorm.utils as utils

class TimeTestCase(unittest.TestCase):
    """Tests for utilities dealing with time"""

    def test_create_datetime_year_month_day(self):
        """test create_datetime with a year, month and day"""
        self.assertEqual(
            utils.create_datetime(2020, 10, 15),
            datetime(2020, 10, 15).replace(tzinfo=tzutc())
        )

    def test_create_datetime_year_day_of_year(self):
        """test create_datetime with a year and day of year"""
        self.assertEqual(
            utils.create_datetime(2020, day_of_year=35),
            datetime(2020, 2, 4).replace(tzinfo=tzutc())
        )

    def test_create_datetime_year_month_day_time(self):
        """test create_datetime with a year, month, day and time"""
        self.assertEqual(
            utils.create_datetime(2020, 10, 15, hour=10, minute=25, second=38),
            datetime(2020, 10, 15, 10, 25, 38).replace(tzinfo=tzutc())
        )

    def test_create_datetime_year_day_of_year_time(self):
        """test create_datetime with a year, day of year and time"""
        self.assertEqual(
            utils.create_datetime(2020, day_of_year=35, hour=23, minute=1, second=40),
            datetime(2020, 2, 4, 23, 1, 40).replace(tzinfo=tzutc())
        )

    def test_yearmonth_regex(self):
        """The YEARMONTH_REGEX should provide a 'year' and 'month'
        named groups
        """
        self.assertDictEqual(
            re.match(utils.YEARMONTH_REGEX, '202010').groupdict(),
            {'year': '2020', 'month': '10'}
        )

    def test_yearmonthday_regex(self):
        """The YEARMONTHDAY_REGEX should provide a 'year', 'month'
        and 'day' named groups
        """
        self.assertDictEqual(
            re.match(utils.YEARMONTHDAY_REGEX, '20201017').groupdict(),
            {'year': '2020', 'month': '10', 'day': '17'}
        )

    def test_find_time_coverage(self):
        """find_time_coverage() should extract the time coverage from a
        URL using the given regexes and functions
        """
        time_patterns = (
            (
                re.compile(rf"dataset_{utils.YEARMONTHDAY_REGEX}.nc$"),
                utils.create_datetime,
                lambda time: (time, time + relativedelta(days=1))
            ),
            (
                re.compile(rf"dataset_{utils.YEARMONTH_REGEX}.nc$"),
                utils.create_datetime,
                lambda time: (time, time + relativedelta(months=1))
            )
        )
        self.assertTupleEqual(
            utils.find_time_coverage(time_patterns, 'ftp://foo/dataset_20200205.nc'),
            (datetime(2020, 2, 5, tzinfo=tzutc()), datetime(2020, 2, 6, tzinfo=tzutc())))
        self.assertTupleEqual(
            utils.find_time_coverage(time_patterns, 'ftp://foo/dataset_202002.nc'),
            (datetime(2020, 2, 1, tzinfo=tzutc()), datetime(2020, 3, 1, tzinfo=tzutc())))

    def test_find_time_coverage_not_found(self):
        """A MetadataNormalizationError must be raised when no time
        coverage can be extracted
        """
        time_patterns = ((re.compile(r'foo'), None, None),)
        with self.assertRaises(errors.MetadataNormalizationError):
            utils.find_time_coverage(time_patterns, 'bar')


class UtilsTestCase(unittest.TestCase):
    """Test case for utils functions"""
    def test_dict_to_string(self):
        """dict_to_string() should return the proper representation"""
        self.assertEqual(
            utils.dict_to_string({'key1': 'value1', 'key2': 'value2'}),
            'key1: value1;key2: value2'
        )

    def test_empty_dict_to_string(self):
        """The representation of an empty dict is an empty string"""
        self.assertEqual(utils.dict_to_string({}), '')

    def test_translate_pythesint_keyword(self):
        """Should return the right keyword given an alias"""
        translation_dict = {
            'keyword1': ('alias11', 'alias12'),
            'keyword2': ('alias21', 'alias22'),
        }
        self.assertEqual(utils.translate_pythesint_keyword(translation_dict, 'alias11'), 'keyword1')
        self.assertEqual(utils.translate_pythesint_keyword(translation_dict, 'alias22'), 'keyword2')
        self.assertEqual(utils.translate_pythesint_keyword(translation_dict, 'alias3'), 'alias3')

    def test_get_gcmd_provider(self):
        """Test looking for a GCMD provider"""
        placeholder = {'foo': 'bar'}
        with mock.patch('metanorm.utils.gcmd_search', side_effect=[None, placeholder]):
            self.assertEqual(utils.get_gcmd_provider('baz'), placeholder)

    def test_get_gcmd_provider_not_found(self):
        """Test looking for a GCMD provider and not finding any"""
        with mock.patch('metanorm.utils.gcmd_search', return_value=None):
            self.assertIsNone(utils.get_gcmd_provider('baz'))

    def test_get_gcmd_platform(self):
        """Test getting a GCMD platform"""
        placeholder = {'foo': 'bar'}
        with mock.patch('metanorm.utils.gcmd_search', return_value=placeholder):
            self.assertEqual(utils.get_gcmd_platform('baz'), placeholder)

    def test_get_gcmd_platform_unknown(self):
        """Test getting an unknown GCMD platform"""
        with mock.patch('metanorm.utils.gcmd_search', return_value=None):
            self.assertEqual(
                utils.get_gcmd_platform('foo'),
                OrderedDict([
                    ('Category', utils.UNKNOWN),
                    ('Series_Entity', utils.UNKNOWN),
                    ('Short_Name', 'foo'),
                    ('Long_Name', 'foo')
                ]))

    def test_get_gcmd_instrument(self):
        """Test getting a GCMD instrument"""
        placeholder = {'foo': 'bar'}
        with mock.patch('metanorm.utils.gcmd_search', return_value=placeholder):
            self.assertEqual(utils.get_gcmd_instrument('baz'), placeholder)

    def test_get_gcmd_instrument_unknown(self):
        """Test getting an unknown GCMD instrument"""
        with mock.patch('metanorm.utils.gcmd_search', return_value=None):
            self.assertEqual(
                utils.get_gcmd_instrument('foo'),
                OrderedDict([
                    ('Category', utils.UNKNOWN),
                    ('Class', utils.UNKNOWN),
                    ('Type', utils.UNKNOWN),
                    ('Subtype', utils.UNKNOWN),
                    ('Short_Name', 'foo'),
                    ('Long_Name', 'foo')
                ]))

    def test_gcmd_search_one_result(self):
        """Test searching GCMD vocabularies when only one result is
        found by Pythesint
        """
        with mock.patch("pythesint.json_vocabulary.JSONVocabulary.get_list",
                        return_value=[{'foo': 'bar', 'baz': 'qux'}]):
            self.assertEqual(
                utils.gcmd_search('instrument', 'bar', ['quux']),
                {'foo': 'bar', 'baz': 'qux'})

    def test_gcmd_search_unambiguous_selection(self):
        """Test searching GCMD vocabularies when multiple results are
        found by pythesint and an additional keyword allows to select
        one without ambiguity
        """
        search_results = [
            {'foo': 'bar', 'baz': 'qux'},
            {'foo': 'bar', 'baz': 'quux'},
        ]
        with mock.patch("pythesint.json_vocabulary.JSONVocabulary.get_list",
                        return_value=search_results):
            self.assertEqual(
                utils.gcmd_search('instrument', 'bar', ['quux']),
                {'foo': 'bar', 'baz': 'quux'})

    def test_gcmd_search_arbitrary_selection(self):
        """Test searching GCMD vocabularies when multiple results are
        found by pythesint and the additional keyword does not allow to
        select one. The first result is then selected.
        """
        search_results = [
            {'foo': 'bar', 'baz': 'qux'},
            {'foo': 'bar', 'baz': 'qux', 'corge': 'grault'},
        ]
        with mock.patch("pythesint.json_vocabulary.JSONVocabulary.get_list",
                        return_value=search_results):
            self.assertEqual(
                utils.gcmd_search('instrument', 'bar', ['qux']),
                {'foo': 'bar', 'baz': 'qux'})

    def test_gcmd_search_no_result(self):
        """Test searching GCMD vocabularies when no result is found"""
        with mock.patch("pythesint.json_vocabulary.JSONVocabulary.get_list", return_value=[]):
            self.assertIsNone(utils.gcmd_search('instrument', 'bar', ['qux']))

    def test_restrict_gcmd_search(self):
        """Test restricting the results of a GCMD search using
        additional keywords. The keyword which restricts the search
        the most should be used
        """
        search_results = [
            {'foo': 'bar', 'baz': 'qux'},
            {'foo': 'bar', 'baz': 'qux', 'corge': 'grault'},
        ]
        self.assertEqual(
            utils.restrict_gcmd_search(search_results, ['qux', 'grault']),
            [{'foo': 'bar', 'baz': 'qux', 'corge': 'grault'}])

    def test_get_cf_standard_name(self):
        """Test getting a standardized dataset parameter from the CF
        vocabulary
        """
        placeholder = {'foo': 'bar'}
        with mock.patch('pythesint.get_cf_standard_name', return_value=placeholder):
            self.assertEqual(
                utils.get_cf_or_wkv_standard_name('baz'),
                placeholder)

    def test_get_wkv_standard_name(self):
        """Test getting a standardized dataset parameter from the well
        known vocabularies
        """
        placeholder = {'foo': 'bar'}
        with mock.patch('pythesint.get_cf_standard_name', side_effect=IndexError), \
                mock.patch('pythesint.get_wkv_variable', return_value=placeholder):
            self.assertEqual(
                utils.get_cf_or_wkv_standard_name('baz'),
                placeholder)

    def test_raises_decorator(self):
        """Test that the `raises()` decorator raises a
        MetadataNormalizationError when the function it decorates
        raises the exception given as argument to the decorator
        """
        # the type annotation prevents Pylance from wrongfully marking
        # the following code as unreachable
        @utils.raises(KeyError)
        def get_foo(self, raw_metadata) -> None:
            raise KeyError

        with self.assertRaises(errors.MetadataNormalizationError) as raised:
            get_foo(mock.Mock(), {})
        self.assertIsInstance(raised.exception.__cause__, KeyError)

    def test_raises_decorator_with_tuple(self):
        """Test that the `raises()` decorator raises a
        MetadataNormalizationError when the function it decorates
        raises one of the exceptions given as argument to the decorator
        """
        # the type annotation prevents Pylance from wrongfully marking
        # the following code as unreachable
        @utils.raises((KeyError, IndexError))
        def get_foo(self, raw_metadata) -> None:
            raise IndexError

        with self.assertRaises(errors.MetadataNormalizationError) as raised:
            get_foo(mock.Mock(), {})
        self.assertIsInstance(raised.exception.__cause__, IndexError)

    def test_raises_decorator_wrong_exception(self):
        """Test that the `raises()` decorator does not catch exceptions
        which are not in its arguments
        """
        # the type annotation prevents Pylance from wrongfully marking
        # the following code as unreachable
        @utils.raises(KeyError)
        def get_foo(self, raw_metadata) -> None:
            raise ValueError

        with self.assertRaises(ValueError):
            get_foo(mock.Mock(), {})


class SubclassesTestCase(unittest.TestCase):
    """Tests for utility functions dealing with subclasses"""

    class Base():
        """Base class for tests"""

    class A(Base):
        """Class for testing"""

    class B(Base):
        """Class for testing"""

    class C(B):
        """Class for testing"""

    class D(A, B):
        """Class for testing"""


    def test_get_all_subclasses(self):
        """Test that get_all_subclasses() returns all subclasses of
        the base class
        """
        self.assertEqual(
            utils.get_all_subclasses(self.Base),
            set((self.A, self.B, self.C, self.D)))

    def test_export_subclasses(self):
        """Test that export_subclasses imports the modules of the
        package and adds subclasses to __all__
        """
        # simulate the output of pkgutil.iter_modules()
        # see https://docs.python.org/3.7/library/pkgutil.html#pkgutil.iter_modules
        modules = (
            (mock.Mock(), 'module1', False),
            (mock.Mock(), 'module2', False)
        )
        with mock.patch('pkgutil.iter_modules', return_value=iter(modules)), \
             mock.patch('importlib.import_module') as mock_import_module, \
             mock.patch('sys.modules') as mock_sys_modules:
            package__all__ = []
            utils.export_subclasses(package__all__, 'package', '/foo/package', self.Base)
        self.assertCountEqual(package__all__, ['Base', 'A', 'B', 'C', 'D'])
