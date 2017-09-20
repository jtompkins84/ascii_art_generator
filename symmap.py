#! /usr/bin/python

import os
import cv2
import csv


symbol_to_norm_dict = dict() # symbol_to_norm_dict in format:  {ord(symbol): norm value}
clamped_norm_dict = dict()   # clamped_norm_dict in format:  {ord(symbol): clamped norm value}
sorted_symbol_list = list()  # sorted by norm values
value_to_symbol_map = dict() # value_to_symbol_map in format:  {grayscale value: symbol}


def __build_symbol_to_norm_dict():
    """
    Builds the symbol-to-norm dictionary mapping.

    Calculates the norm of each symbol in symbol.png image.
    Black being equal to 0, and white equal to MAX, where MAX is the maximum norm value.

    symbol_to_norm_dict in format:  {ord(symbol): norm value}
    """
    # symbols.png is an image file composed of ASCII symbols from 32 to 126
    img = cv2.imread('symbols.png', cv2.IMREAD_GRAYSCALE)
    if img.size == 0:
        print 'symmap.py unable to read symbols.png.'
        return

    curr_path = os.getcwd()
    curr_path += '/symbols'
    if not os.path.exists(curr_path):
        os.mkdir(curr_path)

    img_dem = img.shape[:2]
    cell_pixel_height = 17
    cell_pixel_width = 9
    img_cell_height = img_dem[0] / cell_pixel_height
    img_cell_width = img_dem[1] / cell_pixel_width

    for i in range(img_cell_height):
        for j in range(img_cell_width):
            if i == img_cell_height - 1 and j == img_cell_width - 1:
                break
            y_pos = i * cell_pixel_height
            x_pos = j * cell_pixel_width
            cell = img[y_pos:y_pos + cell_pixel_height, x_pos:x_pos + cell_pixel_width]
            cell_num = 32 + (i * 16) + j
            cv2.imwrite('./symbols/' + str(32 + (i * 16) + j) + '.png', cell)

            cell_norm = int(cv2.norm(cell, cv2.NORM_L1))
            symbol_to_norm_dict[cell_num] = cell_norm


def __build_sorted_symbol_list():
    """
    Builds a list of ascii symbols sorted in order of least-to-greatest norm values and
    based on the values in the symbol-to-norm dictionary mapping.
    """
    for key in symbol_to_norm_dict:
        i = 0
        for i in range(len(sorted_symbol_list)):
            val = symbol_to_norm_dict[key]
            key2 = sorted_symbol_list[i]
            val2 = symbol_to_norm_dict[key2]

            if val < val2:
                break

        sorted_symbol_list.insert(i, key)

    min_key = sorted_symbol_list[0]
    min_val = symbol_to_norm_dict[min_key]
    for key in symbol_to_norm_dict:
        val = symbol_to_norm_dict[key]
        symbol_to_norm_dict[key] = val - min_val


def __build_clamped_norm_dict():
    """
    Builds the clamped-norm dictionary mapping, which is a symbol-to-norm mapping where the norm values are clamped
    inclusively between 0 and 255.

    clamped_norm_dict in format:  {ord(symbol): clamped norm value}
    """
    global clamped_norm_dict
    if symbol_to_norm_dict is None or sorted_symbol_list is None:
        return

    clamped_norm_dict = symbol_to_norm_dict.copy()
    max_value = symbol_to_norm_dict[sorted_symbol_list[-1]]
    for key in clamped_norm_dict:
        clamped_norm_dict[key] =  int(float(clamped_norm_dict[key]) * (255.0 / max_value))


def __build_reduced_value_to_symbol_map(even_distributrion=True):
    """
    Builds a reduced value-to-symbol dictionary mapping based on the clamped values of the clamped-norm dictionary.

    Symbols that share norm values with other symbols are eliminated. Each value between 0 and 255 will be mapped
    to a symbol using one of the provided distributions.
    :param even_distribution: when True, even distribution is used, else "fill" distribution is used.
    """
    global value_to_symbol_map
    for key in clamped_norm_dict:
        value = clamped_norm_dict[key]
        if value not in value_to_symbol_map:
            value_to_symbol_map[value] = chr(key)
        else:
            sym = value_to_symbol_map[value]
            if __is_special_char(sym) and not __is_special_char(key):
                continue
            else:
                value_to_symbol_map[value] = chr(key)

    if even_distributrion:
        __even_distribution_value_map()
    else:
        __fill_distribution_value_map()


