#!/usr/bin/env python3
"""
Comprehensive Video Content Analyzer
Generates detailed scene-by-scene descriptions for social media content planning
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from collections import Counter

try:
    import cv2
except ImportError:
    print("Error: OpenCV (cv2) is not installed.")
    print("Install it with: pip install opencv-python")
    sys.exit(1)


# CONFIGURATION
SCENE_CHANGE_THRESHOLD = 30  # Threshold for detecting new scenes
MIN_SCENE_DURATION = 2.0  # Minimum scene duration in seconds
SAMPLE_RATE = 15  # Analyze every Nth frame for detailed analysis


class ComprehensiveVideoAnalyzer:
    """Generates extremely detailed video descriptions for social media content planning"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.video = cv2.VideoCapture(video_path)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        # Orientation
        if self.width > self.height:
            self.orientation = "Horizontal/Landscape"
            self.aspect_ratio = f"{self.width}:{self.height} (16:9 or similar)"
        elif self.height > self.width:
            self.orientation = "Vertical/Portrait"
            self.aspect_ratio = f"{self.width}:{self.height} (9:16 or similar)"
        else:
            self.orientation = "Square"
            self.aspect_ratio = "1:1"
        
        # Load face detector
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
        except:
            print("Warning: Face/eye detection not available")
            self.face_cascade = None
            self.eye_cascade = None
    
    def __del__(self):
        if hasattr(self, 'video'):
            self.video.release()
    
    def frame_to_timestamp(self, frame_num):
        """Convert frame number to MM:SS.mmm format"""
        seconds = frame_num / self.fps
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{mins:02d}:{secs:02d}.{ms:03d}"
    
    def detect_scene_changes(self):
        """Detect scene changes to break video into segments"""
        print("Detecting scene changes...")
        
        scenes = []
        prev_frame = None
        current_scene_start = 0
        
        frame_count = 0
        
        while True:
            ret, frame = self.video.read()
            if not ret:
                break
            
            if frame_count % SAMPLE_RATE != 0:
                frame_count += 1
                continue
            
            if prev_frame is not None:
                # Calculate scene change
                hsv1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2HSV)
                hsv2 = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
                hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
                
                cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                
                comparison = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
                scene_change = comparison * 100
                
                # If significant scene change detected
                if scene_change > SCENE_CHANGE_THRESHOLD:
                    duration = (frame_count - current_scene_start) / self.fps
                    if duration >= MIN_SCENE_DURATION:
                        scenes.append({
                            'start_frame': current_scene_start,
                            'end_frame': frame_count,
                            'start_time': self.frame_to_timestamp(current_scene_start),
                            'end_time': self.frame_to_timestamp(frame_count),
                            'duration': duration
                        })
                        current_scene_start = frame_count
            
            prev_frame = frame.copy()
            frame_count += 1
            
            if frame_count % 100 == 0:
                progress = (frame_count / self.total_frames) * 100
                print(f"Progress: {progress:.1f}%", end='\r')
        
        # Add final scene
        if current_scene_start < self.total_frames:
            scenes.append({
                'start_frame': current_scene_start,
                'end_frame': self.total_frames,
                'start_time': self.frame_to_timestamp(current_scene_start),
                'end_time': self.frame_to_timestamp(self.total_frames),
                'duration': (self.total_frames - current_scene_start) / self.fps
            })
        
        print(f"\nDetected {len(scenes)} scenes")
        return scenes
    
    def analyze_scene_deeply(self, scene):
        """Perform deep analysis of a single scene"""
        self.video.set(cv2.CAP_PROP_POS_FRAMES, scene['start_frame'])
        
        # Sample frames throughout the scene
        sample_frames = []
        frame_interval = max(1, int((scene['end_frame'] - scene['start_frame']) / 5))
        
        for i in range(5):
            frame_num = scene['start_frame'] + (i * frame_interval)
            if frame_num < scene['end_frame']:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = self.video.read()
                if ret:
                    sample_frames.append((frame_num, frame))
        
        if not sample_frames:
            return None
        
        # Analyze visual elements across sampled frames
        analysis = {
            'faces': [],
            'colors': [],
            'brightness_levels': [],
            'motion_levels': [],
            'sharpness_levels': [],
            'dominant_colors': [],
            'composition': []
        }
        
        prev_frame = None
        for frame_num, frame in sample_frames:
            # Face detection
            if self.face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                analysis['faces'].append(len(faces))
            
            # Color analysis
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h_mean = np.mean(hsv[:,:,0])
            s_mean = np.mean(hsv[:,:,1])
            v_mean = np.mean(hsv[:,:,2])
            
            # Determine dominant color tone
            color_tone = self.get_color_description(h_mean, s_mean, v_mean)
            analysis['dominant_colors'].append(color_tone)
            
            # Brightness
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            analysis['brightness_levels'].append(brightness)
            
            # Sharpness
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()
            analysis['sharpness_levels'].append(sharpness)
            
            # Motion (if not first frame)
            if prev_frame is not None:
                diff = cv2.absdiff(
                    cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY),
                    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                )
                motion = np.mean(diff)
                analysis['motion_levels'].append(motion)
            
            # Composition analysis
            composition = self.analyze_composition(frame)
            analysis['composition'].append(composition)
            
            prev_frame = frame.copy()
        
        return analysis
    
    def get_color_description(self, h, s, v):
        """Convert HSV values to descriptive color terms"""
        # Brightness description
        if v < 85:
            brightness = "dark"
        elif v < 170:
            brightness = "medium"
        else:
            brightness = "bright"
        
        # Saturation
        if s < 50:
            saturation = "muted/desaturated"
        elif s < 150:
            saturation = "moderately saturated"
        else:
            saturation = "vibrant/saturated"
        
        # Hue (color)
        if h < 15 or h > 165:
            color = "red/pink"
        elif h < 35:
            color = "orange/warm"
        elif h < 75:
            color = "yellow/golden"
        elif h < 105:
            color = "green"
        elif h < 135:
            color = "cyan/teal"
        else:
            color = "blue/purple"
        
        if s < 30:
            return f"{brightness}, neutral/grayscale tones"
        else:
            return f"{brightness}, {saturation}, {color} tones"
    
    def analyze_composition(self, frame):
        """Analyze frame composition using rule of thirds"""
        height, width = frame.shape[:2]
        
        # Divide into 9 regions (rule of thirds)
        h_third = height // 3
        w_third = width // 3
        
        regions = {
            'top_left': frame[0:h_third, 0:w_third],
            'top_center': frame[0:h_third, w_third:2*w_third],
            'top_right': frame[0:h_third, 2*w_third:width],
            'middle_left': frame[h_third:2*h_third, 0:w_third],
            'center': frame[h_third:2*h_third, w_third:2*w_third],
            'middle_right': frame[h_third:2*h_third, 2*w_third:width],
            'bottom_left': frame[2*h_third:height, 0:w_third],
            'bottom_center': frame[2*h_third:height, w_third:2*w_third],
            'bottom_right': frame[2*h_third:height, 2*w_third:width]
        }
        
        # Find regions with most activity (brightness variance)
        activity = {}
        for region_name, region in regions.items():
            gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            activity[region_name] = np.std(gray_region)
        
        # Find dominant region
        dominant = max(activity, key=activity.get)
        
        # Determine framing
        if 'center' in dominant or activity['center'] > np.mean(list(activity.values())):
            framing = "center-focused composition"
        elif 'top' in dominant:
            framing = "subject in upper frame"
        elif 'bottom' in dominant:
            framing = "subject in lower frame"
        elif 'left' in dominant:
            framing = "left-weighted composition"
        elif 'right' in dominant:
            framing = "right-weighted composition"
        else:
            framing = "balanced composition"
        
        return framing
    
    def generate_scene_description(self, scene_num, scene, analysis):
        """Generate comprehensive paragraph description of a scene"""
        
        # Calculate averages
        avg_faces = np.mean(analysis['faces']) if analysis['faces'] else 0
        avg_brightness = np.mean(analysis['brightness_levels'])
        avg_motion = np.mean(analysis['motion_levels']) if analysis['motion_levels'] else 0
        avg_sharpness = np.mean(analysis['sharpness_levels'])
        
        # Most common color tone
        color_counter = Counter(analysis['dominant_colors'])
        dominant_color = color_counter.most_common(1)[0][0] if color_counter else "neutral"
        
        # Most common composition
        comp_counter = Counter(analysis['composition'])
        composition = comp_counter.most_common(1)[0][0] if comp_counter else "standard framing"
        
        # Build comprehensive description
        description = []
        
        # === HEADER ===
        description.append(f"SCENE {scene_num}")
        description.append(f"Timestamp: {scene['start_time']} - {scene['end_time']} ({scene['duration']:.1f} seconds)")
        description.append("")
        
        # === VISUAL OVERVIEW ===
        description.append("VISUAL OVERVIEW:")
        
        # Lighting
        if avg_brightness < 85:
            lighting = "Low light, moody atmosphere with dim or dramatic lighting. Dark shadows create depth and intimacy. "
        elif avg_brightness < 170:
            lighting = "Moderate, natural lighting with balanced exposure. Comfortable viewing without harsh highlights or deep shadows. "
        else:
            lighting = "Bright, well-lit scene with high exposure. Clean, airy feel with minimal shadows. "
        description.append(lighting)
        
        # Color grading
        description.append(f"Color grading: {dominant_color}. This creates a {'warm, inviting' if 'warm' in dominant_color or 'orange' in dominant_color or 'golden' in dominant_color else 'cool, modern' if 'blue' in dominant_color or 'cyan' in dominant_color or 'teal' in dominant_color else 'natural, balanced'} aesthetic that {'feels cozy and approachable' if 'warm' in dominant_color else 'conveys professionalism and calm' if 'blue' in dominant_color else 'maintains neutral appeal'}.")
        description.append("")
        
        # === COMPOSITION & FRAMING ===
        description.append("COMPOSITION & FRAMING:")
        description.append(f"The shot uses a {composition}. ")
        
        if self.width > self.height:
            description.append(f"Filmed in {self.orientation} format ({self.aspect_ratio}), optimized for YouTube, desktop viewing, or landscape-oriented platforms. ")
        elif self.height > self.width:
            description.append(f"Filmed in {self.orientation} format ({self.aspect_ratio}), perfectly optimized for Instagram Reels, TikTok, and mobile-first vertical video platforms. ")
        else:
            description.append(f"Filmed in {self.orientation} format ({self.aspect_ratio}), ideal for Instagram feed posts and balanced composition. ")
        
        # Sharpness/clarity
        if avg_sharpness > 500:
            description.append("Crystal clear, sharp focus with high detail and professional quality. ")
        elif avg_sharpness > 200:
            description.append("Clear focus with good detail retention and crisp edges. ")
        else:
            description.append("Soft focus or slight motion blur, creating a dreamy or intimate feel. ")
        
        description.append("")
        
        # === SUBJECTS & PRESENCE ===
        description.append("SUBJECTS & PRESENCE:")
        if avg_faces > 0.5:
            num_people = "one person" if avg_faces < 1.5 else f"approximately {int(avg_faces)} people"
            description.append(f"Human presence: {num_people} visible in frame throughout most of the scene. ")
            description.append("Facial expressions and body language are key elements - potential for emotional connection, eye contact moments, and relatable human reactions. ")
            description.append("This scene has strong potential for personal storytelling, vlogs, talking-head content, or reaction-style videos. ")
        else:
            description.append("No clear human faces detected in this scene. ")
            description.append("This could be B-roll footage, establishing shots, environment-focused content, product shots, or abstract visuals. ")
            description.append("Useful for transition moments, setting atmosphere, or visual variety between talking segments. ")
        
        description.append("")
        
        # === MOTION & ENERGY ===
        description.append("MOTION & ENERGY:")
        if avg_motion > 30:
            description.append("HIGH ENERGY SCENE. Significant movement and dynamic action throughout. ")
            description.append("Fast-paced, attention-grabbing moments with constant visual change. ")
            description.append("Perfect for: hooks, transitions, action sequences, or energetic B-roll. ")
            description.append("Scroll-stopping potential: HIGH - movement naturally catches the eye. ")
        elif avg_motion > 15:
            description.append("MODERATE ENERGY. Noticeable movement with active elements - gestures, camera movement, or subject motion. ")
            description.append("Balanced pace that maintains engagement without overwhelming. ")
            description.append("Perfect for: main content delivery, storytelling segments, or engaging explanations. ")
            description.append("Scroll-stopping potential: MEDIUM - enough motion to hold attention. ")
        else:
            description.append("CALM, STATIC SCENE. Minimal movement, creating a peaceful or contemplative mood. ")
            description.append("Slow pace allows viewers to absorb details and process information. ")
            description.append("Perfect for: emotional moments, important information delivery, peaceful B-roll, or cinematic pauses. ")
            description.append("Scroll-stopping potential: DEPENDS on composition and subject matter - works if emotionally resonant or visually striking. ")
        
        description.append("")
        
        # === SOCIAL MEDIA TAGGING ===
        description.append("SOCIAL MEDIA POTENTIAL:")
        
        tags = []
        
        # Platform recommendations
        platforms = []
        if self.height > self.width:
            platforms.extend(["Instagram Reels", "TikTok", "YouTube Shorts"])
        else:
            platforms.extend(["YouTube", "LinkedIn", "Facebook"])
        
        description.append(f"Best platforms: {', '.join(platforms)}")
        
        # Content type recommendations
        if avg_faces > 0.5:
            if avg_motion > 20:
                description.append("Content type: Vlog-style, talking head, personal story, day-in-the-life, reaction video")
                tags.extend(["personal", "relatable", "vlog", "authentic", "human"])
            else:
                description.append("Content type: Educational, interview, testimonial, calm vlog, thoughtful content")
                tags.extend(["educational", "thoughtful", "calm", "professional", "informative"])
        else:
            if avg_motion > 20:
                description.append("Content type: B-roll montage, travel content, product showcase, dynamic visuals")
                tags.extend(["cinematic", "b-roll", "aesthetic", "travel", "lifestyle"])
            else:
                description.append("Content type: Ambient footage, establishing shots, mood-setting, artistic content")
                tags.extend(["ambient", "aesthetic", "moody", "artistic", "atmospheric"])
        
        # Emotional tags
        if avg_brightness > 170:
            tags.extend(["bright", "positive", "energetic", "uplifting"])
        else:
            tags.extend(["moody", "intimate", "dramatic", "cinematic"])
        
        if "warm" in dominant_color or "orange" in dominant_color:
            tags.extend(["cozy", "warm", "inviting", "nostalgic"])
        elif "blue" in dominant_color or "cyan" in dominant_color:
            tags.extend(["cool", "calm", "professional", "modern"])
        
        description.append(f"Searchable tags: {', '.join(tags)}")
        description.append("")
        
        # === HOOK POTENTIAL ===
        description.append("HOOK & REUSE POTENTIAL:")
        
        # Determine if good for hook
        hook_score = 0
        if avg_motion > 25:
            hook_score += 2
        if avg_faces > 0.5:
            hook_score += 1
        if avg_brightness > 140 or avg_brightness < 100:
            hook_score += 1
        
        if hook_score >= 3:
            description.append("⭐⭐⭐ EXCELLENT HOOK POTENTIAL - High energy, engaging, immediately attention-grabbing")
            description.append("Use this for: Video openers, social media hooks, highlight reels, thumbnail moments")
        elif hook_score == 2:
            description.append("⭐⭐ GOOD HOOK POTENTIAL - Solid engagement, works well for transitions or secondary hooks")
            description.append("Use this for: Mid-video engagement boost, chapter breaks, supporting content")
        else:
            description.append("⭐ SUPPORTING CONTENT - Better for context, atmosphere, or pacing variation")
            description.append("Use this for: Background footage, pacing breaks, atmosphere building")
        
        description.append("")
        
        # === CAPTION SUGGESTIONS ===
        description.append("SUGGESTED CAPTION STYLES:")
        if avg_faces > 0.5 and avg_motion > 15:
            description.append("• 'When [relatable situation]...' - plays on relatability")
            description.append("• 'POV: [situation]' - TikTok/Reels format")
            description.append("• Direct storytelling with emotional hook")
        elif avg_faces > 0.5:
            description.append("• Thoughtful questions or statements")
            description.append("• Educational hooks: 'Here's what nobody tells you about...'")
            description.append("• Personal revelation: 'I realized that...'")
        else:
            description.append("• Descriptive captions: 'The way [x] looks...'")
            description.append("• Aesthetic captions: Single words or short phrases")
            description.append("• Question prompts: 'Where would you go?'")
        
        description.append("")
        description.append("=" * 120)
        description.append("")
        
        return "\n".join(description)
    
    def analyze_full_video(self):
        """Perform complete video analysis"""
        print(f"\nAnalyzing: {os.path.basename(self.video_path)}")
        print(f"Duration: {self.duration:.2f}s")
        print(f"Resolution: {self.width}x{self.height} ({self.orientation})")
        print(f"FPS: {self.fps:.2f}\n")
        
        # Detect scenes
        scenes = self.detect_scene_changes()
        
        # Analyze each scene deeply
        print("\nPerforming deep analysis of each scene...")
        full_analysis = []
        
        for i, scene in enumerate(scenes, 1):
            print(f"Analyzing scene {i}/{len(scenes)}...")
            analysis = self.analyze_scene_deeply(scene)
            if analysis:
                description = self.generate_scene_description(i, scene, analysis)
                full_analysis.append(description)
        
        return full_analysis, scenes


