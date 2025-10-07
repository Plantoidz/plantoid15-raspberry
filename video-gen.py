#!/usr/bin/env python3
import cv2
import numpy as np
import math
import argparse
import os
import subprocess
from pydub import AudioSegment

def load_audio_for_advanced_math(file_path, target_fps=30):
    """Load audio and extract detailed mathematical parameters"""
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_channels(1).set_frame_rate(22050)
    
    raw_data = np.frombuffer(audio.raw_data, dtype=np.int16)
    samples = raw_data.astype(np.float32) / 32768.0
    
    frame_duration = 1.0 / target_fps
    samples_per_frame = int(22050 * frame_duration)
    n_frames = len(samples) // samples_per_frame
    
    volumes = []
    frequencies = []
    beats = []
    bass_energy = []
    mid_energy = []
    high_energy = []
    voice_data = []
    spectral_centroid = []
    spectral_rolloff = []
    zero_crossing_rate = []
    
    for i in range(n_frames):
        start = i * samples_per_frame
        end = start + samples_per_frame
        frame_samples = samples[start:end]
        
        if len(frame_samples) == 0:
            volumes.append(0)
            frequencies.append(0)
            beats.append(0)
            bass_energy.append(0)
            mid_energy.append(0)
            high_energy.append(0)
            voice_data.append(np.zeros(128))
            spectral_centroid.append(0)
            spectral_rolloff.append(0)
            zero_crossing_rate.append(0)
            continue
        
        # Volume (RMS)
        volume = np.sqrt(np.mean(frame_samples**2))
        volumes.append(volume)
        
        # Beat detection
        if i >= 2:
            recent_energy = np.mean(volumes[max(0, i-10):i])
            if recent_energy > 0:
                beat = max(0, (volume - recent_energy) / recent_energy)
            else:
                beat = 0
        else:
            beat = 0
        beats.append(beat)
        
        # Zero crossing rate (rhythm/texture indicator)
        if len(frame_samples) > 1:
            zcr = sum(1 for j in range(1, len(frame_samples)) 
                     if (frame_samples[j-1] >= 0) != (frame_samples[j] >= 0))
            zcr_normalized = zcr / len(frame_samples)
        else:
            zcr_normalized = 0
        zero_crossing_rate.append(zcr_normalized)
        
        # Advanced frequency analysis with FFT
        if len(frame_samples) >= 512:
            fft = np.fft.rfft(frame_samples)
            freqs = np.fft.rfftfreq(len(frame_samples), 1/22050)
            magnitude = np.abs(fft)
            
            if np.sum(magnitude) > 0:
                total_energy = np.sum(magnitude)
                
                # Frequency band energies
                bass_end = len(magnitude) // 6
                bass_power = np.sum(magnitude[:bass_end])
                bass_ratio = bass_power / total_energy
                
                mid_start = len(magnitude) // 6
                mid_end = len(magnitude) // 2
                mid_power = np.sum(magnitude[mid_start:mid_end])
                mid_ratio = mid_power / total_energy
                
                high_start = len(magnitude) // 2
                high_power = np.sum(magnitude[high_start:])
                high_ratio = high_power / total_energy
                
                freq_ratio = high_power / total_energy
                
                # Spectral centroid (brightness)
                centroid = np.sum(freqs * magnitude) / total_energy
                centroid_normalized = min(1.0, centroid / 3000.0)
                
                # Spectral rolloff (frequency spread)
                cumulative_magnitude = np.cumsum(magnitude)
                rolloff_threshold = 0.85 * total_energy
                rolloff_idx = np.where(cumulative_magnitude >= rolloff_threshold)[0]
                if len(rolloff_idx) > 0:
                    rolloff_freq = freqs[rolloff_idx[0]]
                    rolloff_normalized = min(1.0, rolloff_freq / 5000.0)
                else:
                    rolloff_normalized = 0
                
                # Voice extraction
                voice_start = int(85 * len(magnitude) / (22050/2))
                voice_end = int(3000 * len(magnitude) / (22050/2))
                voice_magnitude = magnitude[voice_start:voice_end]
                
                if len(voice_magnitude) > 0:
                    voice_downsampled = np.interp(np.linspace(0, len(voice_magnitude)-1, 128), 
                                                np.arange(len(voice_magnitude)), voice_magnitude)
                    if np.max(voice_downsampled) > 0:
                        voice_downsampled = voice_downsampled / np.max(voice_downsampled)
                else:
                    voice_downsampled = np.zeros(128)
            else:
                bass_ratio = 0
                mid_ratio = 0
                high_ratio = 0
                freq_ratio = 0
                centroid_normalized = 0
                rolloff_normalized = 0
                voice_downsampled = np.zeros(128)
        else:
            bass_ratio = 0
            mid_ratio = 0
            high_ratio = 0
            freq_ratio = 0
            centroid_normalized = 0
            rolloff_normalized = 0
            voice_downsampled = np.zeros(128)
            
        frequencies.append(freq_ratio)
        bass_energy.append(bass_ratio)
        mid_energy.append(mid_ratio)
        high_energy.append(high_ratio)
        voice_data.append(voice_downsampled)
        spectral_centroid.append(centroid_normalized)
        spectral_rolloff.append(rolloff_normalized)
    
    # Smoothing function
    def smooth_array(arr, window=3):
        arr = np.array(arr)
        smoothed = np.copy(arr)
        for i in range(window, len(arr) - window):
            smoothed[i] = np.mean(arr[i-window:i+window+1])
        return smoothed
    
    # Apply smoothing
    volumes = smooth_array(volumes, 2)
    beats = smooth_array(beats, 1)
    frequencies = smooth_array(frequencies, 3)
    bass_energy = smooth_array(bass_energy, 2)
    mid_energy = smooth_array(mid_energy, 2)
    high_energy = smooth_array(high_energy, 2)
    spectral_centroid = smooth_array(spectral_centroid, 3)
    spectral_rolloff = smooth_array(spectral_rolloff, 3)
    zero_crossing_rate = smooth_array(zero_crossing_rate, 2)
    
    def normalize(arr, min_val, max_val):
        arr = np.array(arr)
        if np.max(arr) > np.min(arr):
            normalized = (arr - np.min(arr)) / (np.max(arr) - np.min(arr))
            return normalized * (max_val - min_val) + min_val
        return np.full_like(arr, (min_val + max_val) / 2)
    
    return {
        'num_lines': normalize(beats * 2 + volumes * 0.5, 100, 400).astype(int),
        'spiral_factor': normalize(frequencies, 8, 25),
        'inner_radius': normalize(bass_energy, 60, 120).astype(int),
        'outer_radius': normalize(volumes, 200, 300).astype(int),
        'voice_data': voice_data,
        'bass_energy': normalize(bass_energy, 0, 1),
        'mid_energy': normalize(mid_energy, 0, 1),
        'high_energy': normalize(high_energy, 0, 1),
        'beats': normalize(beats, 0, 1),
        'spectral_centroid': normalize(spectral_centroid, 0, 1),
        'spectral_rolloff': normalize(spectral_rolloff, 0, 1),
        'zero_crossing_rate': normalize(zero_crossing_rate, 0, 1),
        'n_frames': n_frames
    }