def __build_reduced_sorted_symbol_list():
    """
    Builds a list of symbols sorted by norm values.

    Only ascii symbols that are in the reduced value-to-symbol map are
    appended to this list. Ascii symbols that do not have unique clamped-norm-value mappings have been filtered out.

    :return: list containing ascii order integer values sorted by their clamped norm values
    """
    global value_to_symbol_map
    sorted_reduced_symbols = list()
    cur_val = -1
    for sym in sorted_symbol_list:
        val = clamped_norm_dict[sym]
        if val != cur_val:
            cur_val = val
            sorted_reduced_symbols.append(ord(value_to_symbol_map[val]))

    return sorted_reduced_symbols


def __fill_distribution_value_map():
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
    global value_to_symbol_map
    sorted_reduced_symbols = __build_reduced_sorted_symbol_list()

    for sym in sorted_reduced_symbols:
        val = clamped_norm_dict[sym]
        print '{' + str(val) + ' : ' + chr(sym) + ' = \'' + str(sym) + '\' }'

    curr = 0
    for val in range(256):
        if val in value_to_symbol_map:
            print str(val) + ' found in value_to_symbol_map. Symbol: ' + value_to_symbol_map[val]
            if sorted_reduced_symbols[curr] != ord(value_to_symbol_map[val]):
                curr += 1
            continue
        else:
            curr_sym = sorted_reduced_symbols[curr]
            next_sym = sorted_reduced_symbols[curr + 1]
            next_val = clamped_norm_dict[next_sym]
            R = range(val, next_val)
            half = int(len(R) / 2) + (val - 1)
            print R
            for i in R:
                val += 1
                if i < half:
                    value_to_symbol_map[i] = chr(curr_sym)
                else:
                    value_to_symbol_map[i] = chr(next_sym)


def __even_distribution_value_map():
    """
    Distributes value-to-symbol mappings by giving values equal partitions.

    Due to the fact that there are fewer than 256 visible ASCII symbols, each gray-scale value between 0 and 255 cannot
    receive a unique character mapping. Even Distribution evenly partitions the gray-scale color space values (0 - 255)
    across all available ASCII symbols, approximately 67 total symbols when using the reduced symbols list.

    e.g. If partition size is determined to be 4 values, each consecutive 4 values in the value-to-symbol map will
    map to the same symbol. Values 0 - 3 map to '@', values 4 - 7 map to 'Q', etc.
    """
    global value_to_symbol_map
    sorted_reduced_symbols = __build_reduced_sorted_symbol_list()

    print 'len(sorted_reduced_symbols) = ' + str(len(sorted_reduced_symbols))
    for i in range(len(sorted_reduced_symbols)):
        print chr(sorted_reduced_symbols[i]) + ' :: i = ' + str(i)

    sz = len(sorted_reduced_symbols)
    part_sz = int(256 / sz)
    rem = 256 % sz
    val = 0
    for i in range(len(sorted_reduced_symbols)):
        sym = sorted_reduced_symbols[i]
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


def __write_value_map(file_name='value_map'):
    global value_to_symbol_map
    f = open(file_name, 'w')
    writer = csv.DictWriter(f, fieldnames=['value', 'symbol'])

    writer.writeheader()
    for val, sym in value_to_symbol_map.items():
        writer.writerow({'value': val, 'symbol': sym })

    f.close()


def __is_special_char(sym):
    if sym < 65 or (sym > 90 and sym < 97) or sym > 122:
        return True
    else:
        return False


def main():
    for val in range(256):
        sym = value_to_symbol_map[val]
        print '{' + str(val) + ' : ' + str(ord(sym)) + ' = \'' + sym + '\' }'

__build_symbol_to_norm_dict()
__build_sorted_symbol_list()
__build_clamped_norm_dict()
__build_reduced_value_to_symbol_map()
__write_value_map()

if __name__ == '__main__':
    main()
