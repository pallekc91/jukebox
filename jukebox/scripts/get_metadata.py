import pandas as pd
import os
import re 

def get_metadata(filename, database_path=r"../database.csv"):	
	
	filename = filename[::-1]
	_, info = filename.split("_")
	
	artist, name = info.split(" - ", 1)
	
	artist = artist[::-1]
	name = name[::-1]

	songs = pd.read_csv(database_path, engine='python')
	hits = songs[songs['Song Name'] == name]
	song = hits[hits['Artist'] == artist]
	
	if len(song) == 0:
		return 'unknown', 'unknown' , ''
	else:
		song = song.iloc[0]
		artist = '_'.join(artist.split())
		genre = '_'.join(re.split(' |/' , song["Genre(s)"])).lower()
		return  artist, genre, ''

for i, name in enumerate(os.listdir("/projectnb/textconv/jukebox/dataset/accompaniment")):
	print(name, get_metadata(name))

