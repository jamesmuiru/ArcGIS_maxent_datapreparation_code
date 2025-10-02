import arcpy
from arcpy.sa import *
import os

def prepare_maxent_data(roi_shapefile, input_folders, output_base_folder, reference_folder=None):
    """
    Prepare raster data for MaxEnt modeling by resampling, clipping, and converting to ASCII format.
    
    Parameters:
    -----------
    roi_shapefile : str
        Path to the shapefile defining the region of interest for clipping
    input_folders : dict
        Dictionary with folder names as keys and folder paths as values
        Example: {'bioclim': 'C:/path/to/bioclim', 'soil': 'C:/path/to/soil'}
    output_base_folder : str
        Base folder path where processed data will be saved
    reference_folder : str, optional
        Key name of the folder to use as reference (from input_folders dict)
        If None, uses the first folder in input_folders
    
    Returns:
    --------
    dict : Dictionary containing processing results and output paths
    """
    
    # Check out Spatial Analyst extension
    arcpy.CheckOutExtension("Spatial")
    
    # Set overwrite output
    arcpy.env.overwriteOutput = True
    
    print("=" * 80)
    print("MAXENT DATA PREPARATION FUNCTION")
    print("=" * 80)
    print(f"\nROI Shapefile: {roi_shapefile}")
    print(f"Output Base Folder: {output_base_folder}")
    print(f"Input Folders: {len(input_folders)}")
    
    # Validate inputs
    if not os.path.exists(roi_shapefile):
        raise FileNotFoundError(f"ROI shapefile not found: {roi_shapefile}")
    
    for name, path in input_folders.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input folder '{name}' not found: {path}")
    
    # Create output base folder
    os.makedirs(output_base_folder, exist_ok=True)
    
    # Determine reference folder
    if reference_folder is None:
        reference_folder = list(input_folders.keys())[0]
        print(f"\nUsing '{reference_folder}' as reference folder (default)")
    else:
        if reference_folder not in input_folders:
            raise ValueError(f"Reference folder '{reference_folder}' not found in input_folders")
        print(f"\nUsing '{reference_folder}' as reference folder (specified)")
    
    ref_folder_path = input_folders[reference_folder]

    
    # Step 1: Get reference raster properties
    print("\n" + "=" * 80)
    print("Step 1: Identifying reference raster...")
    print("=" * 80)
    
    ref_files = [f for f in os.listdir(ref_folder_path) if f.lower().endswith(('.tif', '.tiff'))]
    
    if not ref_files:
        raise Exception(f"No .tif files found in reference folder: {ref_folder_path}")
    
    reference_raster = os.path.join(ref_folder_path, ref_files[0])
    print(f"Reference raster: {os.path.basename(reference_raster)}")
    
    # Get reference raster properties
    ref_desc = arcpy.Describe(reference_raster)
    ref_raster = arcpy.Raster(reference_raster)
    ref_cell_size = ref_raster.meanCellWidth
    ref_extent = ref_desc.extent
    ref_sr = ref_desc.spatialReference
    
    print(f"\nReference Raster Properties:")
    print(f"  - Cell Size: {ref_cell_size}")
    print(f"  - Spatial Reference: {ref_sr.name}")
    print(f"  - Extent: {ref_extent}")
    
    # Step 2: Clip reference raster to ROI
    print("\n" + "=" * 80)
    print("Step 2: Clipping reference raster to ROI...")
    print("=" * 80)
    
    temp_ref_clipped = r"in_memory\ref_clipped"
    
    try:
        arcpy.management.Clip(
            in_raster=reference_raster,
            rectangle="",
            out_raster=temp_ref_clipped,
            in_template_dataset=roi_shapefile,
            clipping_geometry="ClippingGeometry",
            maintain_clipping_extent="NO_MAINTAIN_EXTENT"
        )
        
        # Get final extent after clipping
        final_raster = arcpy.Raster(temp_ref_clipped)
        final_extent = arcpy.Describe(temp_ref_clipped).extent
        
        print(f"Final clipped extent: {final_extent}")
        print(f"Final dimensions: {final_raster.width} x {final_raster.height}")
        
        # Set environment settings
        arcpy.env.extent = final_extent
        arcpy.env.cellSize = ref_cell_size
        arcpy.env.snapRaster = temp_ref_clipped
        arcpy.env.outputCoordinateSystem = ref_sr
        
    except Exception as e:
        print(f"Error clipping reference raster: {e}")
        arcpy.CheckInExtension("Spatial")
        raise

    
    # Step 3: Process all input folders
    print("\n" + "=" * 80)
    print("Step 3: Processing All Input Folders...")
    print("=" * 80)
    
    results = {
        'success': True,
        'output_folders': {},
        'processed_files': {},
        'failed_files': {},
        'summary': {}
    }
    
    for folder_name, folder_path in input_folders.items():
        print(f"\n{'=' * 80}")
        print(f"Processing Folder: {folder_name}")
        print(f"Path: {folder_path}")
        print(f"{'=' * 80}")
        
        # Create output subfolder
        output_folder = os.path.join(output_base_folder, f"{folder_name}_processed")
        os.makedirs(output_folder, exist_ok=True)
        results['output_folders'][folder_name] = output_folder
        results['processed_files'][folder_name] = []
        results['failed_files'][folder_name] = []
        
        # Get all raster files
        raster_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.tif', '.tiff'))]
        
        if not raster_files:
            print(f"WARNING: No .tif files found in {folder_name}")
            continue
        
        print(f"Found {len(raster_files)} raster file(s) to process\n")
        
        # Process each raster
        for idx, raster_file in enumerate(raster_files, 1):
            try:
                input_path = os.path.join(folder_path, raster_file)
                basename = os.path.splitext(raster_file)[0]
                
                print(f"[{idx}/{len(raster_files)}] Processing: {raster_file}")
                
                # Check if reprojection is needed
                raster_sr = arcpy.Describe(input_path).spatialReference
                current_input = input_path
                
                if raster_sr.name != ref_sr.name:
                    print(f"  - Reprojecting from {raster_sr.name} to {ref_sr.name}")
                    temp_projected = r"in_memory\temp_projected"
                    arcpy.management.ProjectRaster(
                        in_raster=input_path,
                        out_raster=temp_projected,
                        out_coor_system=ref_sr,
                        resampling_type="BILINEAR"
                    )
                    current_input = temp_projected
                
                # Clip to ROI
                temp_clipped = r"in_memory\temp_clipped"
                arcpy.management.Clip(
                    in_raster=current_input,
                    rectangle="",
                    out_raster=temp_clipped,
                    in_template_dataset=roi_shapefile,
                    clipping_geometry="ClippingGeometry",
                    maintain_clipping_extent="NO_MAINTAIN_EXTENT"
                )
                
                # Resample to match reference cell size
                temp_resampled = r"in_memory\temp_resampled"
                arcpy.management.Resample(
                    in_raster=temp_clipped,
                    out_raster=temp_resampled,
                    cell_size=ref_cell_size,
                    resampling_type="BILINEAR"
                )
                
                # Ensure exact alignment using ExtractByMask
                aligned_raster = ExtractByMask(temp_resampled, temp_ref_clipped)
                
                # Convert to ASCII
                output_asc = os.path.join(output_folder, f"{basename}.asc")
                arcpy.conversion.RasterToASCII(aligned_raster, output_asc)
                
                # Verify dimensions
                verify_raster = arcpy.Raster(temp_resampled)
                print(f"  ✓ Dimensions: {verify_raster.width} x {verify_raster.height}")
                print(f"  ✓ Cell Size: {verify_raster.meanCellWidth:.6f}")
                print(f"  ✓ Saved: {os.path.basename(output_asc)}")
                
                results['processed_files'][folder_name].append(output_asc)
                
                # Clean up temporary data
                arcpy.management.Delete(temp_clipped)
                arcpy.management.Delete(temp_resampled)
                if raster_sr.name != ref_sr.name:
                    arcpy.management.Delete(temp_projected)
                    
            except Exception as e:
                print(f"  ✗ ERROR: {str(e)}")
                results['failed_files'][folder_name].append(raster_file)
                results['success'] = False
                continue

    
    # Step 4: Final verification
    print("\n" + "=" * 80)
    print("Step 4: Final Verification")
    print("=" * 80)
    
    all_asc_files = []
    for folder_name, files in results['processed_files'].items():
        all_asc_files.extend(files)
    
    if all_asc_files:
        print(f"\nVerifying {len(all_asc_files)} ASCII file(s)...")
        
        # Read header from first file as reference
        with open(all_asc_files[0], 'r') as f:
            ref_header = [f.readline().strip() for _ in range(6)]
        
        print(f"\nReference header from {os.path.basename(all_asc_files[0])}:")
        for line in ref_header:
            print(f"  {line}")
        
        # Check all files match
        mismatches = []
        for asc_file in all_asc_files[1:]:
            with open(asc_file, 'r') as f:
                header = [f.readline().strip() for _ in range(6)]
            if header != ref_header:
                mismatches.append(os.path.basename(asc_file))
        
        if mismatches:
            print("\n⚠ WARNING: Dimension mismatches detected in:")
            for f in mismatches:
                print(f"  - {f}")
            results['success'] = False
        else:
            print(f"\n✓ SUCCESS: All {len(all_asc_files)} file(s) have matching dimensions!")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    
    for folder_name in input_folders.keys():
        success_count = len(results['processed_files'][folder_name])
        failed_count = len(results['failed_files'][folder_name])
        total = success_count + failed_count
        
        results['summary'][folder_name] = {
            'total': total,
            'success': success_count,
            'failed': failed_count
        }
        
        print(f"\n{folder_name}:")
        print(f"  Total files: {total}")
        print(f"  Successfully processed: {success_count}")
        print(f"  Failed: {failed_count}")
        if results['output_folders'][folder_name]:
            print(f"  Output folder: {results['output_folders'][folder_name]}")
    
    # Clean up
    arcpy.management.Delete(temp_ref_clipped)
    arcpy.CheckInExtension("Spatial")
    
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE!")
    print("=" * 80)
    
    if results['success']:
        print("\n✓ All datasets are ready for MaxEnt modeling!")
    else:
        print("\n⚠ Processing completed with some errors. Please review the summary above.")
    
    return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    
    # Define your ROI shapefile
    roi_shapefile = r"C:\Users\Administrator\Downloads\maxent\roi.shp"
    
    # Define input folders (you can add as many as needed)
    input_folders = {
        'bioclimatic_variables': r"C:\Users\Administrator\Downloads\project_data\bioclimatic_variables",
        'soil': r"C:\Users\Administrator\Downloads\project_data\soil",
        # Add more folders here as needed:
        # 'elevation': r"C:\path\to\elevation",
        # 'vegetation': r"C:\path\to\vegetation",
        # 'landcover': r"C:\path\to\landcover",
    }
    
    # Define output base folder
    output_base_folder = r"C:\Users\Administrator\Downloads\project_data\maxent_ready"
    
    # Run the processing function
    # The first folder in input_folders will be used as reference by default
    # Or specify reference_folder='bioclimatic_variables' to explicitly set it
    results = prepare_maxent_data(
        roi_shapefile=roi_shapefile,
        input_folders=input_folders,
        output_base_folder=output_base_folder,
        reference_folder='bioclimatic_variables'  # Optional: specify reference folder
    )
    
    # Access results
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nOverall Success: {results['success']}")
    print(f"\nOutput Folders:")
    for name, path in results['output_folders'].items():
        print(f"  {name}: {path}")
    
    print(f"\nProcessing Statistics:")
    for name, stats in results['summary'].items():
        print(f"  {name}: {stats['success']}/{stats['total']} files processed successfully")
        
        
        
## sample usage pattern

prepare_maxent_data(
    roi_shapefile,           # Your ROI shapefile
    input_folders,           # Dictionary of folders to process
    output_base_folder,      # Where to save outputs
    reference_folder=None    # Optional: specify which folder to use as reference
)
## Sample demo



input_folders = {
    'bioclimatic_variables': r"C:\path\to\bioclim",
    'soil': r"C:\path\to\soil",
    'elevation': r"C:\path\to\elevation",
    'vegetation': r"C:\path\to\vegetation",
    # Add as many as you need!
}

