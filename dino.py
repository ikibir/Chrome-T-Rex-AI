import cv2
import numpy as np
import mss
from win32.lib import win32con
from win32 import win32api
import win32gui
import keyboard
import time
from threading import Thread
import os, shutil
import random
from pynput.keyboard import Key, Listener

#################################################
template_over   = cv2.imread('Over.jpg',0)
template_dino   = cv2.imread('dino.jpg',0)
template_cactus = cv2.imread('cactus1.jpg',0)
template_cactus2 = cv2.imread('cactus2.jpg',0)
################################################
i=0
############################### #################
discount = 0.3
actions = ["up", "down"]
states = []
state_size, action_size = 50, 2
qtable = np.zeros((state_size, action_size))

#qtable = np.load("table.npy")

learning_rate = 0.6
max_steps = 99
gamma = 0.95
# Exploration parameters
epsilon = 1.0
max_epsilon = 1.0
min_epsilon = 0.01
decay_rate = 0.03
# List of rewards
rewards = []
################################################


def round10(x):

	return int(round(x/10)*10)

def click():
	keyboard.press('space')
	keyboard.release('space')
	time.sleep(0.1)
		
def shortclick():
	keyboard.press('space')
	keyboard.release('space')
	time.sleep(0.3)

def editFrame(img):
	x =  len(img[0])
	y =  len(img)
	img = img[x//6:,:]
	
	imgShow = cv2.resize(img,(500,300))
	imgSave = imgShow[:,50:]
	return imgShow,imgSave

def findTemplates(img):
	global  template_cactus,template_cactus2, template_dino, template_over

	temp_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	dino_img = temp_img[90:200,:]
	end_img = temp_img
	res_dino = cv2.matchTemplate(dino_img, template_dino, cv2.TM_CCOEFF_NORMED)
	res_cactus = cv2.matchTemplate(temp_img, template_cactus, cv2.TM_CCOEFF_NORMED)
	res_cactus2 = cv2.matchTemplate(temp_img, template_cactus2, cv2.TM_CCOEFF_NORMED)
	res_over = cv2.matchTemplate(end_img, template_over, cv2.TM_CCOEFF_NORMED)
	

	dino, cactus, over = False, False, False
	dx,dy, cx, cy =  0,0, 0,0 
	
	
	loc_dino = np.where(res_dino >= 0.6)
	loc_cactus2 = np.where(res_cactus2 >= 0.8)
	loc_cactus = np.where(res_cactus >= 0.7)
	loc_over = np.where(res_over >= 0.7)


	if len(loc_dino) > 0:
		if len(loc_dino[0]) > 0: 
			dino = True
	if len(loc_over) > 0:
		if len(loc_over[0]) > 0: 
			over = True
	if len(loc_cactus) > 0:
		if len(loc_cactus[0]) > 0: 
			cactus = True
	if len(loc_cactus2) > 0:
		if len(loc_cactus2[0]) > 0: 
			cactus = True
	
	for pt in zip(*loc_dino[::-1]):
		cv2.rectangle(img, (pt[0],pt[1]+90), (pt[0]+20, pt[1]+103 ), (0,255,255), 2) 
		dx,dy = pt[0], pt[1]
	for pt in zip(*loc_cactus[::-1]):
		cv2.rectangle(img, (pt[0],pt[1]), (pt[0]+10, pt[1]+10 ), (0,255,255), 2) 
		if pt[0]>dx:
			cx, cy = pt[0], pt[1]
	for pt in zip(*loc_cactus2[::-1]):
		cv2.rectangle(img, (pt[0],pt[1]), (pt[0]+10, pt[1]+10 ), (0,255,255), 2) 
		if pt[0]>dx :
			if cx == 0 or (cx>pt[0] and pt[0]!=0):
				cx, cy = pt[0], pt[1]

	

	return over, round10(dx),round10(dy), round10(cx),round10(cy)

def isscore(x, y):
	
	if not (x == 0 and y ==0):
		if (y-x)>=10:
			return True
	return False

def desicion(x, y):
	if random.random()<0.1:
		return True
	else:
		return False


i, passedTime, over = 0, 0, 0
episode = 1
dx,dy, cx,cy = 0, 0, 0, 0
startTime = time.time()
state, action, reward = 0, 0, 0
with mss.mss() as sct:
	# Part of the screen to capture
	while "Screen capturing":
	# Get raw pixels from the Browser, save it to a Numpy array
		try:
			hwnd = win32gui.FindWindow(None, r'chrome://dino/ - Google Chrome')
			dimensions = win32gui.GetWindowRect(hwnd)
			img = np.array(sct.grab(dimensions))
			readed = True
		except:
			print("Error When Finding Game Window!")
			break

		# GET INFOS
		x = cx
		bdx = dx
		img, imgSave = editFrame(img)
		over, dx, dy, cx, cy = findTemplates(img)

		if dx != 0:
			state = (cx - dx) // 10
			# ACTIONS
			if epsilon>0.2:
				exp_tradeoff = random.uniform(0, 1)
				if exp_tradeoff > epsilon:
				   action = np.argmax(qtable[state,:])
				else:
					action = random.randint(0,1)
				if action == 1:
					click()		
			else:
				action = np.argmax(qtable[state,:])
				if action == 1:
					click()		
			# RESULTS
			reward = 0

		if over:#img[100:101,250:251][0, 0, 0] == 83:
			print("Game Over")
			print("epside: ", episode)
			print("epsilon: ", epsilon)
			epsilon = min_epsilon + (max_epsilon - min_epsilon)*np.exp(-decay_rate*episode) 
			episode += 1
			reward = -100
			i = 0
			click()
			time.sleep(1)
		elif isscore(x, cx):
			reward = 100
			print("Score: ", i)
			i+=1
		elif action == 1:
			reward = -10

		qtable[state, action] = qtable[state, action] + learning_rate * (reward + gamma  - qtable[state, action])

		# Display the picture
		cv2.imshow("OpenCV/Numpy normal", img)

		# Press "q" to quit
		if cv2.waitKey(1) & 0xFF == ord("q"):
			cv2.destroyAllWindows()	
			np.save("table", qtable)
			finishGame = True
			break 
		# UPDATE
		
		if epsilon>0.2:
			time.sleep(0.1)
		  