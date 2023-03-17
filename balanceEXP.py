#!/usr/bin/python3

import os
#os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['DISPLAY'] = ":0.0"

import gc
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
shutter = config.getint('PiCamera','shutter',fallback=30)
iso     = config.getint('PiCamera','iso',fallback=200)
magnify = config.getint('PiCamera','magnify',fallback=4)

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

# initialize camera

from picamera import PiCamera
#cameraRes = (4056,3040)
highRes = (2048,1520)
cameraRes = (320,240)
camera = PiCamera(sensor_mode=0,resolution=cameraRes)
cameraRes = camera.resolution       # the actual resolution may not be the requested resolution
print(f"{cameraRes=}\n")
cameraBuffer = bytearray(3*cameraRes[0]*cameraRes[1])

camera.framerate_range = (20,30)    # preview minimum is 10 FPS.
#camera.framerate = 1
camera.iso           = iso
camera.awb_mode      = 'auto'
camera.exposure_mode = 'auto'
camera.annotate_text_size = 20
camera.annotate_background = True
camera.rotation      = 180
camera.sharpness     = 30

print(f"{camera.framerate=}\n")
print(f"{camera.framerate_range=}\n")

# initialize display surfaces

# lcd - the LightTable - LCD monitor, 1920x1080
lcd = pygame.display.set_mode((1920,1080),pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# tft - camera control - AdaFruit PiTFT, 320x240, 2.8inch, capacitive touch
tft = pygame.Surface((320,240))
tftRes = tft.get_size()
tftRect = tft.get_rect()
# frame buffer
#frameBuffer = open("/dev/fb1","wb")

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

# touch rectangles
width = tftRect.width
height = tftRect.height
Left  = pygame.Rect( (0             , int(height/4)   ) ,(int(width/4), int(height/2) ) )
Right = pygame.Rect( (int(width*3/4), int(height/4)   ) ,(int(width/4), int(height/2) ) )
Up    = pygame.Rect( (int(width/4)  , 0               ) ,(int(width/2), int(height/4) ) )
Down  = pygame.Rect( (int(width/4)  , int(height*3/4) ) ,(int(width/2), int(height/4) ) )

# menu buttons and text
EXPnum  = font.render('9999', True, WHITE)
EXPnumPos  = EXPnum.get_rect(center=(width-60,60))

ISOnum  = font.render('9999', True, WHITE)
ISOnumPos  = ISOnum.get_rect(center=(width-60,120))

AWBtext = font.render('(Fraction(689, 256), Fraction(269, 128))', True, WHITE)
AWBtextPos = AWBtext.get_rect(center=( int(width/2),180) )


#frameBuffer = open("/dev/fb1","wb")
# Output to framebuffer #1
# takes the place of pygame.display.update()
def displayUpdate():
    # We open the TFT screen's framebuffer as a binary file. 
    # Note that we will write bytes into it, hence the "wb" operator
    ###f = open("/dev/fb1","wb")
    # global frameBuffer
    frameBuffer = open("/dev/fb1","wb")
    # According to the TFT screen specs, it supports only 16bits pixels depth
    # pygame surfaces use 24bits pixels depth by default, 
    # but the surface itself provides a very handy method to convert it.
    # once converted, we write the full byte buffer of the pygame surface 
    # into the TFT screen framebuffer like we would in a plain file:
    frameBuffer.write(tft.convert(16,0).get_buffer())
    #frameBuffer.flush()
    # We can then close our access to the framebuffer
    # ...or we can leave it open...
    # can't get it to work unless FB is opened each time, so might as well close too
    frameBuffer.close()
    # why is there a wait here..v
    #time.sleep(0.1)

def tableUpdate(tableColor):
    lcdColor = pygame.Color(0)
    lcdColor.hsla = (tableColor%360,100,50,100)
    lcd.fill(lcdColor)
    pygame.display.flip()


zoom = False
zoomLevel = tftRes[0]/cameraRes[0]/magnify  # ratio of LCD : camera (size of zoom box)
zoomX = zoomY = (1-zoomLevel)/2             # zoom box in middle

tftOn()
tableColor = 0
tableUpdate(tableColor)

active = True
while active:
    
    # touch events
    # to view touch events:
    #     python -m evdev.evtest
    touchEvent, nonEvent, nonEvent = select.select([touch],[], [], 0 )
    if touchEvent:
        events = touch.read()
    else:
        events = []

    for e in events:
        if e.type == evdev.ecodes.EV_ABS:       # touch coordinates
            if e.code == 53:
                X = e.value
            if e.code == 54:
                Y = e.value
                    
        if e.type == evdev.ecodes.EV_KEY:    
            if e.code == 330 and e.value == 1:  # touch execute

                # collide with buttons
                # e.values are pixel coordinates, no conversion required
                pos = (X, Y)
                #pygame.draw.circle(tft, (255, 0, 0), pos , 2, 2)

                if zoom :
                    if Left.collidepoint(pos) :
                        zoomX -= 0.05
                        if zoomX < 0 :
                            zoomX = 0

                    if Right.collidepoint(pos) :
                        zoomX += 0.05
                        if zoomX + zoomLevel > 1 :
                            zoomX = 1 - zoomLevel

                    if Up.collidepoint(pos) :
                        zoomY -= 0.05
                        if zoomY < 0:
                            zoomY = 0

                    if Down.collidepoint(pos) :
                        zoomY += 0.05
                        if zoomY + zoomLevel > 1 :
                            zoomY = 1 - zoomLevel

                    camera.zoom=(zoomX,zoomY,zoomLevel,zoomLevel)

             
    # key and button events
    events = pygame.event.get()
    for e in events:
        if ( e.type == KEYUP) :

            # exit
            # GPIO #27 has the same value as escape
            if e.key == K_q or e.key == 27:
                # quit
                active = False                

            # table color
            if e.key == K_r :
                tableColor = 0
            if e.key == K_y :
                tableColor = 60
            if e.key == K_g :
                tableColor = 120
            if e.key == K_c :
                tableColor = 180
            if e.key == K_b :
                tableColor = 240
            if e.key == K_m :
                tableColor = 300

            if e.key == K_RIGHT :
                tableColor += 10
            if e.key == K_LEFT :
                tableColor -= 10

            tableUpdate(tableColor)

            # zoom
            if e.key == K_z or e.key == 23:
                zoom = not zoom

                if zoom :
                    camera.zoom=(zoomX,zoomY,zoomLevel,zoomLevel)
                else:
                    camera.zoom=(0,0,1,1)

            # capture
            if e.key == K_RETURN or e.key == 17:
                print(f"awb_gains: {camera.awb_gains}\n")

                fileName = "%s/cam%s.jpg" % (os.path.expanduser('~/Pictures'), time.strftime("%Y%m%d-%H%M%S",time.localtime()) )

                print(fileName)
                camera.resolution = highRes
                camera.capture(fileName)
                camera.resolution = cameraRes

            # save settings
            if e.key == K_KP4 or e.key == K_g:
                config.set('PiCamera', 'shutter', str(shutter))
                with open('config.ini', 'w') as f:
                    config.write(f)

    camera.capture(cameraBuffer, format='rgb')
    cameraImage = pygame.image.frombuffer(cameraBuffer,cameraRes, 'RGB')
    tft.blit(cameraImage,(0,0))

    EXPnum = font.render('%d'%int(camera.exposure_speed/1000), True, WHITE)
    textPos = EXPnum.get_rect(center=EXPnumPos.center)
    tft.blit(EXPnum,textPos)

    ISOnum = font.render('%d'%camera.iso, True, WHITE)
    textPos = ISOnum.get_rect(center=ISOnumPos.center)
    tft.blit(ISOnum,textPos)

    AWBtext = font.render(f"{float(camera.awb_gains[0]):.3f},{float(camera.awb_gains[1]):.3f}", True, WHITE)
    textPos = AWBtext.get_rect(center=AWBtextPos.center)
    tft.blit(AWBtext,textPos)

    displayUpdate()

tftOff()
#frameBuffer.close()
camera.close()
pygame.quit()

# GPIO.cleanup() sets all pins to INPUT
# unfortunately, when the TFT pin switches from OUTPUT to INPUT, it turns the TFT back on
# Since the only other pins used are all INPUT anyway, don't need/want to use this
#GPIO.cleanup()

