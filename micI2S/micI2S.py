#!/usr/bin/env python3
"""
PyAudio with direct device specification
"""

import pyaudio
import wave
import struct
import math

# Try to suppress ALSA errors
from ctypes import *
from contextlib import contextmanager

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

def find_device():
    """Find the I2S device by trying different approaches"""
    with noalsaerr():
        p = pyaudio.PyAudio()
    
    # Try to find by name
    for i in range(p.get_device_count()):
        try:
            info = p.get_device_info_by_index(i)
            print(f"Device {i}: {info['name']} - {info['maxInputChannels']} channels")
        except:
            pass
    
    p.terminate()
    
    # The I2S device might be at a specific index based on arecord output
    # Since arecord shows it as card 1, device 0, let's calculate the index
    # In PyAudio, the index might be different
    
    return None  # We'll specify the device manually

def record_direct():
    """Record using direct ALSA device specification"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt32
    CHANNELS = 1
    RATE = 48000
    RECORD_SECONDS = 5
    
    with noalsaerr():
        p = pyaudio.PyAudio()
    
    # Try to open the stream with different device specifications
    stream = None
    
    # Method 1: Try using the default device (since we set it in asound.conf)
    try:
        print("Trying default device...")
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        print("Opened with default device")
    except Exception as e:
        print(f"Default device failed: {e}")
    
    # Method 2: Try specifying hw:1,0 through PyAudio
    if not stream:
        try:
            print("\nTrying hw:1,0 directly...")
            # Find the index for hw:1,0
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        print(f"Trying device index {i}...")
                        stream = p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      input_device_index=i,
                                      frames_per_buffer=CHUNK)
                        print(f"Opened with device index {i}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Direct device specification failed: {e}")
    
    if stream:
        print("\nRecording... Speak into the microphone!")
        frames = []
        
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            # Show level
            rms = 0
            for j in range(0, len(data), 4):
                sample = struct.unpack('<i', data[j:j+4])[0]
                rms += sample * sample
            rms = math.sqrt(rms / (CHUNK))
            print("*" * int(rms / 10000000), end='\r')
        
        print("\nRecording finished!")
        
        stream.stop_stream()
        stream.close()
        
        # Save
        wf = wave.open("pyaudio_test.wav", 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print("Saved to pyaudio_test.wav")
    else:
        print("\nCould not open any audio stream!")
        print("Please use arecord directly instead.")
    
    p.terminate()

if __name__ == "__main__":
    print("PyAudio Direct Device Test")
    print("=" * 50)
    
    find_device()
    print("\n" + "=" * 50)
    record_direct()
