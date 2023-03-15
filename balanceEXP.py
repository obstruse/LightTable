#!/usr/bin/python3

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import time

import pygame
from pygame.locals import *
import select

# config file
from configparser import ConfigParser
import argparse
# change to the python directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# read config file
config = ConfigParser()
config.read('config.ini')
#shutter = config.getint('PiCamera','shutter',fallback=30)
iso     = config.getint('PiCamera','iso',fallback=200)

# setup buttons
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# TFT backlight
GPIO.setwarnings(False)     # want to leave #18 OUTPUT and set to zero at end of program. It generates warning...
GPIO.setup(18, GPIO.OUT)

def tftOn():
    GPIO.output(18,GPIO.HIGH)

def tftOff():
    GPIO.output(18,GPIO.LOW)

def callback(channel):
    print(f"callback channel {channel}")
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=channel))

GPIO.add_event_detect(17, GPIO.FALLING, callback=callback, bouncetime=300)
GPIO.add_event_detect(22, GPIO.FALLING, callback=callback, bouncetime=300)
GPIO.add_event_detect(23, GPIO.FALLING, callback=callback, bouncetime=300)
GPIO.add_event_detect(27, GPIO.FALLING, callback=callback, bouncetime=300)

# initialize pygame display environment
pygame.font.init()
pygame.display.init()
font = pygame.font.SysFont(None,30)

WHITE = (255,255,255)
BLACK = (0,0,0)

timer = pygame.time.Clock()

# initialize camera
from picamera import PiCamera
#cameraRes = (4056,3040)
#cameraRes = (2048,1520)
cameraRes = (320,240)
#cameraRes = (640,480)
camera = PiCamera(sensor_mode=0,resolution=cameraRes)
cameraRes = camera.resolution       # the actual resolution may not be the requested resolution
print(f"camera res: {cameraRes}\n")
cameraBuffer = bytearray(3*cameraRes[0]*cameraRes[1])

camera.framerate_range = (10,30)    # preview minimum is 10 FPS.
#camera.framerate = 1
camera.iso           = iso
camera.awb_mode      = 'auto'
camera.exposure_mode = 'auto'
camera.annotate_text_size = 20
camera.annotate_background = True

print(f"framerate {camera.framerate}\n")
print(f"framerate_range {camera.framerate_range}\n")

print("cam initialized")

# initialize display surface for use on TFT
lcd = pygame.Surface((320,240))
#lcd = pygame.display.set_mode((640,480),pygame.FULLSCREEN)      # pixel dimension of LCD is 320,240, OS configured to 640,480
lcdRes = lcd.get_size()
lcdRect = lcd.get_rect()

# initialize touch
import evdev
touch = evdev.InputDevice('/dev/input/touchscreen')
# We make sure the events from the touchscreen will be handled only by this program
# (so the mouse pointer won't move on X when we touch the TFT screen)
touch.grab()
# Prints some info on how evdev sees our input device
#print(touch)
# Even more info for curious people
#print(touch.capabilities())

# don't need this...
def getPixelsFromCoordinates(coords):
    return (coords)

# touch rectangles
width = lcdRect.width
height = lcdRect.height
Left  = pygame.Rect((0        , height/4)   ,(width/4, height/2) )
Right = pygame.Rect((width*3/4, height/4)   ,(width/4, height/2) )
Up    = pygame.Rect((width/4  , 0       )   ,(width/2, height/4) )
Down  = pygame.Rect((width/4  , height*3/4) ,(width/2, height/4) )

# menu buttons and text
EXPnum  = font.render('9999', True, WHITE)
EXPnumPos  = EXPnum.get_rect(center=(width-60,60))

ISOnum  = font.render('9999', True, WHITE)
ISOnumPos  = ISOnum.get_rect(center=(width-60,120))




