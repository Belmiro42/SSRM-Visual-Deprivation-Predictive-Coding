import random
import sounddevice  as sd
import soundfile    as sf
import time         as timefr
import numpy        as np
import pickle       as dickle
import pyfirmata2
import os

board = pyfirmata2.Arduino('/dev/ttyUSB0')

L1              = board.get_pin('d:4:o')
L2              = board.get_pin('d:5:o')
R2              = board.get_pin('d:3:o')
R1              = board.get_pin('d:6:o')
GREEN           = board.get_pin('d:7:o')
BLUE            = board.get_pin('d:8:o')
RED             = board.get_pin('d:9:o')
SMOOTHNESS      = 10
DEVICE          = "default"

quality_filenames = os.listdir("./Qualities")
alphabet_filenames = os.listdir("./AlphabetSounds")
quality_files = []
alphabet_files = []
list = dickle.load(open("TestOrder.p", "rb"))
board = pyfirmata2.Arduino('/dev/ttyUSB0')
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

def on(led):
    GREEN.write  (1)
    BLUE.write   (1)
    led.write    (1)
    if led == L1:
        led = L2
    if led == R1:
        led = R2
    led.write(1)

def off():
    L1.write     (0)
    L2.write     (0)
    R1.write     (0)
    R2.write     (0)
    RED.write    (0)
    GREEN.write  (0)
    BLUE.write   (0)

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
    
def print_time(fd, start, text):
    now = timefr.time()
    diff = now - start
    fd.write(str(diff) + " " + text + "\n")

def play_sounds():
    start = timefr.time()
    fd = open(f"{start}.txt", "w")
    for i in range(len(list)):
        combination = list[i]
        if (i % 2 == 0):
            print_time(fd, start, "Left")
            sd.play(sin_wave_left, 44100, blocksize = 1024)
            sd.wait()
            if (i < len(list) / 2):
                print_time(fd, start, "Right Light")
                on(R1)
        off()
        
        if (i % 2 == 1):
            print_time(fd, start, "Left")
            sd.play(sin_wave_right, 44100, blocksize = 1024)
            sd.wait()
            if (i < len(list) / 2):
                print_time(fd, start, "Left Light")
                on(L1)
        off()
        
        print(alphabet_filenames[combination[0]], quality_filenames[combination[1]])
        sd.play(alphabet_files[combination[0]][0], alphabet_files[combination[0]][1], device=DEVICE, blocksize = 4096) 
        sd.wait()
        sd.play(quality_files[combination[1]][0], quality_files[combination[1]][1], device=DEVICE, blocksize = 4096)
        sd.wait()
        timefr.sleep(5)

load_audio()
sin_440()  
play_sounds()