def draw_voice_sine_wave(frame, center_x, center_y, voice_spectrum, inner_radius):
    """Draw circular voice sine wave in black & white"""
    if np.max(voice_spectrum) < 0.01:
        return
    
    base_wave_radius = inner_radius * 0.4
    num_points = len(voice_spectrum)
    
    points = []
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        amplitude = voice_spectrum[i] * 15
        radius = base_wave_radius + amplitude
        
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        points.append((x, y))
    
    for i in range(len(points)):
        start_point = points[i]
        end_point = points[(i + 1) % len(points)]
        
        # White with intensity based on voice amplitude
        intensity = int(128 + voice_spectrum[i] * 127)
        color = (intensity, intensity, intensity)
        
        cv2.line(frame, start_point, end_point, color, 1)

def draw_mathematical_circles(frame, center_x, center_y, inner_radius, bass_energy, mid_energy, high_energy, 
                            beat_strength, spectral_centroid, spectral_rolloff, zcr, frame_idx):
    """Draw multiple mathematical circles in black & white"""
    
    # Circle 1: Beat-reactive circle (bright white)
    if beat_strength > 0.2:
        beat_radius = int(inner_radius * (1.4 + beat_strength * 0.6))
        beat_thickness = max(1, int(beat_strength * 3))
        intensity = int(200 + beat_strength * 55)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), beat_radius, color, beat_thickness)
    
    # Circle 2: Mid-frequency circle
    if mid_energy > 0.15:
        mid_radius = int(inner_radius * (0.7 + mid_energy * 0.4))
        pulse = math.sin(frame_idx * 0.1) * mid_energy * 5
        final_mid_radius = int(mid_radius + pulse)
        intensity = int(100 + mid_energy * 155)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_mid_radius, color, 1)
    
    # Circle 3: High-frequency circle
    if high_energy > 0.25:
        high_radius = int(inner_radius * (0.5 + high_energy * 0.3))
        high_pulse = math.sin(frame_idx * 0.3) * high_energy * 8
        final_high_radius = int(high_radius + high_pulse)
        if final_high_radius > 10:
            intensity = int(80 + high_energy * 175)
            color = (intensity, intensity, intensity)
            cv2.circle(frame, (center_x, center_y), final_high_radius, color, 1)
    
    # Circle 4: Bass harmonic circle
    if bass_energy > 0.3:
        bass_harmonic_radius = int(inner_radius * (1.8 + bass_energy * 0.8))
        bass_pulse = math.sin(frame_idx * 0.05) * bass_energy * 15
        final_bass_radius = int(bass_harmonic_radius + bass_pulse)
        intensity = int(120 + bass_energy * 135)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_bass_radius, color, 1)
    
    # Circle 5: Spectral centroid circle
    if spectral_centroid > 0.2:
        centroid_radius = int(inner_radius * (0.9 + spectral_centroid * 0.5))
        golden_ratio = 1.618
        centroid_wave = math.sin(frame_idx * 0.1 * golden_ratio) * spectral_centroid * 12
        final_centroid_radius = int(centroid_radius + centroid_wave)
        intensity = int(100 + spectral_centroid * 155)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_centroid_radius, color, 1)
    
    # Circle 6: Spectral rolloff circle
    if spectral_rolloff > 0.25:
        rolloff_radius = int(inner_radius * (1.3 + spectral_rolloff * 0.7))
        fib_factor = 1.272
        rolloff_wave = math.sin(frame_idx * 0.08 * fib_factor) * spectral_rolloff * 18
        final_rolloff_radius = int(rolloff_radius + rolloff_wave)
        intensity = int(80 + spectral_rolloff * 175)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_rolloff_radius, color, 1)
    
    # Circle 7: Zero crossing rate circle
    if zcr > 0.3:
        zcr_radius = int(inner_radius * (0.6 + zcr * 0.4))
        prime_factor = 1.732
        zcr_wave = math.sin(frame_idx * 0.12 * prime_factor) * zcr * 10
        final_zcr_radius = int(zcr_radius + zcr_wave)
        intensity = int(50 + zcr * 205)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_zcr_radius, color, 1)
    
    # Circle 8: Complex harmonic circle
    combined_energy = (bass_energy + mid_energy + high_energy) / 3
    if combined_energy > 0.2:
        harmonic_radius = int(inner_radius * (1.5 + combined_energy * 0.6))
        wave1 = math.sin(frame_idx * 0.07) * bass_energy * 8
        wave2 = math.sin(frame_idx * 0.13) * mid_energy * 6
        wave3 = math.sin(frame_idx * 0.19) * high_energy * 4
        interference = (wave1 + wave2 + wave3) / 3
        final_harmonic_radius = int(harmonic_radius + interference)
        intensity = int(100 + combined_energy * 155)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_harmonic_radius, color, 1)
    
    # Circle 9: Musical ratio circle
    if combined_energy > 0.15:
        ratio_radius = int(inner_radius * (2.1 + combined_energy * 0.9))
        fifth_wave = math.sin(frame_idx * 0.06 * 1.5) * combined_energy * 20
        final_ratio_radius = int(ratio_radius + fifth_wave)
        intensity = int(80 + combined_energy * 175)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_ratio_radius, color, 1)
    
    # Circle 10: Octave circle
    if bass_energy > 0.25 and mid_energy > 0.15:
        octave_radius = int(inner_radius * (2.5 + (bass_energy + mid_energy) * 0.5))
        octave_wave = math.sin(frame_idx * 0.04 * 2.0) * (bass_energy + mid_energy) * 15
        final_octave_radius = int(octave_radius + octave_wave)
        combined_bass_mid = (bass_energy + mid_energy) / 2
        intensity = int(100 + combined_bass_mid * 155)
        color = (intensity, intensity, intensity)
        cv2.circle(frame, (center_x, center_y), final_octave_radius, color, 1)

