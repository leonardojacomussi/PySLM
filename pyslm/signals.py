import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sign
plt.style.use(['dark_background'])


def sweep(fstart: float,
          fend: float,
          fs: int,
          duration: int,
          startMargin: int,
          stopMargin: int,
          method: str = 'logarithmic',
          windowing: str = 'hann',
          plotFig: bool = False):
    """
    Generates a chirp signal defined by the "method" input, windowed, with
    silence interval at the beggining and end of the signal, plus a hanning
    fade in and fade out.

    >>> x = pytta.generate.sweep()
    >>> x.plot_time()

    Return a signalObj containing a logarithmic chirp signal from 17.8 Hz
    to 22050 Hz, with a fade in beginning at 17.8 Hz time instant and ending at
    the 20 Hz time instant; plus a fade out beginning at 20000 Hz time instant
    and ending at 22050 Hz time instant.

    The fade in and the fade out are made with half hanning window. First half
    for the fade in and last half for the fade out. Different number of points
    are used for each fade, so the number of time samples during each frequency
    is respected.

    """
    # frequency limits [Hz]
    freqLimits = {'fstart': fstart / (2**(1/6)),
                  'fend': min(fend*(2**(1/6)), fs/2)}
    samplingTime = 1/fs  # [s] sampling period

    stopSamples = stopMargin*fs
    # [samples] initial silence number of samples

    startSamples = startMargin*fs
    # [samples] ending silence number of samples

    # marginSamples = startSamples + stopSamples
    # [samples] total silence number of samples

    numSamples = round(duration*fs)  # [samples] full signal number of samples

    sweepSamples = numSamples #- marginSamples + 1
    # [samples] actual sweep number of samples

    # if sweepSamples < fs/10:
    #     raise Exception('Too small resultant sweep. For such big margins you' +
    #                     ' must increase your fftDegree.')

    sweepTime = sweepSamples/fs  # [s] sweep's time length
    timeVecSweep = np.arange(0, sweepTime, samplingTime)  # [s] time vector
    if timeVecSweep.size > sweepSamples:
        timeVecSweep = timeVecSweep[0:int(sweepSamples)]  # adjust length
    sweep = 0.95*sign.chirp(timeVecSweep,
                            freqLimits['fstart'],
                            sweepTime,
                            freqLimits['fend'],
                            'logarithmic',
                            phi=-90)  # sweep, time domain
    sweep = __do_sweep_windowing(sweep,
                                 timeVecSweep,
                                 freqLimits,
                                 fstart,
                                 fend,
                                 windowing)  # fade in and fade out
    # add initial and ending sileces
    timeSignal = np.concatenate((np.zeros(int(startSamples)),
                                 sweep,
                                 np.zeros(int(stopSamples))))

    if plotFig:
        timeVector = np.arange(0, timeSignal.size/fs, 1/fs)
        freqSignal = np.fft.rfft(timeSignal, axis=0, norm=None)
        freqSignal /= 2**0.5
        freqSignal /= len(freqSignal)
        freqVector = np.linspace(0, (timeSignal.size - 1) *
                                 fs /
                                    (2*timeSignal.size),
                                    (int(timeSignal.size/2)+1)
                                 if timeSignal.size % 2 == 0
                                 else int((timeSignal.size+1)/2))
        fig, (ax1, ax2) = plt.subplots(
            num='Sweep ' + method, figsize=(13, 8), ncols=1, nrows=2)
        ax1.plot(timeVector, timeSignal)
        ax1.set_title('Sweep ' + method + ': time domain')
        ax1.set_xlabel("Time [s]")
        ax1.set_ylabel("Amplitude [Pa]")
        ax1.set_xlim([timeVector[0], timeVector[-1]])
        ax1.grid(True, lw=1, ls='--', c='.75')
        ax2.semilogx(freqVector, 10 *
                     np.log10(np.abs(freqSignal)), label="Signal")
        ax2.axvline(x=fstart, label='fstart: %.1f Hz' % fstart, c='red')
        ax2.axvline(x=fend, label='fend: %.1f Hz' % fend, c='blue')
        ax2.set_title('Sweep ' + method + ': frequency domain')
        ax2.set_xlabel("Frequency [Hz]")
        ax2.set_ylabel("Amplitude [dB ref. 1 Pa]")
        ax2.set_xlim([freqVector[1], freqVector[-1]])
        ax2.grid(True, lw=1, ls='--', c='.75')
        ax2.legend(loc='best', shadow=True)
        fig.tight_layout()
        plt.show()
    return timeSignal


