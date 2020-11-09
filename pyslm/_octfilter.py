# -*- coding: utf-8 -*-
"""
@author: leonardojacomussi (GitHub)

@e-mail: leonardo.jacomussi@eac.ufsm.br
"""

from scipy import signal as sig
import matplotlib.pyplot as plt
import numpy as np
plt.style.use(['dark_background'])


class OctFilter(object):
    """
    Class that calculates the parameters of the frequency range
    according to the performance requirements contained in the
    standards IEC 61620-1:2014 and ANSI S1.11:2004 (R2009).

    Parameters
    ----------
    fstart : float, optional
        Start frequency.
        The default is 20.0.
    fend : float, optional
        End frequency.
        The default is 20000.0.
    b : int, optional
        Number of bands per octave.
        The default is 1.
    fs : int, optional
        Sampling rate.
        The default is 48000.
    G : int, optional
        Base.
        The default is 10.
    fr : int, optional.
        Reference frequency.
        The default is 1000.
    order : int, optional
        Order of filter. 
        The default is 4.

    Attributes
    ----------
    f1 : np.array
        Lower frequency.
    fm: np.array
        Center frequency.
    fnom: np.array
        Nominal center frequencies.
    f2: np.array
        Upper frequency.

    Methods
    -------
    filter():
        Filter data using octave filters.
    Standard():
        Returns figures with frequency response and normative parameters.
    Analyze():
        Returns the average square root of the filtered signal.

    Example:
    -------
    >>> # Sample rate
    >>> samplingRate = 48000

    >>> # Filter
    >>> Filter = OctFilter(fstart = 20, fend = 20000, b = 3, fs = samplingRate)

    >>> # Data
    >>> time = np.arange(0, 1, 1/samplingRate)
    >>> signal = np.sin(2 * np.pi * 1000 * time)

    >>> # Applying filter
    >>> filteredSignal = Filter.filter(signal)

    >>> # Standard IEC
    >>> Filter.Standard(std = 'iec', Class = 1, type = 'one') # or
    >>> # Filter.Standard(std = 'iec', Class = 2, type = 'one') # or
    >>> # Filter.Standard(std = 'iec', type = 'all')

    >>> # Standard ANSI
    >>> Filter.Standard(std = 'ansi', Class = 0, type = 'one') # or
    >>> # Filter.Standard(std = 'ansi', Class = 1, type = 'one') # or
    >>> # Filter.Standard(std = 'ansi', Class = 2, type = 'one') # or
    >>> # Filter.Standard(std = 'ansi', type = 'all')

    >>> # Analyze
    >>> rmsData = Filter.Analyze(filteredSignal, plot=True)
    """

    def __init__(self, fstart: float = 20.0, fend: float = 20000.0,
                 b: int = 1, fs: int = 48000, G: int = 10, fr: int = 1000,
                 order: int = 4):
        self.fstart = fstart
        self.fend = fend
        self.b = b
        self.fs = fs
        self.G = G
        self.fr = fr
        self.order = order
        self.Nyquist = self.fs/2
        self.__frequencies()
        self.__design()

    def __frequencies(self):
        """
        Returns
        -------
        Filter specification:
            f1 : np.array
                Lower frequency.
            fm: np.array
                Center frequency.
            fnom: np.array
                Nominal center frequencies.
            f2: np.array
                Upper frequency.
        """

        standardized_fnom = np.array([
            0.1, 0.125, 0.16, 0.2, 0.25, 0.315, 0.4, 0.5, 0.6, 3., 0.8,
            1., 1.25, 1.6, 2., 2.5, 3.15, 4., 5., 6.3, 8., 10., 12.5, 16.,
            20., 25., 31.5, 40., 50., 63., 80., 100., 125., 160., 200., 250.,
            315., 400., 500., 630., 800., 1000., 1250., 1600., 2000., 2500.,
            3150., 4000., 5000., 6300., 8000., 10000., 12500., 16000., 20000.
        ])

        self.f1 = np.empty((0), dtype='float32')
        self.fm = np.empty((0), dtype='float32')
        self.f2 = np.empty((0), dtype='float32')

        if self.G == 10:
            self.G = 10 ** (3 / 10)  # Base ten
        elif self.G == 2:
            self.G = 2
        else:
            print('The base system is not permitted. G must be 10 or 2')

        x = -1000
        f2 = 0

        if self.fend < self.Nyquist:
            while f2 <= self.fend:
                # Excact midband frequencies
                if self.b % 2 == 0:  # even
                    fm = (self.G ** ((2 * x - 59) / (2 * self.b))) * (self.fr)
                else:  # odd
                    fm = (self.G ** ((x - 30) / self.b)) * (self.fr)
                # Bandedge frequencies
                f1 = (self.G ** (-1 / (2 * self.b))) * (fm)
                f2 = (self.G ** (1 / (2 * self.b))) * (fm)
                if f2 >= self.fstart:
                    self.f1 = np.concatenate((self.f1, np.array([f1])), axis=0)
                    self.fm = np.concatenate((self.fm, np.array([fm])), axis=0)
                    self.f2 = np.concatenate((self.f2, np.array([f2])), axis=0)
                x += 1
        else:
            raise ValueError("The final frequency should be essentially less" +
                             " than half the sampling rate: fend < fs/2")
        self.fnom = np.empty((self.fm.size), dtype='float32')
        for idx in range(self.fm.size):
            dist = np.sqrt((standardized_fnom - self.fm[idx])**2)
            self.fnom[idx] =\
                standardized_fnom[np.argmin(dist)]
        return

    def __design(self):
        """
        Returns
        -------
        Filter coefficients
        """

        self.sos = np.empty((0, 6))
        for index in range(self.fm.size):
            lowCutoff = self.f1[index]
            highCutoff = self.f2[index] if self.f2[index] < self.Nyquist else self.Nyquist-1
            sos = sig.butter(N=self.order, Wn=np.array([lowCutoff, highCutoff]),
                             btype='bp', output='sos', fs=self.fs)
            self.sos = np.append(self.sos, sos, axis=0)
        return self.sos

    def filter(self, data: np.ndarray):
        """
        Filter data using octave filters.

        Parameters
        ----------
        data : np.ndarray
            Data that should be filtered.

        Returns
        -------
        filteredSignal : np.ndarray
            Filtered data.

        """

        # Construct signal
        if data.ndim == 1:
            filteredSignal = np.empty([data.size, self.fm.size])
            for index in range(self.fm.size):
                filteredSignal[:, index] = sig.sosfilt(self.sos[(self.order *
                                                                 index):(self.order * index + self.order), :], data)
        elif data.ndim == 2:
            filteredSignal = np.empty([np.size(data, axis=0),
                                       int(self.fm.size), np.size(data, axis=1)])
            for dataIndex in range(np.size(data, axis=1)):
                for bandIndex in range(self.fm.size):
                    filteredSignal[:, bandIndex, dataIndex] =\
                        sig.sosfilt(self.sos[(self.order * bandIndex):
                                             (self.order * bandIndex +
                                              self.order), :], data[:, dataIndex])
        return filteredSignal

    def Standard(self, std: str = 'iec', Class: int = 1, type: str = 'one'):
        """
        Function that generates figures containing the responses of the filters
        with the acceptance limits established by the standard IEC 61260-1:2014
        or by ANSI S1.11:2004(R2009).

        Parameters
        ----------
        std : str, optional
            Standard that wants to analyze the performance of the filter.
            std = 'iec' or std = 'ansi'.
            The default is 'iec'.
        Class : int, optional
            Performance classification..
            For IEC: Class 1 or 2.
            For ANSI: Class 0, 1 or 2.
            The default is 1.
        type : str, optional
            Type of figure generation.
            'one': to generate a single figure containing all frequency
                   responses of the bands, with only an acceptance limit
                   curve for the specified class.
            'all' to generate a figure per frequency band containing the
                  frequency response and acceptance limits for all classes
                  of the specified standard.
            The default is 'one'.

        Returns
        -------
        Figure(s) by matplotlib.pyplot.

        """

        plt.rcParams.update({'figure.max_open_warning': 0})
        np.seterr(divide='ignore')
        std = std.lower()

        acceptanceLimits =\
            {'iec':  # IEC 61260-1:2014 Standard Acceptance limits
             {1:
              {"min": - np.array([70, 60, 40.5, 16.6, 1.2, -0.4, -0.4, -0.4, -0.4, -0.4,
                                  -0.4, -0.4, -0.4, -0.4, 1.2, 16.6, 40.5, 60, 70]),
               "max": - np.array([1000, 1000, 1000, 1000, 1000, 5.3, 1.4, 0.7, 0.5, 0.4,
                                  0.5, 0.7, 1.4, 5.3, 1000, 1000, 1000, 1000, 1000])},
              2:
              {"min": - np.array([60, 54, 39.5, 15.6, 0.8, -0.6, -0.6, -0.6, -0.6, -0.6,
                                  -0.6, -0.6, -0.6, -0.6, 0.8, 15.6, 39.5, 54, 60]),
               "max": - np.array([1000, 1000, 1000, 1000, 1000, 5.8, 1.7, 0.9, 0.7, 0.6,
                                  0.7, 0.9, 1.7, 5.8, 1000, 1000, 1000, 1000, 1000])}},

                'ansi':  # ANSI S1.11:2004(R2009) Standard Acceptance limits
                {0:
                 {"min": - np.array([75, 62, 42.5, 18, 2.3, -0.15, -0.15, -0.15, -0.15, -0.15,
                                     -0.15, -0.15, -0.15, -0.15, 2.3, 18, 42.5, 62, 75]),
                  "max": - np.array([1000, 1000, 1000, 1000, 4.5, 4.5, 1.1, 0.4, 0.2, 0.15,
                                     0.2, 0.4, 1.1, 4.5, 4.5, 1000, 1000, 1000, 1000])},
                 1:
                 {"min": - np.array([70, 61, 42, 17.5, 2, -0.3, -0.3, -0.3, -0.3, -0.3,
                                     -0.3, -0.3, -0.3, -0.3, 2, 17.5, 42, 61, 70]),
                     "max": - np.array([1000, 1000, 1000, 1000, 5.0, 5.0, 1.3, 0.6, 0.4, 0.3,
                                        0.4, 0.6, 1.3, 5.0, 5.0, 1000, 1000, 1000, 1000])},
                 2:
                 {"min": - np.array([60, 55, 41, 16.5, 1.6, -0.5, -0.5, -0.5, -0.5, -0.5,
                                     -0.5, -0.5, -0.5, -0.5, 1.6, 16.5, 41, 55, 60]),
                     "max": - np.array([1000, 1000, 1000, 1000, 5.5, 5.5, 1.6, 0.8, 0.6, 0.5,
                                        0.6, 0.8, 1.6, 5.5, 5.5, 1000, 1000, 1000, 1000])}}}

        breakpoints =\
            np.array([-4, -3, -2, -1, -1/2, -1/2, -3/8, -1/4, -1/8, 0,
                      1/8, 1/4, 3/8, 1/2, 1/2, 1, 2, 3, 4])
        if self.b == 1:
            freq = self.G**breakpoints
        else:
            freq_high = 1 + (((self.G**(1/(2*self.b)) - 1) / (self.G**(1/2) - 1))
                             * (self.G**breakpoints[9:19] - 1))
            freq_low = 1/freq_high[1:freq_high.size]
            freq = np.concatenate((np.flipud(freq_low), freq_high))

        if std == 'iec':
            if Class == 1 or Class == 2:
                if type == 'one':
                    ticks = []
                    for i in range(self.fnom.size):
                        if self.fnom[i] >= 1000:
                            ticks.append(str(self.fnom[i] / 1000)+"k")
                        else:
                            ticks.append(str(int(self.fnom[i])))
                    name = "Filter responses with "+str(self.fm.size)+" bands from " +\
                        str(int(self.fnom[0]))+" Hz to " +\
                        str(int(self.fnom[-1]))+" Hz. " +\
                        "Performance follow IEC 61620-1:2014."
                    plt.figure(name, figsize=(13, 8))
                    for index in range(self.fm.size):
                        w, h = sig.sosfreqz(self.sos[(self.order * index):
                                                     (self.order * index + self.order), :],
                                            worN=self.fs)
                        plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][Class]["min"], 'w--')
                        plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][Class]["max"], 'w--')
                        plt.semilogx((self.fs * 0.5 / np.pi) *
                                     w, 20 * np.log10(abs(h)))
                    plt.title("Acceptance limits - IEC 61260-1:2014 - 1/"+str(self.b)+" octave bands\n"
                              + "Performance for Class "+str(Class))
                    plt.xlabel("Frequency Hz")
                    plt.ylabel("Attenuation dB ref.: 1 Pa")
                    if self.b > 1:
                        plt.xticks(self.fm, ticks, rotation=70)
                    else:
                        plt.xticks(self.fm, ticks, rotation=30)
                    plt.xlim([freq[0]*self.fm[0]-0.5,
                              freq[-1]*self.fm[-1]+10000])
                    plt.ylim([-80, 5])
                    plt.grid(b=True, which='major', color='#999999',
                             linestyle='-', axis='x', alpha=2)
                    fig = plt.gcf()
                    fig.subplots_adjust(bottom=0.15)
                    plt.tight_layout()
                    plt.show()

                elif type == 'all':
                    ticks = []
                    for i in range(self.fnom.size):
                        if self.fnom[i] >= 1000:
                            ticks.append(str(self.fnom[i] / 1000)+"k")
                        else:
                            ticks.append(str(int(self.fnom[i])))
                    for index in range(self.fm.size):
                        name = 'Filter response in 1/{} octave for the {} Hz band.'\
                            .format(self.b, int(self.fnom[index]))
                        plt.figure(name, figsize=(13, 8))
                        w, h = sig.sosfreqz(self.sos[(self.order * index):
                                                     (self.order * index + self.order), :],
                                            worN=self.fs)
                        p1, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][1]["min"], 'b--')
                        p2, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][1]["max"], 'b--')
                        p3, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][2]["min"], 'g--')
                        p4, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][2]["max"], 'g--')
                        p5, = plt.semilogx((self.fs * 0.5 / np.pi) * w, 20 *
                                           np.log10(abs(h)), 'k')
                        plt.title("Acceptance limits - IEC 61260-1:2014 - 1/"+str(self.b)+" octave bands\n"
                                  + "Performance for Class 1 and 2")
                        plt.legend(((p1, p2), (p3, p4), p5),
                                   ("Class 1", "Class 2",
                                    "OctFilter at "+str(int(self.fnom[index]))+" Hz"))
                        plt.xlabel("Frequency Hz")
                        plt.ylabel("Attenuation dB ref.: 1 Pa")
                        if self.b > 1:
                            plt.xticks(self.fm, ticks, rotation=70)
                        else:
                            plt.xticks(self.fm, ticks, rotation=30)
                        plt.xlim([freq[0]*self.fm[0], freq[-1]*self.fm[-1]])
                        plt.ylim([-80, 5])
                        plt.grid(b=True, which='major', color='#999999',
                                 linestyle='-', axis='x', alpha=2)
                        fig = plt.gcf()
                        fig.subplots_adjust(bottom=0.15)
                        plt.tight_layout()
                        plt.show()
                else:
                    raise ValueError("Figure type not defined or does not\n " +
                                     "correspond to supported types.\n" +
                                     "To see a single figure containing " +
                                     "all bands with the limits corresponding " +
                                     "to the defined class, do:\n" +
                                     "type = 'one'\n" +
                                     "To see a figure for each band containing " +
                                     "the limits for all classes, do:\n" +
                                     "type = 'all'")
            else:
                raise ValueError("Class value not defined or does not correspond to the" +
                                 " specified classes by IEC 61260-1:2014 standard " +
                                 "(class 1 or 2). For more, see\n" +
                                 "https://webstore.iec.ch/publication/5063")

        elif std == 'ansi':
            if Class == 0 or Class == 1 or Class == 2:
                if type == 'one':
                    ticks = []
                    for i in range(self.fnom.size):
                        if self.fnom[i] >= 1000:
                            ticks.append(str(self.fnom[i] / 1000)+"k")
                        else:
                            ticks.append(str(int(self.fnom[i])))
                    name = "Filter responses with "+str(self.fm.size)+" bands from " +\
                        str(int(self.fnom[0]))+" Hz to " +\
                        str(int(self.fnom[-1]))+" Hz. " +\
                        "Performance follow ANSI S1.11: 2004 (R2009)."
                    plt.figure(name, figsize=(13, 8))
                    for index in range(self.fm.size):
                        w, h = sig.sosfreqz(self.sos[(self.order * index):
                                                     (self.order * index + self.order), :],
                                            worN=self.fs)
                        plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][Class]["min"], 'w--')
                        plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][Class]["max"], 'w--')
                        plt.semilogx((self.fs * 0.5 / np.pi) *
                                     w, 20 * np.log10(abs(h)))
                    plt.title("Acceptance limits - ANSI S1.11:2004(R2009) - 1/"+str(self.b)+" octave bands\n"
                              + "Performance for Class "+str(Class))
                    plt.xlabel("Frequency Hz")
                    plt.ylabel("Attenuation dB ref.: 1 Pa")
                    if self.b > 1:
                        plt.xticks(self.fm, ticks, rotation=70)
                    else:
                        plt.xticks(self.fm, ticks, rotation=30)
                    plt.xlim([freq[0]*self.fm[0]-0.5,
                              freq[-1]*self.fm[-1]+10000])
                    plt.ylim([-80, 5])
                    plt.grid(b=True, which='major', color='#999999',
                             linestyle='-', axis='x', alpha=2)
                    fig = plt.gcf()
                    fig.subplots_adjust(bottom=0.15)
                    plt.tight_layout()
                    plt.show()

                elif type == 'all':
                    ticks = []
                    for i in range(self.fnom.size):
                        if self.fnom[i] >= 1000:
                            ticks.append(str(self.fnom[i] / 1000)+"k")
                        else:
                            ticks.append(str(int(self.fnom[i])))
                    for index in range(self.fm.size):
                        name = 'Filter response in 1/{} octave for the {} Hz band.'\
                            .format(self.b, int(self.fnom[index]))
                        plt.figure(name, figsize=(13, 8))
                        w, h = sig.sosfreqz(self.sos[(self.order * index):
                                                     (self.order * index + self.order), :],
                                            worN=self.fs)
                        p1, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][0]["min"], 'r--')
                        p2, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][0]["max"], 'r--')
                        p3, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][1]["min"], 'b--')
                        p4, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][1]["max"], 'b--')
                        p5, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][2]["min"], 'g--')
                        p6, = plt.semilogx(
                            freq*self.fm[index], acceptanceLimits[std][2]["max"], 'g--')
                        p7, = plt.semilogx((self.fs * 0.5 / np.pi) * w, 20 *
                                           np.log10(abs(h)), 'k')
                        plt.title("Acceptance limits - ANSI S1.11:2004(R2009) - 1/"+str(self.b)+" octave bands\n"
                                  + "Performance for Class 0, 1 and 2")
                        plt.legend(((p1, p2), (p3, p4), (p5, p6), p7),
                                   ("Class 0", "Class 1", "Class 2",
                                    "OctFilter at "+str(int(self.fnom[index]))+" Hz"))
                        plt.xlabel("Frequency Hz")
                        plt.ylabel("Attenuation dB ref.: 1 Pa")
                        if self.b > 1:
                            plt.xticks(self.fm, ticks, rotation=70)
                        else:
                            plt.xticks(self.fm, ticks, rotation=30)
                        plt.xlim([freq[0]*self.fm[0]-0.5,
                                  freq[-1]*self.fm[-1]+10000])
                        plt.ylim([-80, 5])
                        plt.grid(b=True, which='major', color='#999999',
                                 linestyle='-', axis='x', alpha=2)
                        fig = plt.gcf()
                        fig.subplots_adjust(bottom=0.15)
                        plt.tight_layout()
                        plt.show()
                else:
                    raise ValueError("Figure type not defined or does not\n " +
                                     "correspond to supported types.\n" +
                                     "To see a single figure containing " +
                                     "all bands with the limits corresponding " +
                                     "to the defined class, do:\n" +
                                     "type = 'one'\n" +
                                     "To see a figure for each band containing " +
                                     "the limits for all classes, do:\n" +
                                     "type = 'all'")
            else:
                raise ValueError("Class value not defined or does not correspond to the" +
                                 " specified classes by ANSI S1.11:2004(R2009) standard " +
                                 "(class 0, 1 or 2). For more, see\n" +
                                 "https://webstore.ansi.org/standards/asa/ansiasas1112004r2009")
        else:
            raise ValueError("Standard not defined or not included in this version of " +
                             "the OctFilter Class. Standards considered:\n" +
                             "for IEC 61260-1:2014        ---> std = 'iec'\n" +
                             "for ANSI S1.11:2004(R2009)   ---> std = 'ansi'")
        np.seterr(divide='warn')
        return

    def Analyze(self, filteredSignal: np.ndarray, plot: bool = False):
        """
        This function returns the average square root of the filtered signal.

        Parameters
        ----------
        filteredSignal : np.ndarray
            Signal filtered by the 'OctFilter.filter' method. 
        plot : bool, optional
            True for generating figures.. The default is False.

        Returns
        -------
        meanSignal : np.ndarray
            Root Mean Square of the filtered signal calculated by bands.

        """

        if "filteredSignal" in locals() and filteredSignal.any():
            meanSignal = np.sqrt(np.mean(filteredSignal**2, axis=0))
            if plot:
                duration = filteredSignal[:, 0].size/self.fs
                time = np.empty(filteredSignal.shape)
                # for i in range(filteredSignal.shape[1]):
                time = np.arange(0, duration, 1/self.fs)  # time vector
                minMean = np.min(
                    np.min(20*np.log10(meanSignal), axis=0)-5, axis=0)
                plt.figure('Analyse',  figsize=(13, 8))
                plt.subplot(1, 2, 1)
                if meanSignal.ndim == 1:
                    plt.bar(self.f1, 20 * np.log10(meanSignal) - minMean,
                            align='edge', bottom=minMean, width=(self.f2 - self.f1))
                elif meanSignal.ndim == 2:
                    for i in range(np.size(meanSignal, axis=1)):
                        plt.bar(self.f1, 20 * np.log10(meanSignal[:, i])
                                - minMean, align='edge', bottom=minMean,
                                width=(self.f2 - self.f1))
                plt.xscale('log')
                plt.title("RMS signal")
                plt.xlabel("Frequency Hz")
                plt.ylabel("Level dB ref.: 1 Pa")
                plt.xscale('log')
                plt.subplot(1, 2, 2)
                plt.plot(time, filteredSignal)
                plt.title('Filtered signal')
                plt.xlabel("Time s")
                plt.ylabel("Amplitude Pa")
                plt.show()
            return meanSignal
        else:
            raise Exception("No filtered signal has been declared.")


# %% Runner
# Run only if this script is compiled, not imported.
if __name__ == "__main__":
    # Sample rate
    samplingRate = 48000

    # Filter
    Filter = OctFilter(fstart=20, fend=20000, b=3, fs=samplingRate)

    # Data
    time = np.arange(0, 1, 1/samplingRate)
    signal = np.sin(2 * np.pi * 1000 * time)

    # Applying filter
    filteredSignal = Filter.filter(signal)

    # Standard IEC
    Filter.Standard(std='iec', Class=1, type='one')  # or
    # Filter.Standard(std = 'iec', Class = 2, type = 'one') # or
    # Filter.Standard(std = 'iec', type = 'all')

    # Standard ANSI
    Filter.Standard(std='ansi', Class=0, type='one')  # or
    # Filter.Standard(std = 'ansi', Class = 1, type = 'one') # or
    # Filter.Standard(std = 'ansi', Class = 2, type = 'one') # or
    # Filter.Standard(std = 'ansi', type = 'all')

    # Analyze
    rmsData = Filter.Analyze(filteredSignal, plot=True)
