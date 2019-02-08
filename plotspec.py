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


def zerofill(amp, zeroing):
    return np.append(amp, np.zeros(int(float(len(amp)) * zeroing)))


def readdx(filename):
    f = open(filename, 'r')
    headOn = True
    isReal = True
    real = np.array([])
    imag = np.array([])
    freq = 0.0
    phc0 = 0.0
    phc1 = 0.0
    sweep_width = 0.0
    zeroing = 0.0
    apod = 0.0
    spec_center = 0.0
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
            if head == '##$SPECTRALCENTER':
                spec_center = float(tail.strip())
            if head == '##$SWEEPWIDTH':
                sweep_width = float(tail.strip())
            if head == '##$ZEROING':
                zeroing = float(tail.strip())
            if head == '##$APODIZATION':
                apod = float(tail.strip())
        else:
            if line.strip()[0:2] == '##':
                isReal = False
            else:
                if isReal:
                    real = np.append(real, np.array(map(float, line.split()[1:])) * float(factor[1]))
                else:
                    imag = np.append(imag, np.array(map(float, line.split()[1:])) * float(factor[2]))
    time = np.linspace(float(first[0]), float(last[0]), len(real))
    amp = real + 1.0j * imag
    settings = {}
    settings['PhC0'] = phc0
    settings['PhC1'] = phc1
    settings['Freq'] = freq
    settings['SweepWidth'] = sweep_width
    settings['Zeroing'] = zeroing
    settings['ApodizationFactor'] = apod
    settings['SpectralCenter'] = spec_center
    return time, amp, settings


def indexToFreq(index, n, sampf, spec_center_hz):
    return index * sampf / (float(n - 1)) - sampf * 0.5 + spec_center_hz


def main():
    if len(sys.argv) < 2:
        print "Not enough arguments"
        return
    fname = sys.argv[1]
    if not os.path.isfile(fname):
        print "Cannot open file ", fname
    # 1H
    time, amp, settings = readdx(fname)
    ofreq = settings['Freq']
    phc0 = settings['PhC0']
    phc1 = settings['PhC1']
    #sweep_width = settings['SweepWidth']
    zeroing = settings['Zeroing']
    #apod = settings['ApodizationFactor']
    spec_center = settings['SpectralCenter']
    spec_center_hz = spec_center * ofreq
    # Zero Fill
    amp = zerofill(amp, zeroing)
    # Apodization
    n = len(amp)
    dt = time[1] - time[0]
    sampf = 1.0 / dt
    lowfreq = indexToFreq(0, n, sampf, spec_center_hz)
    highfreq = indexToFreq(n - 1, n, sampf, spec_center_hz)
    xfreq = np.linspace(lowfreq, highfreq, n)
    freq = phasecorr(fftshift(fft(amp)), phc0, phc1)
    genplot(xfreq, np.real(freq))
    return


if __name__ == "__main__":
    main()
