#!/usr/bin/env python3


__author__ = "Nils Amiet"


import subprocess
import argparse
import json
import math
import os
import tempfile
import textwrap

from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy



class MediaInfo():
	"""Collect information about a video file"""

	def __init__(self, path, verbose=True):
		self.probe_media(path)
		self.find_video_stream()
		self.compute_display_resolution()
		self.compute_format()

		if verbose:
			print(self.filename)
			print("%sx%s" % (self.sample_width, self.sample_height))
			print("%sx%s" % (self.display_width, self.display_height))
			print(self.duration)
			print(self.size)


	def probe_media(self, path):
		ffprobe_command = [
		"ffprobe",
		"-v", "quiet",
		"-print_format", "json",
		"-show_format",
		"-show_streams",
		path
		]

		output = subprocess.check_output(ffprobe_command)
		self.ffprobe_dict = json.loads(output.decode("utf-8"))


	def human_readable_size(self, num, suffix='B'):
		for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
			if abs(num) < 1024.0:
				return "%3.1f %s%s" % (num, unit, suffix)
			num /= 1024.0
		return "%.1f %s%s" % (num, 'Yi', suffix)


	def find_video_stream(self):
		for stream in self.ffprobe_dict["streams"]:
			try:
				if stream["codec_type"] == "video":
					self.video_stream = stream
			except:
				pass


	def compute_display_resolution(self):
		width = int(self.video_stream["width"])
		height = int(self.video_stream["height"])
		self.sample_width = width
		self.sample_height = height
		sample_aspect_ratio = self.video_stream["sample_aspect_ratio"]

		if sample_aspect_ratio is not "1:1":
			sample_split = sample_aspect_ratio.split(":")
			sw = int(sample_split[0])
			sh = int(sample_split[1])

			self.display_width = int(width * sw / sh)
			self.display_height = int(height)
		else:
			self.display_width = width
			self.display_height = height


	def compute_format(self):
		format_dict = self.ffprobe_dict["format"]
		
		self.duration_seconds = float(format_dict["duration"])
		self.duration = self.pretty_duration(self.duration_seconds)		

		self.filename = os.path.basename(format_dict["filename"])
		
		size_bytes = int(format_dict["size"])
		self.size = self.human_readable_size(size_bytes)


	def pretty_duration(self, seconds):
		hours = math.floor(seconds / 3600)
		remaining_seconds = seconds - 3600 * hours

		minutes = math.floor(remaining_seconds / 60)
		remaining_seconds = round(remaining_seconds - 60 * minutes)

		duration = ""

		if hours > 0:
			duration +=  "%s:" % (hours,)

		duration += "%s:%s" % (str(minutes).zfill(2), str(remaining_seconds).zfill(2))
		return duration

	def desired_size(self, width=600):
		ratio = width / self.display_width
		desired_height = math.floor(self.display_height * ratio)
		return (width, desired_height)




class MediaCapture():
	"""Capture frames of a video"""

	def __init__(self, path):
		self.path = path


	def make_capture(self, time, width, height, out_path="out.jpg"):

		# TODO if capture fails, retry using slow seek mode (-ss after -i)
		ffmpeg_command = [
		"ffmpeg",
		"-ss", time,
		"-i", self.path,
		"-vframes", "1",
		"-s", "%sx%s" % (width, height),
		out_path
		]

		subprocess.call(ffmpeg_command)


	def compute_blurriness(self, image_path):
		i = Image.open(image_path)
		i = i.convert('L') #convert to grayscale
		
		a = numpy.asarray(i)
		b = abs(numpy.fft.rfft2(a))
		max_freq = self.avg9x(b)

		return 1/max_freq


	def avg9x(self, matrix):
		xs = matrix.flatten()
		srt = sorted(xs, reverse=True)
		percentage = 0.05
		length = math.floor(percentage * len(srt))

		return numpy.median(srt[:length])



	def max_freq(self, matrix):
		m = 0
		for row in matrix:
			mx = max(row)
			if mx > m:
				m = mx

		return m
		

