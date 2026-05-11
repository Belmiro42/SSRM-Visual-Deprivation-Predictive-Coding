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
combinations        = dickle.load(open("TestOrder.p", "rb"))
board               = pyfirmata2.Arduino('/dev/ttyUSB0')
quality_files       = []
alphabet_files      = []
sin_wave            = []
sin_wave_left       = []
sin_wave_right      = []
modify              = True
brightness          = 1

#Randomised Values
beep_trials         = [ 52,   1,   2,  27,   4,  57,  58,  33,   8,   9,  62,  37,  12,  39,  40,  67, 102,  77,  79,  88,  72,  80,  84,  98]
beep_before_after   = [  0,   1,   0,   0,   1,   0,   1,   1,   0,   0,   0,   1,   1,   0,   1,   1,   1,   1,   0,   1,   0,   1,   0,   0]
beep_lr             = [  1,   1,   1,   1,   0,   0,   0,   1,   1,   0,   1,   1,   0,   1,   1,   1,   0,   0,   0,   1,   0,   1,   1,   0]
beep_delay          = [462, 281, 651, 321, 655, 258, 333, 561, 553, 257, 733, 745, 663, 690, 450, 551, 359, 381, 741, 327, 580, 718, 454, 400]



RPL                 = board.get_pin('d:4:o')  #Right Peripheral on Left  Eye
RPR                 = board.get_pin('d:3:o')  #Right Peripheral on Right Eye
LPL                 = board.get_pin('d:5:o')  #Left  Peripheral on Left  Eye
LPR                 = board.get_pin('d:6:o')  #Left  Peripheral on Right Eye

GREEN               = board.get_pin('d:7:o')
RED                 = board.get_pin('d:8:o')
BLUE                = board.get_pin('d:9:p')


def load_audio():
    global combinations
    global alphabet_files
    global quality_files
    for file in quality_filenames:
        data, fs = sf.read("./Qualities/" + file, dtype='float32')
        quality_files.append([data,fs])
    for file in alphabet_filenames:
        data, fs = sf.read("./AlphabetSounds/" + file, dtype='float32')
        alphabet_files.append([data,fs])
    combinations = dickle.load(open("TestOrder.p", "rb"))

def on(led):
    # Colours activate when they're ground (0V). In this case we're giving 
    # green and blue the same voltage as the input from LED so no current 
    # goes through them. Only red activates. (The default is 0V so no 
    # change needed). Could have just set up the circuit with no green/ blue
    # connections.
    GREEN   .write      (1)
    RED     .write      (1)
    BLUE    .write      (globals()["brightness"])
    # Turn on the left or right pairs 
    if led == RPL: RPL.write(1), RPR.write(1)
    else:          LPL.write(1), LPR.write(1)

def off():
    RPL.write     (0), LPL.write     (0), RPR.write     (0), LPR.write     (0)
    RED.write     (0), GREEN.write   (0), BLUE.write    (0)

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
    now                     = timefr.time()
    if start == 0:  diff    = 0
    else:           diff    = int((now - start) * 1000)

    fd.write(str(diff) + " " + text + "\n")

def play_sound(is_right, trial):
    if is_right:    media, sound_dir, light_dir, led = sin_wave_left,  "Left", "Sound", RPL
    else:           media, sound_dir, light_dir, led = sin_wave_right, "Left", "Right", LPL
    print_time(fd, start, sound_dir + " Beep Start")
    
    sd.play(media, 44100, blocksize = 1024)
    if (trial < 16): 
        on(led)
        print_time(fd, start, light_dir + " Light On")
    sd.wait()
    if (trial < 16): off(), print_time(fd, start, light_dir + " Light Off")
    print_time(fd, start, sound_dir + " Beep Stop")

def start_experiment(fd, start):
    for i in range(len(combinations)):
        combination = combinations[i]
        
        if i in beep_trials:
            trial = beep_trials.index(i)
            if beep_before_after[trial]:
                play_sound(beep_lr[trial], trial)
                timefr.sleep(beep_delay[trial]/ 1000)

        print("("+ str(i) + "/104) " + alphabet_filenames[combination[0]][:-4], quality_filenames[combination[1]][:-4])
        print_time(fd, start, alphabet_filenames[combination[0]][:-4] + " " + quality_filenames[combination[1]][:-4])
        sd.play(alphabet_files[combination[0]][0], alphabet_files[combination[0]][1], device="default", blocksize = 4096), sd.wait(), timefr.sleep(0.5)
        sd.play(quality_files[combination[1]][0],  quality_files[combination[1]][1],  device="default", blocksize = 4096), sd.wait()

        if i in beep_trials:
            trial = beep_trials.index(i)
            if not beep_before_after[trial]: 
                timefr.sleep(beep_delay[trial]/ 1000)
                play_sound(beep_lr[trial], trial)

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
        self.LeftBumper = 0
        self.RightBumper = 0
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
                elif event.code == 'BTN_TL':
                    if self.LeftBumper == 0 and event.state != 0 and modify == True:
                        globals()["brightness"] += 0.05
                        print (globals()["brightness"] )
                        if globals()["brightness"] >= 1:
                            globals()["brightness"] = 1
                        on(RPL)
                        timefr.sleep(0.15)
                        off()
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    if self.RightBumper == 0 and event.state != 0 and modify == True:
                        globals()["brightness"] -= 0.05
                        print(globals()["brightness"] )
                        if globals()["brightness"] <= 0:
                            globals()["brightness"] = 0
                        on(LPL)
                        timefr.sleep(0.15)
                        off()
                    self.RightBumper = event.state

def ok():
    input("Calibration Peroid: Press Enter When Complete")
    globals()["modify"] = False

load_audio()
sin_440()  
participant_number = input("Enter Participant Number: ")
fd = open(f"{participant_number}.txt", "w", buffering=1)
start = 0
XboxController()
ok()
start = timefr.time()
start_experiment(fd, start)


