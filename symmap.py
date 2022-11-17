#! /usr/bin/python

import os
import cv2
import csv
import math

# symbol_to_norm_map format:             {ord(symbol): norm value}
# clamped_value_to_symbol_dict format:   {ord(symbol): clamped norm value}
# sorted_symbol_list format:             list of symbols sorted by norm values
# value_to_ascii_map format:            {int(clamped norm): ord(symbol)}

VALUE_MAP = './value_map'


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
        print('symmap.py unable to read \'' + symbols_filepath + '\'.')
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
            cv2.imwrite('./symbols/' + str(32 + (i * 16) + j) + '.png',
                        cell)  # creates images of symbols for debugging purposes
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
    norm_values = [symbol_to_norm_map[x] for x in symbol_to_norm_map]  # extract norm values from symbol_to_norm_dict
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


def __build_distributed_value_to_ascii_map(sorted_symbols_list, distribution):
    value_to_ascii_map = dict()
    D = 0
    for i in range(len(sorted_symbols_list)):
        for j in range(distribution[i]):
            value_to_ascii_map[D] = chr(int(sorted_symbols_list[i]))
            D += 1
    return value_to_ascii_map


def __even_distribution(sorted_symbols_list):
    """
    Distributes value-to-symbol mappings by giving values equal partitions.

    Even Distribution evenly partitions the gray-scale color space values (0 - 255) across all available ASCII symbols
    in the sorted symbols list.

    e.g. If partition size is determined to be 4 values, each consecutive 4 values in the value-to-symbol map will
    map to the same symbol. Values 0 - 3 map to '@', values 4 - 7 map to 'Q', etc.

    :returns: A list of each symbol's distribution. The values of the list represent the number of times the
    character should appear when mapping gray-scale values to a symbol.
    """
    N = len(sorted_symbols_list)
    distribution = [int(256 / N)] * N
    remainder = 256 % N
    for i in range(remainder):
        distribution[i] += 1
    return distribution


def __fill_distribution(sorted_symbols_list, value_to_symbol_map):
    """
    Distributes value-to-symbol mappings by filling gaps between clamped norm values of symbols.

    Fill Distribution takes the difference between each clamped-norm and distributes
    a range of values to each symbol by dividing the difference by 2 and adding the result to the distribution for each
    symbol.

    e.g. Two consecutive symbols from the sorted symbols list have clamped norm values: '@' => 0 and 'Q' => 42.
    Gray-scale values 0 through 42 will be split in half, such that values 0 through 20 will be mapped to '@' and
    values 21 trough 42 are mapped to 'Q'.

    :returns: A list of each symbol's distribution. The values of the list represent the number of times the
    character should appear when mapping gray-scale values to a symbol.
    """
    N = len(sorted_symbols_list)
    values_list = [key for key in value_to_symbol_map]
    values_list.sort()
    distribution = [0] * N
    for i in range(N - 1):
        dif = values_list[i + 1] - values_list[i]
        if dif > 1:
            x1 = int(dif / 2)
            x2 = int(dif / 2) + (dif % 2)
            distribution[i] += x1
            distribution[i + 1] += x2
        else:
            distribution[i + 1] = 1
    distribution[-1] += 1
    return distribution


def __normal_distribution(sorted_symbols_list, mean, sigma2):
    """
    Distributes value-to-symbol mappings using Gaussian probability distribution.

    :returns: A list of each symbol's distribution. The values of the list represent the number of times the
    character should appear when mapping gray-scale values to a symbol.
    """
    N = len(sorted_symbols_list)
    G = 256.0 / (N - 1)  # the width of a distribution for each symbol
    distribution = [(G * i) for i in range(N - 1)]
    distribution.append(256.0)
    for i in range(N):
        g = distribution[i]
        d = (1 / (2 * math.pi * sigma2)) * math.exp(-((g - mean) ** 2) / (2 * sigma2))  # gaussian distribution formula
        distribution[i] = d
    min_val = min(distribution)
    max_val = max(distribution)
    for i in range(N):
        val = distribution[i]
        distribution[i] = (val - min_val) * (1 / (max_val - min_val))  # clamp values between 0 and 1
        distribution[i] = abs(1.0 - distribution[i])
        # The above inverts distribution such that higher probability values now contribute less to the sum.
        # This is necessary so that values closer to the mean are associated with more unique characters than those
        # further from the mean.
    S = sum(distribution)
    # Iterate over and divide each distribution value by the sum, normalizing each value.
    # If value after truncation is zero, set value to 1.
    for i in range(N):
        d = 256 * (distribution[i] / float(S))
        if int(d) < 1:
            d = 1
        distribution[i] = int(d)
    # The sum of the distribution at this point should technically be 256, but will usually be a number less than 256
    # because the quotient above is converted into and int, truncating the values. Also, zero values are artificially
    # being set to 1.
    dif = 256 - sum(distribution)  # gives the remaining number of distribution points to distribute
    i = 0
    j = N - 1
    rng = range(N)
    # Iterates from both sides of the list and adds 1 to the highest value. If there is a tie, both receive +1. This
    # continues until dif == 0.
    # TODO   Improve algorithm to recognize when one side of the distribution should increment over the other.
    # TODO   I.E. max value on either side of mean is 5, right side has six 5's and left side has three 5's,
    # TODO   then the algorithm should iterate and increment over the right side 3 times before incrementing any values on the left.
    while dif > 0 and i in rng and j in rng:
        if distribution[i] == distribution[j]:
            distribution[i] += 1  # increment distribution
            dif -= 1  # decrement number of distribution points left to distribute
            i += 1  # increment left iterator
            if dif > 0:
                distribution[j] += 1  # increment distribution
                dif -= 1  # decrement number of distribution points left to distribute
                j -= 1  # decrement right iterator
        elif distribution[i] > distribution[j]:
            distribution[i] += 1
            dif -= 1
            i += 1
        elif distribution[j] > distribution[i]:
            distribution[j] += 1
            dif -= 1
            j -= 1
    # distribution now sums to 256
    return distribution


