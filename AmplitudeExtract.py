import requests
import os

from dotenv import load_dotenv

import json
import zipfile     
import gzip  

import tempfile    

import logging

logging.basicConfig(
    filename = "log",
    filemode = "a", # Append new logs to file by default, can be "w" to overwrite the file
    format = "{levelname}:{name}:{message}", # format for content output in log file
    style='{', #had to change format 
    level=logging.WARNING, # minimum serverity for log to be recorded in a log file
)


load_dotenv()

API_KEY = os.environ.get("AMP_API_KEY")
API_SECRET = os.environ.get("AMP_SECRET_KEY")

#'https://amplitude.com/api/2/export?start=20220101T00&end=20220101T23'
url = 'https://analytics.eu.amplitude.com/api/2/export'



params = {
    'start': '20251104T00',
    'end': '20251105T00'
}

full_url = f"{url}?start={params['start']}&end={params['end']}"


response = requests.get(full_url, auth=(API_KEY, API_SECRET))


data = response.content

with open('data.zip','wb') as file:
    file.write(data)
# open up the zip file and save it as data in the repo


# Create a temporary directory for extraction place where we can unzip all the files within 
temp_dir = tempfile.mkdtemp()

# Create local output directory
temp_dir = "temp_data"
os.makedirs(temp_dir, exist_ok=True)

#print(full_url)
#print(response.status_code)

#check that we actualy did creat a temp directory 
#print("Temporary directory created:", temp_dir)
#print("Does it exist?", os.path.exists(temp_dir))


with zipfile.ZipFile("data.zip", "r") as zip_ref:
    zip_ref.extractall(temp_dir)
#extract the first zip

#print(os.listdir(temp_dir))
#see if we can see the extracted zip in the temp folder

contents = os.listdir(temp_dir)
#print(contents)  # ['100011471']
#see the flder within the initial zip

contents = os.listdir(temp_dir)          # ['100011471']
folder_path = os.path.join(temp_dir, contents[0])
#print(folder_path)                       # temp_data/100011471
#add that folder name to our main folderpath name 

# List files inside that folder
files_inside = os.listdir(folder_path)
#print(files_inside)  # this already gives us a list of the folders                   

#create write out data path
output_path =  r"C:\Users\Otto Richardson\Documents\GitHub\Amplitude\data"



# for loop to extract each of the gzip files 
for zipfiles in files_inside: #for the list of zip files
    filename = os.path.splitext(zipfiles)[0]
    #print(filename)
    if zipfiles.endswith('.gz'):
        zipfilespath = os.path.join(output_path, filename) #get the full path
        with gzip.open(zipfilespath, 'rb') as gz_file, open(zipfilespath, 'wb') as out_file:  #extract all the zip files

