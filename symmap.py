#! /usr/bin/python

import os
import cv2
import csv


# symbol_to_norm_map format:             {ord(symbol): norm value}
# clamped_value_to_symbol_dict format:   {ord(symbol): clamped norm value}
# sorted_symbol_list format:             list of symbols sorted by norm values
# value_to_symbol_map format:            {int(clamped norm): ord(symbol)}


def __build_symbol_to_norm_map(symbols_filepath='./symbols.png'):
    """
    Builds the symbol-to-norm dictionary mapping.

    Calculates the norm of each symbol in symbol.png image.
    Black being equal to 0, and white equal to MAX, where MAX is the maximum norm value.

    :return: symbol_to_norm_dict in format:  {ord(symbol): norm value}
    """
    # symbols.png is an image file composed of ASCII characters from ordinal values 32 to 126 arranged in a grid
    # like a "sprite sheet."
    img = cv2.imread(symbols_filepath, cv2.IMREAD_GRAYSCALE)
    if img.size == 0:
        print 'symmap.py unable to read \'' + symbols_filepath + '\'.'
        return
    # create a directory for images of each individual character
    curr_path = os.getcwd()
    curr_path += '/symbols'
    if not os.path.exists(curr_path):
        os.mkdir(curr_path)
    # Divides symbol.png into cells. Cell width and height was derived using an image editor.
    img_dem = img.shape[:2]
    cell_pixel_width = 9
    cell_pixel_height = 17
    img_cell_width = img_dem[1] / cell_pixel_width
    img_cell_height = img_dem[0] / cell_pixel_height
    # iterate cell-by-cell, calculating the vector norm of each cell in the image and storing the
    symbol_to_norm_dict = dict()
    for i in range(img_cell_height):
        for j in range(img_cell_width):
            if i == img_cell_height - 1 and j == img_cell_width - 1:
                break
            y_pos = i * cell_pixel_height
            x_pos = j * cell_pixel_width
            cell = img[y_pos:y_pos + cell_pixel_height, x_pos:x_pos + cell_pixel_width]
            cell_num = 32 + (i * 16) + j
            cv2.imwrite('./symbols/' + str(32 + (i * 16) + j) + '.png', cell) # creates images of symbols for debugging purposes
            # cv2.norm Gives the vector norm of the image.
            # The more black there is in the image, the lower the norm value.
            cell_norm = int(cv2.norm(cell, cv2.NORM_L1))
            symbol_to_norm_dict[cell_num] = cell_norm

    return symbol_to_norm_dict

def __build_clamped_symbol_to_norm_map(symbol_to_norm_map):
    """
    Builds the clamped-norm dictionary mapping, which is a symbol-to-norm mapping where the norm values are clamped
    inclusively between 0 and 255.

    :returns: clamped_norm_dict in format:  {ord(symbol): clamped norm value}
    """
    clamped_norm_dict = symbol_to_norm_map.copy()
    norm_values = [symbol_to_norm_map[x] for x in symbol_to_norm_map] # extract norm values from symbol_to_norm_dict
    max_val = max(norm_values)
    min_val = min(norm_values)
    for key in clamped_norm_dict:
        val = symbol_to_norm_map[key]
        clamped_norm_dict[key] = int((val - min_val) * (255.0 / (max_val - min_val)))

    return clamped_norm_dict


def __build_value_to_symbol_map(clamped_value_to_symbol_map):
    """
    Builds a reduced value-to-symbol dictionary mapping based on the clamped values of the clamped-norm dictionary.

    A value can only be associated with one symbol. If a value already has a mapping to a symbol and both symbols are
    a special character, the new symbol will become the mapping for the value. Otherwise, no action is taken and
    the unmapped symbol is ignored. The result is a dictionary where each key represents a value between 0 and 255.
    """
    value_to_symbol_map = dict()
    for key in clamped_value_to_symbol_map:
        value = clamped_value_to_symbol_map[key]
        if value not in value_to_symbol_map:
            value_to_symbol_map[value] = key
        else:
            sym = value_to_symbol_map[value]
            if __is_special_char(sym) and __is_special_char(key):
                value_to_symbol_map[value] = key
    return value_to_symbol_map


def __build_sorted_symbol_list(value_to_symbol_map):
    """
    Builds a list of ascii symbols sorted in order of least-to-greatest norm values and
    based on the values in the symbol-to-norm dictionary mapping.
    """
    sorted_values = [val for val in value_to_symbol_map]
    sorted_values.sort()
    sorted_symbol_list = [value_to_symbol_map[val] for val in sorted_values]

    return sorted_symbol_list


