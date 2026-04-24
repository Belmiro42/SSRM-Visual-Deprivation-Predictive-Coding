from    inputs       import get_gamepad
import  sounddevice  as sd
import  soundfile    as sf
import  time         as timefr
import  numpy        as np
import  pickle       as dickle
import  time         as timefr
import  math
import  pyfirmata2
import  os
import  threading


quality_filenames   = sorted(os.listdir("./Qualities"))
alphabet_filenames  = sorted(os.listdir("./AlphabetSounds"))
list                = dickle.load(open("TestOrder.p", "rb"))
board               = pyfirmata2.Arduino('/dev/ttyUSB1')
quality_files       = []
alphabet_files      = []
sin_wave            = []
sin_wave_left       = []
sin_wave_right      = []

# For an Arduino Nano
L1                  = board.get_pin('d:4:o')
L2                  = board.get_pin('d:5:o')
R2                  = board.get_pin('d:3:o')
R1                  = board.get_pin('d:6:o')
GREEN               = board.get_pin('d:7:o')
BLUE                = board.get_pin('d:8:o')
RED                 = board.get_pin('d:9:o')
SMOOTHNESS          = 10
DEVICE              = "default"


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
    # Colours activate when they're ground (0V). In this case we're giving 
    # green and blue the same voltage as the input from LED so no current 
    # goes through them. Only red activates. (The default is 0V so no 
    # change needed). Could have just set up the circuit with no green/ blue
    # connections.
    GREEN.write  (1)
    BLUE.write   (1)

    # Turn on the left or right pairs 
    if led == L1: L2.write(1), led.write(1)
    else:         R2.write(1), led.write(1)

def off():
    L1.write     (0), L2.write     (0), R1.write     (0), R2.write     (0)
    RED.write    (0), GREEN.write  (0), BLUE.write   (0)

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
    now         = timefr.time()
    diff        = int((now - start) * 1000)
    fd.write(str(diff) + " " + text + "\n")

def play_sounds(fd, start):
    for i in range(len(list)):
        combination = list[i]
        if (i % 2 == 0):
            if (i < len(list) / 2):
                print_time(fd, start, "Right Light On")
                on(R1)
            print_time(fd, start, "Left Beep Start")
            sd.play(sin_wave_left, 44100, blocksize = 1024)
            sd.wait()
            off()
            print_time(fd, start, "Right Light Off")
            print_time(fd, start, "Left Beep Stop")
        
        if (i % 2 == 1):
            print_time(fd, start, "Right Beep Start")
            sd.play(sin_wave_right, 44100, blocksize = 1024)
            if (i < len(list) / 2):
                print_time(fd, start, "Left Light")
                on(L1)
            sd.wait()
            off()
            print_time(fd, start, "Right Light Off")
            print_time(fd, start, "Left Beep Stop")
        
        print(alphabet_filenames[combination[0]][:-4], quality_filenames[combination[1]][:-4])
        print_time(fd, start, alphabet_filenames[combination[0]][:-4] + " " + quality_filenames[combination[1]][:-4])

        sd.play(alphabet_files[combination[0]][0], alphabet_files[combination[0]][1], device=DEVICE, blocksize = 4096) , sd.wait()
        timefr.sleep(0.5)
        sd.play(quality_files[combination[1]][0], quality_files[combination[1]][1], device=DEVICE, blocksize = 4096), sd.wait()
        timefr.sleep(5)

class XboxController(object):
    global fd
    global start
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == "SYN_REPORT":
                    continue
                if event.code == 'ABS_Z':
                    if self.LeftTrigger == 0 and event.state != 0:
                        print_time(fd, start, "No")
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    if self.RightTrigger == 0 and event.state != 0:
                        print_time(fd, start, "Yes")
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'BTN_SOUTH':
                    if self.A == 0 and event.state != 0:
                        print_time(fd, start, "Hallucination")
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    if self.Y == 0 and event.state != 0:
                        print_time(fd, start, "Hallucination")
                    self.Y = event.state 
                elif event.code == 'BTN_WEST':
                    if self.X == 0 and event.state != 0:
                        print_time(fd, start, "Hallucination")
                    self.X = event.state 
                elif event.code == 'BTN_EAST':
                    if self.B == 0 and event.state != 0:
                        print_time(fd, start, "Hallucination")
                    self.B = event.state


load_audio()
sin_440()  
participant_number = input("Enter Participatnt Number: ")
fd = open(f"{participant_number}.txt", "w", buffering=1)
start = timefr.time()
XboxController()
play_sounds(fd, start)