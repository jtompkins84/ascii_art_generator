# Ascii Art Generator
Simple server which converts image to ASCII art string.

## Requirements for Usage
- OpenCV-Python
- Numpy
- Flask

## Usage
- Change to directory and run on terminal/command-line:

```./ascii_art.py```

or

```python ascii_art.py```

development server will run on localhost:5000

- Send POST-request to this server with header ```Content-type: multipart/form-data```, attached image (as form field named "image") and optional arguments
- Get response with raw ASCII-art string

## Optional arguments
- ```scale: float```
- ```scale_x: float```
- ```scale_y: float```
- ```invert: bool```
- ```distr_type: str ('even', 'normal' or 'fill')```
