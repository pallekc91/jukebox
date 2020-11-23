import pretty_midi
import os
import numpy as np


dt = 0.25
def sec_to_idx(t, dt=0.25):
	return int(t/dt)


def load_midi(path, dt=0.25):
	midi_format = pretty_midi.PrettyMIDI(path)

	duration = midi_format.get_end_time()
	info = np.zeros((len(midi_format.instruments), int(duration/dt) + 1, 200))
	for i, instrument in enumerate(midi_format.instruments):
		for note in instrument.notes:
			start = sec_to_idx(note.start)
			end = sec_to_idx(note.end)
			
			if start == end:
				info[i, start, note.pitch] = note.velocity
			else:
				info[i, start:end, note.pitch] = note.velocity
			
			print(note, note.start, note.end, start, end, note.pitch) 
			

	print("Number of instruments:", len(midi_format.instruments))
	print("Midi Length (sec):", duration)
	print("time step (dt):", dt)
	print("Midi Length (idx):", sec_to_idx(duration))
	print("Matrix Shape (before averaging across instruements) :",info.shape)
	 
	info = np.average(info, axis=0)
	print("Matrix Shape (after averaging across instruements) :", info.shape)

	return info

midi_path = "/projectnb/textconv/jukebox/MidiDataset/Cleaned/acdc/Jack.mid"
info = load_midi(midi_path)

print("notes at time = 330s")
a = sec_to_idx(330)
b = sec_to_idx(331)
print(a, b)
for i, row in enumerate(info[a:b]):
	notes = []
	for j, val in enumerate(row):
		if val != 0:
			notes.append((j, val))
	print(i, *notes, sep = ' ')


print(info)
