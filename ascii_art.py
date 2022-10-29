import cv2
from werkzeug.utils import secure_filename

import symmap
from flask import Flask, request

app = Flask(__name__)


def __read_image(path, scale=0.25, scale_x=2.0, scale_y=1.0):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, None, fx=(scale * scale_x), fy=(scale * scale_y), interpolation=cv2.INTER_AREA)
    return img


def __make_ascii_art(image, debug=False, distr_type='fill'):
    """
    Converts all images input as arguments to the program to ascii symbols using the value-to-symbol mapping.
    """
    value_to_ascii_map = symmap.get_value2ascii_map(image, distr_type)
    h, w = image.shape[:2]
    result = list()
    for i in range(h):
        row = None
        # Map gray scale values to ascii characters and concat to 'row' character string.
        for j in range(w):
            if row is None:
                row = value_to_ascii_map[int(image[i][j])]
            else:
                row += value_to_ascii_map[int(image[i][j])]
        # Append row to result list. Rows are appended in order from top to bottom.
        if debug:
            print("width= " + str(w) + "len(row)= " + str(len(row)))
        result.append(row)

    return '\n'.join(result)


@app.route('/', methods=['POST'])
def main():
    file = request.files['image']
    if file.filename == '':
        raise Exception('No loaded file')
    filename = secure_filename(file.filename)
    file.save(f'./uploads/{filename}')
    image = __read_image(f'./uploads/{filename}')
    ascii_art = __make_ascii_art(image)
    return ascii_art


if __name__ == '__main__':
    app.run()
