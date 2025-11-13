# Amplitude

This project uses Amplitude's API to download yesterdats events data as a zip file it opens and extracts all of the hourly files within and saves it to a data within the repo

see my excalidraw: https://excalidraw.com/#json=BUWpy15QGMY4tFz5NVAT8,-cze4Q3CEzeVVxx2xSEe6Q


![image](https://github.com/OttoRichardson/Amplitude/blob/main/images/amplitude.png)

# Amplitude Event Extraction & Unzip Pipeline

## Project Summary

This project automates the download and extraction of event data from **Amplitude** via its Export API. The pipeline saves the data as compressed `.gz` files inside a ZIP, decompresses them, and stores the resulting JSON files in a structured `data/` directory. All actions are logged for transparency and troubleshooting.

---

Pipeline Overview

The pipeline consists of:

1. **API Request** – Fetch daily event data from Amplitude.  
2. **Save ZIP** – Store the raw response locally.  
3. **Temporary Extraction** – Unzip to a temporary folder to handle intermediate files.  
4. **Decompress `.gz` Files** – Convert all compressed JSON files into readable `.json`.  
5. **Store in `data/`** – Save all extracted files in a dedicated directory for further analysis.  
8. **Logging** – Track all stages and errors in `logs/`.

---
Technical Details (Python Implementation)

## Step 1: Load Environment Variables

We use `.env` to securely store API credentials. The pipeline loads them at runtime.

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("AMP_API_KEY")
API_SECRET = os.environ.get("AMP_SECRET_KEY")
```

## Step 2: Configure Logging

Logging tracks each step and errors in a dedicated file.

```python
import logging
from datetime import datetime

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Setup logging
log_filename = f"logs/amplitude_load_unzip_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_filename
)
logger = logging.getLogger()
```
## Step 3: Fetch Data from Amplitude API
We request daily events using the Export API and save the response as a ZIP.

```python
import requests
url = 'https://analytics.eu.amplitude.com/api/2/export'
params = {'start': '20251104T00', 'end': '20251105T00'}
full_url = f"{url}?start={params['start']}&end={params['end']}"
response = requests.get(full_url, auth=(API_KEY, API_SECRET))
zip_file_path = "amp_events.zip"
with open(zip_file_path, "wb") as f:
    f.write(response.content)
logger.info(f"Downloaded zip file saved as {zip_file_path}")
```

## Step 4: Prepare Data Directory
Create a directory to store extracted JSON files.
```
import os

data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
logger.info("Environment setup: beginning unzip process")

```

## Step 5: Extract ZIP to Temporary Folder
We use a temporary folder to safely extract ZIP files.
```
import zipfile
import tempfile

temp_dir = tempfile.mkdtemp()

with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
    zip_ref.extractall(temp_dir)
    logger.info(f"{zip_file_path} extracted to temp directory: {temp_dir}")
```

## Step 6: Locate Day Folder
Amplitude organizes extracted data by day.

```
import os

day_folder = next(f for f in os.listdir(temp_dir) if f.isdigit())
day_path = os.path.join(temp_dir, day_folder)

```

## Step 7: Decompress .gz Files
Iterate through .gz files and save as readable JSON.
```
import gzip
import shutil

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
```

## Step 8: Cleanup Temporary Folder

Remove temporary extraction folder to save space.
```
import shutil

try:
    shutil.rmtree(temp_dir)
    logger.info("Temp directory deleted")
except Exception as e:
    logger.error(f"Failed to delete temp directory: {e}")

```

