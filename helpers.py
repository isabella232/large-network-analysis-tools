"""Helper functions for large network analysis tools.

This is a sample script users can modify to fit their specific needs.

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
import enum
import traceback
import arcpy

arcgis_version = arcpy.GetInstallInfo()["Version"]

# Set some shared global variables that can be referenced from the other scripts
MSG_STR_SPLITTER = " | "
DISTANCE_UNITS = ["Kilometers", "Meters", "Miles", "Yards", "Feet", "NauticalMiles"]
TIME_UNITS = ["Days", "Hours", "Minutes", "Seconds"]
OUTPUT_FORMATS = ["Feature class", "CSV files"]
if arcgis_version >= "2.9":
    # The ODCostMatrix solver object's toArrowTable method was added at Pro 2.9. Allow this output format only
    # in software versions that support it.
    OUTPUT_FORMATS.append("Apache Arrow files")
MAX_AGOL_PROCESSES = 4  # AGOL concurrent processes are limited so as not to overload the service for other users.
DATETIME_FORMAT = "%Y%m%d %H:%M"  # Used for converting between datetime and string


def is_nds_service(network_data_source):
    """Determine if the network data source points to a service.

    Args:
        network_data_source (network data source): Network data source to check.

    Returns:
        bool: True if the network data source is a service URL. False otherwise.
    """
    if not isinstance(network_data_source, str):
        # Probably a network dataset layer
        return False
    return bool(network_data_source.startswith("http"))


def get_tool_limits_and_is_agol(network_data_source, service_name, tool_name):
    """Retrieve a dictionary of various limits supported by a portal tool and whether the portal uses AGOL services.

    Assumes that we have already determined that the network data source is a service.

    Args:
        network_data_source (str): URL to the service being used as the network data source.
        service_name (str): Name of the service, such as "asyncODCostMatrix" or "asyncRoute".
        tool_name (_type_): Tool name for the designated service, such as "GenerateOriginDestinationCostMatrix" or
            "FindRoutes".

    Returns:
        (dict, bool): Dictionary of service limits; Boolean indicating if the service is ArcGIS Online or a hybrid
            portal that falls back to ArcGIS Online.
    """
    arcpy.AddMessage("Getting tool limits from the portal...")
    try:
        tool_info = arcpy.nax.GetWebToolInfo(service_name, tool_name, network_data_source)
        # serviceLimits returns the maximum origins and destinations allowed by the service, among other things
        service_limits = tool_info["serviceLimits"]
        # isPortal returns True for Enterprise portals and False for AGOL or hybrid portals that fall back to using
        # the AGOL services
        is_agol = not tool_info["isPortal"]
        return service_limits, is_agol
    except Exception:
        arcpy.AddError("Error getting tool limits from the portal.")
        errs = traceback.format_exc().splitlines()
        for err in errs:
            arcpy.AddError(err)
        raise


def convert_time_units_str_to_enum(time_units):
    """Convert a string representation of time units to an arcpy.nax enum.

    Raises:
        ValueError: If the string cannot be parsed as a valid arcpy.nax.TimeUnits enum value.
    """
    if time_units.lower() == "minutes":
        return arcpy.nax.TimeUnits.Minutes
    if time_units.lower() == "seconds":
        return arcpy.nax.TimeUnits.Seconds
    if time_units.lower() == "hours":
        return arcpy.nax.TimeUnits.Hours
    if time_units.lower() == "days":
        return arcpy.nax.TimeUnits.Days
    # If we got to this point, the input time units were invalid.
    err = f"Invalid time units: {time_units}"
    arcpy.AddError(err)
    raise ValueError(err)


def convert_distance_units_str_to_enum(distance_units):
    """Convert a string representation of distance units to an arcpy.nax.DistanceUnits enum.

    Raises:
        ValueError: If the string cannot be parsed as a valid arcpy.nax.DistanceUnits enum value.
    """
    if distance_units.lower() == "miles":
        return arcpy.nax.DistanceUnits.Miles
    if distance_units.lower() == "kilometers":
        return arcpy.nax.DistanceUnits.Kilometers
    if distance_units.lower() == "meters":
        return arcpy.nax.DistanceUnits.Meters
    if distance_units.lower() == "feet":
        return arcpy.nax.DistanceUnits.Feet
    if distance_units.lower() == "yards":
        return arcpy.nax.DistanceUnits.Yards
    if distance_units.lower() == "nauticalmiles" or distance_units.lower() == "nautical miles":
        return arcpy.nax.DistanceUnits.NauticalMiles
    # If we got to this point, the input distance units were invalid.
    err = f"Invalid distance units: {distance_units}"
    arcpy.AddError(err)
    raise ValueError(err)


class OutputFormat(enum.Enum):
    """Enum defining the output format for the OD Cost Matrix results."""

    featureclass = 1
    csv = 2
    arrow = 3


def convert_output_format_str_to_enum(output_format):
    """Convert a string representation of the desired output format to an enum.

    Raises:
        ValueError: If the string cannot be parsed as a valid arcpy.nax.DistanceUnits enum value.
    """
    if output_format.lower() == "feature class":
        return OutputFormat.featureclass
    if output_format.lower() == "csv files":
        return OutputFormat.csv
    if output_format.lower() == "apache arrow files":
        return OutputFormat.arrow
    # If we got to this point, the input distance units were invalid.
    err = f"Invalid output format: {output_format}"
    arcpy.AddError(err)
    raise ValueError(err)


def validate_input_feature_class(feature_class):
    """Validate that the designated input feature class exists and is not empty.

    Args:
        feature_class (str, layer): Input feature class or layer to validate

    Raises:
        ValueError: The input feature class does not exist.
        ValueError: The input feature class has no rows.
    """
    if not arcpy.Exists(feature_class):
        err = f"Input dataset {feature_class} does not exist."
        arcpy.AddError(err)
        raise ValueError(err)
    if int(arcpy.management.GetCount(feature_class).getOutput(0)) <= 0:
        err = f"Input dataset {feature_class} has no rows."
        arcpy.AddError(err)
        raise ValueError(err)


def precalculate_network_locations(input_features, network_data_source, travel_mode, config_file_props):
    """Precalculate network location fields if possible for faster loading and solving later.

    Cannot be used if the network data source is a service. Uses the searchTolerance, searchToleranceUnits, and
    searchQuery properties set in the config file.

    Args:
        input_features (feature class catalog path): Feature class to calculate network locations for
        network_data_source (network dataset catalog path): Network dataset to use to calculate locations
        travel_mode (travel mode): Travel mode name, object, or json representation to use when calculating locations.
        config_file_props (dict): Dictionary of solver object properties from config file.
    """
    arcpy.AddMessage(f"Precalculating network location fields for {input_features}...")

    # Get location settings from config file if present
    search_tolerance = None
    if "searchTolerance" in config_file_props and "searchToleranceUnits" in config_file_props:
        search_tolerance = f"{config_file_props['searchTolerance']} {config_file_props['searchToleranceUnits'].name}"
    search_query = config_file_props.get("search_query", None)

    # Calculate network location fields if network data source is local
    arcpy.na.CalculateLocations(
        input_features, network_data_source,
        search_tolerance=search_tolerance,
        search_query=search_query,
        travel_mode=travel_mode
    )


def parse_std_and_write_to_gp_ui(msg_string):
    """Parse a message string returned from the subprocess's stdout and write it to the GP UI according to type.

    Logged messages in the ParallelODCM module start with a level indicator that allows us to parse them and write them
    as errors, warnings, or info messages.  Example: "ERROR | Something terrible happened" is an error message.

    Args:
        msg_string (str): Message string (already decoded) returned from ParallelODCM.py subprocess stdout
    """
    try:
        level, msg = msg_string.split(MSG_STR_SPLITTER)
        if level in ["ERROR", "CRITICAL"]:
            arcpy.AddError(msg)
        elif level == "WARNING":
            arcpy.AddWarning(msg)
        else:
            arcpy.AddMessage(msg)
    except Exception:  # pylint: disable=broad-except
        arcpy.AddMessage(msg_string)
