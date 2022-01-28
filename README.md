
# large-network-analysis-tools

The tools and code samples here help you solve large network analysis problems in ArcGIS Pro. We have provided a python script that can solve a large origin destination cost matrix problem by chunking the input data, solving in parallel, and combining the results into a single output.

## Features
* The LargeNetworkAnalysisTools.pyt toolbox has a geoprocessing tool called "Solve Large OD Cost Matrix" that can be used to solve large origin destination cost matrix problems. You can run this tool as-is out of the box with no changes to the code.
* You can modify the provided scripts to suit your needs, or you can use them as an example when writing your own script.

## Requirements

* ArcGIS Pro 2.5 or later
* One of the following three options:
  * A routable [network dataset](https://pro.arcgis.com/en/pro-app/help/analysis/networks/what-is-network-dataset-.htm) and the Network Analyst extension license
  * An ArcGIS Online account with routing privileges and sufficient [credits](https://pro.arcgis.com/en/pro-app/tool-reference/appendices/geoprocessing-tools-that-use-credits.htm#ESRI_SECTION1_3EF40A7C01C042D8A76DB9518B793E9E)
  * A portal with [ArcGIS Enterprise routing services](https://pro.arcgis.com/en/pro-app/help/analysis/networks/using-arcgis-enterprise-routing-services.htm) configured.
* Origin and destination points you wish to analyze

## Instructions

1. Download the latest release
2. Modify the code to suit your needs if desired
3. Run the code in standalone python, or run the provided geoprocessing tool from within ArcGIS Pro.

### Solve Large OD Cost Matrix tool inputs
- **Origins** (Python: *Origins*) - The feature class or layer containing the origins. Layers are referenced by catalog path, so selection sets and definition queries will be ignored. If you want to subset your data, please copy the subset to a separate feature class before running this tool.
- **Destinations** (Python: *Destinations*) - The feature class or layer containing the destinations. Layers are referenced by catalog path, so selection sets and definition queries will be ignored. If you want to subset your data, please copy the subset to a separate feature class before running this tool.
- **Output OD Lines Feature Class** (Python: *Output_OD_Lines_Feature_Class*) - Path to the output feature class that will contain the OD Cost Matrix Lines output computed by the tool. The schema of this feature class is described in the [arcpy documentation](https://pro.arcgis.com/en/pro-app/latest/arcpy/network-analyst/origindestinationcostmatrix-output-data-types.htm#ESRI_SECTION1_9FF9489173C741DD95472F21B5AD8374). Note that the OriginOID and DestinationOID fields refer to the ObjectIDs of the Output Updated Origins and Output Updated Destinations feature classes and not the original input data.
- **Output Updated Origins** (Python: *Output_Updated_Origins*) - Path to the output feature class that will contain the updated origins, which may be spatially sorted and have added fields. The OriginOID field in the Output OD Lines Feature Class refers to the ObjectID of the Output Updated Origins and not the original input origins.
- **Output Updated Destinations** (Python: *Output_Updated_Destinations*) - Path to the output feature class that will contain the updated destinations, which may be spatially sorted and have added fields. The DestinationOID field in the Output OD Lines Feature Class refers to the ObjectID of the Output Updated Destinations and not the original input destinations.
- **Network Data Source** (Python: *Network_Data_Source*) - Network dataset, network dataset layer, or portal URL to use when calculating the OD Cost Matrix.
- **Travel Mode** (Python: *Travel_Mode*) - Network travel mode to use when calculating the OD Cost Matrix
- **Time Units** (Python: *Time_Units*) - The time units the output Total_Time field will be reported in.
- **Distance Units** (Python: *Distance_Units*) - The distance units the output Total_Distance field will be reported in.
- **Maximum Origins and Destinations per Chunk** (Python: *Max_Inputs_Per_Chunk*) - Defines the chunk size for parallel OD Cost Matrix calculations. For example, if you want to process a maximum of 1000 origins and 1000 destinations in a single chunk, set this parameter to 1000.
- **Maximum Number of Parallel Processes** (Python: *Max_Processes*) - Defines the maximum number of parallel processes to run at once. Do not exceed the number of cores of your machine.
- **Cutoff** (Python: *Cutoff*) - Impedance cutoff limiting the search distance for each origin. For example, you could set up the problem to find only destinations within a 15 minute drive time of the origins. This parameter is optional. Leaving it blank uses no cutoff.
  - If your travel mode has time-based impedance units, Cutoff represents a time and is interpreted in the units specified in the Time Units parameter.
  - If your travel mode has distance-based impedance units, Cutoff represents a distance and is interpreted in the units specified in the Distance Units parameter.
  - If your travel mode has other units (not time- or distance-based), Cutoff should be specified in the units of your travel mode's impedance attribute.
- **Number of Destinations to Find for Each Origin** (Python: *Num_Destinations*) - The number of destinations to find for each origin. For example, setting this to 3 will result in the output including the travel time and distance from each origin to its three closest destinations. This parameter is optional. Leaving it blank results in finding the travel time and distance from each origin to all destinations.
- **Barriers** (Python: *Barriers*) - Point, line, or polygon barriers to use in the OD Cost Matrix analysis. This parameter is optional.
- **Precalculate Network Locations** (Python: *Precalculate_Network_Locations*) - When you solve a network analysis, the input points must "locate" on the network used for the analysis. When chunking your inputs to solve in parallel, inputs may be used many times. Rather than calculating the network location fields for each input every time it is used, it is more efficient to calculate all the network location fields up front and re-use them. Set this parameter to True to pre-calculate the network location fields. This is recommended for every situation unless:
  - You are using a portal URL as the network data source. In this case, pre-calculating network locations is not possible, and the parameter is hidden.
  - You have already pre-calculated the network location fields using the network dataset and travel mode you are using for this analysis. In this case, you can save time by not precalculating them again.

### Running the tool from ArcGIS Pro

You can run the tool in ArcGIS Pro just like any other geoprocessing tool. You just need to connect to the provided Python toolbox from the Catalog Pane either in the Toolboxes section or the Folders section.

If you plan to use ArcGIS Online or a portal as your network data source, make sure you're connected to that portal in your current Pro session.

![Screenshot of tool dialog](./images/ToolDialogScreenshot.png)

### Running the tool from standalone Python

You can call the tool from your own standalone Python script.

As with any custom script tool, you must first import the toolbox within your standalone script:
`arcpy.ImportToolbox(<full path to LargeNetworkAnalysisTools.pyt>)`

Then, you can call the tool in your script:
`arcpy.LargeNetworkAnalysisTools.SolveLargeODCostMatrix(<tool parameters>)`

Here is the full tool signature:
```python
arcpy.LargeNetworkAnalysisTools.SolveLargeODCostMatrix(
    Origins, Destinations, Output_OD_Lines_Feature_Class, Output_Updated_Origins, Output_Updated_Destinations,
    Network_Data_Source, Travel_Mode, Time_Units, Distance_Units, Max_Inputs_Per_Chunk, Max_Processes, Cutoff,
    Num_Destinations, Barriers, Precalculate_Network_Locations
)
```

You can also run the provided scripts by directly calling solve_large_odcm.py from the command line instead of using the geoprocessing tool as the code's gateway. Call `python solve_large_odcm.py -h` to print the command line help to show you how to do this.

## Technical explanation of how this tool works

The tool consists of several scripts:
- **LargeNetworkAnalysisTools.pyt**: This defines the python toolbox and the tool as you see it in the ArcGIS Pro UI. It does some minimal parameter validation and calls solve_large_odcm.py to actually run the analysis.
- **solve_large_odcm.py**: This defines a class, `ODCostMatrixSolver()`, that validates and preprocesses the inputs and then calls parallel_odcm.py as a subprocess to do the parallel solves. The class also parses log messages from the parallel_odcm.py and writes them out as geoprocessing messages.
- **parallel_odcm.py**: This script chunks the inputs, solves the OD Cost Matrices in parallel, and combines the results.
- **od_config.py**: In this file, you can override some OD Cost Matrix analysis settings that are not included in the tool dialog. This is provided to make the scripts easier to customize so you don't have to dig through the more complex parts of the code to find these simple settings.
- **helpers.py**: Contains some helper methods and global variables.

Why do we have both solve_large_odcm.py and parallel_odcm.py? Why do we call parallel_odcm.py as a subprocess? This is necessary to accommodate running this tool from the ArcGIS Pro UI. A script tool running in the ArcGIS Pro UI cannot directly call multiprocessing using concurrent.futures. We must instead spin up a subprocess, and the subprocess must spawn parallel processes for the calculations. Thus, solve_large_odcm.py does all the pre-processing in the main python process, but it passes the inputs to parallel_odcm.py as a separate subprocess, and that subprocess can, in turn, spin up parallel processes for the OD Cost Matrix calculations.

## Resources

* [OD Cost Matrix tutorial](https://pro.arcgis.com/en/pro-app/help/analysis/networks/od-cost-matrix-tutorial.htm)
* [Network Analyst arcpy.nax python module documentation](https://pro.arcgis.com/en/pro-app/arcpy/network-analyst/what-is-the-network-analyst-module.htm)
* [Video presentation about solving large problems from DevSummit 2020](https://youtu.be/9PI7HIm1y8U)

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing
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

A copy of the license is available in the repository's [license.txt](license.txt) file.