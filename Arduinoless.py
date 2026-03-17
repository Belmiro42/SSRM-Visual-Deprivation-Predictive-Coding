import sounddevice  as sd
import soundfile    as sf
import time         as timefr
import numpy        as np
import pickle       as dickle
import pyfirmata2
import os

LEFT            = 4
MIDDLE          = 5
RIGHT           = 6
RED             = 9
GREEN           = 10
BLUE            = 11
SMOOTHNESS      = 10
DEVICE      = "default"

quality_filenames = os.listdir("./Qualities")
alphabet_filenames = os.listdir("./AlphabetSounds")
quality_files = []
alphabet_files = []
list = dickle.load(open("TestOrder.p", "rb"))
sin_wave = []
sin_wave_left = []
sin_wave_right = []

def load_audio():
    global list
    global alphabet_files
    global quality_files
    for file in quality_filenames:
        data, fs = sf.read("./Qualities/" + file, dtype='float32')
        quality_files.append([data,fs])
    for file in alphabet_filenames:
        data, fs = sf.read("./AlphabetSounds/" + file, dtype='float32')
        alphabet_files.append([data,fs])
    list = dickle.load(open("TestOrder.p", "rb"))



def sin_440():
    global sin_wave
    global sin_wave_left
    global sin_wave_right
    fs = 44100
    duration = .15
    frequency = 440.0
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    global audio_data
    sin_wave = 2 * np.sin(2 * np.pi * frequency * t)
    sin_wave_left = np.vstack((sin_wave, np.zeros_like(sin_wave))).T
    sin_wave_right = np.vstack((np.zeros_like(sin_wave), sin_wave)).T

def play_sounds():
    for combination in list:
        sd.play(sin_wave_left, 44100, blocksize = 1024)
        sd.wait()
        
        sd.play(sin_wave_right, 44100, blocksize = 1024)
        sd.wait()
        
        print(alphabet_filenames[combination[0]], quality_filenames[combination[1]])
        sd.play(alphabet_files[combination[0]][0], alphabet_files[combination[0]][1], device=DEVICE, blocksize = 4096) 
        sd.wait()
        sd.play(quality_files[combination[1]][0], quality_files[combination[1]][1], device=DEVICE, blocksize = 4096)
        sd.wait()

load_audio()
sin_440()
play_sounds()