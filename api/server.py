from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel
import traceback
from geopy.exc import GeocoderQueryError
import os
from geopy.geocoders import GoogleV3
import boto3
from dotenv import load_dotenv
from mangum import Mangum
import logging
from io import StringIO
import sys
import asyncio

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Load environment variables if not in Vercel
if os.getenv("VERCEL") != "1": 
    load_dotenv()

# Initialize S3 client
def get_s3_client():
    return boto3.client('s3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-2')
    )


app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatesRequest(BaseModel):
    states: list
    api_key: str
    min_population: int

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working"}

class StreamToLogger:
    def __init__(self, queue):
        self.queue = queue
        
    def write(self, message):
        if message.strip():
            # Put the message in the queue synchronously
            # We'll handle the async part when we read from the queue
            self.queue.put_nowait(message)
    
    def flush(self):
        pass
@app.post("/api/scrape")
async def scrape_data(request: StatesRequest):
    states = request.states
    api_key = request.api_key
    min_population = request.min_population
    
    async def generate_logs():
        try:
            # Initial connection message
            yield "data: " + json.dumps({"type": "log", "message": "Connection established with backend"}) + "\n\n"
            
            # Validate API key
            geolocator = GoogleV3(api_key=api_key)
            try:
                test_location = geolocator.geocode("New York")
                if not test_location:
                    yield "data: " + json.dumps({"type": "error", "message": "Geocoding service unavailable"}) + "\n\n"
                    return
            except GeocoderQueryError:
                yield "data: " + json.dumps({"type": "error", "message": "Invalid Google Maps API key"}) + "\n\n"
                return

            # Create a queue for logs
            log_queue = asyncio.Queue()
            
            # Redirect stdout to our queue
            def handle_log(message):
                if message.strip():
                    asyncio.run_coroutine_threadsafe(log_queue.put(message.strip()), asyncio.get_event_loop())
                
            sys.stdout = StreamToLogger(log_queue)
            
            # Run scraper in a thread executor
            loop = asyncio.get_event_loop()
            
            async def run_scraper_wrapper():
                try: 
                    from .scraper import run_scraper
                    await loop.run_in_executor(None, lambda: run_scraper(states, api_key, min_population))
                    await log_queue.put("SCRAPER_COMPLETE")
                except Exception as e:
                    await log_queue.put(f"SCRAPER_ERROR:{str(e)}")
                    raise
            
            scraper_task = asyncio.create_task(run_scraper_wrapper())
            
            # Stream logs as they come in
            while True:
                try:
                    message = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                    
                    if message == "SCRAPER_COMPLETE":
                        yield "data: " + json.dumps({"type": "complete"}) + "\n\n"
                        break
                    elif message.startswith("SCRAPER_ERROR:"):
                        yield "data: " + json.dumps({"type": "error", "message": message[14:]}) + "\n\n"
                        break
                    else:
                        yield "data: " + json.dumps({"type": "log", "message": message}) + "\n\n"
                except asyncio.TimeoutError:
                    if scraper_task.done():
                        break
                    continue
                    
        except Exception as e:
            yield "data: " + json.dumps({"type": "error", "message": str(e)}) + "\n\n"
        finally:
            sys.stdout = sys.__stdout__

    return StreamingResponse(generate_logs(), media_type="text/event-stream")

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    try:
        bucket_name = os.getenv('S3_BUCKET_NAME')
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable not set")
            
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': filename},
            ExpiresIn=3600
        )
        return {"url": url}
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(500, detail=str(e))


handler = Mangum(app)

# Optional: Keep this if you need direct Lambda invocation
def vercel_handler(request):
    # Convert Vercel request to Lambda event
    body = request.body if hasattr(request, 'body') else None
    event = {
        'httpMethod': request.method,
        'path': request.path,
        'headers': dict(request.headers),
        'queryStringParameters': dict(request.query_params),
        'body': body,
    }
    
    # Call the Mangum handler
    response = handler(event, None)
    
    # Convert Lambda response to FastAPI response
    return JSONResponse(
        content=json.loads(response['body']),
        status_code=response['statusCode'],
        headers=response['headers']
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    __all__ = ["app", "vercel_handler"]