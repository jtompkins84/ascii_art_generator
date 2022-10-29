import cv2
from werkzeug.utils import secure_filename

import symmap
from flask import Flask, request

app = Flask(__name__)


def __to_float(optional):
    if optional is not None:
        return float(optional)
    else:
        return None


def __read_image(path, scale=None, scale_x=None, scale_y=None):
    if scale is None:
        scale = 0.25
    if scale_x is None:
        scale_x = 2.0
    if scale_y is None:
        scale_y = 1.0

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, None, fx=(scale * scale_x), fy=(scale * scale_y), interpolation=cv2.INTER_AREA)
    return img


def __make_ascii_art(image, debug=False, distr_type=None):
    """
    Converts all images input as arguments to the program to ascii symbols using the value-to-symbol mapping.
    """
    if distr_type is None:
        distr_type = 'fill'
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

    form_input = request.form
    scale = __to_float(form_input.get('scale'))
    scale_x = __to_float(form_input.get('scale_x'))
    scale_y = __to_float(form_input.get('scale_y'))
    distr_type = form_input.get('distr_type')

    image = __read_image(f'./uploads/{filename}', scale, scale_x, scale_y)
    ascii_art = __make_ascii_art(image, distr_type=distr_type)
    return ascii_art


if __name__ == '__main__':
    app.run()
