# -*- coding: utf-8 -*-

# python 3, requires python -m pip install pillow

import sys
import os
import math
from PIL import Image

if len(sys.argv) < 2:
	print('usage: %s <directory1> [directory2 [...]]'%(sys.argv[0]))
	exit(0)

def rgb2hsv(color):
	r = color[0]
	g = color[1]
	b = color[2]
	a = color[3]
	cmin = min(r, g, b)
	cmax = max(r, g, b)

	v = cmax
	delta = cmax - cmin;
	if cmax != 0:
		s = delta / cmax        # s
	else:
		# r = g = b = 0        # s = 0, v is undefined
		s = 0;
		h = -1;
		return (h, s, 0, a)

	if delta != 0:
		if r == cmax:
			h = (g-b) / delta      # between yellow & magenta
		elif g == cmax:
			h = 2 + (b-r) / delta  # between cyan & yellow
		else:
			h = 4 + (r-g) / delta  # between magenta & cyan
		h *= 60                # degrees
		if h < 0:
			h += 360
	else:
		h = 0
	return (h, s, v, a)
	
def hsv2rgb(color):
	h = color[0]
	s = color[1]
	v = color[2]
	a = color[3]
	
	if s == 0:
		# achromatic (grey)
		r = g = b = v;
		return (int(r), int(g), int(b), a)

	h /= 60            # sector 0 to 5
	i = int(h)
	f = h - i;          # factorial part of h
	p = v * (1 - s )
	q = v * (1 - s * f)
	t = v * (1 - s * (1-f))
	if i == 0:
		r = v
		g = t
		b = p
	elif i == 1:
		r = q
		g = v
		b = p
	elif i == 2:
		r = p
		g = v
		b = t
	elif i == 3:
		r = p
		g = q
		b = v
	elif i == 4:
		r = t
		g = p
		b = v
	else:
		r = v
		g = p
		b = q
	return (int(r), int(g), int(b), a)
	
def set_contrast(px, c, offset=0):
	opx0 = int(((px[0]-127+offset) * c) + 127)
	opx1 = int(((px[1]-127+offset) * c) + 127)
	opx2 = int(((px[2]-127+offset) * c) + 127)
	opx3 = px[3]
	return (max(0, min(opx0, 255)), max(0, min(opx1, 255)), max(0, min(opx2, 255)), max(0, min(opx3, 255)))
	
def set_hsv(px, hue_offset, saturation, value):
	px = list(rgb2hsv(px))
	px[0] += hue_offset
	px[1] += saturation
	px[2] *= value
	while px[0] < 0:
		px[0] += 360
	while px[0] > 360:
		px[0] -= 360
	px[1] = max(0, min(px[1], 255))
	px[2] = max(0, min(px[2], 255))
	return hsv2rgb(px)
	
def check_process(file):
	if file.split('.')[-1].lower() != 'png':
		return
	print('input: %s'%(file))
	im = Image.open(file)
	rgba_im = im.convert('RGBA')
	#rgba_im.getpixel((0, 0))
	#print(repr(rgba_im.size))
	scanrange = 3
	scandiv = scanrange
	power = 1
	variant = 2
	docontrast = False
	for y in range(rgba_im.size[1]):
		for x in range(rgba_im.size[0]):
			cp = 0
			cpcnt = 0
			cpttl = 0
			px = rgba_im.getpixel((x, y))
			desatmul = (float(px[0])*0.4+float(px[1])*0.5+float(px[2])*0.3)/255.0
			desatmul *= 3
			if desatmul < 0.5:
				desatmul = 0.5
			if px[3] < 127:
				continue
			for y1 in range(y-scanrange, y+scanrange):
				for x1 in range(x-scanrange, x+scanrange):
					if y1 < 0 or y1 >= rgba_im.size[1] or\
					   x1 < 0 or x1 >= rgba_im.size[0]:
						px_check = (0, 0, 0, 0)
					else:
						px_check = rgba_im.getpixel((x1, y1))
					if px_check[3] < 127:
						yr = y1-y
						xr = x1-x
						cp += power/math.sqrt(xr*xr+yr*yr)
						if px_check[3] == 0:
							cpcnt += 1
					cpttl += 1
			cp /= desatmul
			#cpcnt /= cpttl
			#if cpcnt > 0.95:
			#	rgba_im.putpixel((x, y), (0, 0, 0, 0))
			#	continue
			if cp > 0:
				if variant == 1:
					cp = float(cp)/scandiv
					if cp < 1:
						cp = 1
					cp2 = float(cp)/4
					if cp2 < 1:
						cp2 = 1
					px = (int(px[0]/cp), int(px[1]/cp), int(px[2]/cp), int(px[3]/cp2))
				elif variant == 2:
					cp = float(cp+scanrange)/scandiv
					if cp < 1:
						cp = 1
					px = (int(px[0]/cp), int(px[1]/cp), int(px[2]/cp), px[3])
			if docontrast:
				desatmul = (1.0-((float(px[0])*0.4+float(px[1])*0.5+float(px[2])*0.3)/255.0))*0.75
				px = set_hsv(px, -6, 0.5*desatmul, 1)
				rcoef = 0
				if px[0] > 0:
					rcoef = abs(((px[1]+px[2])/2) / px[0])
				px = set_contrast(px, 1.2+0.4*desatmul, 48)
			rgba_im.putpixel((x, y), px)
	#rgba_im.save(file+'.2.png')
	rgba_im.save(file)
	
for rootDir in sys.argv[1:]:
	for dirName, dDirList, dFileList in os.walk(rootDir):
		for file in dFileList:
			file = os.path.normpath(dirName+'/'+file)
			check_process(file)
			
