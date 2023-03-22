#!/usr/bin/python3

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['DISPLAY'] = ":0.0"

import gc
import time

import pygame
from pygame.locals import *
import select

# --------------- config file ---------------
from configparser import ConfigParser
import argparse
# change to the python directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# read config file
config = ConfigParser()
config.read('config.ini')
exposure = config.getint('balanceEXP','exposure',fallback=10000)
iso     = config.getint('balanceEXP','iso',fallback=200)
magnify = config.getint('balanceEXP','magnify',fallback=4)
Rgain   = config.getfloat('balanceEXP','rgain',fallback=3.367)
Bgain   = config.getfloat('balanceEXP','bgain',fallback=1.539)

# --------------- GPIO ---------------
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def callback(channel):
    #print(f"callback channel {channel}")
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=channel))

GPIO.add_event_detect(17, GPIO.FALLING, callback=callback, bouncetime=300)
GPIO.add_event_detect(22, GPIO.FALLING, callback=callback, bouncetime=300)
GPIO.add_event_detect(23, GPIO.FALLING, callback=callback, bouncetime=300)
GPIO.add_event_detect(27, GPIO.FALLING, callback=callback, bouncetime=300)

# --------------- initialize pygame display environment ---------------
pygame.font.init()
pygame.display.init()
font = pygame.font.SysFont(None,30)     # 'M' height is 15 pixels

WHITE = (255,255,255)
RED   = (255,0,0)
BLACK = (0,0,0)

# display surfaces

# lcd - the LightTable - LCD monitor, 1920x1080
lcd = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

def LCDupdate(tableColor):
    lcdColor = pygame.Color(0)
    lcdColor.hsla = (tableColor%360,100,50,100)
    lcd.fill(lcdColor)
    pygame.display.flip()

# tft - camera control 
tftRes = (320,240)          # - AdaFruit PiTFT, 320x240, 2.8inch, capacitive touch
tft = pygame.Surface(tftRes)

class TFT:
    def __init__(self):
        self.framebuffer = open("/dev/fb1","wb")
        # TFT backlight
        GPIO.setwarnings(False)
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18,GPIO.HIGH)

    def update(self):
        self.framebuffer.seek(0)
        self.framebuffer.write(tft.convert(16,0).get_buffer())

    def close(self):
        self.framebuffer.close()
        # TFT backlight
        GPIO.output(18,GPIO.LOW)

TFTdisplay = TFT()

# text surface
txtSurface = pygame.surface.Surface(tftRes)
txtSurface.fill(BLACK)
txtSurface.set_colorkey(BLACK)

# --------------- initialize camera ---------------

from picamera import PiCamera
highRes = (2048,1520)
cameraRes = (tftRes)
camera = PiCamera(sensor_mode=0,resolution=cameraRes)
cameraRes = camera.resolution       # the actual resolution may not be the requested resolution
print(f"{cameraRes=}\n")
cameraBuffer = bytearray(3*cameraRes[0]*cameraRes[1])

camera.framerate_range = (1,30)    # minimum FPS determines maximum exposure time

camera.iso           = iso

camera.awb_mode      = 'auto'
#camera.awb_mode      = 'off'
#camera.awb_gains     = (Rgain,Bgain)

#camera.shutter_speed = exposure
camera.exposure_mode = 'auto'

camera.annotate_text_size = 20
camera.annotate_background = True
camera.rotation      = 180
camera.sharpness     = 30

# --------------- initialize touch ---------------

import evdev
touch = evdev.InputDevice('/dev/input/touchscreen')
touch.grab()        # the touchscreen events will be handled only by this program

# TFT touch rectangles
(width,height) = tftRes
Left  = pygame.Rect( (0             , int(height/4)   ) ,(int(width/4), int(height/2) ) )
Right = pygame.Rect( (int(width*3/4), int(height/4)   ) ,(int(width/4), int(height/2) ) )
Up    = pygame.Rect( (int(width/4)  , 0               ) ,(int(width/2), int(height/4) ) )
Down  = pygame.Rect( (int(width/4)  , int(height*3/4) ) ,(int(width/2), int(height/4) ) )

