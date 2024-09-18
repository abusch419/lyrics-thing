from dotenv import load_dotenv
import os

load_dotenv()

environment = os.getenv("ENVIRONMENT", "dev")  # Default to 'development' if not set
