#!/usr/bin/env python3
"""
Pure Python I2S Microphone Record & Playback Script
Records from INMP441 and handles playback without external commands
"""

import pyaudio
import wave
import numpy as np
import time
import os
import threading
import queue
from datetime import datetime

# Audio configuration
CHUNK = 2048  # Increased buffer size for better playback
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
        self.playback_device = None
        
        # Create recordings directory
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
        
        # Find best playback device
        self._find_playback_device()
    
    def _find_playback_device(self):
        """Find the best playback device"""
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                # Prefer devices with names containing 'bcm2835' or 'headphones'
                if 'bcm2835' in info['name'].lower() or 'headphones' in info['name'].lower():
                    self.playback_device = i
                    print(f"Using playback device: {info['name']}")
                    break
        
        if self.playback_device is None:
            # Use default output device
            self.playback_device = self.p.get_default_output_device_info()['index']
    
    def list_devices(self):
        """List all audio devices"""
        print("\nAvailable Audio Devices:")
        print("-" * 60)
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            print(f"Device {i}: {info['name']}")
            print(f"  Channels: {info['maxInputChannels']} in, {info['maxOutputChannels']} out")
            print(f"  Default Sample Rate: {info['defaultSampleRate']}")
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
    
    def play_audio(self, filename, device_index=None):
        """Play audio file using pure Python/PyAudio"""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        
        print(f"\nPlaying: {filename}")
        
        # Open WAV file
        try:
            wf = wave.open(filename, 'rb')
            
            # Get audio parameters
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            framerate = wf.getframerate()
            frames = wf.getnframes()
            duration = frames / framerate
            
            print(f"Format: {channels} channel(s), {framerate} Hz, {width*8} bit")
            print(f"Duration: {duration:.2f} seconds")
            
            # Determine output format
            if width == 1:
                output_format = pyaudio.paInt8
            elif width == 2:
                output_format = pyaudio.paInt16
            elif width == 3:
                output_format = pyaudio.paInt24
            elif width == 4:
                output_format = pyaudio.paInt32
            else:
                output_format = pyaudio.paInt16
            
            # Use specified device or default
            output_device = device_index if device_index is not None else self.playback_device
            
            # Open output stream with proper channel handling
            if channels == 1:
                # For mono files, we'll handle it differently
                print("Converting mono to stereo for playback...")
                self.play_stream = self.p.open(
                    format=output_format,
                    channels=2,  # Output as stereo
                    rate=framerate,
                    output=True,
                    output_device_index=output_device,
                    frames_per_buffer=CHUNK * 2
                )
            else:
                self.play_stream = self.p.open(
                    format=output_format,
                    channels=channels,
                    rate=framerate,
                    output=True,
                    output_device_index=output_device,
                    frames_per_buffer=CHUNK * 2
                )
            
            # Play the audio
            self.playing = True
            data = wf.readframes(CHUNK)
            
            print("Playing... (Press Ctrl+C to stop)")
            
            while data and self.playing:
                try:
                    if channels == 1:
                        # Convert mono to stereo
                        if width == 1:
                            mono_data = np.frombuffer(data, dtype=np.int8)
                        elif width == 2:
                            mono_data = np.frombuffer(data, dtype=np.int16)
                        elif width == 4:
                            mono_data = np.frombuffer(data, dtype=np.int32)
                        else:
                            mono_data = np.frombuffer(data, dtype=np.int16)
                        
                        # Duplicate the mono channel to create stereo
                        stereo_data = np.zeros((len(mono_data) * 2,), dtype=mono_data.dtype)
                        stereo_data[0::2] = mono_data  # Left channel
                        stereo_data[1::2] = mono_data  # Right channel
                        data_to_play = stereo_data.tobytes()
                    else:
                        data_to_play = data
                    
                    self.play_stream.write(data_to_play)
                    data = wf.readframes(CHUNK)
                    
                except KeyboardInterrupt:
                    print("\nPlayback interrupted")
                    break
                except Exception as e:
                    print(f"\nError during playback: {e}")
                    break
            
            print("\nPlayback finished")
            
        except Exception as e:
            print(f"\nError playing audio: {e}")
        
        finally:
            self.playing = False
            if self.play_stream:
                self.play_stream.stop_stream()
                self.play_stream.close()
                self.play_stream = None
            if 'wf' in locals():
                wf.close()
    
    def play_audio_advanced(self, filename):
        """Advanced playback with better quality using callback"""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        
        print(f"\nPlaying (advanced): {filename}")
        
        wf = wave.open(filename, 'rb')
        
        # Get audio parameters
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        framerate = wf.getframerate()
        
        # Callback function for non-blocking playback
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            
            if len(data) < frame_count * width * channels:
                # Pad with zeros if we're at the end
                data = data + b'\x00' * (frame_count * width * channels - len(data))
                flag = pyaudio.paComplete
            else:
                flag = pyaudio.paContinue
            
            # Convert mono to stereo if needed
            if channels == 1:
                if width == 1:
                    mono_data = np.frombuffer(data[:frame_count * width], dtype=np.int8)
                elif width == 2:
                    mono_data = np.frombuffer(data[:frame_count * width * 2], dtype=np.int16)
                elif width == 4:
                    mono_data = np.frombuffer(data[:frame_count * width * 4], dtype=np.int32)
                else:
                    mono_data = np.frombuffer(data[:frame_count * width * 2], dtype=np.int16)
                
                if len(mono_data) > 0:
                    stereo_data = np.zeros((len(mono_data) * 2,), dtype=mono_data.dtype)
                    stereo_data[0::2] = mono_data
                    stereo_data[1::2] = mono_data
                    data = stereo_data.tobytes()
                else:
                    data = b'\x00' * (frame_count * width * 2)
            
            return (data, flag)
        
        # Open stream with callback
        stream = self.p.open(
            format=self.p.get_format_from_width(width),
            channels=2 if channels == 1 else channels,
            rate=framerate,
            output=True,
            output_device_index=self.playback_device,
            stream_callback=callback,
            frames_per_buffer=4096  # Larger buffer for smoother playback
        )
        
        # Start the stream
        stream.start_stream()
        
        print("Playing... (Press Enter to stop)")
        
        # Wait for playback to complete or user interrupt
        try:
            while stream.is_active():
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        
        # Clean up
        stream.stop_stream()
        stream.close()
        wf.close()
        
        print("Playback finished")
    
    def record_and_play(self, duration):
        """Record audio and immediately play it back"""
        filename = self.record_audio(duration)
        if filename:
            time.sleep(0.5)  # Small pause between record and play
            self.play_audio_advanced(filename)
    
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
    
    def real_time_passthrough(self):
        """Real-time audio passthrough from mic to speaker"""
        print("\nReal-time audio passthrough (press Ctrl+C to stop)")
        print("Note: There will be a small latency\n")
        
        # Use smaller chunks for lower latency
        PASSTHROUGH_CHUNK = 512
        
        try:
            # Open input stream
            input_stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=PASSTHROUGH_CHUNK
            )
            
            # Open output stream (stereo)
            output_stream = self.p.open(
                format=FORMAT,
                channels=2,  # Output as stereo
                rate=RATE,
                output=True,
                output_device_index=self.playback_device,
                frames_per_buffer=PASSTHROUGH_CHUNK
            )
            
            print("Passthrough active... Speak into the microphone!")
            
            while True:
                try:
                    # Read from mic
                    data = input_stream.read(PASSTHROUGH_CHUNK, exception_on_overflow=False)
                    
                    # Convert mono to stereo
                    mono_data = np.frombuffer(data, dtype=np.int32)
                    stereo_data = np.zeros((len(mono_data) * 2,), dtype=np.int32)
                    stereo_data[0::2] = mono_data
                    stereo_data[1::2] = mono_data
                    
                    # Write to speaker
                    output_stream.write(stereo_data.tobytes())
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break
            
        finally:
            print("\n\nStopping passthrough...")
            if 'input_stream' in locals():
                input_stream.stop_stream()
                input_stream.close()
            if 'output_stream' in locals():
                output_stream.stop_stream()
                output_stream.close()
    
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
    print("Pure Python I2S Microphone Record & Playback System")
    print("="*60)
    
    # List devices once at startup
    recorder.list_devices()
    
    while True:
        print("\n" + "="*60)
        print("Options:")
        print("1. Record audio")
        print("2. Play recording (standard)")
        print("3. Play recording (advanced/callback)")
        print("4. Record and immediately playback")
        print("5. Real-time passthrough")
        print("6. Monitor input levels")
        print("7. List recordings")
        print("8. Select playback device")
        print("9. Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-9): ")
        
        if choice == '1':
            duration_input = input("Enter duration in seconds (or press Enter for manual stop): ")
            duration = int(duration_input) if duration_input else None
            recorder.record_audio(duration)
            
        elif choice == '2':
            recordings = recorder.list_recordings()
            if recordings:
                file_choice = input("\nEnter recording number to play (or filename): ")
                try:
                    idx = int(file_choice) - 1
                    if 0 <= idx < len(recordings):
                        filepath = os.path.join(recorder.recordings_dir, recordings[idx])
                        recorder.play_audio(filepath)
                    else:
                        print("Invalid selection")
                except ValueError:
                    if not file_choice.endswith('.wav'):
                        file_choice += '.wav'
                    filepath = os.path.join(recorder.recordings_dir, file_choice)
                    recorder.play_audio(filepath)
        
        elif choice == '3':
            recordings = recorder.list_recordings()
            if recordings:
                file_choice = input("\nEnter recording number to play (or filename): ")
                try:
                    idx = int(file_choice) - 1
                    if 0 <= idx < len(recordings):
                        filepath = os.path.join(recorder.recordings_dir, recordings[idx])
                        recorder.play_audio_advanced(filepath)
                    else:
                        print("Invalid selection")
                except ValueError:
                    if not file_choice.endswith('.wav'):
                        file_choice += '.wav'
                    filepath = os.path.join(recorder.recordings_dir, file_choice)
                    recorder.play_audio_advanced(filepath)
            
        elif choice == '4':
            duration = int(input("Enter recording duration in seconds: "))
            recorder.record_and_play(duration)
            
        elif choice == '5':
            recorder.real_time_passthrough()
            
        elif choice == '6':
            duration = int(input("Enter monitoring duration in seconds (default 10): ") or "10")
            recorder.monitor_input(duration)
            
        elif choice == '7':
            recorder.list_recordings()
            
        elif choice == '8':
            recorder.list_devices()
            device = int(input("Enter output device number: "))
            recorder.playback_device = device
            print(f"Playback device set to: {device}")
            
        elif choice == '9':
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
