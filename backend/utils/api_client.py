import requests
import logging
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('API_BASE_URL')
        self.session = requests.Session()
        self.timeout = int(os.getenv('TEST_TIMEOUT', 30))
        self.logger = logging.getLogger(__name__)
    
    def get(self, endpoint: str, params: Dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout, verify=False)
        self.logger.info(f"GET {url} - Status: {response.status_code}")
        return response
    
    def post(self, endpoint: str, data: Dict = None, json: Dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, data=data, json=json, timeout=self.timeout)
        self.logger.info(f"POST {url} - Status: {response.status_code}")
        return response
    
    def put(self, endpoint: str, data: Dict = None, json: Dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, data=data, json=json, timeout=self.timeout)
        self.logger.info(f"PUT {url} - Status: {response.status_code}")
        return response
    
    def delete(self, endpoint: str) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, timeout=self.timeout)
        self.logger.info(f"DELETE {url} - Status: {response.status_code}")
        return response