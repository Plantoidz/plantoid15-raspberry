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
        """Play audio file using aplay for best quality"""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        
        print(f"\nPlaying: {filename}")
        
        # Get audio file info
        try:
            wf = wave.open(filename, 'rb')
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            framerate = wf.getframerate()
            frames = wf.getnframes()
            duration = frames / framerate
            wf.close()
            
            print(f"Format: {channels} channel(s), {framerate} Hz, {width*8} bit")
            print(f"Duration: {duration:.2f} seconds")
        except Exception as e:
            print(f"Error reading file info: {e}")
        
        # Use aplay directly for best quality
        try:
            print("Playing with aplay...")
            cmd = ['aplay', '-D', 'plughw:0,0', filename]
            
            # Start playback
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for playback to complete
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print("Playback finished successfully")
            else:
                print(f"Playback error: {stderr.decode()}")
                # Try without device specification
                print("Trying default device...")
                subprocess.run(['aplay', filename])
                
        except subprocess.CalledProcessError as e:
            print(f"Error during playback: {e}")
        except FileNotFoundError:
            print("aplay not found. Please install alsa-utils: sudo apt-get install alsa-utils")
    
    def play_audio_with_volume(self, filename, volume=100):
        """Play audio file with volume control (0-200%)"""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        
        print(f"\nPlaying: {filename} at {volume}% volume")
        
        try:
            # Use amixer to set volume if needed
            if volume != 100:
                subprocess.run(['amixer', 'set', 'PCM', f'{volume}%'], 
                             capture_output=True, check=False)
            
            # Play with aplay
            cmd = ['aplay', '-D', 'plughw:0,0', filename]
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            print(f"Error during playback: {e}")
    
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
    
    def continuous_record_play(self):
        """Record and play back in real-time with a small buffer"""
        print("\nReal-time record and playback (press Ctrl+C to stop)")
        print("Note: There will be a small delay between input and output\n")
        
        try:
            # Create a temporary file for buffering
            temp_file = os.path.join(self.recordings_dir, "temp_realtime.wav")
            
            # Start recording in background
            record_cmd = ['arecord', '-D', 'hw:1,0', '-c', '1', '-r', '48000', 
                         '-f', 'S32_LE', '-t', 'wav', temp_file]
            record_process = subprocess.Popen(record_cmd)
            
            # Give it a moment to start recording
            time.sleep(1)
            
            # Start playback
            play_cmd = ['aplay', '-D', 'plughw:0,0', temp_file]
            play_process = subprocess.Popen(play_cmd)
            
            # Wait for user to stop
            print("Recording and playing... Press Ctrl+C to stop")
            record_process.wait()
            
        except KeyboardInterrupt:
            print("\n\nStopping...")
            if 'record_process' in locals():
                record_process.terminate()
            if 'play_process' in locals():
                play_process.terminate()
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        except Exception as e:
            print(f"Error: {e}")
    
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
        print("5. Real-time record & play (experimental)")
        print("6. List recordings")
        print("7. List audio devices")
        print("8. Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-8): ")
        
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
            recorder.continuous_record_play()
            
        elif choice == '6':
            recorder.list_recordings()
            
        elif choice == '7':
            recorder.list_devices()
            
        elif choice == '8':
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