def noise(kind: str,
          fs: int,
          duration: int,
          startMargin: int,
          stopMargin: int,
          windowing: str = 'hann',
          plotFig: bool = False):
    """
    Generates a noise of kind White or Pink, with a silence at the beginning
    and ending of the signal, plus a fade in to avoid abrupt speaker excursioning.
    All noises have normalized amplitude.

        White noise is generated using numpy.randn between [[1];[-1]];
        # FIXME: This looks incorrect because the signal has normal
        # distribution, so no limits but an average and standard deviation.

        Pink noise is still in progress;

        Blue noise is still in progress;
    """

    # [samples] initial silence number of samples
    stopSamples = round(stopMargin*fs)

    # [samples] ending silence number of samples
    startSamples = round(startMargin*fs)

    # [samples] total silence number of samples
    # marginSamples = startSamples + stopSamples

    # [samples] full signal number of samples
    numSamples = int(duration*fs)

    # [samples] Actual noise number of samples
    # noiseSamples = int(numSamples - marginSamples)
    noiseSamples = numSamples

    if kind.upper() in ['WHITE', 'FLAT']:
        noiseSignal = np.random.randn(noiseSamples)
    elif kind.upper() == 'PINK':
        uneven = noiseSamples % 2
        X = np.random.randn(noiseSamples // 2 + 1 + uneven) + \
            1j * np.random.randn(noiseSamples // 2 + 1 + uneven)
        noiseSignal = np.sqrt(np.arange(len(X)) + 1.)
        noiseSignal = (np.fft.irfft(X / noiseSignal)).real
        if uneven:
            noiseSignal = noiseSignal[:-1]
    else:
        pass
    noiseSignal = __do_noise_windowing(noiseSignal, noiseSamples, windowing)
    noiseSignal = noiseSignal / max(abs(noiseSignal))
    noiseSignal = np.concatenate((np.zeros(int(startSamples)),
                                  noiseSignal,
                                  np.zeros(int(stopSamples))))
    if plotFig:
        timeVector = np.arange(0, noiseSignal.size/fs, 1/fs)
        freqSignal = np.fft.rfft(noiseSignal, axis=0, norm=None)
        freqSignal /= 2**0.5
        freqSignal /= len(freqSignal)
        freqVector = np.linspace(0, (noiseSignal.size - 1) *
                                 fs /
                                    (2*noiseSignal.size),
                                    (int(noiseSignal.size/2)+1)
                                 if noiseSignal.size % 2 == 0
                                 else int((noiseSignal.size+1)/2))
        fig, (ax1, ax2) = plt.subplots(
            num=kind.lower() + ' noise', figsize=(13, 8), ncols=1, nrows=2)
        ax1.plot(timeVector, noiseSignal)
        ax1.set_title(kind.lower() + ' noise: time domain')
        ax1.set_xlabel("Time [s]")
        ax1.set_ylabel("Amplitude [Pa]")
        ax1.set_xlim([timeVector[0], timeVector[-1]])
        ax1.grid(True, lw=1, ls='--', c='.75')
        ax2.semilogx(freqVector, 10 *
                     np.log10(np.abs(freqSignal)))
        ax2.set_title(kind.lower() + ' noise: frequency domain')
        ax2.set_xlabel("Frequency [Hz]")
        ax2.set_ylabel("Amplitude [dB ref. 1 Pa]")
        ax2.set_xlim([freqVector[1], freqVector[-1]])
        ax2.grid(True, lw=1, ls='--', c='.75')
        fig.tight_layout()
        plt.show()
    return noiseSignal


def __do_sweep_windowing(inputSweep,
                         timeVecSweep,
                         freqLimits,
                         fstart,
                         fend,
                         window):
    """
    Applies a fade in and fade out that are minimum at the chirp start and end,
    and maximum between the time intervals corresponding to Finf and Fsup.
    """

    # frequencies at time instants: freq(t)
    freqSweep = freqLimits['fstart']*(
        (freqLimits['fend'] / freqLimits['fstart'])**(
            1/max(timeVecSweep))) ** timeVecSweep

    # exact sample where the chirp reaches fstart [Hz]
    fstartSample = np.where(freqSweep <= fstart)
    fstartSample = fstartSample[-1][-1]

    # exact sample where the chirp reaches fend [Hz]
    fendSample = np.where(freqSweep <= fend)
    fendSample = len(freqSweep) - fendSample[-1][-1]
    windowStart = sign.windows.hann(2*fstartSample)
    windowEnd = sign.windows.hann(2*fendSample)

    # Uses first half of windowStart, last half of windowEnd, and a vector of
    # ones with the remaining length, in between the half windows
    fullWindow = np.concatenate((windowStart[0:fstartSample],
                                 np.ones(int(len(freqSweep) -
                                             fstartSample -
                                             fendSample + 1)),
                                 windowEnd[fendSample:-1]))
    newSweep = fullWindow * inputSweep
    return newSweep


def __do_noise_windowing(inputNoise,
                         noiseSamples,
                         window):
    # sample equivalent to the first five percent of noise duration
    fivePercentSample = int((5/100) * (noiseSamples))
    windowStart = sign.windows.hann(2*fivePercentSample)
    fullWindow = np.concatenate((windowStart[0:fivePercentSample],
                                 np.ones(int(noiseSamples-fivePercentSample))))
    newNoise = fullWindow * inputNoise
    return newNoise


# %%
if __name__ == '__main__':
    from sounddevice import play
    from time import sleep

    # Parameters
    fs = 48000
    duration = 10

    # Generating signals
    ssweep = sweep(fstart=60.0, fend=16000.0, fs=fs,
                   duration=duration, startMargin=0.5, stopMargin=5, plotFig=True)
    swhiteNoise = noise(kind="white", fs=fs,
                        duration=duration, startMargin=0.5, stopMargin=5, plotFig=True)
    spinkNoise = noise(kind="pink", fs=fs,
                       duration=duration, startMargin=0.5, stopMargin=5, plotFig=True)

    # Reproducing signals
    play(data=ssweep, samplerate=fs, blocking=True)
    sleep(1.5)
    play(data=swhiteNoise, samplerate=fs, blocking=True)
    sleep(1.5)
    play(data=spinkNoise, samplerate=fs, blocking=True)
    sleep(1.5)
