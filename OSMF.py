import os
import json
import operator

login_name = os.getlogin()

song_path = f'C:\\Users\\{login_name}\\AppData\\Local\\osu!\\Songs'

open('StreamMaps.txt', 'w')
map_count = 1
for folder in os.listdir(song_path):
	for file in os.listdir(os.path.join(song_path, folder)):
		if file.endswith('.osu'):
			# print(f'Checking: {os.path.join(song_path, folder, file)}')
			raw_map = open(os.path.join(song_path, folder, file), 'r', encoding='utf8').readlines()

			if raw_map[0] == 'osu file format v14\n':

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
					# print(point, 'Line:', i)
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

				# print(json.dumps(beatmap, indent=4))

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
				double_count = 0
				triple_count = 0
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

					# Object type
					if raw_hit_object[5][0] in ['B', 'L']:
						object_type = 'Slider'
					elif len(raw_hit_object) == 7:
						object_type = 'Spinner'
					else:
						object_type = 'Circle'

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
							# print(f'Changed BPM to {whole} at {hit_object["time"]}')
							# print(f'New quarter time: {quarter}')
							break

					# Determine if quarter length
					if i != first_object:
						time_difference = hit_object['time'] - previous_object['time']
						next_time_dif = int(next_raw_hit_object[2]) - hit_object['time']
						if quarter - 2 < time_difference < quarter + 2:
							quarter_note_count += 1
							if note_start_time == 0:
								note_start_time = hit_object['time']
							# if object_type == 'Slider':
							# 	print(object_type)
						else:
							note_time_minutes = note_start_time // 60000
							compact_note_time = f'{note_time_minutes}m {note_start_time // 1000 - (note_time_minutes * 60)}s'
							# Declare if stream
							if quarter_note_count == 2:
								double_count += 1
								# print(f'{compact_note_time}: Double')
							elif quarter_note_count == 3:
								triple_count += 1
								# print(f'{compact_note_time}: Triple')
							elif 3 < quarter_note_count < 6:
								burst_count += 1
								total_stream_notes += quarter_note_count
								# print(f'{compact_note_time}: Burst')
							elif quarter_note_count >= 6:
								if current_bpm in stream_count:
									stream_count[current_bpm] += 1
								else:
									stream_count[current_bpm] = 1
								total_stream_notes += quarter_note_count
								# print(f'{compact_note_time}: Stream | Notes: {quarter_note_count}')

							if quarter_note_count > longest_stream:
								longest_stream = quarter_note_count
							quarter_note_count = 1
							note_start_time = 0

							# Print note after stream
							# if not quarter - 2 < next_time_dif < quarter + 2:
							# 	if object_type == 'Slider':
							# 		print(object_type)
							# 	elif object_type == 'Spinner':
							# 		print(object_type)
							# 	elif half - 1 < time_difference < whole:
							# 		print('Jump')
							# 	else:
							# 		print(object_type)
					# else:
					# 	print(object_type)
					previous_object = hit_object

				total_streams = 0
				if len(stream_count) > 0:
					main_bpm = int(max(stream_count.items(), key=operator.itemgetter(1))[0])
				else:
					main_bpm = int(beatmap['bpm']['default']['bpm'])

				for bpm in stream_count:
					total_streams += stream_count[bpm]

				print(f'Map #{map_count}: {beatmap["artist"]} - {beatmap["title"]} [{beatmap["difficulty"]}]')
				total_object_count = len(raw_map) - first_object
				# print(f'{total_stream_notes}(total_stream_notes) / {total_object_count}(total_object_count) * 100')
				try:
					stream_percentage = total_stream_notes / total_object_count * 100
				except:
					stream_percentage = 0
				# print(f'Stream Percentage: {stream_percentage}%')
				# print(f'''\nTotal Object Count: {total_object_count}
				# Doubles: {double_count}
				# Triples: {triple_count}
				# Bursts: {burst_count}
				# Streams: {json.dumps(stream_count)}
				# \tAverage Stream Length: {total_stream_notes / total_streams}
				# \tLongest Stream: {longest_stream}''')

				if stream_percentage >= 25 and main_bpm >= 140:
					with open('StreamMaps.txt', 'a') as f:
						f.write(f'{beatmap["artist"]} - {beatmap["title"]} [{beatmap["difficulty"]}] | Main BPM: {main_bpm} | Total Streams: {total_streams} ({int(stream_percentage)}% Streams)\n')

				map_count += 1

stream_maps = open('StreamMaps.txt', 'r').readlines()
print(f'Found {len(stream_maps)} stream maps')

os.system('pause')
