
import os
import json
import base64
import time
import requests
import sys

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
# Adjust path to image if needed, or use a dummy small base64
TEST_IMAGE_PATH = "scripts/test_receipt.jpg"

def main():
    print(f"Checking API connectivity at {API_URL}...")
    try:
        resp = requests.get(f"{API_URL}/health")
        if resp.status_code == 200:
            print("API is UP.")
        else:
            print(f"API Health Check Failed: {resp.status_code} {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Could not connect to API: {e}")
        print("Please ensure API is running and port forwarded (e.g. localhost:8000)")
        sys.exit(1)

    # 1. Prepare Payload
    print("Preparing Receipt OCR Request...")
    # Use a dummy small image if file doesn't exist for quick test
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Warning: {TEST_IMAGE_PATH} not found. Using dummy 1x1 pixel image.")
        # 1x1 transparent PNG base64 (valid)
        dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+lmXcAAAAASUVORK5CYII="
        files = {
            'image': ('dummy.png', base64.b64decode(dummy_b64), 'image/png')
        }
    else:
        files = {
            'image': ('test_receipt.jpg', open(TEST_IMAGE_PATH, 'rb'), 'image/jpeg')
        }

    # 2. Send Request
    url = f"{API_URL}/upload/receipt"
    print(f"POST {url} ...")
    try:
        resp = requests.post(url, files=files)
        if resp.status_code != 200:
             # It might be 202 if we changed it, but router says returns dict with job_id
             # Wait, router.py returns a dict, status 200 default in FastAPI unless specified.
             print(f"Request failed: {resp.status_code} {resp.text}")
             sys.exit(1)
        
        data = resp.json()
        job_id = data.get("job_id")
        if not job_id:
            print("No job_id returned!")
            print(data)
            sys.exit(1)
            
        print(f"Job enqueued! ID: {job_id}")
        
    except Exception as e:
        print(f"Request Error: {e}")
        sys.exit(1)

    # 3. Poll for Result
    print("Polling for result...")
    for i in range(180):
        time.sleep(1)
        job_url = f"{API_URL}/jobs/{job_id}"
        resp = requests.get(job_url)
        if resp.status_code != 200:
            print(f"Job check failed: {resp.status_code}")
            continue
            
        job_data = resp.json()
        status = job_data.get("status")
        print(f"[{i+1}s] Status: {status}")
        
        if status == "DONE":
            print("Job Completed Successfully!")
            print("Result:", json.dumps(job_data.get("result"), indent=2, ensure_ascii=False))
            sys.exit(0)
        elif status == "FAILED":
            print("Job Failed!")
            print("Error:", job_data.get("error"))
            sys.exit(1)

    print("Timeout waiting for job completion.")
    sys.exit(1)

if __name__ == "__main__":
    main()
