
# Unzip and decompress files to retrieve .json files
# - Initial Unzip of 'data.zip' is to a local 'data' folder
# - JSON files are extracted to this same folder

import os
import zipfile
import gzip
import shutil
import tempfile


def extract_json_files(zip_file_path, output_dir="data"):
    """
    Extract and decompress JSON files from a zip archive containing gzipped files.
    
    Args:
        zip_file_path (str): Path to the zip file to extract
        output_dir (str): Directory to extract JSON files to (default: "data")
    
    Returns:
        int: Number of JSON files extracted
    
    Raises:
        FileNotFoundError: If zip file doesn't exist
        ValueError: If no numeric day folder is found
    """
    if not os.path.exists(zip_file_path):
        raise FileNotFoundError(f"Zip file not found: {zip_file_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    extracted_count = 0
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract main zip file
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the numeric day folder
        try:
            day_folder = next(f for f in os.listdir(temp_dir) if f.isdigit())
        except StopIteration:
            raise ValueError("No numeric day folder found in the zip file")
        
        day_path = os.path.join(temp_dir, day_folder)
        
        # Walk through and decompress all .gz files
        for root, _, files in os.walk(day_path):
            for file in files:
                if file.endswith('.gz'):
                    gz_path = os.path.join(root, file)
                    json_filename = file[:-3]  # Remove .gz extension
                    output_path = os.path.join(output_dir, json_filename)
                    
                    with gzip.open(gz_path, 'rb') as gz_file, open(output_path, 'wb') as out_file:
                        shutil.copyfileobj(gz_file, out_file)
                    
                    extracted_count += 1
    
    print(f"Extracted {extracted_count} JSON files to '{output_dir}' directory!")
    return extracted_count


# Example usage:
if __name__ == "__main__":
    extract_json_files("data.zip")