import random
import uuid
import fetcher
import json
import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import time

# Costanti
NUM_CHANNELS = 10000
DADDY_JSON_FILE = "daddyliveSchedule.json"
M3U8_OUTPUT_FILE = "mergeita.m3u8"
LOGO = "https://raw.githubusercontent.com/cribbiox/eventi/refs/heads/main/ddsport.png"

mStartTime = 0
mStopTime = 0

# File e URL statici per la seconda parte dello script
daddyLiveChannelsFileName = '247channels.html'
daddyLiveChannelsURL = 'https://daddylive.mp/24-7-channels.php'

# Headers and related constants from the first code block (assuming these are needed for requests)
Referer = "https://ilovetoplay.xyz/"
Origin = "https://ilovetoplay.xyz"
key_url = "https%3A%2F%2Fkey2.keylocking.ru%2F"

headers = {
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,ru;q=0.5",
    "Priority": "u=1, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "Sec-Ch-UA-Mobile": "?0",
    "Sec-Ch-UA-Platform": "Windows",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Storage-Access": "active",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

client = requests

def get_stream_link(dlhd_id, event_name="", channel_name="", max_retries=3):
    print(f"Getting stream link for channel ID: {dlhd_id} - {event_name} on {channel_name}...")

    base_timeout = 10  # Base timeout in seconds

    for attempt in range(max_retries):
        try:
            response = client.get(
                f"https://daddylive.mp/embed/stream-{dlhd_id}.php",
                headers=headers,
                timeout=base_timeout
            )
            response.raise_for_status()
            response.encoding = 'utf-8'

            response_text = response.text
            if not response_text:
                print(f"Warning: Empty response received for channel ID: {dlhd_id} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                return None

            soup = BeautifulSoup(response_text, 'html.parser')
            iframe = soup.find('iframe', id='thatframe')

            if iframe is None:
                print(f"Debug: iframe with id 'thatframe' NOT FOUND for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                return None

            if iframe and iframe.get('src'):
                real_link = iframe.get('src')
                parent_site_domain = real_link.split('/premiumtv')[0]
                server_key_link = (f'{parent_site_domain}/server_lookup.php?channel_id=premium{dlhd_id}')
                server_key_headers = headers.copy()
                server_key_headers["Referer"] = f"https://newembedplay.xyz/premiumtv/daddylivehd.php?id={dlhd_id}"
                server_key_headers["Origin"] = "https://newembedplay.xyz"
                server_key_headers["Sec-Fetch-Site"] = "same-origin"

                response_key = client.get(
                    server_key_link,
                    headers=server_key_headers,
                    allow_redirects=False,
                    timeout=base_timeout
                )

                time.sleep(random.uniform(1, 3))
                response_key.raise_for_status()

                try:
                    server_key_data = response_key.json()
                except json.JSONDecodeError:
                    print(f"JSON Decode Error for channel ID {dlhd_id}: Invalid JSON response: {response_key.text[:100]}...")
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue
                    return None

                if 'server_key' in server_key_data:
                    server_key = server_key_data['server_key']
                    stream_url = f"https://{server_key}new.iosplayer.ru/{server_key}/premium{dlhd_id}/mono.m3u8"
                    print(f"Stream URL retrieved for channel ID: {dlhd_id} - {event_name} on {channel_name}")
                    return stream_url
                else:
                    print(f"Error: 'server_key' not found in JSON response from {server_key_link} (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue
                    return None
            else:
                print(f"Error: iframe with id 'thatframe' found, but 'src' attribute is missing for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                return None

        except requests.exceptions.Timeout:
            print(f"Timeout error for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
            return None

        except requests.exceptions.RequestException as e:
            print(f"Request Exception for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
            return None

        except Exception as e:
            print(f"General Exception for channel ID {dlhd_id} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
            return None

    return None  # If we get here, all retries failed

# Rimuove i file esistenti per garantirne la rigenerazione
for file in [M3U8_OUTPUT_FILE, daddyLiveChannelsFileName]:  #, DADDY_JSON_FILE
    if os.path.exists(file):
        os.remove(file)

# Funzioni prima parte dello script
def generate_unique_ids(count, seed=42):
    random.seed(seed)
    return [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(count)]

def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def addChannelsByLeagueSport():
    global channelCount
    processed_schedule_channels = 0  # Counter for schedule channels

    # Define categories to exclude - these must match exact category names in JSON
    excluded_categories = [
        "TV Shows", "Cricket", "Aussie rules", "Snooker", "Baseball",
        "Biathlon", "Cross Country", "Horse Racing", "Ice Hockey",
        "Waterpolo", "Golf", "Darts", "Cycling", "Handball", "Squash"
    ]

    # Debug counters
    total_events = 0
    skipped_events = 0
    category_stats = {}  # To track how many events per category

    # First pass to gather category statistics
    for day, day_data in dadjson.items():
        try:
            for sport_key, sport_events in day_data.items():
                # Clean the sport key by removing HTML tags
                clean_sport_key = sport_key.replace("</span>", "").replace("<span>", "").strip()

                if clean_sport_key not in category_stats:
                    category_stats[clean_sport_key] = 0
                category_stats[clean_sport_key] += len(sport_events)
        except (KeyError, TypeError):
            pass  # Skip problematic days

    # Print category statistics
    print("\n=== Available Categories ===")
    for category, count in sorted(category_stats.items()):
        excluded = "EXCLUDED" if category in excluded_categories else ""
        print(f"{category}: {count} events {excluded}")
    print("===========================\n")

    # Second pass to process events
    for day, day_data in dadjson.items():
        try:
            for sport_key, sport_events in day_data.items():
                # Clean the sport key by removing HTML tags
                clean_sport_key = sport_key.replace("</span>", "").replace("<span>", "").strip()

                total_events += len(sport_events)

                # Skip only exact category matches
                if clean_sport_key in excluded_categories:
                    skipped_events += len(sport_events)
                    continue

                for game in sport_events:
                    for channel in game.get("channels", []):
                        try:
                            # Remove the "Schedule Time UK GMT" part and split the remaining string
                            clean_day = day.replace(" - Schedule Time UK GMT", "")

                            # Remove ordinal suffixes (st, nd, rd, th)
                            clean_day = clean_day.replace("st ", " ").replace("nd ", " ").replace("rd ", " ").replace("th ", " ")

                            # Split the cleaned string
                            day_parts = clean_day.split()

                            if len(day_parts) >= 4:  # Make sure we have enough parts
                                day_num = day_parts[1]
                                month_name = day_parts[2]
                                year = day_parts[3]

                                # Get time from game data
                                time_str = game.get("time", "00:00")

                                # Converti l'orario da UK a CET (aggiungi 1 ora)
                                time_parts = time_str.split(":")
                                if len(time_parts) == 2:
                                    hour = int(time_parts[0])
                                    minute = time_parts[1]
                                    # Aggiungi un'ora all'orario UK
                                    hour_cet = (hour + 1) % 24
                                    # Assicura che l'ora abbia due cifre
                                    hour_cet_str = f"{hour_cet:02d}"
                                    # Nuovo time_str con orario CET
                                    time_str_cet = f"{hour_cet_str}:{minute}"
                                else:
                                    # Se il formato dell'orario non è corretto, mantieni l'originale
                                    time_str_cet = time_str

                                # Convert month name to number
                                month_map = {
                                    "January": "01", "February": "02", "March": "03", "April": "04",
                                    "May": "05", "June": "06", "July": "07", "August": "08",
                                    "September": "09", "October": "10", "November": "11", "December": "12"
                                }
                                month_num = month_map.get(month_name, "01")  # Default to January if not found

                                # Ensure day has leading zero if needed
                                if len(day_num) == 1:
                                    day_num = f"0{day_num}"

                                # Create a datetime object in UTC (no timezone conversion yet)
                                year_short = year[2:4]  # Extract last two digits of year

                                # Format as requested: "01/03/25 - 10:10" con orario CET
                                formatted_date_time = f"{day_num}/{month_num}/{year_short} - {time_str_cet}"

                            else:
                                print(f"Invalid date format after cleaning: {clean_day}")
                                continue

                        except Exception as e:
                            print(f"Error processing date '{day}': {e}")
                            print(f"Game time: {game.get('time', 'No time found')}")
                            continue

                        # Get next unique ID
                        UniqueID = unique_ids.pop(0)

                        try:
                            #### Build channel name with new date format
                            #channelName = game["event"] + " " + formatted_date_time + "  " + channel["channel_name"]
                            channelName = formatted_date_time + "  " + channel["channel_name"]

                            #### Extract event part and channel part for TVG ID
                            #if ":" in game["event"]:
                            #    event_part = game["event"].split(":")[0].strip()
                            #else:
                            #    event_part = game["event"].strip()
                            event_name = game["event"].split(":")[0].strip() if ":" in game["event"] else game["event"].strip()
                            event_details = game["event"]  # Keep the full event details for tvg-name

                            #channel_part = channel["channel_name"].strip()
                            #custom_tvg_id = f"{event_part} - {channel_part}"

                        except (TypeError, KeyError) as e:
                            print(f"Error processing event: {e}")
                            continue

                        # Process channel information
                        channelID = f"{channel['channel_id']}"
                        tvgName = channelName
                        tvLabel = tvgName
                        channelCount += 1
                        print(f"Processing channel {channelCount}: {sport_key} - {channelName}")

                        # Get stream URL
                        stream_url_dynamic = get_stream_link(channelID, game["event"], channel["channel_name"])

                        if stream_url_dynamic:
                            # Write to M3U8 file
                            with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
                                if channelCount == 1:
                                    file.write('#EXTM3U url-tvg="http://epg-guide.com/it.gz"\n')
                            with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
                                # Use sport_key as the group-title, with (D) added to the label
                                #file.write(f'#EXTINF:-1 tvg-id="{custom_tvg_id}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="{sport_key}", {tvLabel} (D)\n')
                                file.write(f'#EXTINF:-1 tvg-id="{event_name} - {event_details.split(":", 1)[1].strip() if ":" in event_details else event_details}" tvg-name="{event_details} {formatted_date_time}" tvg-logo="{LOGO}" group-title="{clean_sport_key}", {channel["channel_name"]}\n')
                                file.write('#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
                                file.write('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36\n')
                                file.write('#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
                                file.write(f"{stream_url_dynamic}\n\n")

                            processed_schedule_channels += 1
                        else:
                            print(f"Failed to get stream URL for channel ID: {channelID}")

        except KeyError as e:
            print(f"KeyError: {e} - Key may not exist in JSON structure")

    # Print summary
    print(f"\n=== Processing Summary ===")
    print(f"Total events found: {total_events}")
    print(f"Events skipped due to category filters: {skipped_events}")
    print(f"Channels successfully processed: {processed_schedule_channels}")
    print(f"===========================\n")

    return processed_schedule_channels

STATIC_LOGOS = {
    "sky uno": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-uno-it.png",
    "rai 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/rai-1-it.png",
    "rai 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/rai-2-it.png",
    "rai 3": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/rai-3-it.png",
    "eurosport 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/eurosport-1-es.png",
    "eurosport 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/eurosport-2-es.png",
    "italia 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/italia1-it.png",
    "la7": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/la7-it.png",
    "la7d": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/la7d-it.png",
    "rai sport": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/rai-sport-it.png",
    "rai premium": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/rai-premium-it.png",
    "sky sports golf": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-golf-it.png",
    "sky sport motogp": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-motogp-it.png",
    "sky sport tennis": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-tennis-it.png",
    "sky sport f1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-f1-it.png",
    "sky sport football": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-football-it.png",
    "sky sport uno": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-uno-it.png",
    "sky sport arena": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-arena-it.png",
    "sky cinema collection": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-collection-it.png",
    "sky cinema uno": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-uno-it.png",
    "sky cinema action": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-action-it.png",
    "sky cinema comedy": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-comedy-it.png",
    "sky cinema uno +24": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-uno-plus24-it.png",
    "sky cinema romance": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-romance-it.png",
    "sky cinema family": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-family-it.png",
    "sky cinema due +24": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-due-plus24-it.png",
    "sky cinema drama": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-drama-it.png",
    "sky cinema suspense": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-cinema-suspense-it.png",
    "sky sport 24": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-24-it.png",
    "sky sport calcio": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png",
    "sky sport": "https://play-lh.googleusercontent.com/u7UNH06SU4KsMM4ZGWr7wghkJYN75PNCEMxnIYULpA__VPg8zfEOYMIAhUaIdmZnqw=w480-h960-rw",
    "sky calcio 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-1-alt-de.png",
    "sky calcio 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-2-alt-de.png",
    "sky calcio 3": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-3-alt-de.png",
    "sky calcio 4": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-4-alt-de.png",
    "sky calcio 5": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-5-alt-de.png",
    "sky calcio 6": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-6-alt-de.png",
    "sky calcio 7": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-select-7-alt-de.png",
    "sky serie": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-serie-it.png",
    "20 mediaset": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/20-it.png",
    "dazn 1": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DAZN_1_Logo.svg/774px-DAZN_1_Logo.svg.png"
}

STATIC_TVG_IDS = {
    "sky uno": "sky uno",
    "rai 1": "rai 1",
    "rai 2": "rai 2",
    "rai 3": "rai 3",
    "eurosport 1": "eurosport 1",
    "eurosport 2": "eurosport 2",
    "italia 1": "italia 1",
    "la7": "la7",
    "la7d": "la7d",
    "rai sport": "rai sport",
    "rai premium": "rai premium",
    "sky sports golf": "sky sport golf",
    "sky sport motogp": "sky sport motogp",
    "sky sport tennis": "sky sport tennis",
    "sky sport f1": "sky sport f1",
    "sky sport football": "sky sport football",
    "sky sport uno": "sky sport uno",
    "sky sport arena": "sky sport arena",
    "sky cinema collection": "sky cinema collection",
    "sky cinema uno": "sky cinema uno",
    "sky cinema action": "sky cinema action",
    "sky cinema comedy": "sky cinema comedy",
    "sky cinema uno +24": "sky cinema uno +24",
    "sky cinema romance": "sky cinemar omance",
    "sky cinema family": "sky cinema family",
    "sky cinema due +24": "sky cinema Due +24",
    "sky cinema drama": "sky cinema drama",
    "sky cinema suspense": "sky cinema suspense",
    "sky sport 24": "sky sport 24",
    "sky sport calcio": "Sky Sport Calcio",
    "sky calcio 1": "Sky Sport",
    "sky calcio 2": "Sky Sport 2",
    "sky calcio 3": "sky sport 3",
    "sky calcio 4": "sky sport 4",
    "sky calcio 5": "sky sport 5",
    "sky calcio 6": "sky sport 6",
    "sky calcio 7": "sky sport 7",
    "sky serie": "sky serie",
    "20 mediaset": "Mediaset 20",
}

STATIC_CATEGORIES = {
    "sky uno": "Sky",
    "rai 1": "Rai Tv",
    "rai 2": "Rai Tv",
    "rai 3": "Rai Tv",
    "eurosport 1": "Sport",
    "eurosport 2": "Sport",
    "italia 1": "Mediaset",
    "la7": "Tv Italia",
    "la7d": "Tv Italia",
    "rai sport": "Sport",
    "rai premium": "Rai Tv",
    "sky sports golf": "Sport",
    "sky sport motogp": "Sport",
    "sky sport tennis": "Sport",
    "sky sport f1": "Sport",
    "sky sport football": "Sport",
    "sky sport uno": "Sport",
    "sky sport arena": "Sport",
    "sky cinema collection": "Sky",
    "sky cinema uno": "Sky",
    "sky cinema action": "Sky",
    "sky cinema comedy": "Sky",
    "sky cinema uno +24": "Sky",
    "sky cinema romance": "Sky",
    "sky cinema family": "Sky",
    "sky cinema due +24": "Sky",
    "sky cinema drama": "Sky",
    "sky cinema suspense": "Sky",
    "sky sport 24": "Sport",
    "sky sport calcio": "Sport",
    "sky calcio 1": "Sport",
    "sky calcio 2": "Sport",
    "sky calcio 3": "Sport",
    "sky calcio 4": "Sport",
    "sky calcio 5": "Sport",
    "sky calcio 6": "Sport",
    "sky calcio 7": "Sport",
    "sky serie": "Sky",
    "20 mediaset": "Mediaset",
}

def fetch_with_debug(filename, url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filename, 'wb') as file:
            file.write(response.content)
    except requests.exceptions.RequestException as e:
        pass

def search_category(channel_name):
    return STATIC_CATEGORIES.get(channel_name.lower().strip(), "Undefined")
def search_streams(file_path, keyword):
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            links = soup.find_all('a', href=True)

        for link in links:
            if keyword.lower() in link.text.lower():
                href = link['href']
                stream_number = href.split('-')[-1].replace('.php', '')
                stream_name = link.text.strip()
                match = (stream_number, stream_name)

                if match not in matches:
                    matches.append(match)
    except FileNotFoundError:
        pass
    return matches

def search_logo(channel_name):
    channel_name_lower = channel_name.lower().strip()
    for key, url in STATIC_LOGOS.items():
        if key in channel_name_lower:
            return url
    return "https://raw.githubusercontent.com/cribbiox/eventi/refs/heads/main/ddlive.png"


def search_tvg_id(channel_name):
    channel_name_lower = channel_name.lower().strip()
    for key, tvg_id in STATIC_TVG_IDS.items():
        if key in channel_name_lower:
            return tvg_id
    return "unknown"

def generate_m3u8_247(matches):
    if not matches:
        return 0

    processed_247_channels = 0 # Counter for 24/7 channels
    with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file: # Appende al file esistente
        for channel in matches:
            channel_id = channel[0]
            channel_name = channel[1].replace("Italy", "").replace("8", "").replace("(251)", "").replace("(252)", "").replace("(253)", "").replace("(254)", "").replace("(255)", "").replace("(256)", "").replace("(257)", "").replace("HD+", "")
            tvicon_path = search_logo(channel_name)
            tvg_id = search_tvg_id(channel_name)
            category = search_category(channel_name)
            print(f"Processing 24/7 channel: {channel_name} - Channel Count (24/7): {processed_247_channels + 1}") # Progress print: 24/7 channel processing

            stream_url_dynamic = get_stream_link(channel_id) # Removed site and MFP_CREDENTIALS arguments

            if stream_url_dynamic:
                # MODIFICATO: Aggiunto (D) dopo il nome del canale
                file.write(f"#EXTINF:-1 tvg-id=\"{tvg_id}\" tvg-name=\"{channel_name}\" tvg-logo=\"{tvicon_path}\" group-title=\"{category}\", {channel_name} (D)\n")
                file.write(f'#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
                file.write('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36\n')
                file.write('#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
                file.write(f"{stream_url_dynamic}\n\n") # Use dynamic stream URL
                processed_247_channels += 1 # Increment counter on successful stream retrieval
            else:
                print(f"Failed to get stream URL for 24/7 channel ID: {channel_id}. Skipping M3U8 entry for this channel.") # Debug removed
                pass # No debug print, just skip

    # Aggiungi manualmente il canale DAZN 1
    print("Aggiunta manuale del canale DAZN 1")
    channel_id = "877"
    channel_name = "DAZN 1"
    tvicon_path = STATIC_LOGOS.get("dazn 1", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DAZN_1_Logo.svg/774px-DAZN_1_Logo.svg.png")
    tvg_id = "DAZN 1"
    category = "Sport"

    stream_url_dynamic = get_stream_link(channel_id)
    if stream_url_dynamic:
        with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
            file.write(f"#EXTINF:-1 tvg-id=\"{tvg_id}\" tvg-name=\"{channel_name}\" tvg-logo=\"{tvicon_path}\" group-title=\"{category}\", {channel_name} (D)\n")
            file.write(f'#EXTVLCOPT:http-referrer=https://ilovetoplay.xyz/\n')
            file.write('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36\n')
            file.write('#EXTVLCOPT:http-origin=https://ilovetoplay.xyz\n')
            file.write(f"{stream_url_dynamic}\n\n")
            processed_247_channels += 1
    else:
        print(f"Failed to get stream URL for DAZN 1 channel ID: {channel_id}")

    #print("M3U8 file updated with 24/7 channels.") # Debug removed
    return processed_247_channels # Return count of processed 24/7 channels


# Inizio del codice principale
channelCount = 0
unique_ids = generate_unique_ids(NUM_CHANNELS)
total_schedule_channels = 0
total_247_channels = 0

# Scarica il file JSON con la programmazione
# fetcher.fetchHTML(DADDY_JSON_FILE, "https://daddylive.mp/schedule/schedule-generated.json")

# Carica i dati dal JSON
dadjson = loadJSON(DADDY_JSON_FILE)

# Aggiunge i canali reali
total_schedule_channels = addChannelsByLeagueSport()

# Fetch e generazione M3U8 per i canali 24/7
fetch_with_debug(daddyLiveChannelsFileName, daddyLiveChannelsURL)
matches_247 = search_streams(daddyLiveChannelsFileName, "Italy")
total_247_channels = generate_m3u8_247(matches_247)

print(f"Script completato. Canali programmazione aggiunti: {total_schedule_channels}, Canali 24/7 aggiunti: {total_247_channels}")
