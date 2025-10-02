# MaxEnt Data Preparation Tool

A Python script for preparing raster environmental data for MaxEnt (Maximum Entropy) species distribution modeling. This tool automates the process of resampling, clipping, aligning, and converting multiple raster datasets to ASCII format required by MaxEnt.

## Features

- **Automated Processing**: Handles multiple folders of raster data in a single run
- **Spatial Alignment**: Ensures all output rasters have identical dimensions, resolution, and extent
- **Format Conversion**: Converts GeoTIFF rasters to ASCII (.asc) format for MaxEnt compatibility
- **Reprojection Support**: Automatically reprojects datasets to match reference coordinate system
- **ROI Clipping**: Clips all rasters to a defined region of interest (shapefile)
- **Comprehensive Verification**: Validates that all processed files have matching dimensions
- **Detailed Reporting**: Provides processing summaries and error tracking

## Requirements

### Software Dependencies
- **ArcGIS Pro** or **ArcGIS Desktop** (10.x or later)
- **Spatial Analyst Extension** (must be licensed and available)
- **Python** (included with ArcGIS installation)
- **arcpy** module (included with ArcGIS)

### Input Data Requirements
- **ROI Shapefile**: A shapefile defining your study area/region of interest
- **Raster Data**: Environmental layers in GeoTIFF format (.tif or .tiff)
  - Examples: bioclimatic variables, soil data, elevation, vegetation indices, etc.

## Installation

1. Ensure ArcGIS Pro or ArcGIS Desktop is installed with Spatial Analyst extension
2. Download the `prepare_maxent_data.py` script
3. No additional Python packages required (uses built-in ArcGIS modules)

## Usage

### Basic Usage

```python
from prepare_maxent_data import prepare_maxent_data

# Define your ROI shapefile
roi_shapefile = r"C:\path\to\your\roi.shp"

# Define input folders containing raster data
input_folders = {
    'bioclimatic_variables': r"C:\path\to\bioclim",
    'soil': r"C:\path\to\soil",
    'elevation': r"C:\path\to\elevation"
}

# Define output folder
output_base_folder = r"C:\path\to\output\maxent_ready"

# Run processing
results = prepare_maxent_data(
    roi_shapefile=roi_shapefile,
    input_folders=input_folders,
    output_base_folder=output_base_folder,
    reference_folder='bioclimatic_variables'  # Optional
)
```

### Parameters

#### `roi_shapefile` (str, required)
Path to the shapefile defining your region of interest. All rasters will be clipped to this boundary.

#### `input_folders` (dict, required)
Dictionary mapping folder names to folder paths containing raster data.
```python
input_folders = {
    'folder_name': r'C:\path\to\folder',
    'another_folder': r'C:\path\to\another'
}
```

#### `output_base_folder` (str, required)
Base directory where processed data will be saved. Subfolders will be created automatically for each input folder.

#### `reference_folder` (str, optional)
Key name from `input_folders` to use as spatial reference. If not specified, the first folder in `input_folders` is used. The reference folder determines:
- Target cell size/resolution
- Target spatial reference system
- Target extent (after clipping to ROI)

### Output Structure

```
output_base_folder/
├── bioclimatic_variables_processed/
│   ├── bio1.asc
│   ├── bio2.asc
│   └── ...
├── soil_processed/
│   ├── soil_ph.asc
│   ├── soil_organic.asc
│   └── ...
└── elevation_processed/
    └── dem.asc
```

### Return Value

The function returns a dictionary containing:

```python
{
    'success': True/False,  # Overall success status
    'output_folders': {
        'folder_name': 'path/to/output/folder'
    },
    'processed_files': {
        'folder_name': ['file1.asc', 'file2.asc']
    },
    'failed_files': {
        'folder_name': ['failed_file.tif']
    },
    'summary': {
        'folder_name': {
            'total': 10,
            'success': 9,
            'failed': 1
        }
    }
}
```

## Processing Steps

