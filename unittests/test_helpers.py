"""Unit tests for the helpers.py module.

Copyright 2022 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import sys
import os
import datetime
import logging
import unittest
import arcpy
import portal_credentials  # Contains log-in for an ArcGIS Online account to use as a test portal

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CWD))
import helpers  # noqa: E402, pylint: disable=wrong-import-position
from od_config import OD_PROPS  # noqa: E402, pylint: disable=wrong-import-position
from rt_config import RT_PROPS  # noqa: E402, pylint: disable=wrong-import-position


class TestHelpers(unittest.TestCase):
    """Test cases for the helpers module."""

    @classmethod
    def setUpClass(self):  # pylint: disable=bad-classmethod-argument
        """Set up shared test properties."""
        self.maxDiff = None

        self.input_data_folder = os.path.join(CWD, "TestInput")
        self.sf_gdb = os.path.join(self.input_data_folder, "SanFrancisco.gdb")
        self.local_nd = os.path.join(self.sf_gdb, "Transportation", "Streets_ND")
        self.portal_nd = portal_credentials.PORTAL_URL

        arcpy.SignInToPortal(self.portal_nd, portal_credentials.PORTAL_USERNAME, portal_credentials.PORTAL_PASSWORD)

        self.scratch_folder = os.path.join(
            CWD, "TestOutput", "Output_Helpers_" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
        os.makedirs(self.scratch_folder)
        self.output_gdb = os.path.join(self.scratch_folder, "outputs.gdb")
        arcpy.management.CreateFileGDB(os.path.dirname(self.output_gdb), os.path.basename(self.output_gdb))

    def test_is_nds_service(self):
        """Test the is_nds_service function."""
        self.assertTrue(helpers.is_nds_service(self.portal_nd))
        self.assertFalse(helpers.is_nds_service(self.local_nd))

    def test_get_tool_limits_and_is_agol(self):
        """Test the _get_tool_limits_and_is_agol function for a portal network data source."""
        services = [
            ("asyncODCostMatrix", "GenerateOriginDestinationCostMatrix"),
            ("asyncRoute", "FindRoutes")
        ]
        for service in services:
            with self.subTest(service=service):
                service_limits, is_agol = helpers.get_tool_limits_and_is_agol(
                    self.portal_nd, service[0], service[1])
                self.assertIsInstance(service_limits, dict)
                self.assertIsInstance(is_agol, bool)
                if service[0] == "asyncODCostMatrix":
                    self.assertIn("maximumDestinations", service_limits)
                    self.assertIn("maximumOrigins", service_limits)
                elif service[0] == "asyncRoute":
                    self.assertIn("maximumStops", service_limits)
                if "arcgis.com" in self.portal_nd:
                    # Note: If testing with some other portal, this test would need to be updated.
                    self.assertTrue(is_agol)

    def test_update_agol_max_processes(self):
        """Test the update_agol_max_processes function."""
        self.assertEqual(helpers.MAX_AGOL_PROCESSES, helpers.update_agol_max_processes(5000))

    def test_convert_time_units_str_to_enum(self):
        """Test the convert_time_units_str_to_enum function."""
        # Test all valid units
        valid_units = helpers.TIME_UNITS
        for unit in valid_units:
            enum_unit = helpers.convert_time_units_str_to_enum(unit)
            self.assertIsInstance(enum_unit, arcpy.nax.TimeUnits)
            self.assertEqual(unit.lower(), enum_unit.name.lower())
        # Test for correct error with invalid units
        bad_unit = "BadUnit"
        with self.assertRaises(ValueError) as ex:
            helpers.convert_time_units_str_to_enum(bad_unit)
        self.assertEqual(f"Invalid time units: {bad_unit}", str(ex.exception))

    def test_convert_distance_units_str_to_enum(self):
        """Test the convert_distance_units_str_to_enum function."""
        # Test all valid units
        valid_units = helpers.DISTANCE_UNITS
        for unit in valid_units:
            enum_unit = helpers.convert_distance_units_str_to_enum(unit)
            self.assertIsInstance(enum_unit, arcpy.nax.DistanceUnits)
            self.assertEqual(unit.lower(), enum_unit.name.lower())
        # Test for correct error with invalid units
        bad_unit = "BadUnit"
        with self.assertRaises(ValueError) as ex:
            helpers.convert_distance_units_str_to_enum(bad_unit)
        self.assertEqual(f"Invalid distance units: {bad_unit}", str(ex.exception))

    def test_convert_output_format_str_to_enum(self):
        """Test the convert_output_format_str_to_enum function."""
        # Test all valid formats
        valid_formats = helpers.OUTPUT_FORMATS
        for fm in valid_formats:
            enum_format = helpers.convert_output_format_str_to_enum(fm)
            self.assertIsInstance(enum_format, helpers.OutputFormat)
        # Test for correct error with an invalid format type
        bad_format = "BadFormat"
        with self.assertRaises(ValueError) as ex:
            helpers.convert_output_format_str_to_enum(bad_format)
        self.assertEqual(f"Invalid output format: {bad_format}", str(ex.exception))

    def test_validate_input_feature_class(self):
        """Test the validate_input_feature_class function."""
        # Test when the input feature class does note exist.
        input_fc = os.path.join(self.sf_gdb, "DoesNotExist")
        with self.subTest(feature_class=input_fc):
            with self.assertRaises(ValueError) as ex:
                helpers.validate_input_feature_class(input_fc)
            self.assertEqual(f"Input dataset {input_fc} does not exist.", str(ex.exception))

        # Test when the input feature class is empty
        input_fc = os.path.join(self.output_gdb, "EmptyFC")
        with self.subTest(feature_class=input_fc):
            arcpy.management.CreateFeatureclass(self.output_gdb, os.path.basename(input_fc))
            with self.assertRaises(ValueError) as ex:
                helpers.validate_input_feature_class(input_fc)
            self.assertEqual(f"Input dataset {input_fc} has no rows.", str(ex.exception))

    def test_validate_network_data_source(self):
        """Test the validate_network_data_source function."""
        # Check that it returns the catalog path of a network dataset layer
        nd_layer = arcpy.na.MakeNetworkDatasetLayer(self.local_nd).getOutput(0)
        with self.subTest(network_data_source=nd_layer):
            self.assertEqual(self.local_nd, helpers.validate_network_data_source(nd_layer))
        # Check that it returns a portal URL with a trailing slash if it initially lacked one
        portal_url = self.portal_nd.strip(r"/")
        with self.subTest(network_data_source=portal_url):
            self.assertEqual(portal_url + r"/", helpers.validate_network_data_source(portal_url))
        # Check for ValueError if the network dataset doesn't exist
        bad_network = os.path.join(self.sf_gdb, "Transportation", "DoesNotExist")
        with self.subTest(network_data_source=bad_network):
            with self.assertRaises(ValueError) as ex:
                helpers.validate_network_data_source(bad_network)
            self.assertEqual(str(ex.exception), f"Input network dataset {bad_network} does not exist.")

    def test_precalculate_network_locations(self):
        """Test the precalculate_network_locations function."""
        loc_fields = {"SourceID", "SourceOID", "PosAlong", "SideOfEdge"}
        inputs = os.path.join(self.sf_gdb, "Analysis", "CentralDepots")

        def check_precalculated_locations(fc):
            """Check precalculated locations."""
            actual_fields = set([f.name for f in arcpy.ListFields(fc)])
            self.assertTrue(loc_fields.issubset(actual_fields), "Network location fields not added")
            for row in arcpy.da.SearchCursor(fc, list(loc_fields)):  # pylint: disable=no-member
                for val in row:
                    self.assertIsNotNone(val)

        # Precalculate locations for OD
        fc_to_precalculate = os.path.join(self.output_gdb, "Precalculated_OD")
        arcpy.management.Copy(inputs, fc_to_precalculate)
        helpers.precalculate_network_locations(fc_to_precalculate, self.local_nd, "Driving Time", OD_PROPS)
        check_precalculated_locations(fc_to_precalculate)

        # Precalculate locations for Route
        fc_to_precalculate = os.path.join(self.output_gdb, "Precalculated_Route")
        arcpy.management.Copy(inputs, fc_to_precalculate)
        helpers.precalculate_network_locations(fc_to_precalculate, self.local_nd, "Driving Time", RT_PROPS)
        check_precalculated_locations(fc_to_precalculate)

    def test_get_oid_ranges_for_input(self):
        """Test the get_oid_ranges_for_input function."""
        ranges = helpers.get_oid_ranges_for_input(os.path.join(self.sf_gdb, "Analysis", "TractCentroids"), 50)
        self.assertEqual([[1, 50], [51, 100], [101, 150], [151, 200], [201, 208]], ranges)

    def test_parse_std_and_write_to_gp_ui(self):
        """Test the parse_std_and_write_to_gp_ui function."""
        # There is nothing much to test here except that nothing terrible happens.
        msgs = [
            f"CRITICAL{helpers.MSG_STR_SPLITTER}Critical message",
            f"ERROR{helpers.MSG_STR_SPLITTER}Error message",
            f"WARNING{helpers.MSG_STR_SPLITTER}Warning message",
            f"INFO{helpers.MSG_STR_SPLITTER}Info message",
            f"DEBUG{helpers.MSG_STR_SPLITTER}Debug message",
            "Poorly-formatted message 1",
            f"Poorly-formatted{helpers.MSG_STR_SPLITTER}message 2"
        ]
        for msg in msgs:
            with self.subTest(msg=msg):
                helpers.parse_std_and_write_to_gp_ui(msg)

    def test_run_gp_tool(self):
        """Test the run_gp_tool function."""
        # Set up a logger to use with the function
        logger = logging.getLogger(__name__)  # pylint:disable=invalid-name
        # Test for handled tool execute error (create fgdb in invalid folder)
        with self.assertRaises(arcpy.ExecuteError):
            helpers.run_gp_tool(
                logger,
                arcpy.management.CreateFileGDB,
                [self.scratch_folder + "DoesNotExist"],
                {"out_name": "outputs.gdb"}
            )
        # Test for handled non-arcpy error when calling function
        with self.assertRaises(TypeError):
            helpers.run_gp_tool(logger, "BadTool", [self.scratch_folder])
        # Valid call to tool with simple function
        helpers.run_gp_tool(
            logger, arcpy.management.CreateFileGDB, [self.scratch_folder], {"out_name": "testRunTool.gdb"})


if __name__ == '__main__':
    unittest.main()
