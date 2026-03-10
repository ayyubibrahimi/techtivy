
import requests
import os 
from dotenv import load_dotenv

load_dotenv()

url = "https://d2ftw.westus2.cloudapp.azure.com/o/token/"
data = {
    "grant_type": "client_credentials",
    "client_id": os.getenv("D2_CLIENT_ID"),
    "client_secret": os.getenv("D2_CLIENT_SECRET")
}

response = requests.post(url, data=data)
print(response.json())