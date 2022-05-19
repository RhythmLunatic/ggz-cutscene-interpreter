#!/usr/bin/env python3.8

import subprocess
import os
import glob

from scipy.misc import face
import png
import sys

from BuildSpeakerPortraitDatabase import StoryFigureSettingDataStruct
		

basePath = os.path.join(os.getcwd(),"../pic") #Normally "figure" but I renamed it
#print(basePath)

storyFigueSettingData = {}
with open(os.path.join("GameData","StoryFigueSettingData.tsv"),'r') as f:
	f.readline() # skip first four lines, I don't know why they're here
	f.readline()
	f.readline()
	f.readline()
	while True:
		line = f.readline()
		if not line:
			break
		info=line.split('\t')
		
		storyFigueSettingData[int(info[0])]=StoryFigureSettingDataStruct(info)

for ID,p in storyFigueSettingData.items():
	if ID==1406: #Bad ID, has wrong values
		continue

	#if not "kiana" in p.pic.lower():
	#	continue
	fileName = os.path.join(basePath,p.pic.lower()+".png")
	#print(fileName)
	if not os.path.isfile(fileName):
		print("Ignoring nonexistent portrait "+fileName)
		continue
	variants = glob.glob(os.path.join(basePath,p.pic.lower())+"_*")
	#print(variants)
	facePos = p.getNormalizedFacePosition()
	#No fucking idea how these ones work but I think it may have something to do with the xpos float being .48 instead of .5
	if ID == 30233:
		facePos = (464,80)
	elif ID == 30234:
		facePos = (448,69)
	for v in variants:
		fNameNoPath = os.path.split(v)[-1]
		fullPath = os.path.join(basePath,v)
		if '001' in v: #Ignore 001, it's the same as 000. Let's delete it to save space too.
			os.remove(fullPath)
			continue
		r=png.Reader(filename=fullPath)
		data = r.read()
		if data[0]>256:
			print("Ignoring already resized image for "+fullPath)
			continue
		
		cmd = ["convert","-background","none",fileName,"-page","+"+str(facePos[0])+"+"+str(facePos[1]),fullPath,"-flatten",fullPath]
		print(" ".join(cmd))
		subprocess.call(cmd)
	#p = 
	#print(p.pic)
	#
