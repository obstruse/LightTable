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
# change to the program directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# read config file
config = ConfigParser()
config.read('config.ini')
exposure = config.getint('balanceEXP','exposure',fallback=10000)
iso     = config.getint('balanceEXP','iso',fallback=200)
magnify = config.getint('balanceEXP','magnify',fallback=4)
Rgain   = config.getfloat('balanceEXP','rgain',fallback=3.367)
Bgain   = config.getfloat('balanceEXP','bgain',fallback=1.539)
saturation = config.getint('balanceEXP','saturation',fallback=20)

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
pygame.mouse.set_visible(False)
font = pygame.font.SysFont(None,30)     # 'M' height is 15 pixels

WHITE = (255,255,255)
RED   = (255,0,0)
GREEN = (0,255,0)
BLUE  = (0,0,255)
BLACK = (0,0,0)

# --------------- display surfaces ---------------

# lcd - the LightTable 
class lcd :
    surface = pygame.display.set_mode((0,0),pygame.FULLSCREEN)  # - LCD monitor, 1920x1080
    currentColor = 0

    def white():
        lcd.surface.fill(WHITE)
        lcd.update()

    def color(color):
        rgb = pygame.Color(0)
        rgb.hsla = (color%360,100,50,100)
        lcd.surface.fill(rgb)
        lcd.update()
        lcd.currentColor = color

    def incr(incr):
        lcd.color(lcd.currentColor+incr)

    def on():
        lcd.color(lcd.currentColor)

    def off():
        lcd.surface.fill(BLACK)
        lcd.update()

    def update():
        pygame.display.flip()

# tft - camera control and preview
tftRes = (320,240)          
(width,height) = tftRes

