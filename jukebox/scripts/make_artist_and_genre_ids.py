import pandas as pd
import re

songs = pd.read_csv(r"../database.csv", engine='python')

all_artists = set()
all_genres = set()

for index, song in songs.iterrows():

	genre = '_'.join(re.split(' |/' ,song["Genre(s)"]))
	all_genres.add(genre.lower())
	
	artist = '_'.join(song["Artist"].split())
	all_artists.add(artist.lower())

with open("artist_ids.txt", "w") as text_file:
	print('unknown' + ";" + '0' , file=text_file)
	
	for i, artist in enumerate(all_artists):
		print(artist + ";" + str(i + 1) , file=text_file)  

with open("genre_ids.txt", "w") as text_file:
	print('unknown' + ";" + '0' , file=text_file)

	for i, genre in enumerate(all_genres):
		print(genre + ";" + str(i + 1), file=text_file)
