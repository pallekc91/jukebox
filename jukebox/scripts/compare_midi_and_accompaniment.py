import os
import av
import pretty_midi
	
base_dir = "/projectnb/textconv/jukebox/dataset/"
accompaniment_dir = os.path.join(base_dir, "accompaniment/")
midi_dir = os.path.join(base_dir, "midi_files/")

midi_paths = {}
acc_paths = {}

for path, subdirs, files in os.walk(midi_dir):
	for name in files:
			
		dir, artist = os.path.split(path)		
		
		artist = '_'.join(artist.lower().split())
		song =  '_'.join(name[:-4].lower().split())
		
		midi_paths[artist + ' - ' + song] = os.path.join(path, name)

for acc_path in os.listdir(accompaniment_dir):
	if acc_path[-3:] != 'wav':
		continue
	else:
		info = acc_path[:-18][::-1]
		artist, song = info.split(" - ", 1)
		
		artist = '_'.join(artist[::-1].lower().split())
		song = '_'.join(song[::-1].lower().split())		

		acc_paths[artist + ' - ' + song] = os.path.join(accompaniment_dir, acc_path)

def get_wav_duration_sec(file, cache=False):
    try:
        with open(file + '.dur', 'r') as f:
            duration = float(f.readline().strip('\n'))
        return duration
    except:
        container = av.open(file)
        audio = container.streams.get(audio=0)[0]
        duration = audio.duration * float(audio.time_base)
        if cache:
            with open(file + '.dur', 'w') as f:
                f.write(str(duration) + '\n')
        return duration

def get_midi_duration_sec(file):
	try:
		midi_format = pretty_midi.PrettyMIDI(file)
		return midi_format.get_end_time()

	except:
		raise Exception("Midi Failure")


anomaly_dir = "/projectnb/textconv/jukebox/dataset/anomalies"
anomaly_acc_dir = os.path.join(anomaly_dir, "accompaniment/")
anomaly_midi_dir = os.path.join(anomaly_dir, "midi")

failure_dir = "/projectnb/textconv/jukebox/dataset/failures"
failure_acc_dir = os.path.join(failure_dir, "accompaniment/")
failure_midi_dir = os.path.join(failure_dir, "midi")

failures, anomalies = [], []
for k, v in acc_paths.items():
	
	try:
		wav_dur = get_wav_duration_sec(v)
		midi_dur = get_midi_duration_sec(midi_paths[k])
		
		diff = wav_dur - midi_dur
		if diff < 0:
			diff = -diff
		if diff > 60:
			print("found anomaly")
			dir, name = os.path.split(midi_paths[k])
			dir, artist = os.path.split(dir)
		
			new_artist_dir = os.path.join(anomaly_midi_dir, artist)	
			if not os.path.exists(new_artist_dir):
				os.makedirs(new_artist_dir)
			
			new_midi_path = os.path.join(new_artist_dir, name)
			
			os.rename(midi_paths[k], new_midi_path)
			
			temp_dir, name = os.path.split(v)
			new_acc_path = os.path.join(anomaly_acc_dir, name)
			os.rename(v, new_acc_path)
			anomalies.append(k)

	except:
		dir, name = os.path.split(midi_paths[k])
		dir, artist = os.path.split(dir)

		new_artist_dir = os.path.join(failure_midi_dir, artist)
		if not os.path.exists(new_artist_dir):
			os.makedirs(new_artist_dir)

		new_midi_path = os.path.join(new_artist_dir, name)
		
		os.rename(midi_paths[k], new_midi_path)

		temp_dir, name = os.path.split(v)
		new_acc_path = os.path.join(failure_acc_dir, name)
		os.rename(v, new_acc_path)
		failures.append(k)

print("Anomalies")
print("Count:", len(anomalies))
print(*anomalies, sep ='\n')
print()
print()

print("Failures")
print("Count:", len(failures))
print(*failures, sep ='\n')

