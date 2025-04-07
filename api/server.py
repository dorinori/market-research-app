from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse 
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


app = FastAPI()

BASE_DIR = Path(__file__).parent

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

# @app.post("/scrape")
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
        
        # Collect results from output files
        # for state in states:
        #     filename = os.path.join("scraped_data", f"{state.replace(' ', '').lower()}_cities_population.json")
        #     if os.path.exists(filename):
        #         with open(filename, "r") as file:
        #             cities_data = json.load(file)
        #         all_results.append({state: {"status": "success", "data": cities_data}})
        #     else:
        #         all_results.append({state: {"status": "error", "message": f"Output file not found for {state}"}})
        
        return {"status": "success"}

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
# @app.get("/download/{filename}")
@app.get("/api/download/{filename}") 
async def download_file(filename: str):
    # Construct the file path
    # file_path = os.path.join(
    #     os.path.dirname(__file__),  # Current directory (app/)
    #     "data",                    # Into data/
    #     "scraped_data",            # Into scraped_data/
    #     filename                   # The requested file
    # )
    
    file_path = BASE_DIR / "data" / "scraped_data" / filename

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return the file for download
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

