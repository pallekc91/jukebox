import math
import os
import re

import librosa
import numpy as np
import pandas as pd

from torch.utils.data import Dataset

from jukebox.data.labels import Labeller
from jukebox.utils.dist_utils import print_all
from jukebox.utils.io import get_duration_sec, load_audio, load_midi


class FilesAudioDataset(Dataset):
    def __init__(self, hps, audio_database):
        super().__init__()
        self.sr = hps.sr
        self.channels = hps.channels
        self.min_duration = hps.min_duration or math.ceil(hps.sample_length / hps.sr)
        self.max_duration = hps.max_duration or math.inf
        self.sample_length = hps.sample_length
        assert hps.sample_length / hps.sr < self.min_duration, f'Sample length {hps.sample_length} per sr {hps.sr} ({hps.sample_length / hps.sr:.2f}) should be shorter than min duration {self.min_duration}'
        self.aug_shift = hps.aug_shift
        self.labels = hps.labels
        self.init_dataset(hps)
        self.songs = pd.read_csv(audio_database, engine='python')

        self.midi_paths = self.create_midi_paths(hps)

    def create_midi_paths(self, hps):
        base_dir, _ = os.path.split(hps.audio_files_dir)

        midi_dir = os.path.join(base_dir, "midi_files/")
        midi_paths = {}
        for path, subdirs, files in os.walk(midi_dir):
            for name in files:
                dir, artist = os.path.split(path)

                artist = '_'.join(artist.lower().split())
                song = '_'.join(name[:-4].lower().split())

                midi_paths[artist + ' - ' + song] = os.path.join(path, name)

        return midi_paths

    def filter(self, files, durations):
        # Remove files too short or too long
        keep = []
        for i in range(len(files)):
            if durations[i] / self.sr < self.min_duration:
                continue
            if durations[i] / self.sr >= self.max_duration:
                continue
            keep.append(i)
        print_all(f'self.sr={self.sr}, min: {self.min_duration}, max: {self.max_duration}')
        print_all(f"Keeping {len(keep)} of {len(files)} files")
        self.files = [files[i] for i in keep]
        self.durations = [int(durations[i]) for i in keep]
        self.cumsum = np.cumsum(self.durations)

    def init_dataset(self, hps):
        # Load list of files and starts/durations
        files = librosa.util.find_files(f'{hps.audio_files_dir}', ['mp3', 'opus', 'm4a', 'aac', 'wav'])
        print_all(f"Found {len(files)} files. Getting durations")
        # cache = dist.get_rank() % 8 == 0 if dist.is_available() else True
        cache = True
        durations = np.array([get_duration_sec(file, cache=cache) * self.sr for file in files])  # Could be approximate
        self.filter(files, durations)

        if self.labels:
            self.labeller = Labeller(hps.max_bow_genre_size, hps.n_tokens, self.sample_length, v3=hps.labels_v3)

    def get_index_offset(self, item):
        # For a given dataset item and shift, return song index and offset within song
        #print('item:', item)
        half_interval = self.sample_length // 2
        shift = np.random.randint(-half_interval, half_interval) if self.aug_shift else 0
        #print(item)
        offset = item * self.sample_length + shift  # Note we centred shifts, so adding now
        midpoint = offset + half_interval
        #print('item:', item)
        #print('half_interval:', half_interval)
        #print('shift:', shift)
        #print('offset:', offset)
        #print('midpoint:', midpoint)
        assert 0 <= midpoint < self.cumsum[-1], f'Midpoint {midpoint} of item beyond total length {self.cumsum[-1]}'
        index = np.searchsorted(self.cumsum, midpoint)  # index <-> midpoint of interval lies in this song
        start, end = self.cumsum[index - 1] if index > 0 else 0.0, self.cumsum[index]  # start and end of current song
        assert start <= midpoint <= end, f"Midpoint {midpoint} not inside interval [{start}, {end}] for index {index}"
        if offset > end - self.sample_length:  # Going over song
            offset = max(start, offset - half_interval)  # Now should fit
        elif offset < start:  # Going under song
            offset = min(end - self.sample_length, offset + half_interval)  # Now should fit
        assert start <= offset <= end - self.sample_length, f"Offset {offset} not in [{start}, {end - self.sample_length}]. End: {end}, SL: {self.sample_length}, Index: {index}"
        offset = offset - start
        return index, offset

    def get_metadata(self, filename, test):
        """
        Insert metadata loading code for your dataset here.
        If artist/genre labels are different from provided artist/genre lists,
        update labeller accordingly.

        Returns:
            (artist, genre, full_lyrics) of type (str, str, str). For
            example, ("unknown", "classical", "") could be a metadata for a
            piano piece.
        """
        filename = filename.split('/')[-1]
        filename = filename[::-1]
        _, info = filename.split("_", 1)
        artist, name = info.split(" - ", 1)
        artist = artist[::-1]
        name = name[::-1]
        hits = self.songs[self.songs['Song Name'] == name]
        song = hits[hits['Artist'] == artist]

        if len(song) == 0:
            return 'unknown', 'unknown', ''
        else:
            song = song.iloc[0]
            artist = artist = '_'.join(artist.split())
            genre = '_'.join(re.split(' |/', song["Genre(s)"])).lower()
            return artist, genre, ''

    def get_song_chunk(self, index, offset, test=False):
        filename, total_length = self.files[index], self.durations[index]
        data, sr = load_audio(filename, sr=self.sr, offset=offset, duration=self.sample_length)
        assert data.shape == (
            self.channels, self.sample_length), f'Expected {(self.channels, self.sample_length)}, got {data.shape}'
        if self.labels:
            artist, genre, lyrics = self.get_metadata(filename, test)
            labels = self.labeller.get_label(artist, genre, lyrics, total_length, offset)
            midi = self.get_midi_chunk(index, offset)
            return (data.T, labels['y'], midi)
        else:
            return data.T

    def get_item(self, item, test=False):
        index, offset = self.get_index_offset(item)
        return self.get_song_chunk(index, offset, test)

    def __len__(self):
        return int(np.floor(self.cumsum[-1] / self.sample_length))

    def __getitem__(self, item):
        return self.get_item(item)

    def get_midi_chunk(self, index, offset):
        filename, total_length = self.files[index], self.durations[index]
        filename = os.path.split(filename)[1]
        info = filename[:-18][::-1]
        artist, song = info.split(" - ", 1)

        artist = '_'.join(artist[::-1].lower().split())
        song = '_'.join(song[::-1].lower().split())
        midi_path = self.midi_paths[artist + ' - ' + song]

        if not os.path.exists(midi_path):
            raise RuntimeError("IT FAILED")
        return load_midi(midi_path, sr=self.sr, offset=offset, duration=self.sample_length)



