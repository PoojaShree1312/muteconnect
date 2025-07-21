import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import speech_recognition as sr
import pyttsx3
import threading
import os

# Initialize Mediapipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize TTS
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Initialize STT
recognizer = sr.Recognizer()

# Sign keyword mappings
sign_keywords = {
    "stop": "Stop",
    "stand": "Stand",
    "good": "Good",
    "go": "Go",
    "peace": "Peace"
}

reverse_signs = {
    "fist": "Stop",
    "open_palm": "Stand",
    "thumbs_up": "Good",
    "pointing": "Go",
    "victory": "Peace"
}

# Load images into dictionary
sign_images = {}

def load_images():
    for keyword in sign_keywords.values():
        try:
            img_path = f"images/{keyword.lower()}.png"
            img = Image.open(img_path).resize((200, 200))
            sign_images[keyword] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Image load error for {keyword}: {e}")
            sign_images[keyword] = None

# GUI elements
root = tk.Tk()
root.title("MuteConnect - Speech and Sign GUI")
root.geometry("500x650")
root.configure(bg="#e1f5fe")

title_label = tk.Label(root, text="MuteConnect", font=("Helvetica", 24, "bold"), bg="#e1f5fe", fg="#01579b")
title_label.pack(pady=20)

image_label = tk.Label(root, bg="#e1f5fe")
image_label.pack(pady=10)

text_label = tk.Label(root, text="", font=("Helvetica", 16), bg="#e1f5fe", fg="#00796b")
text_label.pack(pady=10)

# Speak
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Show both image and text
def show_sign(sign_label):
    text_label.config(text=f"Detected Sign: {sign_label}")
    img = sign_images.get(sign_label)
    if img:
        image_label.config(image=img, text='')
        image_label.image = img
    else:
        image_label.config(image='', text=f"{sign_label}", font=("Helvetica", 32, "bold"), fg="#01579b")

# Speech detection
def recognize_speech():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        speak_text("Please speak now.")
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=8)
            print("Processing...")
            speech_text = recognizer.recognize_google(audio).lower()
            print(f"Recognized Speech: {speech_text}")
            return speech_text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Request error: {e}")
            return None

def start_speech_detection():
    spoken_text = recognize_speech()
    if spoken_text:
        for keyword in sign_keywords:
            if keyword in spoken_text:
                sign_label = sign_keywords[keyword]
                show_sign(sign_label)
                speak_text(f"Detected sign for {keyword}")
                return
        messagebox.showinfo("Result", f"Speech Detected: {spoken_text}\nNo matching sign found.")
        speak_text("No matching sign found.")
    else:
        messagebox.showerror("Error", "Could not understand. Please try again.")

# Webcam detection
def start_webcam_detection():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    last_sign = None
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        detected_sign = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                landmarks = hand_landmarks.landmark
                wrist = landmarks[0]
                thumb_tip = landmarks[4]
                thumb_ip = landmarks[3]
                index_tip = landmarks[8]
                middle_tip = landmarks[12]
                ring_tip = landmarks[16]
                pinky_tip = landmarks[20]

                if (index_tip.y > landmarks[6].y and middle_tip.y > landmarks[10].y and
                    ring_tip.y > landmarks[14].y and pinky_tip.y > landmarks[18].y and
                    thumb_tip.y > thumb_ip.y):
                    detected_sign = "fist"

                elif (index_tip.y < landmarks[6].y and middle_tip.y < landmarks[10].y and
                      ring_tip.y < landmarks[14].y and pinky_tip.y < landmarks[18].y):
                    detected_sign = "open_palm"

                elif (thumb_tip.y < wrist.y and
                      index_tip.y > wrist.y and
                      middle_tip.y > wrist.y and
                      ring_tip.y > wrist.y and
                      pinky_tip.y > wrist.y and
                      thumb_tip.x < index_tip.x - 0.02):
                    detected_sign = "thumbs_up"

                elif (index_tip.y < landmarks[6].y and
                      middle_tip.y > landmarks[10].y and
                      ring_tip.y > landmarks[14].y and
                      pinky_tip.y > landmarks[18].y):
                    detected_sign = "pointing"

                elif (index_tip.y < landmarks[6].y and
                      middle_tip.y < landmarks[10].y and
                      ring_tip.y > landmarks[14].y and
                      pinky_tip.y > landmarks[18].y):
                    detected_sign = "victory"

        if detected_sign and detected_sign != last_sign:
            sign_label = reverse_signs.get(detected_sign)
            if sign_label:
                show_sign(sign_label)
                speak_text(sign_label)
                last_sign = detected_sign

        cv2.imshow("Webcam Sign Detection (Press Q to Quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Button actions
def threaded_webcam_start():
    threading.Thread(target=start_webcam_detection, daemon=True).start()

btn_speech = tk.Button(root, text="Start Speech Detection 🎤", font=("Helvetica", 14), bg="#4caf50", fg="white", command=start_speech_detection)
btn_speech.pack(pady=10)

btn_webcam = tk.Button(root, text="Start Webcam Detection 📸", font=("Helvetica", 14), bg="#2196f3", fg="white", command=threaded_webcam_start)
btn_webcam.pack(pady=10)

btn_exit = tk.Button(root, text="Exit", font=("Helvetica", 14), bg="#f44336", fg="white", command=root.destroy)
btn_exit.pack(pady=20)

# Load sign images after GUI is initialized
load_images()

root.mainloop()