# TODO make these values program arguments
def select_sharpest_images(
	media_info,
	media_capture,
	num_samples=21,
	num_groups=4,
	num_selected=3,
	start_delay_seconds=5,
	end_delay_seconds=5,
	width=None,
	height=None
	):
	# compute list of timestamps (equally distributed)

	delay = start_delay_seconds + end_delay_seconds
	capture_interval = math.floor((media_info.duration_seconds - delay) / num_samples)
	end = int(media_info.duration_seconds - end_delay_seconds)

	def timestamps():
		for i in range(start_delay_seconds, end, capture_interval):
			yield (i, media_info.pretty_duration(i))


	for timestamp in timestamps():
		print(timestamp)


	# compute desired_size
	if not width and not height:
		# TODO make this a program argument
		width = 600
		desired_size = media_info.desired_size(width=width)
		height = desired_size[1]

	blurs = []
	for timestamp in timestamps():
		filename = tempfile.mkstemp()[1] + ".png"

		media_capture.make_capture(
			timestamp[1],
			width,
			height,
			filename)
		blurriness = media_capture.compute_blurriness(filename)

		blurs += [(filename, blurriness, timestamp[0])]


	time_sorted = sorted(blurs, key=lambda x: x[2])

	# group into num_selected groups
	group_size = math.ceil(len(time_sorted)/num_groups)
	groups = chunks(time_sorted, group_size)

	# find top sharpest for each group
	selected_items = [best(x) for x in groups]

	selected_items = sorted(selected_items, key=lambda x: x[1])[:num_selected]

	for filename, score, timestamp in selected_items:
		print(filename, score, timestamp)

	return selected_items


def best(captures):
	return sorted(captures, key=lambda x: x[1])[0]


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]

def compose_contact_sheet(media_info, frames, output_path=None):
	num_frames = len(frames)
	# TODO make this a program argument
	width = 600

	desired_size = media_info.desired_size(width=width)
	loaded_frames = [Image.open(path) for path, x, y in frames]

	vertical_spacing = 5
	height = num_frames * (desired_size[1] + vertical_spacing) - vertical_spacing


	
	

	max_line_length = 96
	header_lines = []
	header_lines += textwrap.wrap(media_info.filename, max_line_length)
	header_lines += ["File size: %s" % media_info.size]
	header_lines += ["Duration: %s" % media_info.duration]
	header_lines += ["Dimensions: %sx%s" % (media_info.sample_width, media_info.sample_height)]

	dejavu_sans_path = "/usr/share/fonts/TTF/DejaVuSans.ttf"
	font = ImageFont.truetype(dejavu_sans_path, 10)

	background = (255, 255, 255)
	header_line_height = 12
	header_margin = 10
	header_height = 2 * header_margin + len(header_lines) * header_line_height
	image = Image.new("RGB", (width, height + header_height), background)
	draw = ImageDraw.Draw(image)

	h = header_margin
	color = (0, 0, 0, 255)
	for line in header_lines:
		draw.text((header_margin, h), line, font=font, fill=color)
		h += header_line_height

	h = header_height
	for frame in loaded_frames:
		image.paste(frame, (0, h))
		h += desired_size[1] + vertical_spacing

	if not output_path:
		output_path = media_info.filename + ".png"
	image.save(output_path)







def main():
	parser = argparse.ArgumentParser(description="Create a video contact sheet")
	parser.add_argument("filename")
	parser.add_argument("-o", "--output",
		help="save to output file",
		dest="output_path")
	parser.add_argument("-v", "--verbose",
		action="store_true",
		help="display verbose messages",
		dest="is_verbose")
	args = parser.parse_args()

	path = args.filename
	output_path = args.output_path

	media_info = MediaInfo(path, verbose=True)
	media_capture = MediaCapture(path)

	frames = select_sharpest_images(media_info, media_capture)

	# TODO compose contact sheet in mxn tile using frames

	# TODO add media info on top or bottom (optional), TOP for now

	compose_contact_sheet(media_info, frames, output_path)


	





if __name__ == "__main__":
	main()