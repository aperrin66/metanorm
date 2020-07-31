"""Tests for the OSISAF metadata normalizer"""
import unittest
from collections import OrderedDict

import dateutil
from dateutil.tz import tzutc
from django.contrib.gis.geos.geometry import GEOSGeometry
import metanorm.normalizers as normalizers


class OSISAFMetadataNormalizer(unittest.TestCase):
    """Tests for the ACDD attributes normalizer"""

    def setUp(self):
        self.normalizer = normalizers.OSISAFMetadataNormalizer([], [])

    def test_summary(self):
        """summary from OSISAFMetadataNormalizer"""

        attributes = {'abstract': 'value_abs'}
        self.assertEqual('value_abs', self.normalizer.get_summary(attributes))

    def test_instrument(self):
        """instrument from OSISAFMetadataNormalizer"""
        attributes = {'instrument_type': 'value_1'}
        # 'instrument_type' must be used in this normalizer
        self.assertEqual(self.normalizer.get_instrument(
            attributes)['Short_Name'], 'value_1')

        attributes = {'product_name': 'osi_saf_2'}
        # in the absence of 'instrument_type' value should be UNKNOWN with GCMD template
        self.assertEqual(
            self.normalizer.get_instrument(attributes),
            OrderedDict([('Category', 'Unknown'),
                         ('Class', 'Unknown'),
                         ('Type', 'Unknown'),
                         ('Subtype', 'Unknown'),
                         ('Short_Name', 'Unknown'),
                         ('Long_Name', 'Unknown')])
        )

    def test_platform(self):
        """platform from OSISAFMetadataNormalizer"""
        attributes = {'platform_name': 'value_1'}
        # 'instrument_type' must be used in this normalizer
        self.assertEqual(self.normalizer.get_platform(
            attributes)['Short_Name'], 'value_1')

        attributes = {'activity_type': 'value_2'}
        # in the absence of 'platform_name' value should be None
        self.assertIsNone(self.normalizer.get_instrument(attributes))

        attributes = {'product_name': 'osi_saf_2'}
        # in the absence of 'platform_name' value should be UNKNOWN with GCMD template
        self.assertEqual(
            self.normalizer.get_platform(attributes),
            OrderedDict([('Category', 'Unknown'),
                         ('Series_Entity', 'Unknown'),
                         ('Short_Name', 'Unknown'),
                         ('Long_Name', 'Unknown')])
        )

    def test_time_coverage_start(self):
        """time_coverage_start from OSISAFMetadataNormalizer."""
        attributes = {'start_date': '2020-07-12 00:00:00'}
        self.assertEqual(self.normalizer.get_time_coverage_start(attributes),
                         dateutil.parser.parse("2020-07-12").replace(tzinfo=tzutc()))

    def test_time_coverage_end(self):
        """time_coverage_end from OSISAFMetadataNormalizer."""
        attributes = {'stop_date': '2020-07-14 00:00:00'}
        self.assertEqual(self.normalizer.get_time_coverage_end(attributes),
                         dateutil.parser.parse("2020-07-14").replace(tzinfo=tzutc()))

    def test_location_geometry(self):
        """location_geometry from OSISAFMetadataNormalizer"""
        attributes = {
            'northernsmost_latitude': "9.47472000",
            'southernmost_latitude': "-15.3505001",
            'easternmost_longitude': "-142.755005",
            'westernmost_longitude': "-175.084000"
        }
        expected_geometry = GEOSGeometry(
            ('POLYGON((' +
             '-175.084000 -15.3505001,' +
             '-142.755005 -15.3505001,' +
             '-142.755005 9.47472000,' +
             '-175.084000 9.47472000,' +
             '-175.084000 -15.3505001))'),
            srid=4326)

        normalizer = normalizers.OSISAFMetadataNormalizer(
            ['location_geometry'], [])
        normalized_params = normalizer.normalize(attributes)

        self.assertIsInstance(normalized_params, dict)
        self.assertTrue('location_geometry' in normalized_params)
        self.assertTrue(
            normalized_params['location_geometry'].equals(expected_geometry))

    def test_provider(self):
        """provider information from OSISAFMetadataNormalizer """
        attributes = {'institution': 'company1'}
        self.assertEqual(self.normalizer.get_provider(attributes),
                         OrderedDict([('Bucket_Level0', 'Unknown'),
                                      ('Bucket_Level1', 'Unknown'),
                                      ('Bucket_Level2', 'Unknown'),
                                      ('Bucket_Level3', 'Unknown'),
                                      ('Short_Name', 'company1'),
                                      ('Long_Name', 'company1'),
                                      ('Data_Center_URL', 'Unknown'),
                                      ]))
