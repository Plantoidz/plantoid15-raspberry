#!/usr/bin/env python3
"""
I2S Microphone Record & Playback Script
Records from INMP441 and handles playback with automatic mono/stereo conversion
"""

import pyaudio
import wave
import numpy as np
import time
import os
import subprocess
import threading
from datetime import datetime

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt32
CHANNELS = 1  # Mono for I2S mic
RATE = 48000

class AudioRecorderPlayer:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.recording = False
        self.playing = False
        self.record_stream = None
        self.play_stream = None
        self.recordings_dir = "recordings"
        
        # Create recordings directory
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
    
    def list_devices(self):
        """List all audio devices"""
        print("\nAvailable Audio Devices:")
        print("-" * 60)
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            print(f"Device {i}: {info['name']}")
            print(f"  Channels: {info['maxInputChannels']} in, {info['maxOutputChannels']} out")
        print("-" * 60)
    
    def record_audio(self, duration=None, filename=None):
        """Record audio from I2S microphone"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"recording_{timestamp}.wav")
        
        print(f"\nRecording to: {filename}")
        print("Press Ctrl+C to stop early" if duration is None else f"Recording for {duration} seconds")
        print("Speak into the microphone!\n")
        
        frames = []
        
        # Open recording stream
        try:
            self.record_stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            self.recording = True
            start_time = time.time()
            
            while self.recording:
                try:
                    data = self.record_stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Calculate and display level
                    audio_data = np.frombuffer(data, dtype=np.int32)
                    rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
                    db = 20 * np.log10(rms / 2147483647.0) if rms > 0 else -100
                    
                    # Visual level meter
                    level_bar = "#" * int((db + 100) / 2)
                    elapsed = time.time() - start_time
                    print(f"\r[{level_bar:<50}] {db:6.1f} dB | {elapsed:6.1f}s", end='', flush=True)
                    
                    # Check duration
                    if duration and elapsed >= duration:
                        break
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\nError during recording: {e}")
                    break
            
        except Exception as e:
            print(f"\nError opening recording stream: {e}")
            return None
        
        finally:
            self.recording = False
            if self.record_stream:
                self.record_stream.stop_stream()
                self.record_stream.close()
                self.record_stream = None
        
        # Save recording
        if frames:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            file_size = os.path.getsize(filename) / 1024 / 1024  # MB
            print(f"\n\nRecording saved: {filename} ({file_size:.2f} MB)")
            return filename
        else:
            print("\n\nNo audio recorded")
            return None
    
    def play_audio(self, filename):
        """Play audio file with automatic format handling"""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        
        print(f"\nPlaying: {filename}")
        
        # Read the WAV file
        try:
            wf = wave.open(filename, 'rb')
            
            # Get audio parameters
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            framerate = wf.getframerate()
            
            print(f"Format: {channels} channel(s), {framerate} Hz, {width*8} bit")
            
            # If mono, we'll play it through a stereo stream by duplicating the channel
            play_channels = 2 if channels == 1 else channels
            
            # Open playback stream
            self.play_stream = self.p.open(
                format=self.p.get_format_from_width(width),
                channels=play_channels,
                rate=framerate,
                output=True,
                frames_per_buffer=CHUNK
            )
            
            self.playing = True
            data = wf.readframes(CHUNK)
            
            while data and self.playing:
                if channels == 1 and play_channels == 2:
                    # Convert mono to stereo by duplicating the channel
                    mono_data = np.frombuffer(data, dtype=self._get_numpy_dtype(width))
                    stereo_data = np.column_stack((mono_data, mono_data))
                    data = stereo_data.tobytes()
                
                self.play_stream.write(data)
                data = wf.readframes(CHUNK)
            
            print("\nPlayback finished")
            
        except Exception as e:
            print(f"\nError during playback: {e}")
            # Fallback to system aplay with sox conversion
            print("Trying system playback with sox conversion...")
            self._play_with_sox(filename)
        
        finally:
            self.playing = False
            if self.play_stream:
                self.play_stream.stop_stream()
                self.play_stream.close()
                self.play_stream = None
            if 'wf' in locals():
                wf.close()
    
    def _get_numpy_dtype(self, width):
        """Get numpy dtype based on sample width"""
        if width == 1:
            return np.int8
        elif width == 2:
            return np.int16
        elif width == 4:
            return np.int32
        else:
            return np.int16
    
    def _play_with_sox(self, filename):
        """Fallback playback using sox and aplay"""
        try:
            # Check if sox is installed
            subprocess.run(['sox', '--version'], capture_output=True, check=True)
            
            # Convert to stereo and play
            print("Converting to stereo and playing...")
            subprocess.run(['sox', filename, '-c', '2', '-t', 'wav', '-', '|', 'aplay'], 
                         shell=True, check=True)
        except subprocess.CalledProcessError:
            print("Sox not found. Trying direct aplay...")
            try:
                subprocess.run(['aplay', '-D', 'plughw:0,0', filename], check=True)
            except subprocess.CalledProcessError:
                print("Playback failed. Please install sox: sudo apt-get install sox")
    
    def record_and_play(self, duration):
        """Record audio and immediately play it back"""
        filename = self.record_audio(duration)
        if filename:
            time.sleep(0.5)  # Small pause between record and play
            self.play_audio(filename)
    
    def list_recordings(self):
        """List all recordings in the recordings directory"""
        recordings = [f for f in os.listdir(self.recordings_dir) if f.endswith('.wav')]
        
        if not recordings:
            print("\nNo recordings found")
            return None
        
        print(f"\nRecordings in {self.recordings_dir}:")
        print("-" * 60)
        for i, recording in enumerate(sorted(recordings), 1):
            filepath = os.path.join(self.recordings_dir, recording)
            size = os.path.getsize(filepath) / 1024 / 1024  # MB
            print(f"{i}. {recording} ({size:.2f} MB)")
        print("-" * 60)
        
        return sorted(recordings)
    
    def monitor_input(self, duration=10):
        """Monitor input levels without recording"""
        print(f"\nMonitoring input levels for {duration} seconds...")
        print("Speak into the microphone!\n")
        
        try:
            stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            start_time = time.time()
            max_db = -100
            
            while time.time() - start_time < duration:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int32)
                    rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
                    db = 20 * np.log10(rms / 2147483647.0) if rms > 0 else -100
                    
                    if db > max_db:
                        max_db = db
                    
                    # Visual level meter
                    level_bar = "#" * int((db + 100) / 2)
                    print(f"\r[{level_bar:<50}] {db:6.1f} dB | Max: {max_db:6.1f} dB", 
                          end='', flush=True)
                    
                except KeyboardInterrupt:
                    break
            
            stream.stop_stream()
            stream.close()
            
            print(f"\n\nMonitoring finished. Max level: {max_db:.1f} dB")
            
        except Exception as e:
            print(f"\nError during monitoring: {e}")
    
    def close(self):
        """Clean up PyAudio"""
        self.p.terminate()

def main():
    """Main program loop"""
    recorder = AudioRecorderPlayer()
    
    print("="*60)
    print("I2S Microphone Record & Playback System")
    print("="*60)
    
    # List devices once at startup
    recorder.list_devices()
    
    while True:
        print("\n" + "="*60)
        print("Options:")
        print("1. Record audio")
        print("2. Play recording")
        print("3. Record and immediately playback")
        print("4. Monitor input levels")
        print("5. List recordings")
        print("6. List audio devices")
        print("7. Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-7): ")
        
        if choice == '1':
            duration_input = input("Enter duration in seconds (or press Enter for manual stop): ")
            duration = int(duration_input) if duration_input else None
            recorder.record_audio(duration)
            
        elif choice == '2':
            recordings = recorder.list_recordings()
            if recordings:
                file_choice = input("\nEnter recording number to play (or filename): ")
                try:
                    # Check if it's a number
                    idx = int(file_choice) - 1
                    if 0 <= idx < len(recordings):
                        filepath = os.path.join(recorder.recordings_dir, recordings[idx])
                        recorder.play_audio(filepath)
                    else:
                        print("Invalid selection")
                except ValueError:
                    # Assume it's a filename
                    if not file_choice.endswith('.wav'):
                        file_choice += '.wav'
                    filepath = os.path.join(recorder.recordings_dir, file_choice)
                    recorder.play_audio(filepath)
            
        elif choice == '3':
            duration = int(input("Enter recording duration in seconds: "))
            recorder.record_and_play(duration)
            
        elif choice == '4':
            duration = int(input("Enter monitoring duration in seconds (default 10): ") or "10")
            recorder.monitor_input(duration)
            
        elif choice == '5':
            recorder.list_recordings()
            
        elif choice == '6':
            recorder.list_devices()
            
        elif choice == '7':
            print("\nGoodbye!")
            break
            
        else:
            print("Invalid choice!")
    
    recorder.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