# Output to framebuffer #1
# takes the place of pygame.display.update()
def displayUpdate():
    # We open the TFT screen's framebuffer as a binary file. Note that we will write bytes into it, hence the "wb" operator
    f = open("/dev/fb1","wb")
    # According to the TFT screen specs, it supports only 16bits pixels depth
    # Pygame surfaces use 24bits pixels depth by default, but the surface itself provides a very handy method to convert it.
    # once converted, we write the full byte buffer of the pygame surface into the TFT screen framebuffer like we would in a plain file:
    f.write(lcd.convert(16,0).get_buffer())
    # We can then close our access to the framebuffer
    f.close()
    # why is there a wait here..v
    #time.sleep(0.1)

zoom = False
zoomLevel = lcdRes[0]/cameraRes[0]/2        # ratio of LCD : camera (size of zoom box)
zoomX = zoomY = (1-zoomLevel)/2             # zoom box in middle

##lcd.fill((0,0,0))
##displayUpdate()
###camera.start_preview()
tftOn()

active = True
while active:
    timer.tick(20)
    
    touchEvent, nonEvent, nonEvent = select.select([touch],[], [], 0 )
    if touchEvent:
        events = touch.read()
    else:
        events = []

    for e in events:
        if e.type == evdev.ecodes.EV_ABS:   # touch coordinates
            if e.code == 53:
                X = e.value
            if e.code == 54:
                Y = e.value
                    
        if e.type == evdev.ecodes.EV_KEY:    
            if e.code == 330 and e.value == 1:  # touched
                # collide with buttons
                p = getPixelsFromCoordinates((X, Y))
                pygame.draw.circle(lcd, (255, 0, 0), p , 2, 2)
             
    events = pygame.event.get()
    for e in events:
        if ( e.type == KEYUP) :
            print(f"keys: {e.key}")
            if e.key == K_q or e.key == 27:
                # quit
                active = False                

            if e.key == K_z or e.key == 23:
                zoom = not zoom

                if zoom :
                    camera.zoom=(zoomX,zoomY,zoomLevel,zoomLevel)
                else:
                    camera.zoom=(0,0,1,1)

            if e.key == K_w or e.key == 17:
                timeStart = time.time()
                camera.capture("testCapture.jpg")
                print(f"time: {time.time() - timeStart}")

            # shutter speed (the keyboard I want to use doesn't have a key pad!!... so KP7-4-1 == T-G-B and KP8-5-2 == Y-H-N 
            #if e.key == K_KP7 or e.key == K_KP1 or e.key == K_t or e.key == K_b:
            #    if e.key == K_KP7 or e.key == K_t:
            #        shutter += 1
            #    else :
            #        shutter -= 1
            #    if shutter < 1 :
            #        shutter = 1
            #    if shutter > 20 :
            #        camera.framerate = 20
            #    else:
            #        camera.framerate = shutter
            #    camera.shutter_speed = int (1000000/shutter)

            # save settings
            if e.key == K_KP4 or e.key == K_g:
                config.set('PiCamera', 'shutter', str(shutter))
                with open('config.ini', 'w') as f:
                    config.write(f)

    ##lcd.fill(BLACK)
    camera.capture(cameraBuffer, format='rgb')
    cameraImage = pygame.image.frombuffer(cameraBuffer,cameraRes, 'RGB')
    lcd.blit(cameraImage,(0,0))

    EXPnum = font.render('%d'%camera.exposure_speed, True, WHITE)
    textPos = EXPnum.get_rect(center=EXPnumPos.center)
    lcd.blit(EXPnum,textPos)

    ISOnum = font.render('%d'%camera.iso, True, WHITE)
    textPos = ISOnum.get_rect(center=ISOnumPos.center)
    lcd.blit(ISOnum,textPos)

    if camera.exposure_speed:
        speed = int(1/camera.exposure_speed*1000000)
    else :
        speed = 0
    camera.annotate_text = f"Shutter: 1/{speed} ISO: {camera.iso}"

    
    displayUpdate()


tftOff()
camera.close()
pygame.quit()

# GPIO.cleanup() sets all pins to INPUT
# unfortunately, when the TFT pin switches from OUTPUT to INPUT, it turns the TFT back on
# Since the only other pins used are all INPUT anyway, don't need/want to use this
#GPIO.cleanup()

