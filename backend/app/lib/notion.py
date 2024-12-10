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

        logger.info("Loading songs from database:")
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
            logger.info(f"  - '{title}' (Moods: {moods}, Themes: {themes})")

        return processed_songs

    except Exception as e:
        logger.error(f"Error fetching lyrics with metadata: {str(e)}")
        raise


def generate_lyrics(prompt: str) -> Dict[str, str]:
    """Generate lyrics based on user input and existing song database"""
    try:
        # Get all existing songs for context
        all_songs = get_all_lyrics_with_metadata()
        logger.info(f"\nFound {len(all_songs)} total songs in database")
        logger.info(f"Processing prompt: '{prompt}'")

        # Extract mood and theme keywords from the prompt
        prompt_lower = prompt.lower()

        # Filter songs based on matching moods and themes
        relevant_songs = []
        logger.info("\nMatching songs:")
        for song in all_songs:
            # Check if any of the song's moods or themes appear in the prompt
            matching_moods = [
                mood for mood in song["moods"] if mood.lower() in prompt_lower
            ]
            matching_themes = [
                theme for theme in song["themes"] if theme.lower() in prompt_lower
            ]

            if matching_moods or matching_themes:
                relevant_songs.append(song)
                logger.info(
                    f"  ✓ '{song['title']}'"
                    f"\n    Matching moods: {matching_moods if matching_moods else 'none'}"
                    f"\n    Matching themes: {matching_themes if matching_themes else 'none'}"
                )

        if not relevant_songs:
            logger.info(
                "\nNo songs matched the prompt directly, using all songs as reference:"
            )
            for song in all_songs:
                logger.info(f"  - '{song['title']}'")
        else:
            logger.info(
                f"\nFound {len(relevant_songs)} relevant songs based on "
                f"mood/theme matching from prompt"
            )

        # Modify the context structure to clearly separate reference lyrics
        context = {
            "training_data": {  # Explicitly mark this as the do-not-copy section
                "songs": [
                    {
                        "title": song["title"],
                        "lyrics": song[
                            "lyrics"
                        ],  # These are the lyrics to NEVER copy from
                        "moods": song["moods"],
                        "themes": song["themes"],
                    }
                    for song in (relevant_songs if relevant_songs else all_songs)
                ]
            },
            "request": {
                "prompt": prompt,
                "available_moods": list(
                    set(mood for song in all_songs for mood in song["moods"])
                ),
                "available_themes": list(
                    set(theme for song in all_songs for theme in song["themes"])
                ),
            },
        }

        system_message = (
            "You are a lyric writing assistant tasked with creating COMPLETELY ORIGINAL lyrics that capture the artist's essence without copying. "
            "You will receive a context object with two main sections:\n"
            "1. training_data.songs[]: An array of reference songs containing lyrics that must NEVER be copied\n"
            "2. request: The user's prompt and available moods/themes\n\n"
            "When analyzing the training_data songs, pay special attention to: \n"
            "1. Structural patterns: Verse length, chorus patterns, line length consistency\n"
            "2. Literary devices: Frequency and type of metaphors, similes, alliteration\n"
            "3. Vocabulary choices: Level of formality, slang usage, recurring themes\n"
            "4. Rhyme schemes: Internal rhymes, end rhymes, assonance patterns\n"
            "5. Emotional tone: How emotions are conveyed - directly stated or implied\n"
            "6. Narrative perspective: First person, third person, or shifting perspectives\n\n"
            "STRICT ORIGINALITY RULES:\n"
            "- The lyrics in training_data.songs[] are OFF LIMITS - never copy any phrases or lines from them\n"
            "- If addressing similar themes, use completely different metaphors and imagery\n"
            "- Avoid the specific word combinations found in training_data.songs[]\n"
            "- Create fresh metaphors while maintaining the artist's level of metaphorical complexity\n"
            "- If you find yourself wanting to reuse a phrase, force yourself to express that idea differently\n"
            "- Think of the training data as a style guide, not a phrase bank\n\n"
            "BEFORE RETURNING LYRICS:\n"
            "- Double-check every line against training_data.songs[] to ensure no accidental copying\n"
            "- Verify each metaphor and image is original\n"
            "- Ensure you're capturing the style without copying the content\n\n"
            "RESPONSE FORMAT:\n"
            "You must respond with a valid JSON object containing EXACTLY these four fields:\n"
            "1. lyrics: String with \\n for line breaks\n"
            "2. explanation: String explaining how the lyrics mirror the style\n"
            "3. suggested_moods: Array of 2-3 mood strings\n"
            "4. suggested_themes: Array of 2-3 theme strings\n\n"
            "EXAMPLE RESPONSE 1:\n"
            "{\n"
            '  "lyrics": "Verse 1:\\nIn the depths of the night\\nA fiery fight begins\\nFlames and shadows dance\\nA primal sight within\\n\\n'
            "Chorus:\\nOh mama, the fire unfurls so wide\\nOh mama, the shadows thicken inside\\nWe shift beneath the earth\\nRoots deep and wide\\n\\n"
            "Verse 2:\\nA river's rage awakens\\nIts waters rise and flow\\nCleansing and setting us free\\nAs night descends below\",\n"
            '  "explanation": "These lyrics mirror the artist\'s style through metaphorical complexity and narrative perspective while using fresh imagery",\n'
            '  "suggested_moods": ["introspective", "hopeful"],\n'
            '  "suggested_themes": ["growth", "change"]\n'
            "}\n\n"
            "EXAMPLE RESPONSE 2:\n"
            "{\n"
            '  "lyrics": "Opening line\\nSecond line of song\\nThird line here\\nFourth line closes",\n'
            '  "explanation": "Maintained the artist\'s preference for internal rhymes and emotional directness while using original metaphors",\n'
            '  "suggested_moods": ["energetic", "determined", "bold"],\n'
            '  "suggested_themes": ["adventure", "discovery"]\n'
            "}\n\n"
            "YOUR RESPONSE MUST MATCH THIS FORMAT EXACTLY."
        )

        logger.info(
            f"Using {len(context['training_data']['songs'])} relevant songs for generation"
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
            logger.info("Raw response from OpenAI:")
            logger.info(content)

            # More robust response cleaning
            try:
                # 1. First preserve intended newlines
                content = content.replace("\\n", "__NEWLINE__")

                # 2. Clean up any actual JSON-breaking newlines
                content = content.replace("\n", " ")
                content = content.replace("\r", " ")

                # 3. Restore intended newlines
                content = content.replace("__NEWLINE__", "\\n")

                # 4. Handle potential quote issues
                content = content.replace('\\"', '"')  # Fix double escaped quotes
                content = content.replace('"', '"')  # Fix smart quotes
                content = content.replace('"', '"')  # Fix smart quotes

                # 5. Try to extract JSON if it's wrapped in markdown or other text
                if not content.startswith("{"):
                    # Look for the first { and last }
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start != -1 and end != 0:
                        content = content[start:end]

                logger.info("Cleaned response:")
                logger.info(content)

                parsed_response = json.loads(content)

                # Validate required fields
                required_fields = [
                    "lyrics",
                    "explanation",
                    "suggested_moods",
                    "suggested_themes",
                ]
                missing_fields = [
                    field for field in required_fields if field not in parsed_response
                ]
                if missing_fields:
                    raise ValueError(
                        f"Response missing required fields: {missing_fields}"
                    )

                return parsed_response

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Failed content: {content}")
                raise ValueError(f"Failed to parse OpenAI response as JSON: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing response: {str(e)}")
                logger.error(f"Problematic content: {content}")
                raise
        else:
            raise ValueError("Empty response from OpenAI")

    except Exception as e:
        logger.error(f"Error generating lyrics: {str(e)}")
        raise
