import os
import json
import zipfile
import gzip
import shutil
import tempfile
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("AMP_API_KEY")
API_SECRET = os.environ.get("AMP_SECRET_KEY")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
log_filename = f"logs/amplitude_load_unzip_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_filename
)
logger = logging.getLogger()

# API request parameters
url = 'https://analytics.eu.amplitude.com/api/2/export'
params = {'start': '20251104T00', 'end': '20251105T00'}
full_url = f"{url}?start={params['start']}&end={params['end']}"

# Make request
response = requests.get(full_url, auth=(API_KEY, API_SECRET))
data = response.content

# Save API response to a zip file
zip_file_path = "amp_events.zip"
with open(zip_file_path, "wb") as f:
    f.write(data)
logger.info(f"Downloaded zip file saved as {zip_file_path}")

# Create local data directory
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
logger.info("Environment setup: beginning unzip process")

# Temporary directory for extraction
temp_dir = tempfile.mkdtemp()

try:
    # Extract main zip
    with zipfile.ZipFile("amp_events.zip", "r") as zip_ref:
        zip_ref.extractall(temp_dir)
        logger.info(f"amp_events.zip extracted to temp directory: {temp_dir}")
    
    # Locate the day folder
    day_folder = next(f for f in os.listdir(temp_dir) if f.isdigit())
    day_path = os.path.join(temp_dir, day_folder)

    # Decompress all .gz files
    for root, _, files in os.walk(day_path):
        for file in files:
            if file.endswith('.gz'):
                gz_path = os.path.join(root, file)
                output_path = os.path.join(data_dir, file[:-3])  # Remove .gz
                try:
                    with gzip.open(gz_path, 'rb') as gz_file, open(output_path, 'wb') as out_file:
                        shutil.copyfileobj(gz_file, out_file)
                    logger.info(f"Successfully processed: {file} -> {file[:-3]}")
                except Exception as e:
                    logger.error(f"Failed to process {file}: {e}")

finally:
    # Cleanup temporary directory
    try:
        shutil.rmtree(temp_dir)
        logger.info("Temp directory deleted")
    except Exception as e:
        logger.error(f"Failed to delete temp directory: {e}")

print("All files extracted to the 'data' directory!")