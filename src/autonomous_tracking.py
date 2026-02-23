"""
Autonomous Human Tracking Drone
================================
Real-time face recognition and PID-based tracking using DJI Tello.

The drone identifies known individuals and autonomously follows them
by adjusting yaw rotation and forward/backward distance.

Usage:
    1. Connect to Tello's Wi-Fi network
    2. Run: python src/autonomous_tracking.py
    3. Press 'q' to quit and land safely
"""

import cv2
import numpy as np
import time
import sys
import face_recognition
from djitellopy import Tello
from config import (
    FRAME_WIDTH, FRAME_HEIGHT,
    PID_KP, PID_KD, PID_KI,
    FB_RANGE_MIN, FB_RANGE_MAX, FB_SPEED,
    SEARCH_SPEED, SEARCH_DELAY,
    MIN_BATTERY, TAKEOFF_HEIGHT,
    KNOWN_FACES,
)


def load_known_faces(face_dict: dict) -> tuple:
    """
    Load reference face images and compute their encodings.

    Args:
        face_dict: Dictionary of {name: image_path} pairs.

    Returns:
        Tuple of (encodings_list, names_list).
    """
    encodings = []
    names = []

    for name, path in face_dict.items():
        try:
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                encodings.append(encoding[0])
                names.append(name)
                print(f"[INFO] Loaded face: {name}")
            else:
                print(f"[WARN] No face found in {path}, skipping.")
        except FileNotFoundError:
            print(f"[WARN] Image not found: {path}, skipping.")

    return encodings, names


def detect_and_recognize(frame, known_encodings, known_names):
    """
    Detect faces in frame and recognize known individuals.

    Args:
        frame: BGR image from drone camera.
        known_encodings: List of known face encodings.
        known_names: List of corresponding names.

    Returns:
        Tuple of (annotated_frame, face_info).
        face_info = ([center_x, center_y], area) of the best match,
                     or ([0, 0], 0) if no known face found.
    """
    # Convert BGR to RGB for face_recognition
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    best_info = ([0, 0], 0)
    best_distance = float("inf")

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Compare with known faces
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        name = "Unknown"
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]

                # Calculate face center and area
                center_x = (left + right) // 2
                center_y = (top + bottom) // 2
                area = (right - left) * (bottom - top)

                # Track the closest known face match
                if face_distances[best_match_index] < best_distance:
                    best_distance = face_distances[best_match_index]
                    best_info = ([center_x, center_y], area)

        # Draw bounding box
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw name label
        cv2.rectangle(
            frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED
        )
        cv2.putText(
            frame, name, (left + 6, bottom - 6),
            cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
        )

    return frame, best_info


def track_face(drone, face_info, frame_width, pid, prev_error):
    """
    PID controller for drone tracking.

    Adjusts yaw (rotation) based on horizontal error and
    forward/backward movement based on face area.

    Args:
        drone: Tello drone instance.
        face_info: Tuple of ([center_x, center_y], area).
        frame_width: Width of the video frame.
        pid: List of [Kp, Kd, Ki] gains.
        prev_error: Previous horizontal error for derivative term.

    Returns:
        Current horizontal error.
    """
    (x, y), area = face_info
    fb = 0  # forward/backward speed

    # --- Yaw control (PD controller) ---
    error_x = x - frame_width // 2
    speed_x = pid[0] * error_x + pid[1] * (error_x - prev_error)
    speed_x = int(np.clip(speed_x, -100, 100))

    # --- Forward/backward control ---
    if FB_RANGE_MIN < area < FB_RANGE_MAX:
        fb = 0  # In optimal range
    elif area > FB_RANGE_MAX:
        fb = -FB_SPEED  # Too close, move back
    elif 0 < area < FB_RANGE_MIN:
        fb = FB_SPEED  # Too far, move forward
    elif area == 0:
        # Target lost — enter search mode
        speed_x = 0
        error_x = 0
        drone.send_rc_control(0, 0, 0, SEARCH_SPEED)
        time.sleep(SEARCH_DELAY)
        return error_x

    # Reset if no face detected
    if x == 0:
        speed_x = 0
        error_x = 0

    # Send control commands: (left/right, forward/back, up/down, yaw)
    drone.send_rc_control(0, fb, 0, speed_x)
    return error_x


def main():
    """Main entry point for the autonomous tracking system."""

    # --- Initialize drone ---
    drone = Tello()
    drone.connect()

    battery = drone.get_battery()
    print(f"[INFO] Battery: {battery}%")

    if battery < MIN_BATTERY:
        print(f"[ERROR] Battery too low ({battery}%). Minimum required: {MIN_BATTERY}%")
        sys.exit(1)

    # --- Load known faces ---
    known_encodings, known_names = load_known_faces(KNOWN_FACES)
    if not known_encodings:
        print("[ERROR] No valid face encodings loaded. Check your images.")
        sys.exit(1)

    print(f"[INFO] Loaded {len(known_encodings)} known face(s): {known_names}")

    # --- Takeoff ---
    drone.streamon()
    drone.takeoff()
    drone.move_up(TAKEOFF_HEIGHT)
    print("[INFO] Drone airborne. Tracking started.")

    pid = [PID_KP, PID_KD, PID_KI]
    prev_error = 0

    try:
        while True:
            # Capture frame
            frame = drone.get_frame_read().frame
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # Detect and recognize faces
            annotated_frame, face_info = detect_and_recognize(
                frame, known_encodings, known_names
            )

            # Track the detected face
            prev_error = track_face(drone, face_info, FRAME_WIDTH, pid, prev_error)

            # Display
            cv2.imshow("Autonomous Tracker", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[INFO] Quit signal received.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")

    finally:
        # Safe shutdown
        print("[INFO] Landing...")
        drone.send_rc_control(0, 0, 0, 0)  # Stop all movement
        drone.land()
        drone.streamoff()
        cv2.destroyAllWindows()
        print("[INFO] Drone landed safely.")


if __name__ == "__main__":
    main()
