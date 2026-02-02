#!/usr/bin/env python3
"""
Advanced Video Scene Analyzer - Comprehensive Attention Trigger Detection
Analyzes videos to identify the most engaging scenes with detailed trigger explanations
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import numpy as np

try:
    import cv2
except ImportError:
    print("Error: OpenCV (cv2) is not installed.")
    print("Install it with: pip install opencv-python")
    sys.exit(1)


# CONFIGURATION
SAMPLE_RATE = 30  # Analyze every Nth frame (higher = faster, less accurate)
MIN_SCENE_DURATION = 1.0  # Minimum scene duration in seconds
MOTION_THRESHOLD = 25  # Threshold for motion detection (0-100)
SCENE_CHANGE_THRESHOLD = 30  # Threshold for scene change detection (0-100)


# COMPREHENSIVE ATTENTION TRIGGER CHECKLIST
ATTENTION_TRIGGERS = {
    # CORE NON-NEGOTIABLES
    'change_scene_cut': {
        'category': 'CORE - Change',
        'description': 'Camera angle change or scene cut',
        'weight': 30,
        'social_impact': 'Instant attention spike - breaks pattern blindness'
    },
    'lighting_change': {
        'category': 'CORE - Change',
        'description': 'Lighting or brightness shift',
        'weight': 25,
        'social_impact': 'Visual contrast = storytelling without words'
    },
    'movement_high': {
        'category': 'CORE - Movement',
        'description': 'Significant movement/action in frame',
        'weight': 20,
        'social_impact': 'Movement catches eye before meaning - prevents scrolling'
    },
    'movement_moderate': {
        'category': 'CORE - Movement',
        'description': 'Moderate movement (gestures, head turns)',
        'weight': 15,
        'social_impact': 'Keeps engagement, suggests human activity'
    },
    'face_detected': {
        'category': 'CORE - Emotion',
        'description': 'Human face visible (potential for emotion/eye contact)',
        'weight': 15,
        'social_impact': 'Faces = connection - we arre wired to look at faces first'
    },
    'multiple_faces': {
        'category': 'CORE - Emotion',
        'description': 'Multiple faces (social interaction)',
        'weight': 10,
        'social_impact': 'Social proof + relationship dynamics = relatability'
    },
    
    # HIGH-PERFORMING SIGNALS
    'high_contrast': {
        'category': 'Contrast',
        'description': 'Strong visual contrast (dark/bright, busy/calm)',
        'weight': 20,
        'social_impact': 'Bigger contrast = stronger hook, instant storytelling'
    },
    'clarity_high': {
        'category': 'Clarity',
        'description': 'Sharp, clear, well-composed frame',
        'weight': 10,
        'social_impact': 'Clear subject = instant understanding, confusion kills retention'
    },
    'motion_pause': {
        'category': 'Tension/Anticipation',
        'description': 'Sudden decrease in motion (pause/stillness)',
        'weight': 15,
        'social_impact': 'Tension builds - people stay to see the release'
    },
    
    # SOCIAL-SPECIFIC BOOSTERS
    'visual_satisfaction': {
        'category': 'Visual Satisfaction',
        'description': 'Aesthetically pleasing composition',
        'weight': 10,
        'social_impact': 'Feels good to watch = rewatch value'
    },
    'screenshot_worthy': {
        'category': 'Screenshot-able',
        'description': 'Frame worth screenshotting',
        'weight': 12,
        'social_impact': 'Screenshot-able = shareable = viral potential'
    }
}


class AdvancedVideoSceneAnalyzer:
    """Analyzes video for comprehensive attention triggers"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.video = cv2.VideoCapture(video_path)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        # Load face detector
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except:
            print("Warning: Face detection not available")
            self.face_cascade = None
        
        # History for motion tracking
        self.motion_history = []
    
    def __del__(self):
        if hasattr(self, 'video'):
            self.video.release()
    
    def frame_to_timestamp(self, frame_num):
        """Convert frame number to timestamp string"""
        seconds = frame_num / self.fps
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{mins:02d}:{secs:02d}.{ms:03d}"
    
    def detect_motion(self, frame1, frame2):
        """Detect motion between two frames - returns motion score (0-100)"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        motion_score = (np.sum(thresh) / 255) / thresh.size * 100
        return motion_score
    
    def detect_scene_change(self, frame1, frame2):
        """Detect scene/camera changes - returns change score (0-100)"""
        hsv1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
        
        hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        
        cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        
        comparison = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
        return comparison * 100
    
    def detect_faces(self, frame):
        """Detect faces in frame - returns number of faces and regions"""
        if self.face_cascade is None:
            return 0, []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces), faces
    
    def calculate_brightness(self, frame):
        """Calculate average brightness (0-100)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray) / 255 * 100
    
    def calculate_contrast(self, frame):
        """Calculate image contrast (0-100)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        std = np.std(gray)
        # Normalize: higher std = higher contrast
        return min(std / 2.55, 100)
    
    def calculate_sharpness(self, frame):
        """Calculate image sharpness/clarity (0-100)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        return min(sharpness / 10, 100)
    
    def is_screenshot_worthy(self, frame, num_faces, sharpness, contrast):
        """Determine if frame is screenshot-worthy"""
        # Criteria: Clear, good contrast, well-composed
        if sharpness > 60 and contrast > 40:
            # Check composition using rule of thirds
            height, width = frame.shape[:2]
            # Simple check: is there content in center or thirds?
            center_region = frame[height//3:2*height//3, width//3:2*width//3]
            center_brightness = np.mean(center_region)
            
            if center_brightness > 30 or num_faces > 0:
                return True
        return False
    
    def analyze_video(self):
        """Analyze entire video with comprehensive trigger detection"""
        print(f"\nAnalyzing: {os.path.basename(self.video_path)}")
        print(f"Duration: {self.duration:.2f}s, FPS: {self.fps:.2f}, Resolution: {self.width}x{self.height}")
        print(f"Processing every {SAMPLE_RATE} frames...\n")
        
        scenes = []
        prev_frame = None
        prev_brightness = 0
        prev_motion = 0
        
        frame_count = 0
        analyzed_frames = 0
        
        while True:
            ret, frame = self.video.read()
            if not ret:
                break
            
            if frame_count % SAMPLE_RATE != 0:
                frame_count += 1
                continue
            
            analyzed_frames += 1
            timestamp = self.frame_to_timestamp(frame_count)
            
            # Initialize metrics
            scene_data = {
                'frame': frame_count,
                'timestamp': timestamp,
                'triggers_detected': {},  # Key: trigger_id, Value: {info}
                'score': 0,
                'raw_metrics': {}
            }
            
            # Calculate current frame metrics
            num_faces, face_regions = self.detect_faces(frame)
            brightness = self.calculate_brightness(frame)
            contrast = self.calculate_contrast(frame)
            sharpness = self.calculate_sharpness(frame)
            
            scene_data['raw_metrics'] = {
                'brightness': brightness,
                'contrast': contrast,
                'sharpness': sharpness,
                'faces': num_faces
            }
            
            # Compare with previous frame
            if prev_frame is not None:
                # 1. MOTION DETECTION
                motion = self.detect_motion(prev_frame, frame)
                scene_data['raw_metrics']['motion'] = motion
                
                if motion > 40:
                    scene_data['triggers_detected']['movement_high'] = {
                        **ATTENTION_TRIGGERS['movement_high'],
                        'value': motion,
                        'explanation': f'Strong motion detected ({motion:.1f}/100) - action in frame catches eye immediately'
                    }
                    scene_data['score'] += ATTENTION_TRIGGERS['movement_high']['weight']
                elif motion > MOTION_THRESHOLD:
                    scene_data['triggers_detected']['movement_moderate'] = {
                        **ATTENTION_TRIGGERS['movement_moderate'],
                        'value': motion,
                        'explanation': f'Moderate motion ({motion:.1f}/100) - keeps viewer engaged with dynamic content'
                    }
                    scene_data['score'] += ATTENTION_TRIGGERS['movement_moderate']['weight']
                
                # 2. MOTION PAUSE DETECTION (Tension/Anticipation)
                if len(self.motion_history) > 3:
                    avg_recent_motion = np.mean(self.motion_history[-3:])
                    if avg_recent_motion > 30 and motion < 15:
                        scene_data['triggers_detected']['motion_pause'] = {
                            **ATTENTION_TRIGGERS['motion_pause'],
                            'value': avg_recent_motion - motion,
                            'explanation': f'Sudden stillness after movement - creates tension and anticipation'
                        }
                        scene_data['score'] += ATTENTION_TRIGGERS['motion_pause']['weight']
                
                self.motion_history.append(motion)
                if len(self.motion_history) > 10:
                    self.motion_history.pop(0)
                
                # 3. SCENE CHANGE DETECTION
                scene_change = self.detect_scene_change(prev_frame, frame)
                scene_data['raw_metrics']['scene_change'] = scene_change
                
                if scene_change > SCENE_CHANGE_THRESHOLD:
                    scene_data['triggers_detected']['change_scene_cut'] = {
                        **ATTENTION_TRIGGERS['change_scene_cut'],
                        'value': scene_change,
                        'explanation': f'Scene cut or camera angle change ({scene_change:.1f}/100) - instant attention reset'
                    }
                    scene_data['score'] += ATTENTION_TRIGGERS['change_scene_cut']['weight']
                
                # 4. LIGHTING CHANGE (Contrast trigger)
                brightness_change = abs(brightness - prev_brightness)
                
                if brightness_change > 15:
                    scene_data['triggers_detected']['lighting_change'] = {
                        **ATTENTION_TRIGGERS['lighting_change'],
                        'value': brightness_change,
                        'explanation': f'Lighting shift ({brightness_change:.1f} change) - visual contrast tells story without words'
                    }
                    scene_data['score'] += ATTENTION_TRIGGERS['lighting_change']['weight']
            
            # 5. FACE DETECTION (Emotion/Eye Contact potential)
            if num_faces > 0:
                scene_data['triggers_detected']['face_detected'] = {
                    **ATTENTION_TRIGGERS['face_detected'],
                    'value': num_faces,
                    'explanation': f'{num_faces} face(s) detected - humans are wired to look at faces, potential for emotional connection'
                }
                scene_data['score'] += ATTENTION_TRIGGERS['face_detected']['weight']
                
                if num_faces > 1:
                    scene_data['triggers_detected']['multiple_faces'] = {
                        **ATTENTION_TRIGGERS['multiple_faces'],
                        'value': num_faces,
                        'explanation': f'{num_faces} people in frame - social interaction, relationship dynamics, relatability'
                    }
                    scene_data['score'] += ATTENTION_TRIGGERS['multiple_faces']['weight']
            
            # 6. HIGH CONTRAST
            if contrast > 50:
                scene_data['triggers_detected']['high_contrast'] = {
                    **ATTENTION_TRIGGERS['high_contrast'],
                    'value': contrast,
                    'explanation': f'Strong visual contrast ({contrast:.1f}/100) - creates visual interest and depth'
                }
                scene_data['score'] += ATTENTION_TRIGGERS['high_contrast']['weight']
            
            # 7. CLARITY (Visual Satisfaction)
            if sharpness > 60:
                scene_data['triggers_detected']['clarity_high'] = {
                    **ATTENTION_TRIGGERS['clarity_high'],
                    'value': sharpness,
                    'explanation': f'Crystal clear image ({sharpness:.1f}/100) - easy to understand, professional look'
                }
                scene_data['score'] += ATTENTION_TRIGGERS['clarity_high']['weight']
            
            # 8. VISUAL SATISFACTION
            if contrast > 40 and sharpness > 50:
                scene_data['triggers_detected']['visual_satisfaction'] = {
                    **ATTENTION_TRIGGERS['visual_satisfaction'],
                    'value': (contrast + sharpness) / 2,
                    'explanation': f'Aesthetically pleasing composition - smooth, clear, satisfying to watch'
                }
                scene_data['score'] += ATTENTION_TRIGGERS['visual_satisfaction']['weight']
            
            # 9. SCREENSHOT-WORTHY FRAME
            if self.is_screenshot_worthy(frame, num_faces, sharpness, contrast):
                scene_data['triggers_detected']['screenshot_worthy'] = {
                    **ATTENTION_TRIGGERS['screenshot_worthy'],
                    'value': 1,
                    'explanation': f'Frame is screenshot-worthy - shareable, memorable, strong posture/emotion/composition'
                }
                scene_data['score'] += ATTENTION_TRIGGERS['screenshot_worthy']['weight']
            
            # Store scene if it has significant triggers
            if scene_data['score'] > 20:
                scenes.append(scene_data)
            
            # Update previous frame data
            prev_frame = frame.copy()
            prev_brightness = brightness
            
            # Progress indicator
            if analyzed_frames % 10 == 0:
                progress = (frame_count / self.total_frames) * 100
                print(f"Progress: {progress:.1f}% ({analyzed_frames} frames analyzed)", end='\r')
            
            frame_count += 1
        
        print(f"\nAnalysis complete! Analyzed {analyzed_frames} frames")
        
        # Sort scenes by score
        scenes.sort(key=lambda x: x['score'], reverse=True)
        
        # Merge nearby scenes
        merged_scenes = self.merge_nearby_scenes(scenes)
        
        return merged_scenes
    
    def merge_nearby_scenes(self, scenes, time_window=3.0):
        """Merge scenes that are within time_window seconds of each other"""
        if not scenes:
            return []
        
        merged = []
        current_group = [scenes[0]]
        
        for i in range(1, len(scenes)):
            time_diff = (scenes[i]['frame'] - current_group[-1]['frame']) / self.fps
            
            if time_diff <= time_window:
                current_group.append(scenes[i])
            else:
                merged_scene = self.create_merged_scene(current_group)
                merged.append(merged_scene)
                current_group = [scenes[i]]
        
        if current_group:
            merged_scene = self.create_merged_scene(current_group)
            merged.append(merged_scene)
        
        return merged
    
    def create_merged_scene(self, scene_group):
        """Create a single scene from a group of nearby scenes"""
        if len(scene_group) == 1:
            return scene_group[0]
        
        start_frame = scene_group[0]['frame']
        end_frame = scene_group[-1]['frame']
        
        # Combine all unique triggers
        all_triggers = {}
        for scene in scene_group:
            all_triggers.update(scene['triggers_detected'])
        
        # Use max score
        max_score = max([s['score'] for s in scene_group])
        
        return {
            'frame': start_frame,
            'timestamp': self.frame_to_timestamp(start_frame),
            'end_timestamp': self.frame_to_timestamp(end_frame),
            'duration': (end_frame - start_frame) / self.fps,
            'triggers_detected': all_triggers,
            'score': max_score,
            'num_peaks': len(scene_group)
        }


def generate_comprehensive_report(video_path, scenes, output_path):
    """Generate detailed report with trigger explanations"""
    
    with open(output_path, 'w') as f:
        f.write("="*120 + "\n")
        f.write("COMPREHENSIVE VIDEO SCENE ANALYSIS - ATTENTION TRIGGER DETECTION\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*120 + "\n\n")
        
        f.write(f"Video: {os.path.basename(video_path)}\n")
        f.write(f"Path: {video_path}\n\n")
        
        # Attention Triggers Reference
        f.write("="*120 + "\n")
        f.write("ATTENTION TRIGGERS REFERENCE GUIDE\n")
        f.write("="*120 + "\n\n")
        
        current_category = None
        for trigger_id, trigger_info in ATTENTION_TRIGGERS.items():
            if trigger_info['category'] != current_category:
                current_category = trigger_info['category']
                f.write(f"\n{current_category}:\n")
                f.write("-" * 120 + "\n")
            
            f.write(f"  • {trigger_info['description']}\n")
            f.write(f"    Why it matters: {trigger_info['social_impact']}\n")
            f.write(f"    Weight: {trigger_info['weight']}/100\n\n")
        
        f.write("\n" + "="*120 + "\n")
        f.write("TOP ATTENTION-GRABBING SCENES\n")
        f.write("="*120 + "\n\n")
        
        if not scenes:
            f.write("No significant scenes detected.\n")
            return
        
        # Show top 20 scenes
        top_scenes = scenes[:20]
        
        for i, scene in enumerate(top_scenes, 1):
            f.write(f"\n{'='*120}\n")
            f.write(f"SCENE #{i} - OVERALL SCORE: {scene['score']:.0f}/100\n")
            f.write(f"{'='*120}\n")
            f.write(f"Timestamp: {scene['timestamp']}")
            if 'end_timestamp' in scene:
                f.write(f" to {scene['end_timestamp']} ({scene['duration']:.1f}s)")
            f.write("\n\n")
            
            # Trigger count
            trigger_count = len(scene['triggers_detected'])
            f.write(f"TRIGGERS DETECTED: {trigger_count}\n")
            f.write("-" * 120 + "\n\n")
            
            # List each trigger with detailed explanation
            for trigger_id, trigger_data in sorted(
                scene['triggers_detected'].items(), 
                key=lambda x: x[1]['weight'], 
                reverse=True
            ):
                f.write(f"✓ {trigger_data['description'].upper()}\n")
                f.write(f"  Category: {trigger_data['category']}\n")
                f.write(f"  Impact: {trigger_data['social_impact']}\n")
                f.write(f"  Analysis: {trigger_data['explanation']}\n")
                f.write(f"  Weight: +{trigger_data['weight']} points\n")
                f.write("\n")
            
            # Editorial Assessment
            f.write("-" * 120 + "\n")
            f.write("EDITORIAL ASSESSMENT:\n")
            f.write("-" * 120 + "\n")
            
            if trigger_count >= 4:
                f.write("🌟🌟🌟 HERO CLIP - MUST USE\n")
                f.write(f"This scene hits {trigger_count} triggers! This is prime content for:\n")
                f.write("  • Video opener/hook (first 3 seconds)\n")
                f.write("  • Key storytelling moment\n")
                f.write("  • Standalone social post\n")
                f.write("  • Thumbnail frame\n")
            elif trigger_count == 3:
                f.write("🌟🌟 STRONG SCENE - HIGH VALUE\n")
                f.write(f"Solid {trigger_count}-trigger moment. Perfect for:\n")
                f.write("  • Mid-video engagement boost\n")
                f.write("  • Transition point\n")
                f.write("  • Supporting key message\n")
            elif trigger_count == 2:
                f.write("🌟 GOOD SCENE - USEFUL\n")
                f.write(f"Decent {trigger_count}-trigger scene. Good for:\n")
                f.write("  • B-roll footage\n")
                f.write("  • Context/setup shots\n")
                f.write("  • Pacing variation\n")
            else:
                f.write("○ DECENT SCENE\n")
                f.write("Has merit but may need enhancement or combination with other shots.\n")
            
            f.write("\n")
        
        # Summary Statistics
        f.write("\n" + "="*120 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("="*120 + "\n\n")
        f.write(f"Total High-Attention Scenes: {len(scenes)}\n")
        f.write(f"Hero Clips (4+ triggers): {len([s for s in scenes if len(s['triggers_detected']) >= 4])}\n")
        f.write(f"Strong Scenes (3 triggers): {len([s for s in scenes if len(s['triggers_detected']) == 3])}\n")
        f.write(f"Good Scenes (2 triggers): {len([s for s in scenes if len(s['triggers_detected']) == 2])}\n")
        
        # Trigger frequency analysis
        all_trigger_ids = []
        for scene in scenes:
            all_trigger_ids.extend(scene['triggers_detected'].keys())
        
        from collections import Counter
        trigger_counts = Counter(all_trigger_ids)
        
        f.write(f"\nMost Common Triggers in Your Video:\n")
        f.write("-" * 120 + "\n")
        for trigger_id, count in trigger_counts.most_common():
            trigger_name = ATTENTION_TRIGGERS[trigger_id]['description']
            f.write(f"  {trigger_name}: {count} occurrences\n")
        
        f.write("\n" + "="*120 + "\n")
        f.write("EDITING RECOMMENDATIONS:\n")
        f.write("="*120 + "\n\n")
        
        hero_clips = [s for s in scenes if len(s['triggers_detected']) >= 4]
        if hero_clips:
            f.write(f"1. START WITH A BANG:\n")
            f.write(f"   Use Scene #{scenes.index(hero_clips[0])+1} ({hero_clips[0]['timestamp']}) as your hook.\n")
            f.write(f"   It has {len(hero_clips[0]['triggers_detected'])} triggers.\n\n")
        
        f.write(f"2. MAINTAIN ENGAGEMENT:\n")
        f.write(f"   Space out your {len(hero_clips)} hero clips throughout the video.\n")
        f.write(f"   Place them every 15-30 seconds to maintain retention.\n\n")
        
        f.write(f"3. USE VARIETY:\n")
        f.write(f"   Mix different trigger types for dynamic content.\n")
        f.write(f"   Don't rely on just one type (e.g., only motion or only faces).\n\n")
        
        f.write("="*120 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python advanced_scene_analyzer.py <video_file_path>")
        print("Example: python advanced_scene_analyzer.py /path/to/video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        sys.exit(1)
    
    print("\n" + "="*120)
    print("ADVANCED VIDEO SCENE ANALYZER - COMPREHENSIVE ATTENTION TRIGGER DETECTION")
    print("="*120)
    
    # Analyze video
    analyzer = AdvancedVideoSceneAnalyzer(video_path)
    scenes = analyzer.analyze_video()
    
    # Generate report
    report_path = video_path.rsplit('.', 1)[0] + '_comprehensive_analysis.txt'
    generate_comprehensive_report(video_path, scenes, report_path)
    
    # Print summary
    print("\n" + "="*120)
    print("ANALYSIS COMPLETE")
    print("="*120)
    print(f"Total Scenes: {len(scenes)}")
    print(f"Hero Clips (4+ triggers): {len([s for s in scenes if len(s['triggers_detected']) >= 4])}")
    print(f"Strong Scenes (3 triggers): {len([s for s in scenes if len(s['triggers_detected']) == 3])}")
    print(f"Good Scenes (2 triggers): {len([s for s in scenes if len(s['triggers_detected']) == 2])}")
    print(f"\nDetailed report: {report_path}")
    
    # Show top 3 scenes
    if scenes:
        print("\nTOP 3 SCENES:")
        for i, scene in enumerate(scenes[:3], 1):
            triggers = list(scene['triggers_detected'].keys())
            print(f"\n{i}. {scene['timestamp']} (Score: {scene['score']:.0f}, {len(triggers)} triggers)")
            for trigger_id in triggers[:3]:  # Show first 3 triggers
                print(f"   • {ATTENTION_TRIGGERS[trigger_id]['description']}")
    
    print("\n" + "="*120 + "\n")


if __name__ == "__main__":
    main()

#/Users/jay/Desktop/CinematicVideosLV/IMG_8309.MOV