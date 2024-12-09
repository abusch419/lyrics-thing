from notion_client import Client
import json
import logging
from openai import OpenAI
from typing import List, Dict
from app.lib.Env import notion_api_key, notion_database_id, openai_api_key

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients with env vars from Env.py
notion = Client(auth=notion_api_key)
openai = OpenAI(api_key=openai_api_key)


def get_lyrics_database():
    """Fetch all entries from the lyrics database"""
    try:
        response = notion.databases.query(database_id=notion_database_id)
        return response["results"]
    except Exception as e:
        logger.error(f"Error fetching lyrics database: {str(e)}")
        raise


def analyze_lyrics(lyrics: str) -> Dict[str, List[str]]:
    """Use GPT to analyze lyrics and suggest moods and themes"""
    prompt = f"""Analyze these lyrics and provide:
    1. A list of 2-3 moods (emotional tones)
    2. A list of 2-3 themes (main topics/ideas)
    
    Lyrics: {lyrics}
    
    Respond in this exact format:
    {{"moods": ["mood1", "mood2"], "themes": ["theme1", "theme2"]}}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        # Safely parse the JSON response
        if response.choices and response.choices[0].message.content:
            return json.loads(response.choices[0].message.content)
        else:
            raise ValueError("Empty response from OpenAI")

    except Exception as e:
        logger.error(f"Error analyzing lyrics: {str(e)}")
        raise


def update_page_properties(page_id: str, moods: List[str], themes: List[str]):
    """Update the moods and themes for a specific page"""
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Moods": {"multi_select": [{"name": mood} for mood in moods]},
                "Themes": {"multi_select": [{"name": theme} for theme in themes]},
            },
        )
    except Exception as e:
        logger.error(f"Error updating page {page_id}: {str(e)}")
        raise


def process_database():
    """Main function to process all lyrics"""
    try:
        pages = get_lyrics_database()
        total_pages = len(pages)
        processed = 0
        skipped = 0

        logger.info(f"Starting to process {total_pages} pages")

        for page in pages:
            try:
                # Skip if already processed
                if (
                    page["properties"]["Moods"]["multi_select"]
                    or page["properties"]["Themes"]["multi_select"]
                ):
                    skipped += 1
                    continue

                # Get the lyrics from the page
                lyrics_property = (
                    page["properties"].get("Lyrics 1", {}).get("rich_text", [])
                )
                if not lyrics_property:
                    logger.warning(f"No lyrics found for page {page['id']}")
                    continue

                lyrics = lyrics_property[0]["text"]["content"]

                # Analyze the lyrics
                analysis = analyze_lyrics(lyrics)

                # Update the page
                update_page_properties(
                    page_id=page["id"],
                    moods=analysis["moods"],
                    themes=analysis["themes"],
                )

                processed += 1
                logger.info(
                    f"Processed {processed}/{total_pages} pages (skipped {skipped})"
                )

            except Exception as e:
                logger.error(f"Error processing page {page['id']}: {str(e)}")
                continue

        logger.info(f"Finished processing. Processed: {processed}, Skipped: {skipped}")
        return {"processed": processed, "skipped": skipped}

    except Exception as e:
        logger.error(f"Error in process_database: {str(e)}")
        raise


def get_all_lyrics_with_metadata() -> List[Dict]:
    """Fetch all lyrics with their associated moods and themes"""
    try:
        response = notion.databases.query(database_id=notion_database_id)
        processed_songs = []

        for page in response["results"]:
            # Get lyrics
            lyrics_property = (
                page["properties"].get("Lyrics 1", {}).get("rich_text", [])
            )
            if not lyrics_property:
                continue

            lyrics = lyrics_property[0]["text"]["content"]

            # Get title
            title_property = page["properties"].get("Lyrics", {}).get("title", [])
            title = title_property[0]["plain_text"] if title_property else "Untitled"

            # Get moods and themes
            moods = [
                item["name"]
                for item in page["properties"].get("Moods", {}).get("multi_select", [])
            ]
            themes = [
                item["name"]
                for item in page["properties"].get("Themes", {}).get("multi_select", [])
            ]

            processed_songs.append(
                {"title": title, "lyrics": lyrics, "moods": moods, "themes": themes}
            )

        return processed_songs

    except Exception as e:
        logger.error(f"Error fetching lyrics with metadata: {str(e)}")
        raise


def generate_lyrics(prompt: str) -> Dict[str, str]:
    """Generate lyrics based on user input and existing song database"""
    try:
        # Get all existing songs for context
        songs = get_all_lyrics_with_metadata()

        # Create a context message that includes all songs
        context = {"existing_songs": songs, "user_request": prompt}

        system_message = (
            "You are a lyric writing assistant. You have access to a database of existing "
            "songs with their moods and themes. Analyze the style, themes, and moods of "
            "the existing songs, and use that to inform how you generate new lyrics. "
            "When writing new lyrics, try to maintain consistency with the artistic voice "
            "shown in the existing songs while incorporating the user's specific requests. "
            "IMPORTANT: Use \\n for newlines in the lyrics. Return your response in this format: "
            '{"lyrics": "Line 1\\nLine 2\\nLine 3", '
            '"explanation": "Single line explanation", '
            '"suggested_moods": ["mood1", "mood2"], '
            '"suggested_themes": ["theme1", "theme2"]}'
        )

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": json.dumps(context)},
            ],
            temperature=0.7,
        )

        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
            # Clean up the response: replace actual newlines with spaces in the JSON
            # but preserve \n literals
            content = content.replace(
                "\\n", "__NEWLINE__"
            )  # temporarily replace \n literals
            content = content.replace("\n", " ")  # replace actual newlines with spaces
            content = content.replace("__NEWLINE__", "\\n")  # restore \n literals

            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Raw content: {content}")
                raise ValueError("Failed to parse OpenAI response as JSON")
        else:
            raise ValueError("Empty response from OpenAI")

    except Exception as e:
        logger.error(f"Error generating lyrics: {str(e)}")
        raise
