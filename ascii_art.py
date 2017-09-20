#! /usr/bin/python

import cv2
import csv
import argparse

IMAGES = list()
FILE_NAMES = list()
VALUE_MAP = './value_map'
DEBUG = False
SCALE = 0.25
value_to_symbol_map = dict()

def __handle_args():
    """
    Handles program arguments.

    :param args: list of arguments
    :return: False if no image files were entered
    """
    global IMAGES, SCALE, DEBUG
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scale', type=float, nargs=1, default=0.25)
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('files', type=str, nargs='+')
    args = parser.parse_args()

    images = args.files
    if len(images) < 1:
        return False

    SCALE = args.scale
    if type(SCALE) is not float:
        SCALE = float(SCALE[0])

    # Load image files into memory as numpy arrays, scale them according to input, and append to IMAGES list.
    for image in images:
        img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        # 2 * SCALE on X-axis --> images need to be 'stretched' horizontally in order not to appear 'squished' after
        # being converted to ascii text.
        img = cv2.resize(img, None, fx=(SCALE*2.0), fy=SCALE, interpolation=cv2.INTER_AREA)
        if img.size == 0:
            print 'Unable to read file \'' + image + '\'.'
        else:
            IMAGES.append(img)
            FILE_NAMES.append(image[:-4])

    DEBUG = args.debug

    return True


def __load_value_map():
    """
    Loads the value-to-symbol mapping used to map gray scale values to ascii symbols.
    """
    with open(VALUE_MAP, 'r') as val_map_file:
        reader = csv.DictReader(val_map_file)
        for row in reader:
            value_to_symbol_map[int(row['value'])] = row['symbol']

        val_map_file.close()
        print 'value-to-symbol map loaded..'


def __make_ascii_art():
    """
    Converts all images input as arguments to the program to ascii symbols using the value-to-symbol mapping.
    """
    for i in range(len(IMAGES)):
        img = IMAGES[i]
        file_name = FILE_NAMES[i]
        height, width = img.shape[:2]
        result = list()
        for i in range(height):
            row = None
            # Map gray scale values to ascii characters and concat to 'row' character string.
            for j in range(width):
                if row is None:
                    row = value_to_symbol_map[int(img[i][j])]
                else:
                    row += value_to_symbol_map[int(img[i][j])]
            # Append row to result list. Rows are appended in order from top to bottom.
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

    __load_value_map()
    __make_ascii_art()


if __name__ == '__main__':


    main()
