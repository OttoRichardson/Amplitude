Amplitude is a product analytics platform that tracks user interactions and behavior across digital products and websites. It allows companies to understand how users engage with their features, identify trends, and make data-driven product decisions. The aim of this project is to capture usage data from the company’s Data School website. the goal is to provide the product and analytics teams with timely, accurate insights into user behavior, helping to optimize the learning experience, measure engagement, and inform strategic decisions.

The pipeline achieves this by extracting event data from Amplitude via its REST API, storing it locally for backup, uploading it to an AWS S3 bucket, and ingesting it into Snowflake using Snowpipe for real-time analytics. The entire process is orchestrated with Kestra to ensure automation, monitoring, and scalability.


# SETTING UP

Step 1: Clone the GitHub Repository Locally
1. Open VS Code.
2. Open a terminal in VS Code.
3. Clone your repo:

git clone https://github.com/your-username/your-repo.git
cd your-repo

Step 2: Create and Switch to a New Git Branch
mkdir data
mkdir env

data/ → to store local backups of Amplitude exports.
env/ → to store your virtual environment if you want it inside the repo (optional; can also use global environments).

Step 4: Update .gitignore
Make sure sensitive or large files are not committed. Add to your .gitignore:

```
Local data and environment
data/
env/
*.env
```

Step 5: Create and Activate a Python Virtual Environment
```
python -m venv env
.\env\Scripts\activate

```
# EXTRACT

## Summary

During the extract stage, the pipeline retrieves event data, saves it as compressed .gz files inside a ZIP, decompresses them, and organizes the resulting JSON files in a structured data/ directory. Key considerations include securely managing API credentials, respecting rate limits, defining the scope of events and time ranges, and ensuring robust logging for transparency and troubleshooting.

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

# LOAD

## Step 9: Load Data to AWS S3

After extracting and processing event data from Amplitude, the next step is to **upload the JSON files to an S3 bucket** for storage, backup, or further processing. This step ensures that the data is accessible to other systems and keeps local storage clean.

import os
from dotenv import load_dotenv
import boto3

# Load environment variables for AWS credentials and bucket name
load_dotenv()

aws_access_key = os.getenv('AWS_ACCESS_KEY')
AWS_ACCESS_SECRET_KEY = os.getenv('AWS_ACCESS_SECRET_KEY')
bucket = os.getenv('AWS_BUCKET_NAME')

# Create S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=AWS_ACCESS_SECRET_KEY
)

# Collect all filenames in the output folder
files_to_upload = []
for root, _, filenames in os.walk(output_folder):
    files_to_upload.extend(filenames)


for file in files_to_upload:
    aws_file_destination = "python-import/" + file
    output_path = os.path.join(output_folder, file)
    s3_client.upload_file(output_path, bucket, aws_file_destination)
    print(f"Uploaded: {file}")




## Integrating Amplitude → S3 → Snowflake

Using IAM User Access Keys
Create an IAM user with a policy granting access to your S3 bucket




# Transformation

## **Medallion Layers**

### **Bronze — Raw**
- JSON event files exported from Amplitude  
- Stored in an S3 bucket  
- Queried in Snowflake via **Storage Integration** and **Snowpipe**

#### **Stream**
- Tracks changes in raw JSON data  
- Fires when new files arrive in raw table

- 

### **Silver — Base & Normalised Tables**
- Flattened & structured data from raw JSON

  
- Stored Procedure #1 processes the Bronze layer  
- Normalised tables created:
  - `events`
  - `sessions`
  - `users`
 <img width="2804" height="808" alt="image" src="https://github.com/user-attachments/assets/bbdce17f-8d7b-47a4-9366-45dd1eee835f" />

- Future normalized tables planned:
  - `locations`
  - `devices`
  <img width="2804" height="1888" alt="image" src="https://github.com/user-attachments/assets/17435448-67d9-4a94-a04f-2ccaef738b12" />


### **Gold — Analytical Models**
- Aggregated & behavioural insights  
- Designed to answer product and UX questions  
- Future analytic tables
  - `Are people getting confused on the web page?`
  - `Who is accessing our page and what company do they work for?`



