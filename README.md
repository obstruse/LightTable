# LightTable?  Mini Green Screen?
![](images/hmm-25.png)
![](images/grr-66.png)
![](images/troll-25.png)

## Setup
- LCD monitor mounted horizontally.
- Raspberry Pi HQ camera mounted approximately 80cm above monitor
- 16mm lens
- Raspberry Pi 3
- PiTFT 320x240 display

  ![](images/camera-33.png)
## Software
- LCD LightTable keyboard commands:

Key | Description
-|-
q | Quit program
ESCAPE | Quit program
TFT #4 | Quit program
|    
r | Table color Red
g | Table color Green
b | Table color Blue
y | Table color Yellow
c | Table color Cyan
m | Table color Magenta
|
RIGHT | Table color increment
LEFT | Table color decrement
|
z | Enable/disable zoom
TFT #3 | Enable/disable zoom
|    
SPACE | Enable/disable menu
TFT #2 | Enable/disable menu
|
RETURN | Capture image
TFT #1 | Capture image

![](images/tens.jpg)

- TFT Display commands:

![](images/cam20230326-194558.jpg)

---
## Workflow
- White Balance
- Exposure
- Focus

  ![](images/focus50-small.png)

Larger version here: [Focus 50% Gray](images/focus50.png)

### Preview
### Capture
### Edit

![](images/tens-red2.png)











---
## Average


```
$ ./spectrometer/average -h
usage: average [-h] [-x WIDTH] [-y HEIGHT] [-v VIDEODEV] [-a AVERAGEITEMS] [-c PIXELCLIP]

Spectrometer

options:
  -h, --help            show this help message and exit
  -x WIDTH, --width WIDTH
  -y HEIGHT, --height HEIGHT
  -v VIDEODEV, --video VIDEODEV
  -a AVERAGEITEMS, --average AVERAGEITEMS
  -c PIXELCLIP, --clip PIXELCLIP
```

### Configuration file 

File located at: `./spectrometer/config.ini`.  Commented entries indicate default values:

File | Description
-|-
[Spectrometer] | section header
#width=1280 | image width
#height=720 | image height
#videoDev=/dev/video0 | USB camera device
#averageItems=20 | number of frames to average
#pixelClip=250 | Out Of Range warning level
#calibDefault=',,410,900' | default calibration settings, HG463 and EU611




Select a line through the camera spectrum image:  

![cameraImage](images/camImage.png)

Click `AVERAGE`, and wait a few moments for the image to settle down.  If the value of a pixel exceeds the Out Of Range warning level, a red mark will appear at the top of the column.


![Averaged](images/spectralAverage.png)

Click on `prefix` to set the file name prefix (e.g. 'cfl').  Click on `decription` to set the description (e.g. 'CFL 2700K').  Click `SAVE`.

Output is a JPG of the resulting average, and a CSV with the average of each pixel and the averages of each color. 

---
## Calibrate

```
$ ./spectrometer/calibrate -h
usage: calibrate [-h] CSVfile

Calibrate

positional arguments:
  CSVfile

options:
  -h, --help  show this help message and exit
```

Calibration uses __landmarks__ to calibrate the output:
- calibrate to landmarks in the spectrum (__CFL Calibration__)
- calibrate to landmarks in the camera response (__CIS Calibration__)



---
### CFL Calibration

[CFL Landmarks](https://commons.wikimedia.org/wiki/File:Fluorescent_lighting_spectrum_peaks_labelled.svg)
![CFL plain](images/cfl-plain.png)

 Type|Wavelength|&nbsp;
 -|-|-
 __CFL__ | 405nm | mercury
 &nbsp; | 436nm | mercury
 &nbsp; | 487nm | terbium
 &nbsp; | 542nm | terbium
 &nbsp; | 546nm | mercury
 &nbsp; | 611nm | europium
 &nbsp; | &nbsp; | &nbsp;

Click `CFL`.  Use the mouse to select the Eu611 peak on the right.  The keys Kp7,Kp9 (Q,E) can be used to fine-tune the selection.  Select the Hg436 peak on the left with the mouse; fine-tune with Kp1,Kp3 (Z,C):

![calibrate CFL](images/calibCFL.png)

Click `SAVE` - the settings are saved in the calibration file.

---
### CIS Calibration

[CIS Landmarks](https://photo.stackexchange.com/questions/122037/why-do-typical-imaging-sensor-colour-filter-spectral-responses-differ-so-much-fr)
![CIS plain](images/cis-plain.png)
 Type|Wavelength|&nbsp;
 -|-|-
 __CIS__ | 465nm | blue response peak
 &nbsp; | 532nm | green response peak
 &nbsp; | 596nm | red response peak
 &nbsp; | 529nm | the red bump
&nbsp; | &nbsp; | &nbsp;


Click `CIS`. Use the mouse to select the red response peak on the right and the blue response peak on the left.  Use the keys Kp7,Kp9 (Q,E) and Kp1,Kp3 (Z,C) to fine-tune the selection:

![calibrate CIS](images/calibCIS.png)

Click `SAVE` - the settings are saved in the calibration file.



---
## Plot

```
$ ./spectrometer/plot -h

Usage: ./spectrometer/plot [-H] [-I] [-L] [--CFL] [--CIS] [--INT] CSVfile

Plot Spectrum

Options:
    -H      Show this message
    -B      -B1 enable background image.  -B0 disable
    -L      -L1 enable landmarks display. -L0 disable
    --CFL   Plot pixel averages and CFL landmarks
    --CIS   Plot color averages and CIS landmarks
    --INT   Plot pixel averages as filled curve

    CSVfile Spectrum data to plot
```
Spectrum data is ploted with the spectrum background image in the range 375nm - 695nm.  Plot opens in gnuplot; use menu bar to save image.



![](images/uv-spectrum-20230106-113618-plot.png)
![](images/air-spectrum-20181215-164105-plot.png)
![](images/cfl-spectrum-20181215-123051-plot.png)
![Aurora](images/aurora.png)

You can also combine the plot options for different results:

![Everything](images/tower2.png)
![Zoom0](images/zoom1.png)
![Tower](images/tower.png)
![Sunrise](images/sunrise4.png)
