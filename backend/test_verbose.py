import requests
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

url = "https://tqmbkpswubye2ubwg2lc2s7ele0ffbzz.lambda-url.us-east-1.on.aws/api/status"

print(f"Testing URL: {url}\n")

try:
    response = requests.get(url, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