def draw_mathematical_patterns(frame, center_x, center_y, inner_radius, spectral_centroid, spectral_rolloff, frame_idx):
    """Draw additional mathematical patterns in black & white"""
    
    # Pattern 1: Fibonacci spiral dots
    if spectral_centroid > 0.3:
        fibonacci_sequence = [1, 1, 2, 3, 5, 8, 13, 21]
        for i, fib_num in enumerate(fibonacci_sequence):
            angle = i * math.pi * 0.618034  # Golden angle
            radius = inner_radius * 0.3 + fib_num * 3 + spectral_centroid * 20
            x = int(center_x + radius * math.cos(angle + frame_idx * 0.01))
            y = int(center_y + radius * math.sin(angle + frame_idx * 0.01))
            dot_size = max(1, int(spectral_centroid * 4))
            
            # Intensity based on fibonacci position and centroid
            dot_energy = (i / len(fibonacci_sequence)) * spectral_centroid
            intensity = int(80 + dot_energy * 175)
            color = (intensity, intensity, intensity)
            cv2.circle(frame, (x, y), dot_size, color, -1)
    
    # Pattern 2: Mathematical cross/grid lines
    if spectral_rolloff > 0.4:
        line_length = int(inner_radius * 0.8 + spectral_rolloff * 40)
        intensity = int(100 + spectral_rolloff * 155)
        color = (intensity, intensity, intensity)
        
        # Horizontal line
        cv2.line(frame, (center_x - line_length, center_y), 
                (center_x + line_length, center_y), color, 1)
        
        # Vertical line
        cv2.line(frame, (center_x, center_y - line_length), 
                (center_x, center_y + line_length), color, 1)
        
        # Diagonal lines (45 degrees) - slightly dimmer
        diag_intensity = int(80 + spectral_rolloff * 135)
        diag_color = (diag_intensity, diag_intensity, diag_intensity)
        diag_offset = int(line_length * 0.707)  # cos(45°)
        cv2.line(frame, (center_x - diag_offset, center_y - diag_offset), 
                (center_x + diag_offset, center_y + diag_offset), diag_color, 1)
        cv2.line(frame, (center_x - diag_offset, center_y + diag_offset), 
                (center_x + diag_offset, center_y - diag_offset), diag_color, 1)

