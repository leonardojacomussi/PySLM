# -*- coding: utf-8 -*-
"""
@author: leonardojacomussi (GitHub)

@e-mail: leonardo.jacomussi@eac.ufsm.br
"""

from scipy.stats import linregress
import matplotlib.pyplot as plt
import scipy.signal as sign
import numpy as np
plt.style.use(['dark_background'])


class weighting(object):
    """
    Class that generates time and frequency weighting filters
    according to IEC 61672-1: 2013 for sound level meters.

    Parameters
    ----------
    fs : int
        Sampling rate [Hz] (e.g. 44100, 48000, 51200)
    tau: float
        Time constant [s] (e.g. 0.035, 0.125, 1.000)
            Ps.: 0.035 to Impulse weighting
                 0.125 to Fast weighting
                 1.000 to Slow weighting
    pRef : float
        Reference sound pressure [Pa]
        Default is 2.0e-05 (20uPa)
    kind : str
        Frequency weighting 'A', 'C' or 'Z'.
        Default is 'A'.
    """

    def __init__(self, fs: int = 48000, tau: float = 0.125,
                 pRef: float = 2e-05, kind: str = 'A'):
        self.fs = fs
        self.tau = tau
        self.pRef = pRef
        self.kind = kind.upper()
        self.time_sos = self.__time_filter_design(tau=self.tau, fs=self.fs)
        self.freq_b, self.freq_a = self.__freq_filter_design(
            fs=self.fs, kind=self.kind)

    def __time_filter_design(self, tau: float, fs: int):
        """
        Defines parameters for time weighting the sound pressure squared
        using a low-pass filter with one real pole at: -1 / tau.

        Parameters
        ----------
        tau : float
            Time constant [s] (e.g. 0.035, 0.125, 1.000)
            Ps.: 0.035 to Impulse weighting
                0.125 to Fast weighting
                1.000 to Slow weighting
        fs : int
            Sampling rate [Hz] (e.g. 44100, 48000, 51200)

        Returns
        -------
        sos : array_like
            Array of second-order filter coefficients, must have shape
            ``(n_sections, 6)``. Each row corresponds to a second-order
            section, with the first three columns providing the numerator
            coefficients and the last three providing the denominator
            coefficients.

        See also
        --------
        [Standard] IEC 61672-1:2013
        [Function] scipy.signal.tf2sos
        [Function] time
        """
        b = [1/(tau*fs)]  # Numerator
        a = [1, -np.exp(-1/(tau*fs))]  # Denominator
        sos = sign.tf2sos(b, a)
        return sos

    def time(self, signal: np.ndarray, sos=None, tau=None, reshape=True):
        """
        Apply a time-weighted filter defined by the parameters
        established in `__time_filter_design` function.

        Parameters
        ----------
        signal : np.ndarray
            Sound pressure square [Pa^2] (e.g. pressure**2)

        sos : list, optional
            Array of second-order filter coefficients, must have shape
            ``(n_sections, 6)``. Each row corresponds to a second-order
            section, with the first three columns providing the numerator
            coefficients and the last three providing the denominator
            coefficients.

        reshape : boolean
            If true, reshape the input signal to the form defined by fs * tau
            over time, for example:
                fs = 44100
                tau = 0.125
                int (tau * fs) = 5512
                returns a vector with `` n`` columns per 5512 columns, in a 
                1 second signal, it will return 8 columns per 5512 rows.

                Note: Because ``fs*tau`` is generally not an integer, samples
                are discarded. This results in a drift of samples for longer
                signals (e.g. 60 minutes at 44.1 kHz).
            If False, returns the filtered input signal in its original shape.
            Default is True.

        Returns
        -------
        np.ndarray
            Sound pressure square weighted

        See also
        --------
        [Standard] IEC 61672-1:2013
        [Function] __time_filter_design
        [Function] scipy.signal.sosfilt
        """
        if reshape:
            if tau == None:
                tau = self.tau
                sos = self.time_sos
            else:
                sos = self.__time_filter_design(tau=tau, fs=self.fs)
            numSamples = signal.size
            a = np.floor(tau*self.fs).astype(int)
            signal = signal[0:a*(numSamples//a)]
            b = int(numSamples/a)
            signal = signal.reshape(b, a)
            filteredSignal = sign.sosfilt(sos, signal)
        else:
            filteredSignal = sign.sosfilt(self.time_sos, signal)
            # sos = self.time_sos if sos == None else sos
        return filteredSignal

    def __freq_filter_design(self, fs: int, kind: str):
        """
        Returns b and a coefficients of ou A or C weighting filter.

        Parameters
        ----------
        fs : int
            Sampling rate of the signals that well be filtered.

        Returns
        -------
        b, a : ndarray
            Filter coefficients for a digital weighting filter.
            b -> Numerator of the analog filter transfer function.
            a -> Denominator of the analog filter transfer function.

        See also
        --------
        [Standard] IEC 61672-1:2013
        [Function] frequency
        [Function] scipy.signal.bilinear
        """
        if not kind.upper() in ['A', 'C', 'Z']:
            raise ValueError("Weighting type not defined or not " +
                             "supported, try 'A', 'C' or 'Z'.")
        if kind.upper() == 'A':
            f1 = 20.598997
            f2 = 107.65265
            f3 = 737.86223
            f4 = 12194.217
            A1000 = 1.9997
            numerators = [(2*np.pi*f4)**2 *
                          (10**(A1000 / 20.0)), 0., 0., 0., 0.]
            denominators = np.convolve([1., +4*np.pi * f4, (2*np.pi * f4)**2],
                                       [1., +4*np.pi * f1, (2*np.pi * f1)**2])
            denominators = np.convolve(np.convolve(denominators, [1., 2*np.pi * f3]),
                                       [1., 2*np.pi * f2])
            b, a = sign.bilinear(numerators, denominators, fs)
        elif kind.upper() == 'C':
            f1 = 20.598997
            f4 = 12194.217
            C1000 = 0.0619
            numerators = [(2*np.pi * f4)**2 * (10**(C1000 / 20)), 0, 0]
            denominators = np.convolve([1, +4*np.pi * f4, (2*np.pi * f4)**2],
                                       [1, +4*np.pi * f1, (2*np.pi * f1)**2])
            b, a = sign.bilinear(numerators, denominators, fs)
        elif kind.upper() == 'Z':
            b, a = None, None
        else:
            raise AttributeError(
                "Kind %s is not supported, please try 'A', 'C' or 'Z'." % self.kind)
        return b, a

    def frequency(self, signal: np.ndarray, b=None, a=None):
        """
        Apply a frequency-weighted filter defined by the parameters
        established in `__freq_filter_design` function.

        Parameters
        ----------
        signal : np.ndarray
            Sound pressure [Pa]

        b, a : ndarray, optional
            Filter coefficients for a digital weighting filter.
            b -> Numerator of the analog filter transfer function.
            a -> Denominator of the analog filter transfer function.

        Returns
        -------
        np.ndarray
            Sound pressure weighted

        See also
        --------
        [Standard] IEC 61672-1:2013
        [Function] __freq_filter_design
        [Function] scipy.signal.lfilter
        """
        if self.kind.upper() in ['A', 'C']:
            if b == None or a == None:
                b, a = self.freq_b, self.freq_a
            else:
                pass
            filteredSignal = sign.lfilter(b=b, a=a, x=signal)
        elif self.kind.upper() == 'Z':
            filteredSignal = signal
        else:
            raise AttributeError(
                "Kind %s is not supported, please try 'A', 'C' or 'Z'." % self.kind)
        return filteredSignal

    def standard(self, kind: str = 'freq', saveFig: bool = False):
        """
        Function that generates figures containing the responses of the time
        or frequency weighting filters with the acceptance limits established
        by the IEC 61672-1: 2013 standard.

        Parameters
        ----------
        kind : str, optional
            Filter type if you want to analyze the response.
            kind = 'freq' or kind = 'time'.
            The default is 'freq'.
        saveFig : bool, optional
            Option to save figure in pdf.
            True to save, False not to save.
            The default is False.

        Returns
        -------
        Figure by matplotlib.pyplot.
        """
        np.seterr(divide='ignore')
        if kind.lower() == 'freq':
            # A-weighting
            bA, aA = self.__freq_filter_design(fs=self.fs, kind='A')
            freq, A_spectrum = sign.freqz(b=bA, a=aA, worN=self.fs)
            A = 20*np.log10(np.abs(A_spectrum))

            # C-weighting
            bC, aC = self.__freq_filter_design(fs=self.fs, kind='C')
            freq, C_spectrum = sign.freqz(b=bC, a=aC, worN=self.fs)
            C = 20*np.log10(np.abs(C_spectrum))

            acceptanceLimits =\
                {"A": np.array([-50.5, -44.7, -39.4, -34.6, -30.2, -26.2, -22.5, -19.1,
                                -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9, -0.8,
                                0.0, 0.6, 1.0, 1.2, 1.3, 1.2, 1.0, 0.5, -0.1, -1.1, -2.5,
                                -4.3, -6.6, -9.3]),
                 "C": np.array([-6.2, -4.4, -3.0, -2.0, -1.3, -0.8, -0.5, -0.3, -0.2, -0.1,
                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.2, -0.3,
                                -0.5, -0.8, -1.3, -2.0, -3.0, -4.4, -6.2, -8.5, -11.2]),
                 "max": np.array([1, 1, 1.5, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                                  0.5, 0.5, 0.5, 0.5, 0.3, 0.5, 1.0, 1.0, 1.5, 1.5, 2.0,
                                  2.0, 3.0, 3.0, 3.0, 3.0, 2.5, 2.0]),
                 "min": np.array([-1, -1.5, -1.5, -1, -1, -1, -1, -0.5, -0.5, -0.5, -0.5,
                                  -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.3, -0.5, -1.0, -1.0,
                                  -1.5, -1.5, -2.0, -2.0, -2.5, -2.5, -200, -200, -200, -200]),
                 "freq": np.array([20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0,
                                   200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0,
                                   1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0,
                                   10000.0, 12500.0, 16000.0, 20000.0])}

            freq = (self.fs*0.5/np.pi)*freq
            strFreq = ['20', '25', '31,5', '40', '50', '63', '80', '100', '125', '160', '200', '250',
                       '315', '400', '500', '630', '800', '1k', '1,25k', '1,6k', '2k', '2,5k', '3,15k',
                       '4k', '5k', '6,3k', '8k', '10k', '12,5k', '16k', '20k']

            fig, (ax1, ax2, ax3) = plt.subplots(num="Frequency weighting: Standard IEC 61672-1",
                                                figsize=(15, 9), nrows=3, ncols=1)
            ax1.semilogx(freq, A)
            ax1.semilogx(acceptanceLimits["freq"],
                         acceptanceLimits["max"] + acceptanceLimits["A"], '--r')
            ax1.semilogx(acceptanceLimits["freq"],
                         acceptanceLimits["min"] + acceptanceLimits["A"], '--r')
            ax1.set_title('A-weighting: Standard IEC 61672-1')
            ax1.set_xlabel("Frequency Hz")
            ax1.set_ylabel("Attenuation dB ref.: 20" + r'$\mu$' + "Pa")
            ax1.legend(['A-weighting', 'Acceptance limits'],
                       loc='lower center')
            ax1.set_xticks(acceptanceLimits["freq"])
            ax1.set_xticklabels(strFreq, rotation=45)
            ax1.set_xlim([20, 20000])
            ax1.set_ylim([-70, 10])
            ax1.grid(True, lw=1, ls='--', c='.75')

            ax2.semilogx(freq, C)
            ax2.semilogx(acceptanceLimits["freq"],
                         acceptanceLimits["max"] + acceptanceLimits["C"], '--r')
            ax2.semilogx(acceptanceLimits["freq"],
                         acceptanceLimits["min"] + acceptanceLimits["C"], '--r')
            ax2.set_title('C-weighting: Standard IEC 61672-1')
            ax2.set_xlabel("Frequency Hz")
            ax2.set_ylabel("Attenuation dB ref.: 20" + r'$\mu$' + "Pa")
            ax2.legend(['C-weighting', 'Acceptance limits'],
                       loc='lower center')
            ax2.set_xticks(acceptanceLimits["freq"])
            ax2.set_xticklabels(strFreq, rotation=45)
            ax2.set_xlim([20, 20000])
            ax2.set_ylim([-70, 10])
            ax2.grid(True, lw=1, ls='--', c='.75')

            ax3.semilogx(freq, np.zeros((freq.size)))
            ax3.semilogx(acceptanceLimits["freq"],
                         acceptanceLimits["max"] + 0, '--r')
            ax3.semilogx(acceptanceLimits["freq"],
                         acceptanceLimits["min"] + 0, '--r')
            ax3.set_title('Z-weighting: Standard IEC 61672-1')
            ax3.set_xlabel("Frequency Hz")
            ax3.set_ylabel("Attenuation dB ref.: 20" + r'$\mu$' + "Pa")
            ax3.legend(['Z-weighting', 'Acceptance limits'],
                       loc='lower center')
            ax3.set_xticks(acceptanceLimits["freq"])
            ax3.set_xticklabels(strFreq, rotation=45)
            ax3.set_xlim([20, 20000])
            ax3.set_ylim([-70, 10])
            ax3.grid(True, lw=1, ls='--', c='.75')
            plt.tight_layout()
            if saveFig:
                plt.savefig(fname="Time weighting (sine at 4 kHz).pdf",
                            bbox_inches='tight', pad_inches=0)
            plt.show()

        elif kind.lower() == 'time':
            def decayRate(signal: np.ndarray, fs: int):
                """
                Calculates the rate of fade out of the weighted sound pressure
                level.
                """
                # Fade-out dB/s
                initial_point = np.where(signal == max(signal))[0][0]
                final_point = signal.shape[0]
                x = np.arange(initial_point, final_point)/fs
                y = signal[initial_point: final_point]
                slope, intercept = linregress(x, y)[0:2]
                del intercept
                fade_out = -slope
                return fade_out

            # Central frequency of the sinusoidal signal [Hz]
            freq = 4000
            # List of time-weighting (tau) [-]
            weighting = [0.035, 0.125, 1.000]
            # Original signal (sin(2.pi.f.t)) [Pa]->(simulated)
            data = np.concatenate(
                (np.zeros((int(self.fs*1))),
                 np.sin(2*np.pi*freq*np.arange(0, 5, 1/self.fs)),
                 np.zeros((int(self.fs*15)))))
            square = np.concatenate(
                (np.zeros((int(self.fs*1))),
                 np.ones((5*self.fs))*0.5,
                 np.zeros((15*self.fs))))
            # SPL of original signal [dB]
            SPL_DATA = 10*np.log10(data**2/self.pRef**2)
            # Time vector [s]
            time = np.arange(0, data.size/self.fs, 1/self.fs)
            # Save picture in PDF format
            saveFig = False  # True for save, False for not save

            for tau in range(len(weighting)):
                # Signal weighted by the fir method (filter design)
                sos = self.__time_filter_design(tau=weighting[tau], fs=self.fs)
                weightedSignal = self.time(data**2, sos=sos, reshape=False)
                freqVec, spectrum = sign.sosfreqz(sos=sos, worN=data.size)
                # SPL of signal weighted by the fir method
                SPL_weightedSignal = 10*np.log10(weightedSignal/self.pRef**2)

                if weighting[tau] == 0.035:
                    impulseDecay = decayRate(
                        signal=SPL_weightedSignal, fs=self.fs)

                    fig, (ax1, ax2, ax3) = plt.subplots(
                        num="Time weighting for sinusoidal signal at " +
                        str(freq) + " Hz", figsize=(15, 9), nrows=3, ncols=1)
                    del fig
                    ax1.plot(time, SPL_DATA)
                    ax1.plot(time, SPL_weightedSignal)

                    ax2.plot(time, square, '--')
                    ax2.plot(time, weightedSignal)

                    ax3.semilogx((self.fs*0.5/np.pi)*freqVec,
                                 20*np.log10(abs(spectrum)))

                elif weighting[tau] == 0.125:
                    fastDecay = decayRate(
                        signal=SPL_weightedSignal, fs=self.fs)

                    ax1.plot(time, SPL_weightedSignal)

                    ax2.plot(time, weightedSignal)

                    ax3.semilogx((self.fs*0.5/np.pi)*freqVec,
                                 20*np.log10(abs(spectrum)))

                else:
                    slowDecay = decayRate(
                        signal=SPL_weightedSignal, fs=self.fs)

                    ax1.plot(time, SPL_weightedSignal)
                    ax1.set_title("Time weighting: Standard IEC 61672-1\n" +
                                  "(response after the sudden cessation of a steady " +
                                  str(int(freq/1000)) + " kHz sinusoidal digital input signal)")
                    ax1.legend([r'sin $_{4 kHz, 5 s}$',
                                r'Impulse $_{\tau=35ms}$' + '\nRate of decay: ' +
                                str(np.round(impulseDecay, 1)).replace(
                                    ".", ",")+" dB/s",
                                r'Fast $_{\tau=125ms}$' + '\nRate of decay: ' +
                                str(np.round(fastDecay, 1)).replace(
                                    ".", ",")+" dB/s",
                                r'Slow $_{\tau=1000ms}$' + '\nRate of decay: ' +
                                str(np.round(slowDecay, 1)).replace(".", ",")+" dB/s"],
                               loc='upper right')
                    ax1.set_ylim(bottom=0, top=100)
                    ax1.set_xlim(left=time[0], right=time[-1])
                    ax1.set_xlabel("Time s")
                    ax1.set_ylabel("SPL dB ref.: 20"+r'$\mu$'+'Pa')
                    ax1.grid(True, lw=1, ls='--', c='.75')

                    ax2.plot(time, weightedSignal)
                    ax2.set_title("Linear response over time")
                    ax2.legend([r'Real time',
                                r'Impulse $_{\tau=35ms}$',
                                r'Fast $_{\tau=125ms}$',
                                r'Slow $_{\tau=1000ms}$'],
                               loc='upper right')
                    ax2.set_ylim(bottom=0, top=0.7)
                    ax2.set_xlim(left=time[0], right=time[-1])
                    ax2.set_xlabel("Time s")
                    ax2.set_ylabel('Pa'+r'$^{2}$')
                    ax2.grid(True, lw=1, ls='--', c='.75')

                    ax3.semilogx((self.fs*0.5/np.pi)*freqVec,
                                 20*np.log10(abs(spectrum)))
                    ax3.set_title("Filter frequency response function")
                    ax3.legend([r'Impulse $_{\tau=35ms}$',
                                r'Fast $_{\tau=125ms}$',
                                r'Slow $_{\tau=1000ms}$'],
                               loc='upper right')
                    ax3.set_ylim(bottom=-110, top=10)
                    ax3.set_xlim(left=1, right=20000)
                    ax3.set_xlabel("Frequency Hz")
                    ax3.set_ylabel("SPL dB ref.: 1 Pa")
                    ax3.grid(True, lw=1, ls='--', c='.75')
                    plt.tight_layout()
                    if saveFig:
                        plt.savefig(fname="Time weighting (sine at 4 kHz).pdf",
                                    bbox_inches='tight', pad_inches=0)
                    plt.show()
        else:
            raise ValueError("Kind not defined or not " +
                             "supported, try 'freq' or 'time'.")
        return


# %%
if __name__ == "__main__":
    # Sampling rate
    samplingRate = 48000
    # Declaring weight
    weight = weighting(fs=samplingRate, tau=1.0)
    # See normative requirements
    weight.standard(kind='freq')
    weight.standard(kind='time')
    