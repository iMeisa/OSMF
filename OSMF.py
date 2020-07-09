import os
import json
import operator

login_name = os.getlogin()

song_path = f'C:\\Users\\{login_name}\\AppData\\Local\\osu!\\Songs'

custom_param = input('Set custom bpm? [y/N] ') in 'yY'

if not custom_param:
	min_bpm = 140
	max_bpm = 9999
else:
	min_bpm = int(input('Min BPM (Whole number): '))
	max_bpm = int(input('Max BPM (Whole number): '))

open('StreamMaps.txt', 'w')
map_count = 1
for folder in os.listdir(song_path):
	if os.path.isdir(os.path.join(song_path, folder)):
		for file in os.listdir(os.path.join(song_path, folder)):
			if file.endswith('.osu'):
				raw_map = open(os.path.join(song_path, folder, file), 'r', encoding='utf8').readlines()

				if raw_map[0] == 'osu file format v14\n':

					try:
						timing_points_index = raw_map.index('[TimingPoints]\n')
						objects_index = raw_map.index('[HitObjects]\n')
						metadata_index = raw_map.index('[Metadata]\n')

						beatmap = {'bpm':
							  		{'default': {'time': 0, 'bpm': 0, 'beatLength': 0}, 'changes': []}
							  	}

						for i in range(metadata_index + 1, len(raw_map)):
							if raw_map[i] == '\n':
								break

							if raw_map[i].startswith('Title:'):
								beatmap['title'] = raw_map[i][6:-1]
							if raw_map[i].startswith('Artist:'):
								beatmap['artist'] = raw_map[i][7:-1]
							if raw_map[i].startswith('Version:'):
								beatmap['difficulty'] = raw_map[i][8:-1]

						# Determine BPM and BPM changes
						for i in range(timing_points_index + 1, len(raw_map)):
							if raw_map[i] == '\n':
								break

							point = raw_map[i].split(',')
							try:
								time = int(point[0])
							except:
								print('idk')
							try:
								beatLength = float(point[1])
							except:
								print('still dunno')
							if beatLength > 0:
								default_bpm = beatmap['bpm']['default']
								bpm = str(int(60000 // beatLength))
								if default_bpm['bpm'] == 0:
									default_bpm['time'] = time
									default_bpm['bpm'] = bpm
									default_bpm['beatLength'] = beatLength
								else:
									beatmap['bpm']['changes'].append({'time': time, 'bpm': bpm, 'beatLength': beatLength})

						first_object = objects_index + 1
						previous_object = {'time': 0, 'x': 0, 'y':0}
						current_bpm = beatmap['bpm']['default']['bpm']
						whole = beatmap['bpm']['default']['beatLength']
						half = whole / 2
						quarter = half / 2


						def adjust_beat_length(beat_length, new_bpm):
							global current_bpm
							global whole
							global half
							global quarter

							current_bpm = new_bpm
							whole = beat_length
							half = whole / 2
							quarter = half / 2


						quarter_note_count = 1
						note_start_time = 0
						burst_count = 0
						stream_count = {}
						total_stream_notes = 0
						longest_stream = 0
						for i in range(first_object, len(raw_map)):
							raw_hit_object = raw_map[i].split(',')
							if i != len(raw_map) - 1:
								next_raw_hit_object = raw_map[i + 1].split(',')
							else:
								next_raw_hit_object = '000'

							hit_object = {'time': int(raw_hit_object[2]), 'x': int(raw_hit_object[0]), 'y': int(raw_hit_object[1])}

							changes = beatmap['bpm']['changes']
							for change in changes:
								time_change = change['time']
								new_beatlength = change['beatLength']
								new_bpm = change['bpm']
								if time_change < previous_object['time']:
									continue
								elif hit_object['time'] >= time_change:
									adjust_beat_length(new_beatlength, new_bpm)
									break

							# Determine if quarter length
							if i != first_object:
								time_difference = hit_object['time'] - previous_object['time']
								if quarter - 2 < time_difference < quarter + 2:
									quarter_note_count += 1
									if note_start_time == 0:
										note_start_time = hit_object['time']

								else:
									# Declare if stream
									if 3 < quarter_note_count < 6:
										burst_count += 1
										total_stream_notes += quarter_note_count
									elif quarter_note_count >= 6:
										if current_bpm in stream_count:
											stream_count[current_bpm] += 1
										else:
											stream_count[current_bpm] = 1
										total_stream_notes += quarter_note_count

									if quarter_note_count > longest_stream:
										longest_stream = quarter_note_count
									quarter_note_count = 1
									note_start_time = 0

							previous_object = hit_object

						if len(stream_count) > 0:
							main_bpm = int(max(stream_count.items(), key=operator.itemgetter(1))[0])
						else:
							main_bpm = int(beatmap['bpm']['default']['bpm'])

						total_streams = 0
						for bpm in stream_count:
							total_streams += stream_count[bpm]

						print(f'Map #{map_count}: {beatmap["artist"]} - {beatmap["title"]} [{beatmap["difficulty"]}]')
						total_object_count = len(raw_map) - first_object
						try:
							stream_percentage = total_stream_notes / total_object_count * 100
						except:
							stream_percentage = 0

						if stream_percentage >= 25 and main_bpm >= min_bpm and main_bpm <= max_bpm:
							with open('StreamMaps.txt', 'a') as f:
								f.write(f'{beatmap["artist"]} - {beatmap["title"]} [{beatmap["difficulty"]}] | Main BPM: {main_bpm} | Total Streams: {total_streams} ({int(stream_percentage)}% Streams)\n')

						map_count += 1
					except:
						print('idk')

stream_maps = open('StreamMaps.txt', 'r').readlines()
print(f'Found {len(stream_maps)} stream maps')

os.system('pause')