def draw_advanced_mathematical_burst(frame, width, height, num_lines, spiral_factor, inner_radius, outer_radius, 
                                   voice_spectrum, bass_energy, mid_energy, high_energy, beat_strength, 
                                   spectral_centroid, spectral_rolloff, zcr, frame_idx):
    """Advanced mathematical visualization with multiple elements"""
    center_x = width // 2
    center_y = height // 2
    
    # Draw gradient thickness radial lines (main pattern)
    for i in range(num_lines):
        angle = (i / num_lines) * 2 * math.pi
        
        spiral_offset = math.sin(angle * spiral_factor) * 0.2 + 0.8
        line_length = (outer_radius - inner_radius) * spiral_offset
        
        length_variation = 0.95 + (i % 11) * 0.01
        final_length = line_length * length_variation
        
        start_x = center_x + math.cos(angle) * inner_radius
        start_y = center_y + math.sin(angle) * inner_radius
        end_x = center_x + math.cos(angle) * (inner_radius + final_length)
        end_y = center_y + math.sin(angle) * (inner_radius + final_length)
        
        # Gradient thickness
        start_thickness = 0.5
        end_thickness = 2.0 + (i % 5) * 0.5
        
        perp_angle = angle + math.pi / 2
        perp_cos = math.cos(perp_angle)
        perp_sin = math.sin(perp_angle)
        
        start_half_thickness = start_thickness / 2
        start_p1_x = int(start_x + perp_cos * start_half_thickness)
        start_p1_y = int(start_y + perp_sin * start_half_thickness)
        start_p2_x = int(start_x - perp_cos * start_half_thickness)
        start_p2_y = int(start_y - perp_sin * start_half_thickness)
        
        end_half_thickness = end_thickness / 2
        end_p1_x = int(end_x + perp_cos * end_half_thickness)
        end_p1_y = int(end_y + perp_sin * end_half_thickness)
        end_p2_x = int(end_x - perp_cos * end_half_thickness)
        end_p2_y = int(end_y - perp_sin * end_half_thickness)
        
        points = np.array([[start_p1_x, start_p1_y], 
                          [start_p2_x, start_p2_y], 
                          [end_p2_x, end_p2_y], 
                          [end_p1_x, end_p1_y]], np.int32)
        
        cv2.fillPoly(frame, [points], (255, 255, 255))
    
    # Draw all mathematical elements
    draw_mathematical_circles(frame, center_x, center_y, inner_radius, bass_energy, mid_energy, high_energy, 
                            beat_strength, spectral_centroid, spectral_rolloff, zcr, frame_idx)
    
    draw_mathematical_patterns(frame, center_x, center_y, inner_radius, spectral_centroid, spectral_rolloff, frame_idx)
    
    # Draw the main inner circle
    cv2.circle(frame, (center_x, center_y), inner_radius - 5, (0, 0, 0), -1)
    cv2.circle(frame, (center_x, center_y), inner_radius, (255, 255, 255), 1)
    
    # Draw voice sine wave in the center
    draw_voice_sine_wave(frame, center_x, center_y, voice_spectrum, inner_radius)

