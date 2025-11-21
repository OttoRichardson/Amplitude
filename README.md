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
- Tracks changes in raw JSON data Stores this in a table
- Row are deleted once table is used in a DML query

![Alt text](https://github.com/OttoRichardson/Amplitude/blob/main/images/raw.png)
 

### **Silver — Base & Normalised Tables**
- Flattened & structured data from raw JSON

![Alt text](https://github.com/OttoRichardson/Amplitude/blob/main/images/base.png)

- Stored Procedure #1 processes the Bronze layer

```
CREATE OR REPLACE PROCEDURE AMPLITUDE_BASE_UPDATE()
RETURNS varchar
LANGUAGE SQL
AS
$$
BEGIN
CREATE OR REPLACE TEMP TABLE AMPLITUDE_EVENTS_NEW AS
(SELECT * FROM AMPLITUDE_EVENTS_STREAM);

INSERT INTO  AMPLITUDE_EVENTS_BASE1
SELECT
json_data:"$insert_id"::VARCHAR AS "$insert_id",
json_data:"$insert_key"::VARCHAR AS    "$insert_key",
json_data:"$schema"::VARCHAR AS    "$schema",
json_data:"adid"::VARCHAR AS   "adid",
json_data:"amplitude_attribution_ids"::VARCHAR AS  "amplitude_attribution_ids",
json_data:"amplitude_event_type"::VARCHAR AS   "amplitude_event_type",
json_data:"amplitude_id"::INTEGER AS   "amplitude_id",
json_data:"app"::INTEGER AS    "app",
json_data:"city"::VARCHAR AS   "city",
json_data:"client_event_time"::VARCHAR AS  "client_event_time",
json_data:"client_upload_time"::VARCHAR AS "client_upload_time",
json_data:"country"::VARCHAR AS    "country",
json_data:"data"::VARCHAR AS   "data",
json_data:"data_type"::VARCHAR AS  "data_type",
json_data:"device_brand"::VARCHAR AS   "device_brand",
json_data:"device_carrier"::VARCHAR AS "device_carrier",
json_data:"device_family"::VARCHAR AS  "device_family",
json_data:"device_id"::VARCHAR AS  "device_id",
json_data:"device_manufacturer"::VARCHAR AS    "device_manufacturer",
json_data:"device_model"::VARCHAR AS   "device_model",
json_data:"device_type"::VARCHAR AS    "device_type",
json_data:"dma"::VARCHAR AS    "dma",
json_data:"event_id"::INTEGER AS   "event_id",
json_data:"event_properties"::VARCHAR AS   "event_properties",
json_data:"event_time"::VARCHAR AS "event_time",
json_data:"event_type"::VARCHAR AS "event_type",
json_data:"global_user_properties"::VARCHAR AS "global_user_properties",
json_data:"group_properties"::VARCHAR AS   "group_properties",
json_data:"groups"::VARCHAR AS "groups",
json_data:"idfa"::VARCHAR AS   "idfa",
json_data:"ip_address"::VARCHAR AS "ip_address",
json_data:"is_attribution_event"::VARCHAR AS   "is_attribution_event",
json_data:"language"::VARCHAR AS   "language",
json_data:"library"::VARCHAR AS    "library",
json_data:"location_lat"::VARCHAR AS   "location_lat",
json_data:"location_lng"::VARCHAR AS   "location_lng",
json_data:"os_name"::VARCHAR AS    "os_name",
json_data:"os_version"::VARCHAR AS "os_version",
json_data:"partner_id"::VARCHAR AS "partner_id",
json_data:"paying"::VARCHAR AS "paying",
json_data:"plan"::VARCHAR AS   "plan",
json_data:"platform"::VARCHAR AS   "platform",
json_data:"processed_time"::VARCHAR AS "processed_time",
json_data:"region"::VARCHAR AS "region",
json_data:"sample_rate"::VARCHAR AS    "sample_rate",
json_data:"server_received_time"::VARCHAR AS   "server_received_time",
json_data:"server_upload_time"::VARCHAR AS "server_upload_time",
json_data:"session_id"::INTEGER AS "session_id",
json_data:"source_id"::VARCHAR AS  "source_id",
json_data:"start_version"::VARCHAR AS  "start_version",
json_data:"user_creation_time"::VARCHAR AS "user_creation_time",
json_data:"user_id"::VARCHAR AS    "user_id",
json_data:"user_properties"::VARCHAR AS    "user_properties",
json_data:"uuid"::VARCHAR AS   "uuid",
json_data:"version_name"::VARCHAR AS   "version_name"
FROM AMPLITUDE_EVENTS_NEW ;


INSERT INTO  AMPLITUDE_EVENTS_BASE2
WITH CTE AS 
(
SELECT

json_data:session_id AS session_id,
json_data:event_id AS event_id,
f.key as column_name,
value
FROM  AMPLITUDE_EVENTS_NEW as t,
LATERAL FLATTEN(input => t.json_data:"event_properties") as f
)
SELECT 
*
FROM  CTE
PIVOT (MAX(value) FOR COLUMN_NAME IN (ANY ORDER BY COLUMN_NAME ))

;


RETURN 'BASE TABLES UPDATED';

END
$$
;
```

TEMP TABLE used here as once it is used it removes the rows in the stream however now they are in the Temp Table can be used in both Base1 and Base2 Steps to update this table before the Temp Table is deleted ar the end of the procedure.

- Task - triggered from stream

```
CREATE OR REPLACE TASK AMPLITUDE_BASE_UPDATE_TASK
warehouse = DATASCHOOL_WH
when system$stream_has_data('AMPLITUDE_EVENTS_STREAM')
as 
call AMPLITUDE_BASE_UPDATE();
```



### Considerations for building Normalised tables, how does the archetecture work?


![Alt text](https://github.com/OttoRichardson/Amplitude/blob/main/images/diagram.png)

- Normalised tables created:
  - `events`
```
CREATE OR REPLACE TABLE AMPLITUDE_EVENTS AS (
SELECT 
"event_type",
"event_id",
"event_time",
"session_id",
"'[Amplitude] Page Counter'" AS Page_Counter, 
REPLACE("'[Amplitude] Page Title'",'"','') AS Page_Title,
REPLACE("'[Amplitude] Page URL'",'"','') AS URL
FROM AMPLITUDE_EVENTS_BASE1 B1
JOIN AMPLITUDE_EVENTS_BASE2 B2
ON B1."session_id" = B2.SESSION_ID AND  B1."event_id" = B2.event_id

ORDER BY 
"session_id" ASC, "event_id" ASC
)
```
  - `sessions` 
  - `users`
 <img width="2804" height="808" alt="image" src="https://github.com/user-attachments/assets/bbdce17f-8d7b-47a4-9366-45dd1eee835f" />

- Future normalized tables planned:
  - `locations`
  - `devices`
  <img width="2804" height="1888" alt="image" src="https://github.com/user-attachments/assets/17435448-67d9-4a94-a04f-2ccaef738b12" />

### Sensitive Data Handling
- IP addresses & geolocations stored separately  
- Follows data protection best practices

- Stored Procedure
```
CREATE OR REPLACE PROCEDURE AMPLITUDE_NORMALISED_UPDATE()
RETURNS varchar
LANGUAGE SQL
AS

$$
BEGIN

INSERT INTO AMPLITUDE_EVENTS
SELECT 
"event_type",
"event_id",
"event_time",
"session_id",
"'[Amplitude] Page Counter'" AS Page_Counter, 
REPLACE("'[Amplitude] Page Title'",'"','') AS Page_Title,
REPLACE("'[Amplitude] Page URL'",'"','') AS URL
FROM AMPLITUDE_EVENTS_BASE1 B1
JOIN AMPLITUDE_EVENTS_BASE2 B2
ON B1."session_id" = B2.SESSION_ID AND  B1."event_id" = B2.event_id
;


MERGE INTO AMPLITUDE_USERS AS D USING
(
SELECT 
MAX("user_id") AS email,
"amplitude_id" AS USER_ID
FROM 
AMPLITUDE_EVENTS_BASE1
GROUP BY  "amplitude_id"
)
 AS C 

on D.USER_ID = C.USER_ID

WHEN MATCHED AND C.email IS NOT NULL THEN 
    UPDATE SET D.email = C.email
WHEN NOT MATCHED THEN
    INSERT (email, USER_ID)
    values
    (C.email, C.USER_ID)
;

INSERT INTO AMPLITUDE_SESSION
SELECT 
"amplitude_id"as user_id,
"session_id",
"device_id"
FROM
AMPLITUDE_EVENTS_BASE1
;

RETURN 'NORMALISED TABLES UPDATED';

END
$$
;
```

Events and Session table updates are both insert statments as they will always contain new data

Note: there should be a where cause using a parameter to check that the event data on the data is greater than the previous last event date. so that we cant insert duplicate data. 

User table is a merge, as we might want to update a user if we have found their email 
```
WHEN MATCHED AND C.email IS NOT NULL THEN 
    UPDATE SET D.email = C.email
```

- Chained Task

```
CREATE OR REPLACE TASK AMPLITUDE_NORMALISED_UPDATE_TASK
warehouse = DATASCHOOL_WH
AFTER AMPLITUDE_BASE_UPDATE_TASK
as 
call AMPLITUDE_NORMALISED_UPDATE();
```

## ⚙️ Automation (Streams & Tasks)

### **Stream**
- Tracks changes in raw JSON data  
- Fires when new files arrive in raw table

### **Task 1 → Update Base Table**
- Runs SP #1  
- Transforms Bronze → Silver

### **Task 2 → Update Normalised Tables**
- Chained Task Runs SP #2  
- Transforms Silver → More Silver



### **Gold — Analytical Models**
- Aggregated & behavioural insights  
- Designed to answer product and UX questions  
- Future analytic tables
  - ` User Journey Analysis & Detecting Website Issues**`
    - Is a user making repeated clicks?  
    - Are users returning to the **same page** frequently?  
    - Are users stuck in loops (A → B → A patterns)?

investigate events table, use window functions to look at paths

  - `Identifying Company Traffic (IP + Email Matching)`

Logic for Company Identification
1. Extract email domain  
2. Remove common domains (`gmail`, `yahoo`, etc.)  
3. Map unique domain → **suspected company**  
4. If multiple users share same IP → infer office network  
5. Produce table:
   - `user_id`  
   - `suspected_company`  
   - reasoning (domain/IP match)


# Refactoring Amplitude SQL into DBT

## Overview
This project focuses on refactoring existing SQL for Amplitude events into a DBT workflow. The goal is to implement best practices in DBT

## DAG plan

![Alt text](https://github.com/OttoRichardson/Amplitude/blob/main/images/DAG.png)

- **DBT Workflow Changes**: Refactoring may change the way we work, especially with staging and intermediate layers.
   
- **Staging Layer**: The  `base_1` is staging and `base_2` table becomes an intermediate table, as staging should have no transformations.

- **Avoid Direct Joins**: We avoid joining `base_1` to `base_2` directly. Instead, include `base_1` as CET and join back to create a `base_2` with full data.


## sources yaml

```
yaml
version: 2

sources:
  - name: RAW_AMPLITUDE
    database: TIL_DATA_ENGINEERING
    schema: OTTORICHARDSON_STAGING
    tables:
      - name: AMPLITUDE_EVENTS_RAW_PYTHON
        columns:
          - name: JSON_DATA
            data_type: variant
            description: "Raw JSON payload from Amplitude"
            data_tests:
              - not_null
      - name: AMPLITUDE_EVENTS_RAW_PYTHON_FRESHNESS
        loaded_at_field: server_upload_time_ts
        freshness:
          warn_after: {count: 24, period: hour}
```

Freshness cannot be tested on the main raw table, so a separate view (AMPLITUDE_EVENTS_RAW_PYTHON_FRESHNESS) is created for monitoring data recency.

This checks for delays up to one day and issues warnings if data is stale.


## staging



### Project Configuration
In project YAML we define staging materializations and tags
```
    amplitude:
      +materialized: view
      schema: staging
      tags: ["daily"]
```
The daily tag allows this model to be referenced in daily refreshes.


## model yaml

define some tests and take descriptions form docblocks

```
      - name: event_id
        data_type: number
        description: "{{ doc('event_id') }}"
        data_tests:
          - not_null:
              severity: warn
          - unique:
              severity: warn

      - name: event_type
        data_type: varchar
        description: "{{ doc('event_type') }}"
        data_tests:
          - accepted_values:
              severity: warn
              arguments:
                values: [
                  'video_loaded',
                  '[Amplitude] Form Started',
                  'video_started',
                  'session_start',
                  '[Amplitude] Element Changed',
                  'video_finished',
                  '[Amplitude] Page Viewed',
                  '[Amplitude] Element Clicked',
                  'Activate Modal Search',
                  'video_paused',
                  '[Amplitude] Form Submitted',
                  'Data Skills Video',
                  '[Amplitude] File Downloaded'
                ]
```

to refeance the description dynamicly using jinja print statment need to create descriptions in a doc blocks md file, see format

```
{% docs event_time %}
The timestamp when the event occurred, as recorded in Amplitude.
{% enddocs %}

{% docs event_type %}
The type of event performed

          | Event Type |
          |------------|
          | video_loaded |
          | [Amplitude] Form Started |
          | video_started |
          | session_start |
          | [Amplitude] Element Changed |
          | video_finished |
          | [Amplitude] Page Viewed |
          | [Amplitude] Element Clicked |
          | Activate Modal Search |
          | video_paused |
          | [Amplitude] Form Submitted |
          | Data Skills Video |
          | [Amplitude] File Downloaded |
{% enddocs %}

```

## Using dbt-codegen for Best Practices

we are leveraging the [`dbt-codegen`](https://github.com/dbt-labs/dbt-codegen) package in our project.

### Setup

- **Installed as a package** in `packages.yml
      - package: dbt-labs/codegen
        version: 0.14.0

We use the generate_model_import_ctes macro from dbt-codegen to standardize how our soucres are brought in as CTEs into our models.

We use the generate_model_yaml macro to Automatically lists all columns in the table for documentation in _models.yml file


##
base layer model 
follows the same sql as in snowflake however in DBT, we are using **Jinja templating** to reference tables

```
select *
from {{ source('RAW_AMPLITUDE', 'AMPLITUDE_EVENTS_RAW_PYTHON') }}
```
When moving to a different environment (e.g., dev → prod) Only the sources.yml file needs to be updated with the appropriate database/schema. All models referencing the source via {{ source(...) }} will automatically point to the correct tables.

## Intermediade layer

this follows the same structure as in Snowflake but using CTEs for imputs as dbt best practice and with **Jinja templating** to reference tables

## Mart

created two tables off from event data 

1. to capture more granular information on users’ paths through the website

**Use window functions** to propagate metrics like `Page_Counter` across rows for each session:

```
LAST_VALUE(Page_Counter IGNORE NULLS)
OVER (
    PARTITION BY session_id 
    ORDER BY event_time, event_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS Page_Counter

```


2. detect web issues

Here i focused on Detecting Repeated Clicks. To do this without over-aggregating wanted to create a repeat_click_flag by identifing events where event_id remained the same but event_time changed

```
WITH event_changes AS (
    SELECT
        session_id,
        event_id,
        event_time,
        LAG(event_time) OVER (PARTITION BY session_id ORDER BY event_time, event_id) AS prev_event_time,
        LAG(event_id) OVER (PARTITION BY session_id ORDER BY event_time, event_id) AS prev_event_id
    FROM {{ ref('int_amplitude__events') }}
),
time_changed AS (
    SELECT
        session_id,
        event_id, 
        event_time
    FROM event_changes
    WHERE event_time != prev_event_time
      AND prev_event_id = event_id
),
joined AS (
    SELECT
        e.*,
        CASE 
            WHEN t.event_id IS NOT NULL THEN 'Y'
            ELSE 'N'
        END AS repeat_click_flag
    FROM {{ ref('int_amplitude__events') }} e
    LEFT JOIN time_changed t
        ON e.session_id = t.session_id
       AND e.event_id = t.event_id
)
SELECT *
FROM joined
ORDER BY event_id
```

### Observations:

Only about 6 instances where event_id didn’t change but event_time did.

Next steps:

If these are actual repeated clicks, continue analysis.

If they are data errors, create a generic DBT test to flag duplicates.

```
{% test duplicate_events(model) %}
WITH event_changes AS (
    SELECT
        session_id,
        event_id,
        event_time,
        LAG(event_time) OVER (PARTITION BY session_id ORDER BY event_time, event_id) AS prev_event_time,
        LAG(event_id) OVER (PARTITION BY session_id ORDER BY event_time, event_id) AS prev_event_id
    FROM {{ model }}
),
time_changed AS (
    SELECT
        session_id,
        event_id
    FROM event_changes
    WHERE event_time != prev_event_time
      AND prev_event_id = event_id
)
SELECT
    session_id
FROM time_changed
GROUP BY session_id
HAVING COUNT(event_id) > 1

{% endtest %}
```

## Orchestration

To manage and orchestrate our Amplitude-related tables in the marts layer, we added a **tag configuration** in the project YAML:

```
    marts:
      amplitude:
        +materialized: table
        query_tag: dbt_marts
        tags: amplitude
```

we can build all Amplitude tables and their upstream dependencies with:
```
dbt build --select +tag:amplitude
```
the + selects all upstream dependencies of the tagged models.

The build command not only creates the models but also runs all associated tests.

Orchestration

This command can be scheduled to run daily, ensuring that all Amplitude mart tables are refreshed automatically.
