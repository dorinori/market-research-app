from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
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

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working"}

@app.post("/api/scrape")
async def scrape_data(request: StatesRequest):
    """
    Modified scrape endpoint that works with AWS Lambda
    """
    states = request.states
    api_key = request.api_key
    logger.info(f"Starting scrape for states: {states}")
    
    try:
        # Validate Google Maps API key
        geolocator = GoogleV3(api_key=api_key)
        try:
            test_location = geolocator.geocode("New York")
            if not test_location:
                raise HTTPException(status_code=400, detail="Geocoding service unavailable")
        except GeocoderQueryError as e:
            raise HTTPException(status_code=400, detail="Invalid Google Maps API key")
        
        # Replace subprocess call with direct function import
        try:
            # Import your scraper logic directly
            from scraper import run_scraper  # Make sure scraper.py is in your deployment package
            print(states)
            # Run the scraper directly instead of via subprocess
            results = run_scraper(states, api_key)
            
            return JSONResponse({
                "status": "success",
                "states_processed": states,
                "api_key_valid": True,
                "data": results  # Include any results from the scraper
            })
            
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Scraper module not available. Ensure scraper.py is included in deployment."
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

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