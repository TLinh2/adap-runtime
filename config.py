import os
from dotenv import load_dotenv

load_dotenv()

HOST_ID = os.getenv("HOST_ID")
HOST_IP = os.getenv("HOST_IP")
SCHEDULER = os.getenv("SCHEDULER")
RESOURCE_INTERVAL = float(os.getenv("RESOURCE_INTERVAL"))
MAX_WAIT_MS = float(os.getenv("MAX_WAIT_MS"))
MAX_WAIT_SECONDS = MAX_WAIT_MS / 1000.0
