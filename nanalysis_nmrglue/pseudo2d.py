import argparse
from pathlib import Path
from pprint import pprint

import matplotlib.pyplot as plt

import numpy as np

import nmrglue


def load_2d_dx(filename):
    """
    Load a .dx file
    :param filename: Filename to load
    :return: The Jcamp-DX LDRS, 2D time domain data
    """
    ldrs = nmrglue.jcampdx.read(filename)[0]['_datatype_NDNMRFID'][0]
    datatables = ldrs['DATATABLE']
    _, _, real_factor, imag_factor = tuple(
        map(float, ldrs['FACTOR'][0].split(', '))
    )
    rows = []
    row_data = np.array([], dtype=np.complex128)
    for r_i in datatables:
        lines = r_i.splitlines()
        real = 'R..R' in lines[0]
        unscaled = []
        for line in lines[1:]:
            line_data = [int(s) for s in line.split()[1:]]
            unscaled.extend(line_data)
        if real:
            row_data = np.array(unscaled, dtype=np.complex128) * real_factor
        else:
            row_data += (
                np.array(unscaled, dtype=np.complex128) * 1j * imag_factor
            )
            rows.append(row_data)
    del ldrs['DATATABLE']
    return ldrs, np.array(rows)


def plot_p2d(dic, data):
    """
    Plot superimposed pseudo-2D data
    :param dic: nmrglue dictionary
    :param data: Data to plot
    """
    fig, ax = plt.subplots()
    low, high = low_high_ppm(dic)
    x_values = np.linspace(high, low, data.shape[-1])
    ax.plot(x_values, data.T.real)
    ax.invert_xaxis()
    plt.show()
    return


def dic_value(dic, name, index=0):
    """
    Get a float value from the dictionary
    """
    return float(dic[name][index])


def create_dic(ldrs):
    """
    Create a dictionary to use with nmrglue, from the LDRs
    """
    dic = ldrs
    dic['FDDIMORDER'] = [2]
    sw = dic_value(ldrs, '$SWH')
    dic['FDF2SW'] = sw
    dic['FD2DPHASE'] = 0
    dic['FDF2QUADFLAG'] = 1
    car = 1e6 * (dic_value(ldrs, '$SFO1') - dic_value(ldrs, '$SF'))
    dic['FDF2CAR'] = car
    dic['FDF2OBS'] = dic_value(ldrs, '.OBSERVEFREQUENCY')
    dic['FDF2FTFLAG'] = 0
    return dic


def nanalysis_process(dic, data):
    """
    Process Nanalysis pseudo-2D data using nmrglue
    """
    delay = None
    if '$GRPDLY' in dic:
        delay = dic_value(dic, '$GRPDLY')

    base = '$PROCESSINGSETTINGS2DF2'
    try:
        # 3.x software
        expEnabled = dic_value(dic, f'{base}EXPONENTIALAPODIZATIONENABLED')
        expValue = dic_value(dic, f'{base}EXPONENTIALFACTOR')
    except KeyError:
        # Older software
        expEnabled = True
        expValue = dic_value(dic, '$APODIZATION')
    if expEnabled:
        # Note: Instead of using 'one=True', the first points should be using
        #       an apodization function that is mirrored, but nmrglue does
        #       not support this.
        if delay is None:
            start = 1
        else:
            start = int(delay)
        dic, data = nmrglue.pipe_proc.em(
            dic, data, lb=expValue, start=start, one=True
        )

    try:
        # 3.x software
        zeroing = dic_value(dic, f'{base}ZEROINGFACTOR')
    except KeyError:
        # Older software
        zeroing = dic_value(dic, '$ZEROING')
    dic, data = nmrglue.pipe_proc.zf(dic, data, zf=zeroing)
    dic, data = nmrglue.pipe_proc.ft(dic, data)

    # Remove digital filter
    p1 = dic_value(dic, '$PHC1')
    groupDelayCorrection = 0
    if delay is not None:
        groupDelayCorrection -= delay * 360

    dic, data = nmrglue.pipe_proc.ps(
        dic, data, p0=-dic_value(dic, '$PHC0'), p1=-p1 + groupDelayCorrection
    )
    return dic, data


def low_high_ppm(dic):
    """
    Get the low and high frequency domain PPM values
    """
    sw = dic_value(dic, '$SW')
    offset = dic_value(dic, '$O1P')
    low = offset - sw / 2
    high = offset + sw / 2
    return low, high


def save_fd_csv(original_filename, dic, data):
    """
    Save a .csv file for each row. Processed frequency domain data.
    :param original_filename: The filename that was loaded
    :param dic: nmrglue dictionary
    :param data: Processed data
    """
    low, high = low_high_ppm(dic)
    x_values = np.linspace(high, low, data.shape[-1])
    for row in range(data.shape[0]):
        filename = Path(original_filename).with_suffix(f'.{row}.csv')
        real_data = data[row].real
        imaginary_data = data[row].imag
        np.savetxt(
            filename,
            np.array([x_values, real_data, imaginary_data]).T,
            fmt='%.12f',
            delimiter=',',
        )
        print(f'Saved {filename}')
    return


def parse_args():
    description = 'Load a pseudo-2D .dx file'
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('filename', help='The pseudo-2D .dx file to load')
    parser.add_argument(
        '--debug', action='store_true', help='Print debug information'
    )
    parser.add_argument(
        '--plot', action='store_true', help='Plot pseudo-2D data'
    )
    parser.add_argument(
        '--save-fd-csv',
        action='store_true',
        help='Save frequency domain .csv files',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    ldrs_, data_ = load_2d_dx(args.filename)
    if args.debug:
        pprint(ldrs_)
    dic_ = create_dic(ldrs_)
    dic_, data_ = nanalysis_process(dic_, data_)
    if args.plot:
        plot_p2d(dic_, data_)
    if args.save_fd_csv:
        save_fd_csv(args.filename, dic_, data_)
