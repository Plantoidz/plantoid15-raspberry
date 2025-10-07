#!/usr/bin/env python3
import numpy as np
import math
import argparse
import os
import subprocess
from pydub import AudioSegment
from PIL import Image, ImageDraw

def load_audio_for_advanced_math(file_path, target_fps=30):
    """Load audio and extract detailed mathematical parameters (no changes needed here)."""
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
        
        volume = np.sqrt(np.mean(frame_samples**2))
        volumes.append(volume)
        
        if i >= 2:
            recent_energy = np.mean(volumes[max(0, i-10):i])
            beat = max(0, (volume - recent_energy) / recent_energy) if recent_energy > 0 else 0
        else:
            beat = 0
        beats.append(beat)
        
        if len(frame_samples) > 1:
            zcr = sum(1 for j in range(1, len(frame_samples)) if (frame_samples[j-1] >= 0) != (frame_samples[j] >= 0))
            zcr_normalized = zcr / len(frame_samples)
        else:
            zcr_normalized = 0
        zero_crossing_rate.append(zcr_normalized)
        
        if len(frame_samples) >= 512:
            fft = np.fft.rfft(frame_samples)
            freqs = np.fft.rfftfreq(len(frame_samples), 1/22050)
            magnitude = np.abs(fft)
            
            if np.sum(magnitude) > 0:
                total_energy = np.sum(magnitude)
                bass_ratio = np.sum(magnitude[:len(magnitude)//6]) / total_energy
                mid_ratio = np.sum(magnitude[len(magnitude)//6:len(magnitude)//2]) / total_energy
                high_ratio = np.sum(magnitude[len(magnitude)//2:]) / total_energy
                freq_ratio = high_ratio
                centroid = np.sum(freqs * magnitude) / total_energy
                centroid_normalized = min(1.0, centroid / 3000.0)
                cumulative_magnitude = np.cumsum(magnitude)
                rolloff_threshold = 0.85 * total_energy
                rolloff_idx = np.where(cumulative_magnitude >= rolloff_threshold)[0]
                rolloff_normalized = min(1.0, freqs[rolloff_idx[0]] / 5000.0) if len(rolloff_idx) > 0 else 0
                voice_start = int(85 * len(magnitude) / (22050/2))
                voice_end = int(3000 * len(magnitude) / (22050/2))
                voice_magnitude = magnitude[voice_start:voice_end]
                if len(voice_magnitude) > 0:
                    voice_downsampled = np.interp(np.linspace(0, len(voice_magnitude)-1, 128), np.arange(len(voice_magnitude)), voice_magnitude)
                    if np.max(voice_downsampled) > 0: voice_downsampled /= np.max(voice_downsampled)
                else: voice_downsampled = np.zeros(128)
            else:
                bass_ratio, mid_ratio, high_ratio, freq_ratio, centroid_normalized, rolloff_normalized = 0,0,0,0,0,0
                voice_downsampled = np.zeros(128)
        else:
            bass_ratio, mid_ratio, high_ratio, freq_ratio, centroid_normalized, rolloff_normalized = 0,0,0,0,0,0
            voice_downsampled = np.zeros(128)
            
        frequencies.append(freq_ratio)
        bass_energy.append(bass_ratio)
        mid_energy.append(mid_ratio)
        high_energy.append(high_ratio)
        voice_data.append(voice_downsampled)
        spectral_centroid.append(centroid_normalized)
        spectral_rolloff.append(rolloff_normalized)

    def smooth_array(arr, window=3):
        arr = np.array(arr)
        smoothed = np.convolve(arr, np.ones(window*2+1)/(window*2+1), mode='same')
        smoothed[:window] = arr[:window]
        smoothed[-window:] = arr[-window:]
        return smoothed

    volumes, beats, frequencies = smooth_array(volumes, 2), smooth_array(beats, 1), smooth_array(frequencies, 3)
    bass_energy, mid_energy, high_energy = smooth_array(bass_energy, 2), smooth_array(mid_energy, 2), smooth_array(high_energy, 2)
    spectral_centroid, spectral_rolloff, zero_crossing_rate = smooth_array(spectral_centroid, 3), smooth_array(spectral_rolloff, 3), smooth_array(zero_crossing_rate, 2)

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

# --- ALL DRAWING FUNCTIONS CONVERTED TO PILLOW ---

def draw_voice_sine_wave(draw, center_x, center_y, voice_spectrum, inner_radius):
    """Draw circular voice sine wave using Pillow"""
    if np.max(voice_spectrum) < 0.01: return
    
    base_wave_radius = inner_radius * 0.4
    points = []
    for i in range(len(voice_spectrum)):
        angle = (i / len(voice_spectrum)) * 2 * math.pi
        radius = base_wave_radius + voice_spectrum[i] * 15
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        points.append((x, y))
    
    for i in range(len(points)):
        start_point = points[i]
        end_point = points[(i + 1) % len(points)]
        intensity = int(128 + voice_spectrum[i] * 127)
        color = (intensity, intensity, intensity)
        draw.line([start_point, end_point], fill=color, width=1)

def draw_mathematical_circles(draw, center_x, center_y, inner_radius, bass_energy, mid_energy, high_energy, 
                            beat_strength, spectral_centroid, spectral_rolloff, zcr, frame_idx):
    """Draw multiple mathematical circles using Pillow"""
    def draw_circle_outline(center, radius, fill_color, width):
        if radius <= 0: return
        box = [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius]
        draw.ellipse(box, outline=fill_color, width=width)

    if beat_strength > 0.2:
        radius = int(inner_radius * (1.4 + beat_strength * 0.6))
        thickness = max(1, int(beat_strength * 3))
        intensity = int(200 + beat_strength * 55)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), thickness)
    
    if mid_energy > 0.15:
        radius = int(inner_radius * (0.7 + mid_energy * 0.4) + math.sin(frame_idx * 0.1) * mid_energy * 5)
        intensity = int(100 + mid_energy * 155)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if high_energy > 0.25:
        radius = int(inner_radius * (0.5 + high_energy * 0.3) + math.sin(frame_idx * 0.3) * high_energy * 8)
        if radius > 10:
            intensity = int(80 + high_energy * 175)
            draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if bass_energy > 0.3:
        radius = int(inner_radius * (1.8 + bass_energy * 0.8) + math.sin(frame_idx * 0.05) * bass_energy * 15)
        intensity = int(120 + bass_energy * 135)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if spectral_centroid > 0.2:
        radius = int(inner_radius * (0.9 + spectral_centroid * 0.5) + math.sin(frame_idx * 0.1 * 1.618) * spectral_centroid * 12)
        intensity = int(100 + spectral_centroid * 155)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if spectral_rolloff > 0.25:
        radius = int(inner_radius * (1.3 + spectral_rolloff * 0.7) + math.sin(frame_idx * 0.08 * 1.272) * spectral_rolloff * 18)
        intensity = int(80 + spectral_rolloff * 175)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if zcr > 0.3:
        radius = int(inner_radius * (0.6 + zcr * 0.4) + math.sin(frame_idx * 0.12 * 1.732) * zcr * 10)
        intensity = int(50 + zcr * 205)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    combined_energy = (bass_energy + mid_energy + high_energy) / 3
    if combined_energy > 0.2:
        wave = (math.sin(frame_idx*0.07)*bass_energy*8 + math.sin(frame_idx*0.13)*mid_energy*6 + math.sin(frame_idx*0.19)*high_energy*4) / 3
        radius = int(inner_radius * (1.5 + combined_energy * 0.6) + wave)
        intensity = int(100 + combined_energy * 155)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if combined_energy > 0.15:
        radius = int(inner_radius * (2.1 + combined_energy * 0.9) + math.sin(frame_idx * 0.06 * 1.5) * combined_energy * 20)
        intensity = int(80 + combined_energy * 175)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

    if bass_energy > 0.25 and mid_energy > 0.15:
        combined_bass_mid = (bass_energy + mid_energy) / 2
        radius = int(inner_radius * (2.5 + combined_bass_mid * 1.0) + math.sin(frame_idx * 0.04 * 2.0) * (bass_energy + mid_energy) * 15)
        intensity = int(100 + combined_bass_mid * 155)
        draw_circle_outline((center_x, center_y), radius, (intensity, intensity, intensity), 1)

def draw_mathematical_patterns(draw, center_x, center_y, inner_radius, spectral_centroid, spectral_rolloff, frame_idx):
    """Draw additional mathematical patterns using Pillow"""
    if spectral_centroid > 0.3:
        fib_seq = [1, 1, 2, 3, 5, 8, 13, 21]
        for i, fib_num in enumerate(fib_seq):
            angle = i * math.pi * 0.618034
            radius = inner_radius * 0.3 + fib_num * 3 + spectral_centroid * 20
            x = center_x + radius * math.cos(angle + frame_idx * 0.01)
            y = center_y + radius * math.sin(angle + frame_idx * 0.01)
            dot_size = max(1, int(spectral_centroid * 4))
            intensity = int(80 + (i / len(fib_seq)) * spectral_centroid * 175)
            dot_color = (intensity, intensity, intensity)
            draw.ellipse([x - dot_size, y - dot_size, x + dot_size, y + dot_size], fill=dot_color)

    if spectral_rolloff > 0.4:
        line_length = int(inner_radius * 0.8 + spectral_rolloff * 40)
        intensity = int(100 + spectral_rolloff * 155)
        color = (intensity, intensity, intensity)
        draw.line([center_x - line_length, center_y, center_x + line_length, center_y], fill=color, width=1)
        draw.line([center_x, center_y - line_length, center_x, center_y + line_length], fill=color, width=1)
        
        diag_intensity = int(80 + spectral_rolloff * 135)
        diag_color = (diag_intensity, diag_intensity, diag_intensity)
        diag_offset = int(line_length * 0.707)
        draw.line([center_x - diag_offset, center_y - diag_offset, center_x + diag_offset, center_y + diag_offset], fill=diag_color, width=1)
        draw.line([center_x - diag_offset, center_y + diag_offset, center_x + diag_offset, center_y - diag_offset], fill=diag_color, width=1)

def draw_advanced_mathematical_burst(draw, width, height, num_lines, spiral_factor, inner_radius, outer_radius, 
                                   voice_spectrum, bass_energy, mid_energy, high_energy, beat_strength, 
                                   spectral_centroid, spectral_rolloff, zcr, frame_idx):
    """Master drawing function using Pillow."""
    center_x, center_y = width // 2, height // 2
    
    for i in range(num_lines):
        angle = (i / num_lines) * 2 * math.pi
        spiral_offset = math.sin(angle * spiral_factor) * 0.2 + 0.8
        line_length = (outer_radius - inner_radius) * spiral_offset
        final_length = line_length * (0.95 + (i % 11) * 0.01)
        
        start_x = center_x + math.cos(angle) * inner_radius
        start_y = center_y + math.sin(angle) * inner_radius
        end_x = center_x + math.cos(angle) * (inner_radius + final_length)
        end_y = center_y + math.sin(angle) * (inner_radius + final_length)
        
        perp_angle = angle + math.pi / 2
        perp_cos, perp_sin = math.cos(perp_angle), math.sin(perp_angle)
        
        start_half_thickness, end_half_thickness = 0.25, 1.0 + (i % 5) * 0.25
        
        points = [
            (start_x + perp_cos * start_half_thickness, start_y + perp_sin * start_half_thickness),
            (start_x - perp_cos * start_half_thickness, start_y - perp_sin * start_half_thickness),
            (end_x - perp_cos * end_half_thickness, end_y - perp_sin * end_half_thickness),
            (end_x + perp_cos * end_half_thickness, end_y + perp_sin * end_half_thickness)
        ]
        draw.polygon(points, fill=(255, 255, 255))
    
    draw_mathematical_circles(draw, center_x, center_y, inner_radius, bass_energy, mid_energy, high_energy, beat_strength, spectral_centroid, spectral_rolloff, zcr, frame_idx)
    draw_mathematical_patterns(draw, center_x, center_y, inner_radius, spectral_centroid, spectral_rolloff, frame_idx)
    
    ir_fill = inner_radius - 5
    draw.ellipse([center_x - ir_fill, center_y - ir_fill, center_x + ir_fill, center_y + ir_fill], fill=(0, 0, 0))
    ir_outline = inner_radius
    draw.ellipse([center_x - ir_outline, center_y - ir_outline, center_x + ir_outline, center_y + ir_outline], outline=(255, 255, 255), width=1)
    
    draw_voice_sine_wave(draw, center_x, center_y, voice_spectrum, inner_radius)

def create_advanced_mathematical_visualization(slider_data, output_path, width=800, height=800, fps=30):
    """Create visualization with Pillow and pipe frames to FFmpeg."""
    n_frames = slider_data['n_frames']

    command = [
        'ffmpeg', '-y', '-f', 'rawvideo',
        '-vcodec', 'rawvideo', '-s', f'{width}x{height}',
        '-pix_fmt', 'rgb24',  # Pillow uses RGB format
        '-r', str(fps), '-i', '-',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-crf', '28', '-preset', 'medium', output_path
    ]
    
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)

    for frame_idx in range(n_frames):
        img = Image.new('RGB', (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        params = {k: v[frame_idx] for k, v in slider_data.items() if k != 'n_frames'}
        
        draw_advanced_mathematical_burst(draw, width, height, 
                                       int(params['num_lines']), params['spiral_factor'], 
                                       int(params['inner_radius']), int(params['outer_radius']), 
                                       params['voice_data'], params['bass_energy'], 
                                       params['mid_energy'], params['high_energy'], 
                                       params['beats'], params['spectral_centroid'], 
                                       params['spectral_rolloff'], params['zero_crossing_rate'], 
                                       frame_idx)
        
        proc.stdin.write(img.tobytes())
        
        if frame_idx % 60 == 0:
            print(f"Progress: {((frame_idx + 1) / n_frames * 100):.0f}%", flush=True)
    
    proc.stdin.close()
    proc.wait()

def merge_audio_video(video_path, audio_path, output_path):
    """Merge the generated video with the original audio using FFmpeg."""
    temp_output_path = output_path.replace('.mp4', '_final.mp4')
    cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path, 
           '-c:v', 'copy', '-c:a', 'aac', '-shortest', temp_output_path]
    
    try:
        # Use capture_output=True to hide FFmpeg's verbose output unless there's an error
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # Replace original output with the final merged file
        os.rename(temp_output_path, output_path)
        if os.path.exists(video_path):
            os.remove(video_path)
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg audio/video merge:")
        print("FFmpeg stdout:", e.stdout)
        print("FFmpeg stderr:", e.stderr)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
        return False

def main():
    parser = argparse.ArgumentParser(description='Advanced mathematical music visualizer using Pillow and FFmpeg.')
    parser.add_argument('input_file', help='Input audio file (e.g., mp3, wav)')
    parser.add_argument('--output', '-o', default='advanced_math_music.mp4', help='Output video file path')
    parser.add_argument('--fps', type=int, default=24, help='Frame rate for the output video')
    parser.add_argument('--size', type=int, default=540, help='Dimension for the square video (e.g., 540 for 540x540)')
    
    args = parser.parse_args()
    
    # Use a temporary path for the video-only file
    temp_video_path = args.output.replace('.mp4', '_temp_video.mp4')
    # make sure that all the directories exist before creating the movie, otherwise it will fail
    parent_directory = os.path.dirname(temp_video_path)
    if parent_directory: # Ensure the path is not empty
        os.makedirs(parent_directory, exist_ok=True)
    
    print("Step 1: Analyzing audio...")
    slider_data = load_audio_for_advanced_math(args.input_file, args.fps)
    
    print(f"Step 2: Generating {slider_data['n_frames']} video frames ({args.size}x{args.size} @ {args.fps}fps)...")
    create_advanced_mathematical_visualization(slider_data, temp_video_path, width=args.size, height=args.size, fps=args.fps)
    
    print("Step 3: Merging audio and video...")
    success = merge_audio_video(temp_video_path, args.input_file, args.output)
    
    if success:
        print(f"\nSuccessfully created visualization: {args.output}")
    else:
        print("\nFailed to create the final video.")

if __name__ == "__main__":
    main()
