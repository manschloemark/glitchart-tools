# Glitch Art Tools

Scripts and GUI programs that can be used to make glitch art.  
Not all of it is literal glitch art, but it's all the same style.  

I'll be adding more tools to perform all sorts of glitches, some emulating actual glitches.

## Requirements
- Python 3.6+
- PySide6
- Pillow (PIL)

## Running
To run the GUI use `python glitchart-qt.py`

![An image of the GUI](./examples/gui.jpg)

## Features
![Example Image](./examples/banquet.jpg)

### Pixelsorting
![Sorting rows of an image](./examples/diagonaltracers.jpg)
Sort pixels from the image

### Line Offsets
![Columns offset by cos line number](./examples/offset.jpg)
Rotate lines by some amount or by using sine and cosine

### Line Offsets With Aura
![Offset overlayed on the original](./examples/auraoffset.jpg)
Same as regular line offsets but the rotated image is overlayed on top of the original with less opacity.

### Swizzling / Channel Swapping
![Turning an RGB image into a BGR](./examples/bgr.jpg)
Swap RGB channels of pixels. I call it swizzling in reference to OpenGL [swizzling](https://www.khronos.org/opengl/wiki/Data_Type_(GLSL)#Swizzling)

### Tips
- Click and drag on the image you are editing to edit a specific part of it. 
- You can set the output of a glitch to the next input using the 'Use as input' button.


