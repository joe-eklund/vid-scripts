#!/usr/bin/env python
"""
@author Joe Eklund

This script takes an mkv file as input and remuxes to mp4. It will remove all
other streams and create an mp4 of the following format:

Stream 0:0 Video    [direct copy of source]
Stream 0:1 Audio 1  [AAC 2.0 Stereo 160 kbps]
Stream 0:2 Audio 2  [AC3 5.1 Surround - Direct Copy of AC3]

It assumes the following for default:

Stream 0:0 is the video source.
Stream 0:1 is audio source in surround sound (ac3).
"""

import subprocess
import sys
import os
import shutil
import errno
import re

def make_dir(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

INPUT_FILE = sys.argv[1]

OUTPUT_FILE = 'done/' + INPUT_FILE[:-3] + 'mp4'

print 'Remuxing: ' + INPUT_FILE + '\nto\n' + OUTPUT_FILE

#Make temp and done folders for temp files and finished files
make_dir('temp')
make_dir('done')

#Copy AC3
print 'Copying surround sound.'
subprocess.check_call(['ffmpeg', '-y', '-i', INPUT_FILE, '-map', '0:1', '-c:a',
    'copy', 'temp/AC3.mp4'])


#Create AAC
print 'Creating AAC stereo.'
subprocess.check_call(['ffmpeg', '-y', '-i', INPUT_FILE, '-map', '0:1', '-c:a',
    'libfdk_aac', '-b:a', '160k', '-ac', '2', 'temp/AAC.mp4'])

#Get AC3 volume
print 'Grabbing AC3 volume.'

ac3_process = subprocess.Popen(['ffmpeg', '-i', 'temp/AC3.mp4', '-af',
        'volumedetect', '-f', 'null', '/dev/null'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#ffmpeg stores output to stderr
ac3_out, ac3_err = ac3_process.communicate()


ac3_max_volume_string = re.search('max_volume:(.+?)dB',ac3_err).group(1)
ac3_max_volume = float(ac3_max_volume_string)
print 'Max AC3 Volume: ' + str(ac3_max_volume)

#Get AAC volume
print 'Grabbing AAC volume.'

aac_process = subprocess.Popen(['ffmpeg', '-i', 'temp/AAC.mp4', '-af',
        'volumedetect', '-f', 'null', '/dev/null'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#ffmpeg stores output to stderr
aac_out, aac_err = aac_process.communicate()

aac_max_volume_string = re.search('max_volume:(.+?)dB',aac_err).group(1)
aac_max_volume = float(aac_max_volume_string)
print 'Max AAC Volume: ' + str(aac_max_volume)


#Calculate volume boost
print 'Calculating volume boost.'
boost = abs(aac_max_volume - ac3_max_volume)

print 'Volume to boost: ' + str(boost)

boost_command = 'volume=' + str(boost) + 'dB'

#Making AAC Track
subprocess.check_call([
        'ffmpeg', '-y', '-i', INPUT_FILE,
        '-map', '0:1',
        '-c:a', 'libfdk_aac',
        '-b:a', '160k',
        '-ac', '2',
        '-af:a', boost_command,
        'temp/AAC_Boosted.mp4'])

#Remux
print 'Remuxing final video.'

subprocess.check_call([
        'ffmpeg', '-y', '-i', INPUT_FILE,
        '-i', 'temp/AAC_Boosted.mp4',
        '-map', '0:0', '-map', '1:0', '-map', '0:1',
        '-c:v', 'copy',
        '-c:a:0', 'copy',
        '-c:a:1', 'copy',
        '-metadata:s:a:0', 'language=eng',
        '-metadata:s:a:1', 'language=eng',
        OUTPUT_FILE])

print 'Cleaning up'
shutil.rmtree('temp')