# --------------- menu buttons and text ---------------
B = {
    "AWB":  {"row":2, "col":1, "type":"label", "value":"AWB"},
    "Rgain":{"row":5, "col":1, "type":"output", "value":"0.0"},
    "Bgain":{"row":7, "col":1, "type":"output", "value":"0.0"},
    "HOLD1":{"row":12, "col":1, "type":"button", "value":"HOLD", "enabled":True, "handler":"AWBhold()"},
    "SAVE1":{"row":15, "col":1, "type":"button", "value":"SAVE", "enabled":False, "handler":"AWBsave()"},
    
    "EXP":  {"row":2, "col":2, "type":"label", "value":"EXP"},
    "exposure":{"row":5, "col":2, "type":"output", "value":"1/0"},
    "HOLD2":{"row":12, "col":2, "type":"button", "value":"HOLD", "enabled":True, "handler":"EXPhold()"},
    "SAVE2":{"row":15, "col":2, "type":"button", "value":"SAVE", "enabled":False, "handler":"EXPsave()"},
    
    "ISO":  {"row":2, "col":3, "type":"label", "value":"ISO"},
    "sensitivity":{"row":5, "col":3, "type":"output", "value":"0"},
    "ISOplus":{"row":9, "col":3, "type":"button", "value":"+", "enabled":False, "handler":"ISOplus()"},
    "ISOminus":{"row":12, "col":3, "type":"button", "value":"-", "enabled":False, "handler":"ISOminus()"},
    "SAVE3":{"row":15, "col":3, "type":"button", "value":"SAVE", "enabled":False, "handler":"ISOsave()"},
    } 



def TXTdisplay(key):
    # if the line is shorter, need to clear previous box
    pygame.draw.rect(txtSurface, BLACK, B[key].get('rect',(0,0,0,0)),0)

    # convert row,col to x,y
    x = int(width/3.0 * (B[key]['col'] - 0.5))
    y = int(height/16.0 * (B[key]['row'] - 0.5))

    # buttons have a border and a status background
    if B[key].get('type','none') == 'button' :
        # buttons are 1/3 the width and 3/16 of height
        boxRect = pygame.Rect(0,0,int(width/3.0), int(3*height/16.0))
        boxRect.center = (x,y)
        if B[key].get('enabled',False) :
            # draw highlighted color
            pygame.draw.rect(txtSurface,RED,boxRect,0)
        pygame.draw.rect(txtSurface,WHITE,boxRect,2) 

    tempSurface = font.render(B[key].get('value',''),True,B[key].get('color',WHITE))
    tempRect = tempSurface.get_rect()
    tempRect.center = (x,y)
    txtSurface.blit(tempSurface, tempRect)

    B[key]['rect'] = tempRect
    if B[key].get('type','none') == 'button' :
        # the button size  (boxRect) is bigger than the text size (tempRect)
        B[key]['rect'] = boxRect

# button handlers
def AWBhold():
    button_enabled = not B['HOLD1']['enabled']

    if button_enabled :
        camera.awb_mode = 'off'
    else:
        camera.awb_mode = 'auto'

    B['HOLD1']['enabled'] = button_enabled
    TXTdisplay('HOLD1')


zoom = False
zoomLevel = tftRes[0]/cameraRes[0]/magnify  # ratio of LCD : camera (size of zoom box)
zoomX = zoomY = (1-zoomLevel)/2             # zoom box in middle

tableColor = 0
LCDupdate(tableColor)

# display all of the objects
for key in list(B):
    TXTdisplay(key)

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
                
                else:
                    for key in list(B) :
                        if B[key]['type'] == 'button' and B[key]['rect'].collidepoint(pos) :
                            eval(B[key]['handler'])
                            break



             
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

            LCDupdate(tableColor)

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
                fileName2 = "%s/cam%s-TFT.jpg" % (os.path.expanduser('~/Pictures'), time.strftime("%Y%m%d-%H%M%S",time.localtime()) )
                fileName3 = "%s/cam%s-TFT-2.jpg" % (os.path.expanduser('~/Pictures'), time.strftime("%Y%m%d-%H%M%S",time.localtime()) )

                print(fileName)
                pygame.image.save(tft,fileName2)
                camera.resolution = highRes
                camera.capture(fileName)
                camera.resolution = cameraRes

            # save settings
            #if e.key == K_KP4 or e.key == K_g:
            #    config.set('PiCamera', 'shutter', str(shutter))
            #    with open('config.ini', 'w') as f:
            #        config.write(f)

    #camera.annotate_text = f"speed: {camera.exposure_speed} - {camera.shutter_speed}"
    camera.capture(cameraBuffer, format='rgb')
    cameraImage = pygame.image.frombuffer(cameraBuffer,cameraRes, 'RGB')
    tft.blit(cameraImage,(0,0))

    # update text overlay

    B['exposure']['value'] = f"1/{int(1000000/camera.exposure_speed)}"
    TXTdisplay('exposure')

    B['sensitivity']['value'] = f"{camera.iso}"
    TXTdisplay('sensitivity')

    B['Bgain']['value'] = f"{float(camera.awb_gains[1]):.3f}"
    TXTdisplay('Bgain')
    B['Rgain']['value'] = f"{float(camera.awb_gains[0]):.3f}"
    TXTdisplay('Rgain')

    # add text overlay
    tft.blit(txtSurface,(0,0))
    TFTdisplay.update()

TFTdisplay.close()
camera.close()
pygame.quit()

# GPIO.cleanup() sets all pins to INPUT
# unfortunately, when the TFT pin switches from OUTPUT to INPUT, it turns the TFT back on
# Since the only other pins used are all INPUT anyway, don't need/want to use this
#GPIO.cleanup()

