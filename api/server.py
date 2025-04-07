from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
from pydantic import BaseModel
import sys
import traceback
from geopy.exc import GeocoderQueryError
import os
from geopy.geocoders import GoogleV3
from pathlib import Path
import boto3
from dotenv import load_dotenv  # For local development

if os.getenv("VERCEL") != "1": 
    load_dotenv()

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-2')
)

app = FastAPI()

# BASE_DIR = Path(__file__).parent

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatesRequest(BaseModel):
    states: list  # expects a list of strings (states)
    api_key: str

async def read_stream(stream, callback):
    while True:
        line = stream.readline()
        if not line:
            break
        callback(line.strip())

@app.post("/api/scrape")
async def scrape(request: StatesRequest):
    states = set(request.states)
    api_key = request.api_key
    print(f"Running scraper for states: {states}, api: {api_key}")
    
    all_results = []
    try:
        # Test the API key first
        geolocator = GoogleV3(api_key=api_key)
        try: 
            test_location = geolocator.geocode("New York")
            if not test_location:
                raise HTTPException(status_code=400, detail="Geocoding service unavailable")
        except GeocoderQueryError as e:
            raise HTTPException(status_code=400, detail="Invalid Google Maps API key")
        
        # Start the subprocess
        process = subprocess.Popen(
            ["python3", "scraper.py", json.dumps(list(states)), api_key],  # Properly serialize states list
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Read output in real-time
        def handle_output(line):
            # if line.startswith("Scraping"):
                print(f"Scraper Console Output: {line}")
            
        # Read both stdout and stderr
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                handle_output(output.strip())
        
        # Check return code
        # return_code = process.poll()
        # print("Subprocess completed with return code:", return_code)
        
        return JSONResponse({
            "status": "success",
            "states_processed": list(states),
            "api_key_valid": True
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    try:
        bucket_name = os.getenv('S3_BUCKET_NAME')
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': f'{filename}'},
            ExpiresIn=3600  # 1-hour valid URL
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