def __fill_distribution_value_map(value_to_symbol_map, sorted_symbols_list):
    """
    Distributes value-to-symbol mappings by filling gaps between clamped norm values of symbols.

    Due to the fact that there are fewer than 256 visible ascii symbols, each gray-scale value between 0 and 255 cannot
    receive a unique character mapping. Fill Distribution uses clamped values of the symbols in the reduced sorted
    symbols list to distribute value-to-symbol mappings, so that each value between 0 and 255 receives a mapping to an
    ascii character. The algorithm "fills" the gaps between clamped-norm values of each symbol in the sorted reduced
    symbols list by splitting the gap in mappings of the values between two consecutive symbols

    e.g. Two consecutive symbols from the reduced sorted symbols list have clamped norm values: '@' => 0 and 'Q' => 42.
    Gray-scale values 0 through 42 will be split in half, such that values 0 through 20 will be mapped to '@' and
    values 21 trough 42 are mapped to 'Q'.
    """

    for sym in sorted_symbols_list:
        val = value_to_symbol_map[sym]
        print '{' + str(val) + ' : ' + chr(sym) + ' = \'' + str(sym) + '\' }'

    curr = 0
    for val in range(256):
        if val in value_to_symbol_map:
            print str(val) + ' found in value_to_symbol_map. Symbol: ' + value_to_symbol_map[val]
            if sorted_symbols_list[curr] != ord(value_to_symbol_map[val]):
                curr += 1
            continue
        else:
            curr_sym = sorted_symbols_list[curr]
            next_sym = sorted_symbols_list[curr + 1]
            next_val = value_to_symbol_map[next_sym]
            R = range(val, next_val)
            half = int(len(R) / 2) + (val - 1)
            print R
            for i in R:
                val += 1
                if i < half:
                    value_to_symbol_map[i] = chr(curr_sym)
                else:
                    value_to_symbol_map[i] = chr(next_sym)


def __even_distribution_value_map(value_to_symbol_map, sorted_symbols_list):
    """
    Distributes value-to-symbol mappings by giving values equal partitions.

    Due to the fact that there are fewer than 256 visible ASCII symbols, each gray-scale value between 0 and 255 cannot
    receive a unique character mapping. Even Distribution evenly partitions the gray-scale color space values (0 - 255)
    across all available ASCII symbols, approximately 67 total symbols when using the reduced symbols list.

    e.g. If partition size is determined to be 4 values, each consecutive 4 values in the value-to-symbol map will
    map to the same symbol. Values 0 - 3 map to '@', values 4 - 7 map to 'Q', etc.
    """
    print 'len(sorted_reduced_symbols) = ' + str(len(sorted_symbols_list))
    for i in range(len(sorted_symbols_list)):
        print chr(sorted_symbols_list[i]) + ' :: i = ' + str(i)

    sz = len(sorted_symbols_list)
    part_sz = int(256 / sz)
    rem = 256 % sz
    val = 0
    for i in range(len(sorted_symbols_list)):
        sym = sorted_symbols_list[i]
        if rem > 0:
            pad_partition = part_sz + 1
            for i in range(pad_partition):
                value_to_symbol_map[val] = chr(sym)
                val += 1
            rem -= 1
        else:
            for i in range(part_sz):
                value_to_symbol_map[val] = chr(sym)
                val += 1


def __write_value_map(value_to_symbol_map, file_name='value_map'):
    f = open(file_name, 'w')
    writer = csv.DictWriter(f, fieldnames=['value', 'symbol'])

    writer.writeheader()
    for val, sym in value_to_symbol_map.items():
        writer.writerow({'value': val, 'symbol': sym })

    f.close()


def __is_special_char(sym):
    return (sym < 65 or (sym > 90 and sym < 97) or sym > 122)


def main():
    for val in range(256):
        sym = value_to_symbol_map[val]
        print '{' + str(val) + ' : ' + str(ord(sym)) + ' = \'' + sym + '\' }'


symbol_to_norm_map = __build_symbol_to_norm_map()
clamped_symbol_to_norm_map = __build_clamped_symbol_to_norm_map(symbol_to_norm_map)
value_to_symbol_map = __build_value_to_symbol_map(clamped_symbol_to_norm_map)
sorted_symbol_list = __build_sorted_symbol_list(value_to_symbol_map)
# temporary algorithm to convert the ordinal values of the symbols to actual ascii characters
for key in value_to_symbol_map:
    value_to_symbol_map[key] = chr(value_to_symbol_map[key])
__write_value_map(value_to_symbol_map)

if __name__ == '__main__':
    main()
