'''
    Loadding model
'''

import nemo.collections.asr as nemo_asr
asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")

'''
    Loadding audo recorder
'''

import pyaudio
import wave
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
WAVE_OUTPUT_FILENAME = "output.wav"

audio = pyaudio.PyAudio()
frames = []
recording = False
stream = None
recording_thread = None

def record():
    global stream, frames, recording
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    while recording:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        except Exception as e:
            print("Audio input overflowed:", e)
    stream.stop_stream()
    stream.close()

'''
    Loadding keyboard writer
'''

from evdev import InputDevice, categorize, ecodes, list_devices, KeyEvent, UInput
import time

capabilities = {
    ecodes.EV_KEY: [
        # Alphabet keys (A-Z)
        getattr(ecodes, f'KEY_{chr(ord("A") + i)}') for i in range(26)
    ] + [
        # Number keys (0-9)
        getattr(ecodes, f'KEY_{i}') for i in range(10)
    ] + [
        ecodes.KEY_LEFTSHIFT,  # For uppercase letters
        ecodes.KEY_SPACE,      # Spacebar
        ecodes.KEY_DOT,        # Dot key
        ecodes.KEY_COMMA,      # Comma key
        ecodes.KEY_QUESTION,   # Question mark key
    ],
}

# Find the first keyboard device
def find_keyboard():
    for dev_path in list_devices():
        dev = InputDevice(dev_path)
        if 'keyboard' in dev.name.lower() or 'kbd' in dev.name.lower():
            return dev
    raise RuntimeError("No keyboard device found")

keyboard = find_keyboard()

print("Press and hold Left or Right Ctrl to record. ESC to exit.")

def press_key(uinput, key_code):
    uinput.write(ecodes.EV_KEY, key_code, 1) # Key down
    uinput.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)
    time.sleep(0.05) # Small delay for the system to register

def release_key(uinput, key_code):
    uinput.write(ecodes.EV_KEY, key_code, 0) # Key up
    uinput.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)

def press_and_release_key(uinput, key_code):
    press_key(uinput, key_code)
    release_key(uinput, key_code)

def write_string(uinput, text):
    for char in text:
        if 'a' <= char <= 'z':
            key_code = getattr(ecodes, f'KEY_{char.upper()}')
            press_and_release_key(uinput, key_code)
        elif 'A' <= char <= 'Z':
            press_key(uinput, ecodes.KEY_LEFTSHIFT)
            key_code = getattr(ecodes, f'KEY_{char.upper()}')
            press_and_release_key(uinput, key_code)
            release_key(uinput, ecodes.KEY_LEFTSHIFT) # Release shift
        elif char == ' ':
            press_and_release_key(uinput, ecodes.KEY_SPACE)
        elif char == '.':
            press_and_release_key(uinput, ecodes.KEY_DOT)
        elif char == ',':
            press_and_release_key(uinput, ecodes.KEY_COMMA)
        elif char == '?':
            press_and_release_key(uinput, ecodes.KEY_QUESTION)
        elif '0' <= char <= '9':
            # For numbers, directly press the corresponding key
            key_code = getattr(ecodes, f'KEY_{char}')
            press_and_release_key(uinput, key_code)

'''
    Main
'''

try:
    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            # Left Ctrl: KEY_LEFTCTRL, Right Ctrl: KEY_RIGHTCTRL
            if key_event.scancode in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL):
                if key_event.keystate == KeyEvent.key_down and not recording:
                    recording = True
                    recording_thread = threading.Thread(target=record)
                    recording_thread.start()
                    print("Recording started...")
                elif key_event.keystate == KeyEvent.key_up and recording:
                    recording = False
                    print("Recording stopped.")
                    recording_thread.join()
                    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    with UInput(capabilities, name='my-virtual-keyboard') as uinput:
                        write_string(uinput, asr_model.transcribe([WAVE_OUTPUT_FILENAME], batch_size=1)[0].text)
            elif key_event.scancode == ecodes.KEY_ESC and key_event.keystate == KeyEvent.key_down:
                print("Exiting...")
                break
finally:
    audio.terminate()