def create_advanced_mathematical_visualization(slider_data, output_path='advanced_math_music.mp4', 
                                             width=800, height=800, fps=30):
    """Create advanced mathematical visualization by piping frames to FFmpeg."""
    
    # FFmpeg command
    # -y: overwrite output file if it exists
    # -f rawvideo: input format is raw video
    # -vcodec rawvideo: input codec
    # -s {width}x{height}: input frame size
    # -pix_fmt bgr24: input pixel format (OpenCV uses BGR)
    # -r {fps}: input frame rate
    # -i -: read input from stdin (the pipe)
    # -c:v libx264: USE THE SUPERIOR H.264 CODEC FOR OUTPUT
    # -pix_fmt yuv420p: output pixel format for broad compatibility
    # -crf 23: Constant Rate Factor (quality level). 18 is high quality, 28 is lower. 23 is a great default.
    # -preset slow: Encoding speed vs. compression. 'slow' gives better compression. 'medium' or 'fast' is faster.
    # output_path: the final output file
    command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '35',
        '-preset', 'slow',
        output_path
    ]

    # Start the FFmpeg process
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Your original frame generation loop
    n_frames = slider_data['n_frames']
    # ... (all the array extractions) ...
    num_lines_array = slider_data['num_lines']
    spiral_factor_array = slider_data['spiral_factor']
    inner_radius_array = slider_data['inner_radius']
    outer_radius_array = slider_data['outer_radius']
    voice_data_array = slider_data['voice_data']
    bass_energy_array = slider_data['bass_energy']
    mid_energy_array = slider_data['mid_energy']
    high_energy_array = slider_data['high_energy']
    beats_array = slider_data['beats']
    spectral_centroid_array = slider_data['spectral_centroid']
    spectral_rolloff_array = slider_data['spectral_rolloff']
    zcr_array = slider_data['zero_crossing_rate']

    for frame_idx in range(n_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # ... (all your frame data calculations) ...
        num_lines = int(num_lines_array[frame_idx])
        spiral_factor = float(spiral_factor_array[frame_idx])
        inner_radius = int(inner_radius_array[frame_idx])
        outer_radius = int(outer_radius_array[frame_idx])
        voice_spectrum = voice_data_array[frame_idx]
        bass_energy = float(bass_energy_array[frame_idx])
        mid_energy = float(mid_energy_array[frame_idx])
        high_energy = float(high_energy_array[frame_idx])
        beat_strength = float(beats_array[frame_idx])
        spectral_centroid = float(spectral_centroid_array[frame_idx])
        spectral_rolloff = float(spectral_rolloff_array[frame_idx])
        zcr = float(zcr_array[frame_idx])
        
        draw_advanced_mathematical_burst(frame, width, height, num_lines, spiral_factor, 
                                       inner_radius, outer_radius, voice_spectrum,
                                       bass_energy, mid_energy, high_energy, beat_strength, 
                                       spectral_centroid, spectral_rolloff, zcr, frame_idx)
        
        # Write frame to FFmpeg's stdin
        proc.stdin.write(frame.tobytes())
        
        if frame_idx % 60 == 0:
            progress = (frame_idx + 1) / n_frames * 100
            print(f"Progress: {progress:.0f}%")
    
    # Close the pipe and wait for FFmpeg to finish
    proc.stdin.close()
    proc.wait()

def merge_audio_video(video_path, audio_path, output_path):
    cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path, 
           '-c:v', 'copy', '-c:a', 'aac', '-shortest', output_path]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(video_path) and video_path != output_path:
            os.remove(video_path)
        return True
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Advanced mathematical music visualizer')
    parser.add_argument('input_file', help='Input audio file')
    parser.add_argument('--output', '-o', default='advanced_math_music.mp4', help='Output video')
    parser.add_argument('--fps', type=int, default=30, help='Frame rate')
    
    args = parser.parse_args()
    # Create a temporary file path for the video-only output
    temp_video = args.output.replace('.mp4', '_temp.mp4')
    
    print("Step 1: Analyzing audio...")
    slider_data = load_audio_for_advanced_math(args.input_file, args.fps)
    
    print("Step 2: Generating video frames and encoding with FFmpeg...")
    create_advanced_mathematical_visualization(slider_data, temp_video, 800, 800, args.fps)
    
    print("Step 3: Merging audio and video...")
    success = merge_audio_video(temp_video, args.input_file, args.output)
    
    if success:
        print(f"Successfully created visualization: {args.output}")
    else:
        print("Error during audio/video merge.")

if __name__ == "__main__":
    main()