def generate_comprehensive_report(video_path, scene_descriptions, scenes, output_path):
    """Generate the final comprehensive report"""
    
    with open(output_path, 'w') as f:
        # === HEADER ===
        f.write("=" * 120 + "\n")
        f.write("COMPREHENSIVE VIDEO CONTENT ANALYSIS\n")
        f.write("DETAILED SCENE-BY-SCENE BREAKDOWN FOR SOCIAL MEDIA CONTENT PLANNING\n")
        f.write("=" * 120 + "\n\n")
        
        f.write(f"Video File: {os.path.basename(video_path)}\n")
        f.write(f"Full Path: {video_path}\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("=" * 120 + "\n")
        f.write("EXECUTIVE SUMMARY\n")
        f.write("=" * 120 + "\n\n")
        
        analyzer = cv2.VideoCapture(video_path)
        duration = analyzer.get(cv2.CAP_PROP_FRAME_COUNT) / analyzer.get(cv2.CAP_PROP_FPS)
        width = int(analyzer.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(analyzer.get(cv2.CAP_PROP_FRAME_HEIGHT))
        analyzer.release()
        
        f.write(f"Total Scenes Detected: {len(scenes)}\n")
        f.write(f"Total Duration: {duration:.2f} seconds ({int(duration//60)}:{int(duration%60):02d})\n")
        f.write(f"Resolution: {width} x {height}\n")
        
        if height > width:
            f.write(f"Format: VERTICAL/PORTRAIT - Optimized for Instagram Reels, TikTok, YouTube Shorts\n")
        elif width > height:
            f.write(f"Format: HORIZONTAL/LANDSCAPE - Optimized for YouTube, LinkedIn, Desktop viewing\n")
        else:
            f.write(f"Format: SQUARE - Optimized for Instagram Feed\n")
        
        f.write("\n" + "=" * 120 + "\n")
        f.write("DETAILED SCENE-BY-SCENE ANALYSIS\n")
        f.write("=" * 120 + "\n\n")
        
        # Write all scene descriptions
        for description in scene_descriptions:
            f.write(description)
        
        # === CONTENT REUSE GUIDE ===
        f.write("\n" + "=" * 120 + "\n")
        f.write("CONTENT REUSE QUICK REFERENCE GUIDE\n")
        f.write("=" * 120 + "\n\n")
        
        f.write("BEST SCENES FOR:\n\n")
        
        f.write("Instagram Reels / TikTok:\n")
        f.write("  → Scenes with high energy, human faces, and vertical format\n")
        f.write("  → Look for scenes 1-15 seconds with strong hooks\n")
        f.write("  → Prioritize relatable, emotional, or visually striking moments\n\n")
        
        f.write("YouTube (Main Content):\n")
        f.write("  → Longer scenes (15+ seconds) with clear storytelling\n")
        f.write("  → Educational or informative segments\n")
        f.write("  → Calm, well-lit talking head content\n\n")
        
        f.write("YouTube Shorts:\n")
        f.write("  → Dynamic, fast-paced scenes under 60 seconds\n")
        f.write("  → Strong hook in first 3 seconds\n")
        f.write("  → Works in both vertical and horizontal\n\n")
        
        f.write("Thumbnails:\n")
        f.write("  → Look for scenes with faces, high clarity, good lighting\n")
        f.write("  → Emotional expressions or action moments\n")
        f.write("  → Center-focused composition\n\n")
        
        f.write("B-Roll:\n")
        f.write("  → Scenes without faces or dialogue\n")
        f.write("  → Aesthetic, atmospheric shots\n")
        f.write("  → Can be lower motion for peaceful moments\n\n")
        
        f.write("=" * 120 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_video_analyzer.py <video_file_path>")
        print("Example: python comprehensive_video_analyzer.py /path/to/video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        sys.exit(1)
    
    print("\n" + "="*120)
    print("COMPREHENSIVE VIDEO CONTENT ANALYZER")
    print("Generating detailed scene descriptions for social media content planning")
    print("="*120)
    
    # Analyze video
    analyzer = ComprehensiveVideoAnalyzer(video_path)
    scene_descriptions, scenes = analyzer.analyze_full_video()
    
    # Generate report
    report_path = video_path.rsplit('.', 1)[0] + '_comprehensive_content_analysis.txt'
    generate_comprehensive_report(video_path, scene_descriptions, scenes, report_path)
    
    print("\n" + "="*120)
    print("ANALYSIS COMPLETE")
    print("="*120)
    print(f"Scenes Analyzed: {len(scenes)}")
    print(f"Report saved to: {report_path}")
    print("="*120 + "\n")


if __name__ == "__main__":
    main()

#/Users/jay/Desktop/CinematicVideosLV/IMG_8309.MOV    