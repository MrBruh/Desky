# Written by Michael Denissov
# Precompiled face detection models and help from https://www.pyimagesearch.com/2020/01/06/raspberry-pi-and-movidius-ncs-face-recognition/
# Thank you to the same link as above for providing the tutorials that I followed to use the models

from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import pickle
import time
import cv2
import os
import pygame
import sys
from pygame.locals import *

import serial
import time

def my_map(x, in_min, in_max, out_min, out_max):
    return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)

ser = serial.Serial("/dev/ttyAMA1", 9600)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--detector", required=True,
	help="path to OpenCV's deep learning face detector")
ap.add_argument("-m", "--embedding-model", required=True,
	help="path to OpenCV's deep learning face embedding model")
ap.add_argument("-r", "--recognizer", required=True,
	help="path to model trained to recognize faces")
ap.add_argument("-l", "--le", required=True,
	help="path to label encoder")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

protoPath = os.path.sep.join(["face_detection_model", "deploy.prototxt"])
modelPath = os.path.sep.join(["face_detection_model",
	"res10_300x300_ssd_iter_140000.caffemodel"])

detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)
detector.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

embedder = cv2.dnn.readNetFromTorch("face_embedding_model/openface_nn4.small2.v1.t7")
embedder.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

recognizer = pickle.loads(open("output/recognizer.pickle", "rb").read())
le = pickle.loads(open("output/le.pickle", "rb").read())

vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

fps = FPS().start()

#pygame stuff
pygame.init()

#Create a displace surface object
#DISPLAYSURF = pygame.display.set_mode((0, 0))
DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

mainLoop = True
w, h = pygame.display.get_surface().get_size()
print(w, h)
x = 0
y = 0
mouse_movement = []
pos_i = 0
mouse_movement.append(h/2)

cuteness = False
moving = "none"

def draw_normal():
	DISPLAYSURF.fill((0,0,0))
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 + 125, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 - 125, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 + 125, h/2), 50)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 - 125, h/2), 50)
	pygame.display.update()

def draw_happy():
	DISPLAYSURF.fill((0,0,0))
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 + 125, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 - 125, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 + 125, h/2), 50)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 - 125, h/2), 50)
	pygame.draw.circle(DISPLAYSURF, (255,20,147, 10), (w - 100, h - 100), 80)
	pygame.draw.circle(DISPLAYSURF, (255,20,147, 10), (100, h - 100), 80)
	pygame.display.update()

def draw_right():
	DISPLAYSURF.fill((0,0,0))
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 + 125 + 200, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 - 125 + 200, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 + 125 + 200, h/2), 50)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 - 125 + 200, h/2), 50)
	pygame.display.update()

def draw_left():
	DISPLAYSURF.fill((0,0,0))
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 + 125 - 200, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 - 125 - 200, h/2), 80)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 + 125 - 200, h/2), 50)
	pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 - 125 - 200, h/2), 50)
	pygame.display.update()

face_state = "normal"

draw_normal()
time_last_detected = time.perf_counter()
routine_mode = False

time_last_happy = 0
happy_mode = False

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			mainLoop = False
		if event.type == pygame.MOUSEMOTION:
			x,y = pygame.mouse.get_pos()

			if y > mouse_movement[pos_i]: # moving down

				if moving == "none":
					moving = "down"
				elif moving == "down":
					pass
				elif moving == "up":
					moving = "down"
					mouse_movement.append(y)
					pos_i += 1

			elif y < mouse_movement[pos_i]: # moving up

				if moving == "none":
					moving = "up"
				elif moving == "down":
					moving = "up"
					mouse_movement.append(y)
					pos_i += 1
				elif moving == "up":
					pass
			print(mouse_movement)
			if len(mouse_movement) == 6:
				pos_i = 1
				avg1 = 0
				avg2 = 0
				for pos in mouse_movement:
					if pos_i % 2 == 1:
						avg1 += pos
					else:
						avg2 += pos
				avg1 /= 2
				avg2 /= 2
				if abs(avg1-avg2) > 200:
					cuteness = True
					print("CUUUUUUUUUUUTE")
					ser.write(str.encode("jk@"))
					cuteness = False
					happy_mode = True
					time_last_happy = time.perf_counter()
					draw_happy()
				pos_i = 0
				mouse_movement.clear()
				moving = "none"
				mouse_movement.append(h/2)

			mouse_movement[pos_i] = y

	if time.perf_counter() - time_last_happy > 2 and happy_mode:
		draw_normal()
	pygame.display.update()

	frame = vs.read()

	frame = imutils.resize(frame, width=600)
	(h, w) = frame.shape[:2]

	
	imageBlob = cv2.dnn.blobFromImage(
		cv2.resize(frame, (300, 300)), 1.0, (300, 300),
		(104.0, 177.0, 123.0), swapRB=False, crop=False)


	detector.setInput(imageBlob)
	detections = detector.forward()

	if time.perf_counter() - time_last_detected > 20 and not routine_mode:
		routine_mode = True
		ser.write(str.encode("rk@"))
		print("rk")

	#print(time_last_detected, time.perf_counter(), time_last_detected - time.perf_counter())

	for i in range(0, detections.shape[2]):

		confidence = detections[0, 0, i, 2]

		if confidence > args["confidence"]:

			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")
			#print((startX+endX)/2)


			face = frame[startY:endY, startX:endX]
			(fH, fW) = face.shape[:2]


			if fW < 20 or fH < 20:
				
				continue

			time_last_detected = time.perf_counter()

			faceBlob = cv2.dnn.blobFromImage(cv2.resize(face,
				(96, 96)), 1.0 / 255, (96, 96), (0, 0, 0),
				swapRB=True, crop=False)
			embedder.setInput(faceBlob)
			vec = embedder.forward()


			preds = recognizer.predict_proba(vec)[0]
			j = np.argmax(preds)
			proba = preds[j]
			name = le.classes_[j]


			text = "{}: {:.2f}%".format(name, proba * 100)
			y = startY - 10 if startY - 10 > 10 else startY + 10
			cv2.rectangle(frame, (startX, startY), (endX, endY),
				(0, 0, 255), 2)
			position = (int)((startX + endX) / 2)

			command = ""

			if position >= 350:
				command = "t" + str(-1 * my_map(position, 350, 600, 170, 255)) + "k@"
				if face_state != "left":
					draw_left()
					face_state = "left"
			elif position <= 250:
				command = "t" + str(-1 * my_map(position, 0, 250, -255, -170)) + "k@"
				if face_state != "right":
					draw_right()
					face_state = "right"
			else:
				command = "sk"
				if face_state != "normal":
					draw_normal()
					face_state = "normal"
			routine_mode = False
			print(command)
			ser.write(str.encode(command))


			cv2.putText(frame, text, (startX, y),
				cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

	fps.update()


	#cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF


	if key == ord("q"):
		break

fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

cv2.destroyAllWindows()
vs.stop()