class tft:
    surface = pygame.Surface(tftRes)    # - AdaFruit PiTFT, 320x240, 2.8inch, capacitive touch
    framebuffer = open("/dev/fb1","wb")
    # TFT backlight
    GPIO.setwarnings(False)
    GPIO.setup(18, GPIO.OUT)
    GPIO.output(18,GPIO.HIGH)

    def update():
        tft.framebuffer.seek(0)
        tft.framebuffer.write(tft.surface.convert(16,0).get_buffer())

    def blink():
        GPIO.output(18,GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(18,GPIO.HIGH)

    def close():
        tft.framebuffer.close()
        # TFT backlight
        GPIO.output(18,GPIO.LOW)

# --------------- initialize camera ---------------

from picamera import PiCamera
highRes = (2048,1520)
cameraRes = (tftRes)
camera = PiCamera(sensor_mode=0,resolution=cameraRes)
cameraRes = camera.resolution       # the actual resolution may not be the requested resolution
print(f"camera resolution: {cameraRes}\n")
cameraBuffer = bytearray(3*cameraRes[0]*cameraRes[1])

camera.framerate_range = (1,30)    # minimum FPS determines maximum exposure time

camera.iso           = iso

#camera.awb_mode      = 'auto'
camera.awb_mode      = 'off'
camera.awb_gains     = (Rgain,Bgain)

#camera.exposure_mode = 'auto'
camera.shutter_speed = exposure

camera.annotate_text_size = 20
camera.annotate_background = True
camera.rotation      = 180
camera.sharpness     = 30
camera.saturation    = saturation

# --------------- initialize touch ---------------

import evdev
touch = evdev.InputDevice('/dev/input/touchscreen')
touch.grab()        # the touchscreen events will be handled only by this program

# --------------- overlay surfaces ---------------

# button menu surface
buttonSurface = pygame.surface.Surface(tftRes)
buttonSurface.fill(BLACK)
buttonSurface.set_colorkey(BLACK)

# zoom menu surface
zoomSurface = pygame.Surface(tftRes)
zoomSurface.fill(BLACK)
zoomSurface.set_colorkey(BLACK)

# (the zoom settings)
zoomLevel = tftRes[0]/cameraRes[0]/magnify  # ratio of LCD : camera (size of zoom box)
zoomX = zoomY = (1-zoomLevel)/2             # zoom box in middle

# --------------- menu buttons and text ---------------

# keyboard stuff
K = {
    K_q:    {"handler":"keyQuit()","desc":"Quit program"},
    27:     {"handler":"keyQuit()","desc":"Quit program (TFT #4 or Escape key)"},
    
    K_r:    {"handler":"lcd.color(0)","desc":"Table color Red"},
    K_g:    {"handler":"lcd.color(120)","desc":"Table color Green"},
    K_b:    {"handler":"lcd.color(240)","desc":"Table color Blue"},
    K_y:    {"handler":"lcd.color(60)","desc":"Table color Yellow"},
    K_c:    {"handler":"lcd.color(180)","desc":"Table color Cyan"},
    K_m:    {"handler":"lcd.color(300)","desc":"Table color Magenta"},
    K_w:    {"handler":"lcd.white()","desc":"Table color White"},

    K_RIGHT:{"handler":"lcd.incr(10)","desc":"Table color increment"},
    K_LEFT: {"handler":"lcd.incr(-10)","desc":"Table color decrement"},

    K_z:    {"handler":"keyZoom()","desc":"Enable/disable zoom"},
    23:     {"handler":"keyZoom()","desc":"Enable/disable zoom (TFT #3)"},
    
    K_SPACE:{"handler":"keyMenu()","desc":"Enable/disable menu"},
    22:     {"handler":"keyMenu()","desc":"Enable/disable menu (TFT #2)"},

    K_RETURN:{"handler":"keyCapture()","desc":"Capture image"},
    17:     {"handler":"keyCapture()","desc":"Capture image (TFT #1)"},
}

# nothing to display for keys.  Maybe a help screen?

# zoom panning rectangles
Z = {
    "Left": {"row":8, "col":1, "type":"zoom", "handler":"zoomHorizontal(0.02)"},
    "Right":{"row":8, "col":3, "type":"zoom", "handler":"zoomHorizontal(-0.02)"},
    "Up":   {"row":4, "col":2, "type":"zoom", "handler":"zoomVertical(0.02)"},
    "Down": {"row":13, "col":2, "type":"zoom", "handler":"zoomVertical(-0.02)"},
}

def zoomDisplay(key):
    # convert row,col to x,y
    x = int(width/3.0 * (Z[key]['col'] - 0.5))
    y = int(height/16.0 * (Z[key]['row'] - 0.5))

    pygame.draw.circle(zoomSurface, WHITE,   (x,y), int(height/6.0),2)
    pygame.draw.circle(zoomSurface, (1,1,1), (x,y), int(height/6.0),1)

    boxRect = pygame.Rect(0,0, int(width/3.0),int(height/3.0) )
    boxRect.center = (x,y)
    Z[key]['rect'] = boxRect

# TFT buttons and text
B = {
    "AWB":  {"row":2, "col":1, "type":"label", "value":"AWB"},
    "Rgain":{"row":5, "col":1, "type":"output", "value":"0.0"},
    "Bgain":{"row":7, "col":1, "type":"output", "value":"0.0"},
    "HOLD1":{"row":12, "col":1, "type":"button", "value":"HOLD", "enabled":True, "handler":"AWBhold(key)"},
    "SAVE1":{"row":15, "col":1, "type":"button", "value":"SAVE", "enabled":False, "handler":"AWBsave(key)"},
    
    "EXP":  {"row":2, "col":2, "type":"label", "value":"EXP"},
    "exposure":{"row":5, "col":2, "type":"output", "value":"1/0"},
    "HOLD2":{"row":12, "col":2, "type":"button", "value":"HOLD", "enabled":True, "handler":"EXPhold(key)"},
    "SAVE2":{"row":15, "col":2, "type":"button", "value":"SAVE", "enabled":False, "handler":"EXPsave(key)"},
    
    "ISO":  {"row":2, "col":3, "type":"label", "value":"ISO"},
    "sensitivity":{"row":5, "col":3, "type":"output", "value":"0"},
    "ISOplus":{"row":9, "col":3, "type":"button", "value":"+", "enabled":False, "handler":"ISOincr(key,100)"},
    "ISOminus":{"row":12, "col":3, "type":"button", "value":"-", "enabled":False, "handler":"ISOincr(key,-100)"},
    "SAVE3":{"row":15, "col":3, "type":"button", "value":"SAVE", "enabled":False, "handler":"ISOsave(key)"},
    } 

def buttonDisplay(key):
    # if the line is shorter, need to clear previous box
    pygame.draw.rect(buttonSurface, BLACK, B[key].get('rect',(0,0,0,0)),0)

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
            pygame.draw.rect(buttonSurface,RED,boxRect,0)
        pygame.draw.rect(buttonSurface,WHITE,boxRect,2) 

    tempSurface = font.render(B[key].get('value',''),True,B[key].get('color',WHITE))
    tempRect = tempSurface.get_rect()
    tempRect.center = (x,y)
    buttonSurface.blit(tempSurface, tempRect)

    B[key]['rect'] = tempRect
    if B[key].get('type','none') == 'button' :
        # the button size  (boxRect) is bigger than the text size (tempRect)
        B[key]['rect'] = boxRect

#------------------------------------------------

active = True
zoom = False
menu = True

#------------------------------------------------
#------------------------------------------------
def main() :
    (X,Y) = (0,0)

    # tableColor
    lcd.color(240)

    # display all of the objects
    for key in list(B):
        buttonDisplay(key)
    for key in list(Z):
        zoomDisplay(key)

    while active:   
        # touch events (button/zoom)
        #      (to view touch events:  python -m evdev.evtest)
        touchEvent, nonEvent, nonEvent = select.select([touch],[], [], 0 )
        if touchEvent:
            events = touch.read()
        else:
            events = []

        for e in events:
            # if no menu, ignore the events:
            if not menu:
                break

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
    
                    if zoom :
                        for key in list(Z) :
                            if Z[key]['type'] == 'zoom' and Z[key]['rect'].collidepoint(pos):
                                eval (Z[key]['handler'])
                                break
                    
                    else:
                        for key in list(B) :
                            if B[key]['type'] == 'button' and B[key]['rect'].collidepoint(pos) :
                                eval(B[key]['handler'])
                                break
                
        # key events
        events = pygame.event.get()
        for e in events:
            if ( e.type == KEYUP) :
                for key in list(K):
                    if key == e.key:
                        eval(K[key]['handler'])
                        break

        #camera.annotate_text = f"speed: {camera.exposure_speed} - {camera.shutter_speed}"
        camera.capture(cameraBuffer, format='rgb')
        cameraImage = pygame.image.frombuffer(cameraBuffer,cameraRes, 'RGB')
        tft.surface.blit(cameraImage,(0,0))

        # update button menu overlay
        B['exposure']['value'] = f"1/{int(1000000/camera.exposure_speed)}"
        B['sensitivity']['value'] = f"{camera.iso}"
        B['Bgain']['value'] = f"{float(camera.awb_gains[1]):.3f}"
        B['Rgain']['value'] = f"{float(camera.awb_gains[0]):.3f}"
        
        for key in list(B):
            if B[key]['type'] == 'output' :
                buttonDisplay(key)

        # add menu overlay
        if menu:
            if zoom:
                # add zoom menu overlay
                tft.surface.blit(zoomSurface,(0,0))
            else:
                # add button menu overlay
                tft.surface.blit(buttonSurface,(0,0))

        tft.update()

    tft.close()
    camera.close()
    pygame.quit()

    # GPIO.cleanup() sets all pins to INPUT
    # unfortunately, when the TFT pin switches from OUTPUT to INPUT, it turns the TFT back on
    # Since the only other pins used are all INPUT anyway, don't need/want to use this
    #GPIO.cleanup()

#------------------------------------------------
#------------------------------------------------

#------------------------------------------------
# key handlers
def keyQuit():
    global active
    active = False

def keyMenu():
    global menu
    menu = not menu

def keyZoom():
    global zoom
    zoom = not zoom

    if zoom :
        camera.zoom=(zoomX,zoomY,zoomLevel,zoomLevel)
    else:
        camera.zoom=(0,0,1,1)

def keyCapture():
    #fileName = "%s/cam%s.jpg" % (os.path.expanduser('~/Pictures'), time.strftime("%Y%m%d-%H%M%S",time.localtime()) )
    pathName = os.path.expanduser('~/Pictures')
    timeStamp= time.strftime("%Y%m%d-%H%M%S",time.localtime())

    camera.resolution = highRes

    lcd.off()
    camera.capture(f"{pathName}/cam{timeStamp}.jpg")
    lcd.on()
    camera.capture(f"{pathName}/cam{timeStamp}-mask.jpg")

    camera.resolution = cameraRes

    tft.blink()

#------------------------------------------------
# zoom handlers
def zoomHorizontal(incr):
    global zoomX
    zoomX += incr
    if zoomX < 0:
        zoomX = 0
    if zoomX + zoomLevel > 1:
        zoomX = 1 - zoomLevel
    camera.zoom=(zoomX,zoomY,zoomLevel,zoomLevel)

def zoomVertical(incr):
    global zoomY
    zoomY += incr
    if zoomY < 0:
        zoomY = 0
    if zoomY + zoomLevel > 1:
        zoomY = 1 - zoomLevel   
    camera.zoom=(zoomX,zoomY,zoomLevel,zoomLevel)

#------------------------------------------------
# button handlers
def AWBhold(key):
    button_enabled = not B[key]['enabled']

    if button_enabled :
        # hold
        saveGains = camera.awb_gains
        camera.awb_mode = 'off'
        camera.awb_gains = saveGains
    else:
        # float
        camera.awb_mode = 'auto'

    B[key]['enabled'] = button_enabled
    buttonDisplay(key)
    tft.blink()

def AWBsave(key):
    (Rgain, Bgain) = camera.awb_gains

    # write config
    config.set('balanceEXP', 'Rgain',f"{float(Rgain):.3f}")
    config.set('balanceEXP', 'Bgain',f"{float(Bgain):.3f}")
    with open('config.ini', 'w') as f:
            config.write(f)

    tft.blink()
    
def EXPhold(key):
    button_enabled = not B[key]['enabled']

    if button_enabled :
        # hold
        saveEXP = camera.exposure_speed
        camera.shutter_speed = saveEXP
    else:
        # float
        camera.shutter_speed = 0
        camera.exposure_mode = 'auto'

    B[key]['enabled'] = button_enabled
    buttonDisplay(key)
    tft.blink()

def EXPsave(key):
    # write config
    config.set('balanceEXP', 'exposure',f"{camera.exposure_speed}")
    with open('config.ini', 'w') as f:
            config.write(f)

    tft.blink()

def ISOincr(key,incr):
    iso = camera.iso
    iso += incr

    if iso > 800 :
        iso = 800
    if iso < 100 :
        iso = 100
    
    camera.iso = iso
    tft.blink()

def ISOsave(key):
    # write config
    config.set('balanceEXP', 'iso',f"{camera.iso}")
    with open('config.ini', 'w') as f:
            config.write(f)

    tft.blink()

#------------------------------------------------
#------------------------------------------------
if __name__ == '__main__':
    main()
