import json
import time
from datetime import timedelta,datetime,date
import psycopg2
from psycopg2 import sql
from email_validator import validate_email, EmailNotValidError

 #Connection to database
connection = psycopg2.connect(
    dbname="Demo",
    user="postgres",
    password="Meet@2712",
    host="localhost",
    port="5432"
)
curr = connection.cursor()

try:
    # read file from Songs.json as file and store data in spotify_json
    with open("Songs.json", 'r') as file:
        spotify_json = json.load(file)
except FileNotFoundError:
    print("file Songs.json is not found.")
    exit()

# create function for convert duration time from millisecond to minutes
def duration_time(ms):
    t = timedelta(milliseconds= ms)
    min = int(t.seconds / 60)
    sec = int(t.seconds % 60)
    return f"{min}:{sec:02d}"

#creating empty list
genre_names = []

# Validate playlist details
def is_valid_playlist(playlist_data):
    input_playlist_name = playlist_data['playlist_name']
    input_description = playlist_data['description']
    input_username = playlist_data['creator']['username']
    email = playlist_data['creator']['email']
    return all([is_valid_alpha(input_playlist_name),
                is_valid_alpha(input_description),
                is_valid_username(input_username),
                is_valid(email)])

# Validate track details
def is_valid_track(track):
    input_trackName = track['track_name']
    input_artist = track['artist']
    input_albumName = track['album']['name']
    input_date = track['album']['release_date']
    input_popularity = track['popularity']
    input_durationtime = track['duration_ms']
    return all([is_valid_special_character(input_trackName),
                is_valid_alpha(input_artist),
                is_valid_special_character(input_albumName),
                is_valid_date(input_date),
                is_valid_durationtime(input_durationtime),
                is_valid_popularity(input_popularity)])

# Validate all json details
def is_valid_json(spotify_json):
    for playlist_data in spotify_json:
        if is_valid_playlist(playlist_data):
            for track in playlist_data['tracks']:
                if is_valid_track(track):
                    pass
                else:
                    print("Validation failed for track details.")
                    return False
        else:
            print("Validation failed for playlist details.")
            return False
    return True

# function for validating release_date
def is_valid_date(input_date):
    try:
        dateObject = datetime.strptime(input_date, "%Y-%m-%d")
        if dateObject.date() <= date.today():
            return True
        else:
            # raise ValueError("Date cannot be in the future")
            print(f"Date cann't be in the future ' {input_date} ', enter past or present date.")
            return False
    except ValueError:
        # raise ValueError("Incorrect date formate for , it should be YYYY-MM-DD")
        print(f"Incorrect date formate for ' {input_date} ', it should be YYYY-MM-DD")
        return False

# function for validating popularity
def is_valid_popularity(input_popularity):
    try:
        # check if popularity is intger or not
        if input_popularity == int(input_popularity):
            # Check if popularity is in between 0 - 100
            if 0 <= input_popularity <= 100:
                return True
            else:
                print(f"Popularity ' {input_popularity} ' must be in between 0 to 100.")
                return False
        else:
            print(f"Popularity ' {input_popularity} ' must be in integer.")
            return False
    except ValueError:
        print(f"Popularity ' {input_popularity} ' must be in integer and must be in between 0 to 100. .")
        return False


# function for validating duration_time
def is_valid_durationtime(input_durationtime):
    try:
        # check if duration time is intger or not
        if input_durationtime == int(input_durationtime):
            # Check if duration is greater than or equal to 100000
            if input_durationtime >= 100000:
                return True
            else:
                print(f"Duration time ' {input_durationtime} ' must be >= 100000")
                return False
        else:
            print(f"Duration time ' {input_durationtime} ' must be an integer.")
            return False
    except ValueError:
        print(f"Duration time ' {input_durationtime} ' must be an integer and >=100000.")
        return False

# create function to validate the value(must be alphabet and space)
def is_valid_alpha(input_data):
    input_dec = input_data.replace('.', '')
    # Check if description contains only alphabets and spaces
    if input_dec.replace(' ', '').isalpha():
        if len(input_dec) >= 6:
            return True
        else:
            print(f"Length of  ' {input_data} ' must be >=6.")
            return False
    else:
        print(f" ' {input_dec} ' must contain only alphabets and spaces.")
        return False

