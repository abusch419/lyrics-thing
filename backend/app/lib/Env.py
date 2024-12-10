from dotenv import load_dotenv
import os

load_dotenv()

environment = os.getenv("ENVIRONMENT", "dev")  # Default to 'development' if not set
notion_api_key = os.getenv("NOTION_API_KEY")
notion_database_id = os.getenv("NOTION_DATABASE_ID")
openai_api_key = os.getenv("OPENAI_API_KEY")
