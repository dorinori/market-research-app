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

app = FastAPI()

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

@app.post("/scrape")
async def scrape(request: StatesRequest):
    states = set(request.states)
    api_key = request.api_key
    print(f"Running scraper for states: {states}, api: {api_key}")
    
    all_results = []  # Store results for all states
    try:
        # Start the subprocess with stdout and stderr piped
        process = subprocess.Popen(
            ["python3", "scraper.py", str(states), api_key],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        geolocator = GoogleV3(api_key=api_key)
        try: 
            test_location = geolocator.geocode("New York")
            if not test_location:
                raise HTTPException(status_code=400, detail="Geocoding service unavailable")
        except GeocoderQueryError as e:
            raise HTTPException(status_code=400, detail="Invalid Google Maps API key")

        # # Print output in real-time
        # def print_output(line):
        #     print(line)
        #     sys.stdout.flush()  # Ensure immediate output

        # Read stdout and stderr in real-time
        # import asyncio
        # await asyncio.gather(
        #     read_stream(process.stdout, print_output),
        #     read_stream(process.stderr, print_output)
        # )

        # Wait for the process to complete
        return_code = process.wait()

        # Collect results
        # for state in states:
        #     print("Scraping:", state)
        #     if return_code == 0:
        #         filename = os.path.join("scraped_data", f"{state.replace(' ', '').lower()}_cities_population.json")
        #         with open(filename, "r") as file:
        #             cities_data = json.load(file)
        #         all_results.append({state: {"status": "success", "data": cities_data}})
        #     else:
        #         all_results.append({state: {"status": "error", "message": f"Process returned {return_code}"}})
        # print("Finished Scraping")
        # return {"status": "success", "data": all_results}
        return

    except HTTPException as he:
        # Re-raise HTTPExceptions (like our invalid key error)
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/download/{filename}")
async def download_file(filename: str):
    # Construct the file path
    file_path = os.path.join("scraped_data", filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return the file for download
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )