#!/usr/bin/env python3
'''
@author: pjnozisk
'''

import sys

class ANSIColor(object):
	"""
	Forms colored text using an Xterm-compatible
	ANSI escape sequence for a foreground color

	"""
	ansi_colors = {
		"red" :  "\033[31m",
		"magenta" : "\033[35m",
		"yellow" : "\033[33m",
		"green" : "\033[32m",
		"cyan" :  "\033[36m",
		"blue" :  "\033[34m",
		"white" : "\033[37m",
		"black" : "\033[30m",
		"bright_green" : "\033[92m",
		"bright_blue" : "\033[94m"

	}
	__color_reset = "\033[0m"

	def __init__(self, color, *args):
		"""
		:ivar color: ANSI color name
		:ivar args: variable text arguments
		:vartype color: str
		:vartype args: tuple
		"""
		self.color = color
		if not self.color in self.ansi_colors:
			raise ValueError('Invalid ANSI color {}'.format(color))
		self.text = ' '.join(args)
		if sys.stdout.isatty():
			self.text = self.ansi_colors[color] + self.text + self.__color_reset

	def __repr__(self):
		return self.text

class RGBColor(object):
	"""
	Forms colored text using an Xterm-compatible
	escape sequence for a RGB foreground color

	"""
	__color_reset = "\033[0m"

	def __init__(self, r=0, g=0, b=0, *args):
		"""
		:ivar r: red component of RGB color (0..255)
		:ivar g: green component of RGB color (0..255)
		:ivar b: blue component of RGB color (0..255)
		:ivar args: variable text arguments
		:vartype r: int
		:vartype g: int
		:vartype b: int
		:vartype args: tuple
		"""
		if r < 0 or r > 255: raise ValueError('Invalid color value {}'.format(r))
		if g < 0 or g > 255: raise ValueError('Invalid color value {}'.format(g))
		if b < 0 or b > 255: raise ValueError('Invalid color value {}'.format(b))
		self.text = ' '.join(args)
		if sys.stdout.isatty():
			self.text = "\033[38;2;%d;%d;%dm" % (r, g, b) + self.text + self.__color_reset

	def __repr__(self):
		return self.text

class PaletteColor(object):
	"""
	Forms colored text using an Xterm-compatible
	escape sequence for a local-terminal-specific palette color

	"""
	__color_reset = "\033[0m"
	def __init__(self, index, *args):
		"""
		:ivar index: index of palette color as defined by local terminal
		:ivar args: variable text arguments
		:vartype index: int
		:vartype args: tuple
		"""
		if index < 0 or index > 255: raise ValueError('Invalid palette index {}'.format(index))
		self.text = ' '.join(args)
		if sys.stdout.isatty():
			self.text = "\033[38;5;%dm" % index + self.text + self.__color_reset

	def __repr__(self):
		return self.text

if __name__ == '__main__':
	for i in range(1,255):
		print(PaletteColor(i, "Your Terminal's Palette Color", str(i)))
	print("Form your own RGB Color, like", RGBColor(255, 165, 0,  "Orange"), "here")
	print("Here is what RGB color ", RGBColor(0, 0x3f, 0x3f, "Dark Teal"), "looks like on your terminal")
	print("ANSI Color:", ANSIColor("magenta","Magenta"))
	print("ANSI Color:", ANSIColor("red","Red"))
	print("ANSI Color:", ANSIColor("yellow","Yellow"))
	print("ANSI Color:", ANSIColor("green","Green"))
	print("ANSI Color:", ANSIColor("cyan","Cyan"))
	print("ANSI Color:", ANSIColor("blue","Blue"))
	print("ANSI Color:", ANSIColor("white","White"))
