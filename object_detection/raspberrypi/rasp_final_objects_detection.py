# object detection 실행 및 서버 통신

import cv2
import torch
import threading
import time
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import socket

SERVER_IP = '192.168.5.78'  ## PC IP
SERVER_PORT = 22222  

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))

BUZZER_PIN = 12
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
# Create PWM object with frequency 500Hz
buzzer_pwm = GPIO.PWM(BUZZER_PIN, 500)

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', 
                       path='/home/ubuntu/Desktop/workdir/object_detection/yolov5/object_detection_code/barbell_tracking.pt', force_reload=True)
model.eval()

# Set device to CPU
device = torch.device('cpu')

print("<Safety System Online>")
# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

# Define ROI coordinates (x1, y1, x2, y2)
roi_x1, roi_y1 = 0, 180  # Top-left corner of ROI
roi_x2, roi_y2 = 640, 360  # Bottom-right corner of ROI

# Global variable to store the latest frame
latest_frame = None
lock = threading.Lock()

# Flag to control threads
running = True

def send_warning_to_server():
    warning_message = "Warning on Bench Press Zone!"
    client_socket.sendall(warning_message.encode('utf-8'))
    
    
def buzz(duration):
    # Start PWM with duty cycle 50% (half of the period)
    buzzer_pwm.start(50)
    time.sleep(duration)
    # Stop PWM
    buzzer_pwm.stop()
    GPIO.output(BUZZER_PIN, GPIO.LOW)  # Ensure buzzer is off after PWM stops

def capture_frames():
    global latest_frame, running
    while running:
        ret, frame = cap.read()
        if not ret:
            break
        with lock:
            latest_frame = frame.copy()

def process_frames():
    global running
    cooldown_start = time.time()
    
    while running:
        with lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()
        
        # Draw ROI rectangle on a copy of the frame with red color (BGR format)
        overlay = frame.copy()
        cv2.rectangle(overlay, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 0, 255), -1)  # -1 to fill the rectangle
        
        # Add overlay with transparency
        alpha = 0.3  # Transparency factor
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Add warning text
        cv2.putText(frame, 'WARNING', (10, 215), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)
        
        # Crop frame to ROI
        roi_frame = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        
        # Perform inference on ROI
        results = model(roi_frame)
        
        # Draw bounding boxes and labels on the ROI frame
        results.render()
        roi_frame_with_boxes = results.ims[0]
        
        # Replace the ROI area in the original frame with the annotated ROI frame
        frame[roi_y1:roi_y2, roi_x1:roi_x2] = roi_frame_with_boxes
        
        # Display the frame with detected objects
        cv2.imshow('Bench Press Warning System', frame)
        
        # Check if any objects are detected
        if results.xyxy[0].shape[0] > 0 :
            # Object detected and not in cooldown
            print("<Warning!>")
            buzz(1)  # Buzz for 1 seconds
            send_warning_to_server() # send message to server
        
        # Check for 'q' key press to exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            running = False

    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()

# Create threads for capturing and processing frames
capture_thread = threading.Thread(target=capture_frames)
process_thread = threading.Thread(target=process_frames)

# Start the threads
capture_thread.start()
process_thread.start()

# Join the threads
capture_thread.join()
process_thread.join()

# Cleanup GPIO
GPIO.cleanup()

print("<Program ended>")
