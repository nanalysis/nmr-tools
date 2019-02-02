#!/usr/bin/python
import sys, os
import numpy as np
from scipy.fftpack import fft, fftshift
import matplotlib.pyplot as plt


def genplot(x1, y1, x2=[], y2=[], x3=[], y3=[], title=''):
    plt.plot(x1, y1, '-k')
    if len(x2) > 0:
        plt.plot(x2, y2, '-r')
    if len(x3) > 0:
        plt.plot(x3, y3, '-b')
    plt.title(title)
    plt.grid()
    plt.show()
    return


def phasecorr(amp, phc0, phc1):
    fac = 1.0j * np.pi / 180.0
    idx = np.linspace(-0.5, 0.5, len(amp))
    ampc = amp * np.exp(fac * (phc0 + phc1 * idx))
    return ampc


def readdx(filename):
    f = open(filename, 'r')
    headOn = True
    isReal = True
    real = np.array([])
    imag = np.array([])
    freq = 0.0
    phc0 = 0.0
    phc1 = 0.0
    for line in f:
        if headOn:
            headtail = line.translate(None, '\n\r\t').split('=')
            head = headtail[0].translate(None, '() -_/\\')
            tail = ''

            if len(headtail) > 1:
                tail = headtail[1].strip()
            if head == '##FACTOR':
                factor = tail.translate(None, ' ()').split(',')
            if head == '##FIRST':
                first = tail.translate(None, ' ()').split(',')
            if head == '##LAST':
                last = tail.translate(None, ' ()').split(',')
            if head == '##DATATABLE':
                headOn = False
            if head == '##.OBSERVEFREQUENCY':
                freq = float(tail.translate(None, ' '))
            if head == '##$PHASECORRECTION':
                phc0, phc1 = map(float, tail.translate(None, ' ').split(','))
        else:
            if line.strip()[0:2] == '##':
                isReal = False
            else:
                if isReal:
                    real = np.append(real,
                                     np.array(map(float, line.split()[1:])) *
                                     float(factor[1]))
                else:
                    imag = np.append(imag,
                                     np.array(map(float, line.split()[1:])) *
                                     float(factor[2]))
    time = np.linspace(float(first[0]), float(last[0]), len(real))
    amp = real + 1.0j * imag
    return time, amp, freq, phc0, phc1


def savecsv(outname, xfreq, freq):
    output = open(outname, 'w')
    if len(xfreq) != len(freq):
        print('Error. Length of vectors does not match')
        return
    for i in range(len(xfreq)):
        output.write('%f,%f,%f\r\n' %
                     (xfreq[i], np.real(freq[i]), np.imag(freq[i])))
    output.close()
    print('File ' + outname + ' saved.')
    return


def main():
    if len(sys.argv) < 2:
        print "Not enough arguments"
        return
    fname = sys.argv[1]
    if not os.path.isfile(fname):
        print "Cannot open file ", fname
    # 1H
    time, amp, ofreq, phc0, phc1 = readdx(fname)
    dt = time[1] - time[0]
    sampf = 1.0 / dt
    n = len(time)
    mfreq = sampf * 0.5
    xfreq = np.linspace(-mfreq, mfreq, n)
    freq = phasecorr(fftshift(fft(amp)), phc0, phc1)
    outname = fname.strip()
    outname = outname[0:outname.rfind('.')] + '.csv'
    savecsv(outname, xfreq, freq)
    return


if __name__ == "__main__":
    main()
