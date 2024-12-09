from dotenv import load_dotenv
import os

load_dotenv()

environment = os.getenv("ENVIRONMENT", "dev")  # Default to 'development' if not set
slack_integration_secret = os.getenv("SLACK_INTEGRATION_SECRET")
notion_api_key = os.getenv("NOTION_API_KEY")
notion_database_id = os.getenv("NOTION_DATABASE_ID")
openai_api_key = os.getenv("OPENAI_API_KEY")