# create function to validate the value(must be alphabet, space and punctuation)
def is_valid_special_character(input_data):
    # Check if description contains only alphabets,special character(punctuation) and spaces
    if input_data.isascii():
        if len(input_data) >= 6:
            return True
        else:
            print(f"Length of  ' {input_data} ' must be >=6.")
            return False
    else:
        print(f" ' {input_data} ' must contain alphabets,punctuation and spaces.")
        return False

# Validating the value of playlist username
def is_valid_username(input_data):
    input_under = input_data.replace('_', '')
    # Check if username contains only alphabets, numbers, and underscores
    if input_under.isalnum():
        if len(input_under) >= 6:
            return True
        else:
            print(f"Length of Username ' {input_data} ' must be >=6.")
            return False
    else:
        print(f"Username ' {input_data} ' must contain only alphabets, numbers, or underscores.")
        return False

# Validating the value of paylist Email
def is_valid(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

 # inserting value in table if and only all details are true
if is_valid_json(spotify_json):
    for playlist_data in spotify_json:
        # Insert values from the  json data to playlist  table  in database
        try:
            curr.execute(sql.SQL("""
                INSERT INTO playlist (playlist_name, description, creator_username, creator_email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (playlist_name, creator_username) DO NOTHING
                """),
                (
                    playlist_data['playlist_name'],
                    playlist_data['description'],
                    playlist_data['creator']['username'],
                    playlist_data['creator']['email']
                ))
        except psycopg2.Error as e:
            print("Error occur while inserting in playlist table", e)

        #Insert values from the  json data to track  table  in database

        for track in playlist_data['tracks']:
            genres_str = ','.join(track['genres'])
            try:
                curr.execute(
                    sql.SQL("SELECT playlist_id FROM playlist WHERE playlist_name = %s AND creator_username = %s"),
                    (playlist_data['playlist_name'], playlist_data['creator']['username'])
                )
                result = curr.fetchone()
                playlist_id = result[0] if result else None

                if playlist_id is not None:
                    # Insert album data into the album table
                    curr.execute(sql.SQL("""
                               INSERT INTO album (name, release_date)
                               VALUES (%s, %s)
                               ON CONFLICT DO NOTHING
                           """), (
                        track['album']['name'],
                        track['album']['release_date']
                    ))
                    # Get the album_id
                    curr.execute(sql.SQL("""
                               SELECT album_id FROM album
                               WHERE name = %s AND release_date = %s
                           """), (
                        track['album']['name'],
                        track['album']['release_date']
                    ))
                    album_id = curr.fetchone()[0]

                    #insert value into track table
                    curr.execute(sql.SQL("""
                        INSERT INTO track (track_name,playlist_id, artist, album_name, release_date, duration_time, popularity, genres, explicit_content, album_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (track_name, artist) DO NOTHING
    
                        """),
                        (
                            track['track_name'],
                            playlist_id,
                            track['artist'],
                            track['album']['name'],
                            track['album']['release_date'],
                            duration_time(track['duration_ms']),
                            track['popularity'],
                            genres_str,
                            track['explicit_content'],
                            album_id
                        ))
                    # track_id retrieve
                    curr.execute(sql.SQL("""
                                SELECT track_id FROM track
                                WHERE track_name = %s AND artist = %s
                            """), (
                        track['track_name'],
                        track['artist']
                    ))
                    track_id = curr.fetchone()[0]
            except psycopg2.Error as e:
                print("Error occur while inserting data in track table", e)
        # Extract genre names from the JSON data
        for track in playlist_data['tracks']:
            genre_names.extend(track['genres'])

        # Remove duplicate genre
        genre_names = list(set(genre_names))

        # Insert genre names into the genre table
        for genre_name in genre_names:
            try:
                curr.execute(sql.SQL("""
                    INSERT INTO genre (genre_name)
                    VALUES (%s)
                    ON CONFLICT (genre_name) DO NOTHING
                     """), (genre_name,))
                # genre_id retrieve
                curr.execute(sql.SQL("""
                                INSERT INTO track_genres (track_id, genre_id)
                                SELECT %s, genre_id FROM genre
                                WHERE genre_name = %s
                            """), (
                    track_id,
                    genre_name
                ))
            except psycopg2.Error as e:
                print("Error occur while inserting data in genres table", e)
else:
    print("validation failed.")

time.sleep(1)

connection.commit()

# Close the cursor and connection
curr.close()
connection.close()