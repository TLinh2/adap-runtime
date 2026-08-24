import os
from dotenv import load_dotenv

load_dotenv()

HOST_ID = os.getenv("HOST_ID")
HOST_IP = os.getenv("HOST_IP")
SCHEDULER = os.getenv("SCHEDULER")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD"))
RESOURCE_INTERVAL = os.getenv("RESOURCE_INTERVAL")
