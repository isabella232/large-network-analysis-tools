"""Python toolbox that defines tools for solving large network analysis problems.

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
# Disable a bunch of linter errors caused by the standard python toolbox class definitions that we cannot change
# pylint: disable=invalid-name, useless-object-inheritance, too-few-public-methods, no-self-use, too-many-locals
# pylint: disable=useless-return, unused-argument
import arcpy

import helpers
from solve_large_odcm import ODCostMatrixSolver
from solve_large_route_pair_analysis import RoutePairSolver


class Toolbox(object):
    """Tools for solving large network analysis problems."""

    def __init__(self):
        """Define the toolbox."""
        self.label = "Large Network Analysis Tools"
        self.alias = "LargeNetworkAnalysisTools"

        # List of tool classes associated with this toolbox
        self.tools = [SolveLargeODCostMatrix, SolveLargeAnalysisWithKnownPairs]


class SolveLargeODCostMatrix(object):
    """Sample script tool to solve a large OD Cost Matrix by chunking the input data and solving in parallel."""

    def __init__(self):
        """Define the tool."""
        self.label = "Solve Large OD Cost Matrix"
        self.description = (
            "Solve a large OD Cost Matrix problem by chunking the input data and solving in parallel."
        )
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        param_origins = arcpy.Parameter(
            displayName="Origins",
            name="Origins",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        param_destinations = arcpy.Parameter(
            displayName="Destinations",
            name="Destinations",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        param_network = arcpy.Parameter(
            displayName="Network Data Source",
            name="Network_Data_Source",
            datatype="GPNetworkDataSource",
            parameterType="Required",
            direction="Input"
        )

        param_travel_mode = arcpy.Parameter(
            displayName="Travel Mode",
            name="Travel_Mode",
            datatype="NetworkTravelMode",
            parameterType="Required",
            direction="Input"
        )
        param_travel_mode.parameterDependencies = [param_network.name]

        param_time_units = arcpy.Parameter(
            displayName="Time Units",
            name="Time_Units",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param_time_units.filter.list = helpers.TIME_UNITS
        param_time_units.value = "Minutes"

        param_distance_units = arcpy.Parameter(
            displayName="Distance Units",
            name="Distance_Units",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param_distance_units.filter.list = helpers.DISTANCE_UNITS
        param_distance_units.value = "Miles"

        param_chunk_size = arcpy.Parameter(
            displayName="Maximum Origins and Destinations per Chunk",
            name="Max_Inputs_Per_Chunk",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param_chunk_size.value = 1000

        param_max_processes = arcpy.Parameter(
            displayName="Maximum Number of Parallel Processes",
            name="Max_Processes",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param_max_processes.value = 4

        param_out_origins = arcpy.Parameter(
            displayName="Output Updated Origins",
            name="Output_Updated_Origins",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output"
        )

        param_out_destinations = arcpy.Parameter(
            displayName="Output Updated Destinations",
            name="Output_Updated_Destinations",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output"
        )

        param_output_format = arcpy.Parameter(
            displayName="Output OD Cost Matrix Format",
            name="Output_Format",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param_output_format.filter.list = helpers.OUTPUT_FORMATS
        param_output_format.value = helpers.OUTPUT_FORMATS[0]

        param_out_od_lines = arcpy.Parameter(
            displayName="Output OD Lines Feature Class",
            name="Output_OD_Lines_Feature_Class",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output"
        )

        param_out_folder = arcpy.Parameter(
            displayName="Output Folder",
            name="Output_Folder",
            datatype="DEFolder",
            parameterType="Optional",
            direction="Output"
        )

        param_cutoff = arcpy.Parameter(
            displayName="Cutoff",
            name="Cutoff",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )

        param_num_dests = arcpy.Parameter(
            displayName="Number of Destinations to Find for Each Origin",
            name="Num_Destinations",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        )

        param_time_of_day = arcpy.Parameter(
            displayName="Time of Day",
            name="Time_Of_Day",
            datatype="GPDate",
            parameterType="Optional",
            direction="Input"
        )

        param_barriers = arcpy.Parameter(
            displayName="Barriers",
            name="Barriers",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
            category="Advanced"
        )

        param_precalculate_network_locations = arcpy.Parameter(
            displayName="Precalculate Network Locations",
            name="Precalculate_Network_Locations",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Advanced"
        )
        param_precalculate_network_locations.value = True

        params = [
            param_origins,  # 0
            param_destinations,  # 1
            param_network,  # 2
            param_travel_mode,  # 3
            param_time_units,  # 4
            param_distance_units,  # 5
            param_chunk_size,  # 6
            param_max_processes,  # 7
            param_out_origins,  # 8
            param_out_destinations,  # 9
            param_output_format,  # 10
            param_out_od_lines,  # 11
            param_out_folder,  # 12
            param_cutoff,  # 13
            param_num_dests,  # 14
            param_time_of_day,  # 15
            param_barriers,  # 16
            param_precalculate_network_locations  # 17
        ]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        param_network = parameters[2]
        param_output_format = parameters[10]
        param_out_od_lines = parameters[11]
        param_out_folder = parameters[12]
        param_precalculate = parameters[17]

        # Make appropriate OD Cost Matrix output parameter visible based on chosen output format
        if not param_output_format.hasBeenValidated and param_output_format.altered and param_output_format.valueAsText:
            try:
                output_format = helpers.convert_output_format_str_to_enum(param_output_format.valueAsText)
                if output_format is helpers.OutputFormat.featureclass:
                    param_out_od_lines.enabled = True
                    param_out_folder.enabled = False
                else:  # For CSV and Arrow
                    param_out_od_lines.enabled = False
                    param_out_folder.enabled = True
            except ValueError:
                # The output format is invalid. Just do nothing.
                pass

        # Turn off and hide Precalculate Network Locations parameter if the network data source is a service
        update_precalculate_parameter(param_network, param_precalculate)

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        param_network = parameters[2]
        param_max_processes = parameters[7]
        param_output_format = parameters[10]
        param_out_od_lines = parameters[11]
        param_out_folder = parameters[12]

        # If the network data source is arcgis.com:
        # - Cap max processes
        cap_max_processes_for_agol(param_network, param_max_processes)
        # - Show an error if attempting to use Arrow output, which is not supported at this time
        if param_network.altered and param_network.valueAsText and helpers.is_nds_service(param_network.valueAsText):
            if param_output_format.altered and param_output_format.valueAsText:
                output_format = helpers.convert_output_format_str_to_enum(param_output_format.valueAsText)
                if output_format is helpers.OutputFormat.arrow:
                    param_output_format.setErrorMessage((
                        f"{param_output_format.valueAsText} output format is not available when a service is used as "
                        "the network data source."
                    ))

        # Make the appropriate output parameter required based on the user's choice of output format. Just require
        # whichever output parameter is enabled. Enablement is controlled in updateParameters() based on the user's
        # choice in the output format parameter.
        # The 735 error code doesn't display an actual error but displays the little red star to indicate that the
        # parameter is required.
        for param in [param_out_od_lines, param_out_folder]:
            if param.enabled:
                if not param.valueAsText:
                    param.setIDMessage("Error", 735, param.displayName)
            else:
                param.clearMessage()

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Initialize the solver class
        time_of_day = parameters[15].value
        if time_of_day:
            time_of_day = time_of_day.strftime(helpers.DATETIME_FORMAT)
        od_solver = ODCostMatrixSolver(
            parameters[0].value,  # origins
            parameters[1].value,  # destinations
            get_catalog_path(parameters[2]),  # network
            parameters[3].value,  # travel mode
            parameters[8].valueAsText,  # output origins
            parameters[9].valueAsText,  # output destinations
            parameters[6].value,  # chunk size
            parameters[7].value,  # max processes
            parameters[4].valueAsText,  # time units
            parameters[5].valueAsText,  # distance units
            parameters[10].valueAsText,  # output format
            parameters[11].valueAsText,  # output OD lines
            parameters[12].valueAsText,  # output data folder
            parameters[13].value,  # cutoff
            parameters[14].value,  # number of destinations to find
            time_of_day,  # time of day
            parameters[17].value,  # Should precalculate network locations
            get_catalog_path_multivalue(parameters[16])  # barriers
        )

        # Solve the OD Cost Matrix analysis
        od_solver.solve_large_od_cost_matrix()

        return


class SolveLargeAnalysisWithKnownPairs(object):
    """Sample script tool to solve a large analysis with known origin-destination pairs."""

    def __init__(self):
        """Define the tool."""
        self.label = "Solve Large Analysis With Known OD Pairs"
        self.description = ((
            "Solve a large analysis with known origin-destination pairs by chunking the input data and solving in "
            "parallel."
        ))
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        param_origins = arcpy.Parameter(
            displayName="Origins",
            name="Origins",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        param_origin_id_field = arcpy.Parameter(
            displayName="Origin Unique ID Field",
            name="Origin_Unique_ID_Field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param_origin_id_field.parameterDependencies = [param_origins.name]
        param_origin_id_field.filter.list = ["Short", "Long", "Double", "Single", "Text", "OID"]

        param_assigned_dest_field = arcpy.Parameter(
            displayName="Assigned Destination Field",
            name="Assigned_Destination_Field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param_assigned_dest_field.parameterDependencies = [param_origins.name]
        param_assigned_dest_field.filter.list = ["Short", "Long", "Double", "Single", "Text", "OID"]

        param_destinations = arcpy.Parameter(
            displayName="Destinations",
            name="Destinations",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        param_dest_id_field = arcpy.Parameter(
            displayName="Destination Unique ID Field",
            name="Destination_Unique_ID_Field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param_dest_id_field.parameterDependencies = [param_destinations.name]
        param_dest_id_field.filter.list = ["Short", "Long", "Double", "Single", "Text", "OID"]

        param_network = arcpy.Parameter(
            displayName="Network Data Source",
            name="Network_Data_Source",
            datatype="GPNetworkDataSource",
            parameterType="Required",
            direction="Input"
        )

        param_travel_mode = arcpy.Parameter(
            displayName="Travel Mode",
            name="Travel_Mode",
            datatype="NetworkTravelMode",
            parameterType="Required",
            direction="Input"
        )
        param_travel_mode.parameterDependencies = [param_network.name]

        param_time_units = arcpy.Parameter(
            displayName="Time Units",
            name="Time_Units",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param_time_units.filter.list = helpers.TIME_UNITS
        param_time_units.value = "Minutes"

        param_distance_units = arcpy.Parameter(
            displayName="Distance Units",
            name="Distance_Units",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param_distance_units.filter.list = helpers.DISTANCE_UNITS
        param_distance_units.value = "Miles"

        param_chunk_size = arcpy.Parameter(
            displayName="Maximum OD Pairs per Chunk",
            name="Max_Pairs_Per_Chunk",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param_chunk_size.value = 1000

        param_max_processes = arcpy.Parameter(
            displayName="Maximum Number of Parallel Processes",
            name="Max_Processes",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param_max_processes.value = 4

        param_out_routes = arcpy.Parameter(
            displayName="Output Routes",
            name="Output_Routes",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output"
        )

        param_time_of_day = arcpy.Parameter(
            displayName="Time of Day",
            name="Time_Of_Day",
            datatype="GPDate",
            parameterType="Optional",
            direction="Input"
        )

        param_barriers = arcpy.Parameter(
            displayName="Barriers",
            name="Barriers",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
            category="Advanced"
        )

        param_precalculate_network_locations = arcpy.Parameter(
            displayName="Precalculate Network Locations",
            name="Precalculate_Network_Locations",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Advanced"
        )
        param_precalculate_network_locations.value = True

        param_sort_origins = arcpy.Parameter(
            displayName="Sort Origins by Assigned Destination",
            name="Sort_Origins",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Advanced"
        )
        param_sort_origins.value = True

        param_reverse_direction = arcpy.Parameter(
            displayName="Reverse Direction of Travel",
            name="Reverse_Direction",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Advanced"
        )
        param_reverse_direction.value = False

        params = [
            param_origins,  # 0
            param_origin_id_field,  # 1
            param_assigned_dest_field,  # 2
            param_destinations,  # 3
            param_dest_id_field,  # 4
            param_network,  # 5
            param_travel_mode,  # 6
            param_time_units,  # 7
            param_distance_units,  # 8
            param_chunk_size,  # 9
            param_max_processes,  # 10
            param_out_routes,  # 11
            param_time_of_day,  # 12
            param_barriers,  # 13
            param_precalculate_network_locations,  # 14
            param_sort_origins,  # 15
            param_reverse_direction  # 16
        ]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        param_network = parameters[5]
        param_precalculate = parameters[14]

        # Turn off and hide Precalculate Network Locations parameter if the network data source is a service
        update_precalculate_parameter(param_network, param_precalculate)

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        param_network = parameters[5]
        param_max_processes = parameters[10]

        # If the network data source is arcgis.com, cap max processes
        cap_max_processes_for_agol(param_network, param_max_processes)

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Initialize the solver class
        time_of_day = parameters[12].value
        if time_of_day:
            time_of_day = time_of_day.strftime(helpers.DATETIME_FORMAT)
        rt_solver = RoutePairSolver(
            parameters[0].value,  # origins
            parameters[1].valueAsText,  # unique origin ID field
            parameters[2].valueAsText,  # assigned destination field
            parameters[3].value,  # destinations
            parameters[4].valueAsText,  # unique destination ID field
            get_catalog_path(parameters[5]),  # network
            parameters[6].value,  # travel mode
            parameters[7].valueAsText,  # time units
            parameters[8].valueAsText,  # distance units
            parameters[9].value,  # chunk size
            parameters[10].value,  # max processes
            parameters[11].valueAsText,  # output routes
            time_of_day,  # time of day
            get_catalog_path_multivalue(parameters[13]),  # barriers
            parameters[14].value,  # Should precalculate network locations
            parameters[15].value,  # Should sort origins
            parameters[16].value  # Reverse direction of travel
        )

        # Solve the OD Cost Matrix analysis
        rt_solver.solve_large_route_pair_analysis()

        return


def get_catalog_path(param):
    """Get the catalog path for a single value parameter if possible.

    Args:
        param (arcpy.Parameter): Parameter from which to retrieve the catalog path.

    Returns:
        str: Catalog path to the data
    """
    param_value = param.value
    if not param_value:
        return ""
    # If the value is a layer object, get its data source (catalog path)
    if hasattr(param_value, "dataSource"):
        return param_value.dataSource
    # Otherwise, it's probably already a string catalog path. Just return its text value.
    return param.valueAsText


def get_catalog_path_multivalue(param):
    """Get a list of catalog paths for a multivalue feature layer parameter if possible.

    Args:
        param (arcpy.Parameter): Parameter from which to retrieve the catalog paths.

    Returns:
        list(str): List of catalog paths to the data
    """
    if not param.values:
        return []
    # Get both the values as geoprocessing objects and the string values
    values = param.values
    # Have to strip the quotes that get added if there are spaces in the filepath.
    string_values = [val.strip("'") for val in param.valueAsText.split(";")]
    catalog_paths = []
    for idx, val in enumerate(values):
        # If the value is a layer object, get its data source (catalog path)
        if hasattr(val, "dataSource"):
            catalog_paths.append(val.dataSource)
        # Otherwise, it's probably already a string catalog path. The only way to get it is to retrive it from the
        # valueAsText string that we split up above.
        else:
            catalog_paths.append(string_values[idx])
    return catalog_paths


def update_precalculate_parameter(param_network, param_precalculate):
    """Turn off and hide Precalculate Network Locations parameter if the network data source is a service.

    Args:
        param_network (arcpy.Parameter): Parameter for the network data source
        param_precalculate (arcpy.Parameter): Parameter for precalculate network locations
    """
    if not param_network.hasBeenValidated and param_network.altered and param_network.valueAsText:
        if helpers.is_nds_service(param_network.valueAsText):
            param_precalculate.value = False
            param_precalculate.enabled = False
        else:
            param_precalculate.enabled = True


def cap_max_processes_for_agol(param_network, param_max_processes):
    """If the network data source is arcgis.com, cap max processes.

    Args:
        param_network (arcpy.Parameter): Parameter for the network data source
        param_max_processes (arcpy.Parameter): Parameter for the max processes
    """
    if param_network.altered and param_network.valueAsText and helpers.is_nds_service(param_network.valueAsText):
        if param_max_processes.altered and param_max_processes.valueAsText:
            if "arcgis.com" in param_network.valueAsText and param_max_processes.value > helpers.MAX_AGOL_PROCESSES:
                param_max_processes.setErrorMessage((
                    f"The maximum number of parallel processes cannot exceed {helpers.MAX_AGOL_PROCESSES} when the "
                    "ArcGIS Online services are used as the network data source."
                ))
