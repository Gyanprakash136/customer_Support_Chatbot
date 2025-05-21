import requests
import webbrowser
import os
from telnetlib import EC
import ec
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.support.wait import WebDriverWait
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import datetime
from datetime import date
from datetime import time
import wikipedia
import time

print("Hello , This is me Rudransh AI")
print("Here some of the command instruction  help you \n suppose you want to open chrome:just type open chrome\n you want to listen music: just type open spotify then search and play the music that you want\nYou want to check the weather of your city or any city of the world just type weather\nYou want to see the time : just type show time\n for date : show date\n for date and time : show date and time\nwant to watch some youtube video :just type open youtube and search for the video\n want to have information about anything in real time : wikipedia")


def wikipedia_search(search):
    result = wikipedia.summary(search,sentences=10)
    return result



def music_player():
    username = "31tovi5smi4ijbjdlq75c5cwu3ma"
    clientID = 'fe5aab4342e146eeb6b03a5eaf004ba9'
    clientSecret = '137d55b2965e456d8cf2ab3b67e827f3'
    redirect_uri = 'https://google.com/callback/'
    scope = "user-read-private"  # Add appropriate scopes as needed

    try:
        # Create the SpotifyOAuth object
        sp_oauth = SpotifyOAuth(
            client_id=clientID,
            client_secret=clientSecret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=f".cache-{username}"
        )

        # Check if there's a cached token first
        token_info = sp_oauth.get_cached_token()

        if not token_info:
            # No token found, need to authenticate
            auth_url = sp_oauth.get_authorize_url()
            print(f"Please go to this URL and authorize the app: {auth_url}")
            print("After authorizing, you'll be redirected to Google. Copy the entire URL you were redirected to.")

            response = input("Enter the URL you were redirected to: ")

            # Extract the code from the URL
            code = sp_oauth.parse_response_code(response)

            # Get the access token with the code
            token_info = sp_oauth.get_access_token(code)

        # Create the Spotify object with the access token
        spotify = spotipy.Spotify(auth=token_info['access_token'])

        # Get user info
        user_info = spotify.current_user()
        print(json.dumps(user_info, sort_keys=True, indent=4))

        # Main program loop
        while True:
            print("\nWelcome to the Spotify Search, " + user_info['display_name'])
            print("0 - Exit the program")
            print("1 - Search for a Song")

            try:
                user_input = int(input("Enter Your Choice: "))

                if user_input == 1:
                    search_song = input("Enter the song name: ")
                    results = spotify.search(search_song, limit=1, offset=0, type="track")

                    songs_dict = results['tracks']
                    song_items = songs_dict['items']

                    if song_items:
                        song = song_items[0]['external_urls']['spotify']
                        artist = song_items[0]['artists'][0]['name']
                        song_name = song_items[0]['name']

                        print(f"Found: '{song_name}' by {artist}")
                        print(f"Opening in browser: {song}")
                        webbrowser.open(song)
                        print('Song has opened in your browser.')
                    else:
                        print("No songs found matching your search.")

                elif user_input == 0:
                    print("Goodbye! Have a great day!")
                    break
                else:
                    print("Please enter a valid option (0 or 1).")

            except ValueError:
                print("Please enter a number (0 or 1).")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your client ID and secret are correct")
        print("2. When copying the redirect URL, include the entire URL with the code parameter")
        print("3. Use the URL before any additional redirects happen")

def  youtube_video_play(query):
    driver_path = r"C:\Users\KIIT0001\chromedriver-win64\chromedriver-win64\chromedriver.exe"  # location of driver path in  the pc
    service = Service(driver_path)  # tells python script to use this driver only
    driver = webdriver.Chrome(service=service)  # it opens the chrome using the driver

    driver.get("https://www.youtube.com")  # bot goes to youtube.com just like the typing browser manually

    time.sleep(2)  #

    search_box = driver.find_element(By.NAME, 'search_query')
    # This line says: “Hey bot, find the search bar on YouTube’s page.”

    # How? The HTML of the search bar has a name="search_query", and you’re using that to find it.

    search_box.send_keys(query)  # bot type the search query that we gave to in the terminal window
    search_box.send_keys(Keys.RETURN)  # it simlulates hitting the enter key just like we do after writing search query

    time.sleep(2)

    videos = driver.find_elements(By.ID, 'video-title')
    # This line collects all video titles from the search results.

    # find_elements returns a list of all matching videos
    driver.maximize_window()
    if videos:
        videos[1].click()      #REASON FOR THE SECOND VIDEO NOT THE FIRST VIDEO IS YOUTUBE YOUTUBE HAVE ADS IN THE FIRST INDEX
    else:
        print("No videos found")
        driver.quit()
        exit()
    # solved the issue of duration with the help of gpt , so the issue was I wanted the video play till it's duration then browser get automatically get's closed
    try:
        duration_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ytp-time-duration')))
        video_duration_text = duration_element.text.strip()

        print(f"Video dureation found:{video_duration_text}")

        if not video_duration_text:
            raise ValueError("No duration found(probably a live video)")

        def time_to_seconds(text):
            parts = text.split(":")
            parts = list(map(int, parts))
            if len(parts) == 2:
                minutes, seconds = parts
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hour, minutes, seconds = parts
                return hour * 3600 + minutes * 60 + seconds
            else:
                return 0

        total_seconds = time_to_seconds(video_duration_text)

        time.sleep(total_seconds + 5)
    except Exception as e:
        print(f"Special case found:{e}")
        print("waiting for 1 hour assuming it as a live session ")
        time.sleep(3600)

    driver.quit()
  # issue is all about ads  add nhi rahega then our bot will come again in

def chrome_opener(query):
    url = f"https://www.google.com/search?q={query}"

    # Replace this path with the actual path where Chrome is installed on your system
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # If you're on a 64-bit system and installed it from a different user account, try:
    # chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    if os.path.exists(chrome_path):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        webbrowser.get('chrome').open(url)
    else:
        print("Chrome path not found. Please check the path to chrome.exe.")



def weather(city):
    api_key = "53811063385dce4d7579485f2dd0e2c1"
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    parameter = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(base_url, params=parameter)
    data = response.json()
    if data["cod"] == 200:
        weather = data['weather'][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data['main']["humidity"]
        print(f"Weather in {city}")
        print(f"Today's temperature:{temperature}")
        print(f"Humidity:{humidity}")
        print(f"Weather description:{weather}")
    else:
        print("Your city data is not avalilable")


print("Hey buddy , This side Rudransh AI your helping hand.")
while True:
    print("Good morning buddy,How can I help you")
    a = str(input("Enter your response:"))
    if (a == "good morning"):
        print("Good morning mate")
    elif (a == "weather"):
        city = str(input("Enter you city:"))
        weather(city)
    elif (a == "open chrome"):
        user = str(input("What to do you want to search today:"))
        chrome_opener(user)
    elif(a=='bye'):
        print("Bye buddy see you soon!")
        break
    elif a=="open youtube":
        search_query = input("What do you want to play on the youtube:")
        youtube_video_play(search_query)
    elif a=="open spotify":
        music_player()
    elif a=="show date":
        today = date.today()
        print(f"Today's date is {today}")
    elif a=="show time":
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f"Current time :{current_time}")
    elif a=="show date and time":
        now = datetime.datetime.now()
        formatted_Date_Time = now.strftime("%Y-%m-%d %H:%M:%S")
        print(formatted_Date_Time)
    elif a=="wikipedia":
        search = input("What information do want to fetch today ?")
        w = wikipedia_search(search)
        print(w)