The tool performs the following operations on each raster:

1. **Reference Identification**: Selects a reference raster to establish target properties
2. **Reprojection** (if needed): Projects rasters to match reference coordinate system
3. **Clipping**: Clips rasters to ROI boundary
4. **Resampling**: Resamples to match reference cell size using bilinear interpolation
5. **Alignment**: Ensures exact pixel alignment using mask extraction
6. **Format Conversion**: Converts to ASCII format (.asc)
7. **Verification**: Validates dimensions across all output files

## Example Scenarios

### Scenario 1: Basic Species Distribution Modeling

```python
roi = r"C:\data\study_area.shp"

input_folders = {
    'worldclim': r"C:\data\worldclim_bioclim",
    'soilgrids': r"C:\data\soil_properties"
}

output = r"C:\data\maxent_inputs"

results = prepare_maxent_data(roi, input_folders, output)
```

### Scenario 2: Multiple Environmental Layers

```python
input_folders = {
    'climate': r"C:\data\bioclim",
    'topography': r"C:\data\elevation",
    'soil': r"C:\data\soil",
    'landcover': r"C:\data\lulc",
    'vegetation': r"C:\data\ndvi"
}

results = prepare_maxent_data(
    roi_shapefile=r"C:\data\roi.shp",
    input_folders=input_folders,
    output_base_folder=r"C:\data\processed",
    reference_folder='climate'  # Use climate data as reference
)
```

## Important Notes

### Spatial Considerations
- All output rasters will match the reference raster's cell size and coordinate system
- Ensure your ROI shapefile is in a compatible projection (or will be handled automatically)
- Bilinear interpolation is used for resampling (suitable for continuous data)

### Performance Tips
- Processing time depends on:
  - Number of rasters
  - Raster dimensions
  - ROI extent
  - System resources
- Large datasets may take considerable time
- Temporary data is stored in memory when possible

### Troubleshooting

**Error: "Spatial Analyst extension not available"**
- Ensure Spatial Analyst license is available
- Check license manager in ArcGIS

**Error: "No .tif files found in folder"**
- Verify folder paths are correct
- Ensure raster files have .tif or .tiff extension

**Dimension mismatches detected**
- May indicate processing errors
- Check individual failed files in results dictionary
- Review console output for specific errors

**Memory errors**
- Reduce ROI extent
- Process fewer folders at once
- Close other applications

## Best Practices

1. **Test with Small Dataset**: Run on a subset first to verify settings
2. **Check Coordinate Systems**: Ensure ROI and rasters are in appropriate projections
3. **Reference Selection**: Choose the highest quality/most important layer as reference
4. **Backup Original Data**: Keep original rasters unchanged
5. **Review Output**: Always verify dimensions and check ASCII headers
6. **Documentation**: Keep track of which reference folder/settings were used

## MaxEnt Integration

After processing, use the output ASCII files in MaxEnt:

1. **Environmental Layers**: Point MaxEnt to the output folders
2. **Samples File**: Ensure species occurrence data coordinates match the processed rasters' extent
3. **Settings**: All layers will have identical dimensions, so no additional alignment needed

## License

This tool uses ArcGIS software which requires appropriate licensing. Ensure you have the necessary licenses before use.

## Support

For issues related to:
- **ArcGIS/arcpy**: Consult Esri documentation or support
- **MaxEnt**: Refer to MaxEnt software documentation
- **Script functionality**: Review error messages in console output

## Version History

- **v1.0**: Initial release with core functionality
  - Multi-folder processing
  - Automatic alignment and resampling
  - ASCII conversion
  - Comprehensive verification

## Contributing

Suggested improvements:
- Support for additional raster formats
- Alternative resampling methods
- Parallel processing for large datasets
- GUI interface
- Progress bars for long operations

---

**Author**: Environmental Data Processing Tool  
**Purpose**: Streamline preparation of environmental data for MaxEnt species distribution modeling  
**Last Updated**: 2025
