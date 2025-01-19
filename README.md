# edge-overlay
Detects all edges currently on screen, and draws them highlighted in green on a global overlay. It also measures the fps at which the detection is running, which are displayed in blue in the top-left corner. This project was meant as a test to see if I could work with screen analysis and screen overlays in Python, and may only be compatible with Windows.

## Example
![Screenshot 2025-01-19 085129](https://github.com/user-attachments/assets/d5e4a089-d07d-4ef3-aa20-6ab06e3a7c20)

## Language
Python

## Modules
Overlay: PyQt6
<br>
Screen capture: mss
<br>
Edge detection: cv2
<br>
Math: numpy
<br>
Timing: time
<br>
System interaction: sys, ctypes
