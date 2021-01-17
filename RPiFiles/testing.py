# A file for quick tests not related to OpenVINO

import serial
import pygame
import sys
from pygame.locals import *
from time import sleep

pygame.init()

#Create a displace surface object
DISPLAYSURF = pygame.display.set_mode((0, 0))
#DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
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

pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 + 125, h/2), 80)
pygame.draw.circle(DISPLAYSURF, (0,0,100, 50), (w/2 - 125, h/2), 80)
pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 + 125, h/2), 50)
pygame.draw.circle(DISPLAYSURF, (0,0,255), (w/2 - 125, h/2), 50)

while mainLoop:
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
					cuteness = False
				pos_i = 0
				mouse_movement.clear()
				moving = "none"
				mouse_movement.append(h/2)

			mouse_movement[pos_i] = y

			

	pygame.display.update()

pygame.quit()

#def my_map(x, in_min, in_max, out_min, out_max):
#    return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)
#
#ser = serial.Serial("/dev/ttyAMA1", 9600)
#
#position = 400
#
#command = my_map(position, 350, 600, 110, 255)
#
#print(command)
#
#ser.write(b'd110k')
#
#sleep(2)
#
#ser.write(b'sk')
