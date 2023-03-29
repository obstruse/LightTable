# LCD LightTable
![](images/hmm-25.png)
![](images/grr-66.png)
![](images/troll-25.png)

---
## Setup
- LCD monitor mounted horizontally
- PiTFT 320x240 display
- Raspberry Pi HQ camera mounted approximately 80cm above monitor
- 16mm lens
- Raspberry Pi 3


  ![](images/camera-33.png)
---
## Software
### Keyboard Commands:

Key | Description
:-:|:-
q | Quit program
ESCAPE | Quit program
TFT #4 | Quit program
r | Table color Red
g | Table color Green
b | Table color Blue
y | Table color Yellow
c | Table color Cyan
m | Table color Magenta
RIGHT | Table color increment
LEFT | Table color decrement
z | Enable/disable zoom
TFT #3 | Enable/disable zoom   
SPACE | Enable/disable menu
TFT #2 | Enable/disable menu
RETURN | Capture image
TFT #1 | Capture image

![](images/tens.jpg)

---

### TFT Display commands:
- AWB - Average White Balance
  - Red Gain
  - Blue Gain
  - **HOLD**: prevent the AWB from changing
  - **SAVE**: write current AWB values to config.ini.
- EXP - Exposure
  - Exposure time
  - **HOLD**: prevent the EXP from changing
  - **SAVE**: write current EXP value to config.ini.
- ISO - Sensitivity
  - ISO
  - **+**: increment ISO by 100.  maximum 800
  - **-**: decrement ISO by 100.  minimum 100
  - **SAVE**: write current ISO value to config.ini.


![](images/cam20230326-194558.jpg)

### TFT Buttons

Button | Description
-|-
#1 | Capture image
#2 | Enable/disable menu
#3 | Enable/disable zoom
#4 | Quit 

### TFT Zoom
- Press 'z' on keyboard, or TFT #3 to enter zoom mode
- Zoom magnification is determined by config.ini key 'magnify'. Default is 4X
- If menu is enabled, four circles will appear to move the zoom window

![](images/TFTzoom.png)

---

### Configuration File

Program settings are stored in `config.ini` located in the same directory as `lighttable.py`

&nbsp;|Configuration Settings|&nbsp;
-|-|-
**Key**|**Description**|**Default**
exposure | exposure time in usec | 10000
iso | sensitivity | 200
magnify | zoom magnification | 4
Rgain | red gain | 3.367
Bgain | blue gain | 1.539
saturation | image saturation | 20


---
## Workflow

### White Balance
- Cover LCD with White Card
- Turn on final lighting
- Release HOLD on AWB
- When Red/Blue gains stop changing, set HOLD
- SAVE the AWB to config.ini
### Focus
- Place the focus target on the LCD. Raise the target to approximately the height of the object.
- Open camera iris, adjust focus.  Lock focus.
  |![](images/focus50-small.png)|
  |:-:|
  |Focus Target|
  |(larger version here: [Focus 50% Gray](images/focus50.png))|

### Exposure

- Preview
- Capture
### Edit
- Open background image in gimp
- Open 'as Layers...' mask image
- Select the mask layer, Add Alpha Channel ( Layer | Transparency | Add Alpha Channel )
- Select mask background color ( Select | By Color ).  Adjust Threshold as needed (e.g. 16)
- Invert the selection ( Select | Invert ) The object is now selected.
- Delete the selection.  The object on the top mask layer (which has reflections from the table color) is removed revealing the object below (taken when the table light was off)
- Invert the selection ( Select | Invert ) The mask background is now selected.
- Replace background, etc...

### Script-fu


  
  ![](images/triangles-50.png)
---
![](images/tens-red2.png)
![](images/clamp-50.png)
![](images/clamp2-50.png)