def __calc_mean_sigma(img):
    height, width = img.shape[:2]
    N = width * height
    mean = sigma2 = 0
    for i in range(height):
        for j in range(width):
            mean += img[i][j]
    mean = mean / N
    for i in range(height):
        for j in range(width):
            sigma2 += (img[i][j] - mean) ** 2
    sigma2 = sigma2 / (N - 1)
    return mean, sigma2


def __write_value_map(value_to_symbol_map=None, file_name='./value_map'):
    if value_to_symbol_map is None:
        symbol_to_norm_map = __build_symbol_to_norm_map()
        clamped_symbol_to_norm_map = __build_clamped_symbol_to_norm_map(symbol_to_norm_map)
        value_to_symbol_map = __build_value_to_symbol_map(clamped_symbol_to_norm_map)
    f = open(file_name, 'w')
    writer = csv.DictWriter(f, fieldnames=['value', 'symbol'])

    writer.writeheader()
    for val, sym in value_to_symbol_map.items():
        writer.writerow({'value': val, 'symbol': sym})

    f.close()


def __load_value_map():
    """
    Loads the value-to-symbol mapping used to map gray scale values to ascii symbols.
    """
    value_to_symbol_map = dict()
    with open(VALUE_MAP, 'r') as val_map_file:
        reader = csv.DictReader(val_map_file)
        for row in reader:
            value_to_symbol_map[int(row['value'])] = row['symbol']

        val_map_file.close()
        print('value-to-symbol map loaded..')
    return value_to_symbol_map


def __is_special_char(sym):
    return sym < 65 or (90 < sym < 97) or sym > 122


def get_value2ascii_map(img=None, distr_type='even'):
    distribution = None
    if distr_type == 'even':
        distribution = __even_distribution(sorted_symbol_list)
    elif distr_type == 'fill':
        distribution = __fill_distribution(sorted_symbol_list, value_to_symbol_map)
    elif distr_type == 'normal':
        mean, s2 = __calc_mean_sigma(img)
        distribution = __normal_distribution(sorted_symbol_list, mean, s2)
    value_to_ascii_map = __build_distributed_value_to_ascii_map(sorted_symbol_list, distribution)
    return value_to_ascii_map


def main():
    symbol_to_norm_map = __build_symbol_to_norm_map()
    clamped_symbol_to_norm_map = __build_clamped_symbol_to_norm_map(symbol_to_norm_map)
    value_to_symbol_map = __build_value_to_symbol_map(clamped_symbol_to_norm_map)
    sorted_symbol_list = __build_sorted_symbol_list(value_to_symbol_map)
    # even_distr = __even_distribution(sorted_symbol_list)
    # fill_distr = __fill_distribution(sorted_symbol_list, value_to_symbol_map)  # DEBUG
    normal_distr = __normal_distribution(sorted_symbol_list, 80, 2000)
    value_to_ascii_map = __build_distributed_value_to_ascii_map(sorted_symbol_list, normal_distr)

    __write_value_map(value_to_symbol_map)

    for val in range(256):
        sym = value_to_ascii_map[val]
        print('{' + str(val) + ' : ' + str(ord(sym)) + ' = \'' + sym + '\' }')


if not os.path.exists(VALUE_MAP):
    __write_value_map()
value_to_symbol_map = __load_value_map()
sorted_symbol_list = __build_sorted_symbol_list(value_to_symbol_map)

if __name__ == '__main__':
    main()
