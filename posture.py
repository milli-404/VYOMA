import cv2
import mediapipe as mp
import numpy as np
import os

# Suppress TensorFlow Lite INFO and WARNING messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def calculate_angle(a, b, c):
    """Calculate angle between three points (a, b, c) in degrees."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

def analyze_posture(video_path, sport="General"):
    try:
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    except Exception as e:
        print(f"Error: Failed to initialize MediaPipe Pose: {e}")
        return 0, False, 0  # accuracy, is_valid, wrong_streak

    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'. Please ensure it's a valid video.")
        return 0, False, 0

    correct_frames = 0
    total_frames = 0
    exercise_detected = False
    feedback = []
    key_frames = []
    wrong_streak = 0  # New: Track consecutive wrong postures
    max_wrong_streak = 0  # Track max streak for injury flag

    print(f"\nAnalyzing {sport} posture with MediaPipe... (Press 'q' to exit)")
    print("MediaPipe is tracking 33 pose landmarks to detect sport-specific movements.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        total_frames += 1

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark

            # Extract key landmarks
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
            left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
            left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]
            right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x,
                         landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
            right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x,
                          landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
            right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x,
                           landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]

            is_correct = False

            if sport == "Football":
                # Check for kicking motion (knee angle + hip position for swing)
                knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
                hip_angle = calculate_angle(left_hip, right_hip, right_knee)
                if 80 < knee_angle < 100 and hip_angle > 150:
                    correct_frames += 1
                    key_frames.append(total_frames)
                    wrong_streak = 0  # Reset streak
                    is_correct = True
                    cv2.putText(image, f"Good Kick! Knee: {knee_angle:.1f}°", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    exercise_detected = True
                else:
                    wrong_streak += 1
                    max_wrong_streak = max(max_wrong_streak, wrong_streak)
                    cv2.putText(image, f"Adjust Kick (Knee: {knee_angle:.1f}°)", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    feedback.append(f"Frame {total_frames}: Ensure knee at ~90° and hips forward.")

            elif sport == "Volleyball":
                # Check for serving motion (arm extended + wrist above shoulder)
                shoulder_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
                wrist_y = left_wrist[1]
                shoulder_y = left_shoulder[1]
                if shoulder_elbow_angle > 160 and wrist_y < shoulder_y - 0.1:
                    correct_frames += 1
                    key_frames.append(total_frames)
                    wrong_streak = 0  # Reset streak
                    is_correct = True
                    cv2.putText(image, f"Good Serve! Arm: {shoulder_elbow_angle:.1f}°", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    exercise_detected = True
                else:
                    wrong_streak += 1
                    max_wrong_streak = max(max_wrong_streak, wrong_streak)
                    cv2.putText(image, f"Raise Arm (Angle: {shoulder_elbow_angle:.1f}°)", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    feedback.append(f"Frame {total_frames}: Extend arm fully and raise wrist above shoulder.")

            # Log MediaPipe usage
            print(f"Frame {total_frames}: {len(landmarks)} landmarks detected. Streak: {wrong_streak}")

        else:
            cv2.putText(image, "No Pose Detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            feedback.append(f"Frame {total_frames}: No pose detected by MediaPipe.")
            wrong_streak += 1  # Count no pose as wrong
            max_wrong_streak = max(max_wrong_streak, wrong_streak)

        cv2.imshow('MediaPipe Posture Analysis', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Validate video duration
    if total_frames < 30:
        print(f"Error: Video too short ({total_frames} frames). Please provide a video with at least 1 second of content.")
        return 0, False, 0

    # Calculate accuracy and validate exercise
    accuracy = (correct_frames / total_frames * 100) if total_frames > 0 else 0
    min_valid_frames = total_frames * 0.3  # Require at least 30% of frames to be valid
    is_valid_exercise = exercise_detected and correct_frames >= min_valid_frames
    injury_risk = max_wrong_streak >= 3  # Flag if 3+ consecutive wrongs

    print(f"\nPosture analysis completed for {sport}!")
    print(f"Total Frames: {total_frames}, Correct Frames: {correct_frames}, Accuracy: {accuracy:.2f}%")
    print(f"Max Wrong Streak: {max_wrong_streak} (Injury Risk: {'High' if injury_risk else 'Low'})")
    print(f"MediaPipe processed {total_frames} frames, detecting pose landmarks in {correct_frames} frames.")
    if is_valid_exercise:
        print(f"Valid {sport} exercise detected in frames: {key_frames[:5]}...")
    else:
        print(f"No valid {sport} exercise detected. Video may not contain the expected movements.")
        feedback.append(f"Ensure the video contains clear {sport} movements (e.g., kicks for Football, serves for Volleyball).")

    if feedback:
        print("\nFeedback for improvement:")
        for f in feedback[:5]:
            print(f"- {f}")

    return accuracy, is_valid_exercise, max_wrong_streak  # Return streak for injury check