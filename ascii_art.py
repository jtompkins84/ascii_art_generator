#!/usr/bin/env python

import cv2
import argparse
import symmap

IMAGES = list()
FILE_NAMES = list()
VALUE_MAP = './value_map'
SCALE = 0.25
value_to_ascii_map = dict()

def __handle_args():
    """
    Handles program arguments.

    :param args: list of arguments
    :return: False if no image files were entered
    """
    global IMAGES, SCALE, SCALE_X, SCALE_Y, DEBUG, DISTR_TYPE
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scale', type=float, nargs=1, default=0.25,
                        help="Scales the image by this factor before generating the ASCII art text file.")
    parser.add_argument('-x', '--scale-x', type=float, nargs=1, default=2.25,
                        help="Scales the width of the image by the following factor before generating the ASCII art text file. Default value works best with Monospace font.")
    parser.add_argument('-y', '--scale-y', type=float, nargs=1, default=1.0,
                        help="Scales the height of the image by the following factor before generating the ASCII art text file. Default value works best with Monospace font.")
    parser.add_argument('--debug', action='store_true',
                        help="Prints some useful debug information.")
    parser.add_argument('-d', '--distribution', choices=['even', 'fill', 'normal'],
                        default='normal', help="Try different distributions to achieve better results!")
    parser.add_argument('files', type=str, nargs='+', help="The images files to convert to ASCII art.")
    args = parser.parse_args()

    images = args.files
    if len(images) < 1:
        return False

    SCALE = args.scale
    if type(SCALE) is not float:
        SCALE = float(SCALE[0])
    SCALE_X = args.scale_x
    SCALE_Y = args.scale_y

    # Load image files into memory as numpy arrays, scale them according to input, and append to IMAGES list.
    for image in images:
        img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        # 2 * SCALE on X-axis --> images need to be 'stretched' horizontally in order not to appear 'squished' after
        # being converted to ascii text.
        img = cv2.resize(img, None, fx=(SCALE*SCALE_X), fy=(SCALE*SCALE_Y), interpolation=cv2.INTER_AREA)
        if img.size == 0:
            print 'Unable to read file \'' + image + '\'.'
        else:
            IMAGES.append(img)
            FILE_NAMES.append(image[:-4])

    DEBUG = args.debug
    DISTR_TYPE = args.distribution

    return True


def __make_ascii_art():
    """
    Converts all images input as arguments to the program to ascii symbols using the value-to-symbol mapping.
    """
    for i in range(len(IMAGES)):
        img = IMAGES[i]
        file_name = FILE_NAMES[i]
        value_to_ascii_map = symmap.get_value2ascii_map(img, DISTR_TYPE)
        h, w = img.shape[:2]
        test = None
        result = list()
        for i in range(h):
            row = None
            # Map gray scale values to ascii characters and concat to 'row' character string.
            for j in range(w):
                if row is None:
                    row = value_to_ascii_map[int(img[i][j])]
                else:
                    row += value_to_ascii_map[int(img[i][j])]
            # Append row to result list. Rows a   re appended in order from top to bottom.
            if DEBUG:
                print "width= " + str(w) + "len(row)= " + str(len(row))
            result.append(row)

        # Write ascii symbols to text file.
        with open(file_name + '.txt', 'w') as out_file:
            for row in result:
                out_file.write(row)
                out_file.write('\n')
            out_file.close()
            print 'Wrote ' + file_name + '.txt..'


def main():
    if not __handle_args() or len(IMAGES) < 1:
        print 'No valid image file argument was given.'
        return

    __make_ascii_art()


if __name__ == '__main__':


    main()
