import matplotlib.pyplot as plt
import numpy as np
import pyslm
plt.style.use(['dark_background'])


class rooms(object):
    """
    Description:
    ------------
    This module does calculations compliant to ISO 3382-1 in order to obtain room
    acoustic paramters. It has an implementation of Lundeby et al. [1] algorithm 
    to estimate the correction factor for the cumulative integral, as suggested 
    by the ISO 3382-1.

    This module was originally implemented within the PyTTa package [2] by the
    original authors and adapted for this project along the lines of the expected
    input and output parameters for the sound level meter. More information about
    the implementation of the Lundeby algorithm can be obtained at [2] and by the
    authors' e-mail.

    Parameters:
    -----------
    IR : np.ndarray
        Response to impulse measured in a room [Pa].
    fs : int
        Sampling rate [Hz].
    fstart : float, optional
        Initial frequency of the frequency band.
            For octave bands it should be >= 63 [Hz]
            For bands of third octave or even narrower it should be >= 50 [Hz]
        Default is 100.0 [Hz]
    fend : float, optional
        Final frequency of the frequency band.
            For octave bands it should be <= 8000 [Hz]
            For bands of third octave or even narrower it should be> = 10000 [Hz]
        Default is 10000.0 [Hz]
    b : int, optional
        Octave band filter fraction, for example:
            1 for octave band and
            3 for third octave band, and so on.
        Default is 1.
    bypassLundeby : bool, optional
        Key to choose not to use the Lundeby algorithm.
        Default is False
    plotLundebyResults : bool, optional
        Key to choose to plot the decay curves, straight slope and crossing point
        between the end of the sound energy decay and background noise estimated by
        the Lundeby medium by frequency bands.
        Default is False
    suppressWarnings : bool, optional
        Key to choose to suppress warnings.
        Default is False
    IREndManualCut : float, optional
        Final cut-off time in seconds for the impulsive response in the background noise level,
        if not defined the `_crop_IR` method will be used automatically.
        Default is None

    Attributes:
    -----------
    bands : np.ndarray
        Vector containing the standard central frequency bands of the octave filter.
    results : dict
        Dictionary containing the reverberation time ('EDT', 'T15', 'T20' and 'T30') and
        energy ('D50', 'D80', 'C50' and 'C80') parameters according to ISO 3382-1.
            See also Example for more information.

    Methods:
    --------
    plot_RT() :
        Returns a figure by matplotlib in bars containing the reverb time parameters
        ('EDT', 'T15', 'T20' and 'T30') contained in the `results` attribute.
            See the method documentation for more details on the input parameters.
    plot_definition() :
        Returns a figure by matplotlib in bars containing the definition parameters
        ('D50' and 'D80') contained in the `results` attribute.
            See the method documentation for more details on the input parameters.
    plot_clarity():
        Returns a figure by matplotlib in bars containing the clarity parameters
        ('C50' and 'C80') contained in the `results` attribute.
            See the method documentation for more details on the input parameters.

    Example:
    --------
    >>> ################# Configuring input parameters #################
    >>> # Load the impulse response into a vector of type numpy.ndarray
    >>> IR = np.load('ImpulseResponse.npy')
    >>> # Sampling rate
    >>> fs = 48000
    >>> # Initial frequency of octave band
    >>> fstart = 63
    >>> # Final frequency of octave band
    >>> fend = 8000
    >>> # Octave band filter fraction
    >>> b = 1
    >>> # Key for use Lundeby method
    >>> bypassLundeby = False
    >>> # Key to plot the decay curve and Lundeby parameters
    >>> plotLundebyResults = False
    >>> # Key to not suppress warning messages
    >>> suppressWarnings = False
    >>> # Final cut-off time in seconds for the impulsive
    >>> # response in the background noise level
    >>> IREndManualCut = None

    >>> ######### Applying input parameters in the room class #########
    >>> # Instantiate the room class with the input parameters
    >>> roomsParams = rooms(IR=IR,
    >>>                     fs=fs,
    >>>                     fstart=fstart,
    >>>                     fend=fend,
    >>>                     b=b,
    >>>                     bypassLundeby=bypassLundeby,
    >>>                     plotLundebyResults=plotLundebyResults,
    >>>                     suppressWarnings=suppressWarnings,
    >>>                     IREndManualCut=IREndManualCut)

    >>> ###### Getting the parameters by the `results` attribute #######
    >>> # Early decay time
    >>> EDT = roomsParams.results['EDT']
    >>> print("EDT: ", EDT)
    >>> # Reverberation time RT15
    >>> RT15 = roomsParams.results['RT15']
    >>> print("RT15: ", RT15)
    >>> # Reverberation time RT20
    >>> RT20 = roomsParams.results['RT20']
    >>> print("RT20: ", RT20)
    >>> # Reverberation time RT30
    >>> RT30 = roomsParams.results['RT30']
    >>> print("RT30: ", RT30)
    >>> # Definition D50
    >>> D50 = roomsParams.results['D50']
    >>> print("D50: ", D50)
    >>> # Definition D80
    >>> D80 = roomsParams.results['D80']
    >>> print("D80: ", D80)
    >>> # Clarity C50
    >>> C50 = roomsParams.results['C50']
    >>> print("C50: ", C50)
    >>> # Clarity C80
    >>> C80 = roomsParams.results['C80']
    >>> print("C80: ", C80)

    >>> ############# View the reverberation time parameters ############
    >>> roomsParams.plot_RT()
    >>> roomsParams.plot_definition()
    >>> roomsParams.plot_clarity()

    Original authors:
    -----------------
        João Vitor Gutkoski Paes, joao.paes@eac.ufsm.br
        Matheus Lazarin, matheus.lazarin@eac.ufsm.br
        Rinaldi Petrolli, rinaldi.petrolli@eac.ufsm.br

    Adapted by:
    -----------
        Leonardo Jacomussi, leonardo.jacomussi@eac.ufsm.br

    References:
    -----------
    [1] Lundeby, Virgran, Bietz and Vorlaender - Uncertainties of Measurements in
        Room Acoustics - ACUSTICA Vol. 81 (1995)
    [2] https://github.com/PyTTAmaster/PyTTa
    """

    def __init__(self, IR: np.ndarray, fs: int, fstart: float = 100.0,
                 fend: float = 10000.0, b: int = 1, bypassLundeby: bool = False,
                 plotLundebyResults: bool = False, suppressWarnings: bool = False,
                 IREndManualCut=None):
        self._fs = fs
        numSamples = IR.size
        timeVector = np.arange(0, numSamples/fs, 1/fs)
        IR, self._timeVector, self._numSamples = self._crop_IR(
            IR, timeVector, numSamples, IREndManualCut)
        self._timeLength = self._numSamples/fs
        b, fstart, fend = self._ajust_frequency(
            b, fstart, fend, suppressWarnings)
        self._filter = pyslm.OctFilter(fstart=fstart, fend=fend, fs=fs, b=b)
        self._hSignal = self._filter.filter(data=IR)
        self.bands = self._filter.fnom
        listEDC = self._cumulative_integration(bypassLundeby,
                                               plotLundebyResults,
                                               suppressWarnings)

        EDT = self.reverberation_time('EDT', listEDC)
        RT15 = self.reverberation_time(15, listEDC)
        RT20 = self.reverberation_time(20, listEDC)
        RT30 = self.reverberation_time(30, listEDC)
        D50 = self.definition(listEDC, 50)
        D80 = self.definition(listEDC, 80)
        C50 = self.clarity(listEDC, 50)
        C80 = self.clarity(listEDC, 80)
        self.results = {'EDT': EDT, 'RT15': RT15, 'RT20': RT20, 'RT30': RT30,
                        'D50': D50, 'D80': D80, 'C50': C50, 'C80': C80, 'freq': self.bands}

    def _ajust_frequency(self, b, fstart, fend, suppressWarnings):
        if b == 1:
            if fstart < 63:
                fstart = 63
                if not suppressWarnings:
                    print(":WARNING: The lower limit of the frequency band in one octave " +
                          "must not be less than 63 Hz. `fstart` limit set to 63 Hz.")
            if fend > 8000:
                fend = 8000
                if not suppressWarnings:
                    print(":WARNING: The upper limit of the frequency band in an octave " +
                          "must not exceed 8 kHz. `fend` limit set to 8 kHz.")
        elif b == 3:
            if fstart < 50:
                fstart = 50
                if not suppressWarnings:
                    print(":WARNING: The lower limit of the third octave frequency band " +
                          "must not be less than 50 Hz. `fstart` limit set to 50 Hz.")
            if fend > 10000:
                fend = 10000
                if not suppressWarnings:
                    print(":WARNING: The upper limit of the third octave frequency band " +
                          "must not exceed 10 kHz. `fend` limit set to 10 kHz.")
        else:
            if b < 1:
                raise Exception(
                    "Please set the octave band `b` as an integer value.")
            else:
                if fstart < 50:
                    fstart = 50
                    if not suppressWarnings:
                        print(":WARNING: The upper limit of the frequency band for narrower bands " +
                              "should not be greater than 10 kHz. 'fend' limit set to 10 kHz.")
                if fend > 10000:
                    fend = 10000
                    if not suppressWarnings:
                        print(":WARNING: The upper limit of the third octave frequency band " +
                              "must not exceed 10 kHz. Fend limit set to 10 kHz.")
        return b, fstart, fend

    def _crop_IR(self, timeSignal, timeVector, numSamples, IREndManualCut):
        """Cut the impulse response at background noise level."""
        timeSignal = timeSignal
        timeVector = timeVector
        numSamples = numSamples
        # Cut the end automatically or manual
        if IREndManualCut is None:
            winTimeLength = 0.1  # [s]
            meanSize = 5  # [blocks]
            dBtoReplica = 6  # [dB]
            blockSamples = int(winTimeLength * self._fs)
            timeWinData, timeVecWin = self._level_profile(
                timeSignal, numSamples, blockSamples)
            endTimeCut = timeVector[-1]
            for blockIdx, blockAmplitude in enumerate(timeWinData):
                if blockIdx >= meanSize:
                    anteriorMean = 10*np.log10(
                        np.sum(timeWinData[blockIdx-meanSize:blockIdx])/meanSize)
                    if 10*np.log10(blockAmplitude) > anteriorMean+dBtoReplica:
                        endTimeCut = timeVecWin[blockIdx-meanSize//2]
                        break
        else:
            endTimeCut = IREndManualCut
        endTimeCutIdx = np.where(timeVector >= endTimeCut)[0][0]
        timeSignal = timeSignal[:endTimeCutIdx]
        # Cut the start automatically
        timeSignal, _ = self._circular_time_shift(timeSignal)
        numSamples = timeSignal.size
        return timeSignal, timeVector, numSamples

    def _level_profile(self, timeSignal, numSamples, blockSamples=None):
        """
        Gets h(t) in octave bands and do the local time averaging in nblocks.
        Returns h^2_averaged(block).
        """
        def mean_squared(x):
            return np.mean(x**2)

        if blockSamples is None:
            blockSamples = 100
        nblocks = int(numSamples // blockSamples)
        profile = np.zeros((nblocks), dtype=np.float32)
        timeStamp = np.zeros((nblocks))

        tmp = timeSignal
        for idx in range(nblocks):
            profile[idx] = mean_squared(tmp[:blockSamples])
            timeStamp[idx] = idx*blockSamples/self._fs
            tmp = tmp[blockSamples:]
        return profile, timeStamp

    def _start_sample_ISO3382(self, timeSignal, threshold):
        squaredIR = timeSignal**2
        # assume the last 10% of the IR is noise, and calculate its noise level
        last10Idx = -int(len(squaredIR)//10)
        noiseLevel = np.mean(squaredIR[last10Idx:])
        # get the maximum of the signal, that is the assumed IR peak
        max_val = np.max(squaredIR)
        max_idx = np.argmax(squaredIR)
        # check if the SNR is enough to assume that the signal is an IR. If not,
        # the signal is probably not an IR, so it starts at sample 1
        idxNoShift = np.asarray([max_val < 100*noiseLevel or
                                 max_idx > int(0.9*squaredIR.shape[0])])
        # less than 20dB SNR or in the "noisy" part
        if idxNoShift.any():
            print("noiseLevelCheck: The SNR too bad or this is not an " +
                  "impulse response.")
            return 0
        # find the first sample that lies under the given threshold
        threshold = abs(threshold)
        startSample = 1

        if max_idx > 0:
            abs_dat = 10*np.log10(squaredIR[:max_idx]) \
                - 10.*np.log10(max_val)
            thresholdNotOk = True
            thresholdShift = 0
            while thresholdNotOk:
                if len(np.where(abs_dat < (-threshold+thresholdShift))[0]) > 0:
                    lastBelowThreshold = \
                        np.where(abs_dat < (-threshold+thresholdShift))[0][-1]
                    thresholdNotOk = False
                else:
                    thresholdShift += 1
            if thresholdShift > 0:
                print("_start_sample_ISO3382: 20 dB threshold too high. " +
                      "Decreasing it.")
            if lastBelowThreshold > 0:
                startSample = lastBelowThreshold
            else:
                startSample = 1
        return startSample

    def _circular_time_shift(self, timeSignal, threshold=20):
        # find the first sample where inputSignal level > 20 dB or > bgNoise level
        startSample = self._start_sample_ISO3382(timeSignal, threshold)
        newTimeSignal = timeSignal[startSample:]
        return (newTimeSignal, startSample)

    def _Lundeby_correction(self, band, timeSignal, suppressWarnings=True):
        returnTuple = (np.float32(0), np.float32(0),
                       np.int32(0), np.float32(0))
        timeSignal, sampleShift = self._circular_time_shift(timeSignal)
        if sampleShift is None:
            return returnTuple

        numSamples = self._numSamples
        numSamples -= sampleShift  # discount shifted samples
        numParts = 5  # number of parts per 10 dB decay. N = any([3, 10])
        dBtoNoise = 7  # stop point 10 dB above first estimated background noise
        useDynRange = 15  # dynamic range

        # Window length - 10 to 50 ms, longer periods for lower frequencies and vice versa
        repeat = True
        i = 0
        winTimeLength = 0.01
        while repeat:  # loop to find proper winTimeLength
            winTimeLength = winTimeLength + 0.01*i
            # 1) local time average:
            blockSamples = int(winTimeLength * self._fs)
            timeWinData, timeVecWin = self._level_profile(
                timeSignal, numSamples, blockSamples)

            # 2) estimate noise from h^2_averaged(block):
            bgNoiseLevel = 10 * \
                np.log10(
                    np.mean(timeWinData[-int(timeWinData.size/10):]))

            # 3) Calculate premilinar slope
            startIdx = np.argmax(
                np.abs(timeWinData/np.max(np.abs(timeWinData))))
            try:
                stopIdx = startIdx + np.where(10*np.log10(timeWinData[startIdx+1:])
                                              >= bgNoiseLevel + dBtoNoise)[0][-1]
            except:
                print("Deu ruim")
            dynRange = 10*np.log10(timeWinData[stopIdx]) \
                - 10*np.log10(timeWinData[startIdx])
            if (stopIdx == startIdx) or (dynRange > -5):
                if not suppressWarnings:
                    print(band, "[Hz] band: SNR too low for the preliminar slope",
                          "calculation.")
                # return returnTuple

            # X*c = EDC (energy decaying curve)
            X = np.ones((stopIdx-startIdx, 2), dtype=np.float32)
            X[:, 1] = timeVecWin[startIdx:stopIdx]
            c = np.linalg.lstsq(X, 10*np.log10(timeWinData[startIdx:stopIdx]),
                                rcond=-1)[0]

            if (c[1] == 0) or np.isnan(c).any():
                if not suppressWarnings:
                    print(
                        band, "[Hz] band: regression failed. T would be inf.")
                # return returnTuple

            # 4) preliminary intersection
            crossingPoint = (bgNoiseLevel - c[0]) / c[1]  # [s]
            if (crossingPoint > 2*(self._timeLength + sampleShift/self._fs)):
                if not suppressWarnings:
                    print(band, "[Hz] band: preliminary intersection point between",
                          "bgNoiseLevel and the decay slope greater than signal length.")
                # return returnTuple

            # 5) new local time interval length
            nBlocksInDecay = numParts * dynRange / -10

            dynRangeTime = timeVecWin[stopIdx] - timeVecWin[startIdx]
            blockSamples = int(self._fs * dynRangeTime / nBlocksInDecay)

            # 6) average
            timeWinData, timeVecWin = self._level_profile(
                timeSignal, numSamples, blockSamples)

            oldCrossingPoint = 11+crossingPoint  # arbitrary higher value to enter loop
            loopCounter = 0

            while (np.abs(oldCrossingPoint - crossingPoint) > 0.001):
                # 7) estimate background noise level (BGL)
                bgNoiseMargin = 7
                idxLast10Percent = int(len(timeWinData)-(len(timeWinData)//10))
                bgStartTime = crossingPoint - bgNoiseMargin/c[1]
                if (bgStartTime > timeVecWin[-1:][0]):
                    idx10dBDecayBelowCrossPoint = len(timeVecWin)-1
                else:
                    idx10dBDecayBelowCrossPoint = \
                        np.where(timeVecWin >= bgStartTime)[0][0]
                BGL = np.mean(timeWinData[np.min(
                    np.array([idxLast10Percent,
                              idx10dBDecayBelowCrossPoint])):])
                bgNoiseLevel = 10*np.log10(BGL)

                # 8) estimate late decay slope
                stopTime = (bgNoiseLevel + dBtoNoise - c[0])/c[1]
                if (stopTime > timeVecWin[-1]):
                    stopIdx = 0
                else:
                    stopIdx = int(np.where(timeVecWin >= stopTime)[0][0])

                startTime = (bgNoiseLevel + dBtoNoise +
                             useDynRange - c[0])/c[1]
                if (startTime < timeVecWin[0]):
                    startIdx = 0
                else:
                    startIdx = int(np.where(timeVecWin <= startTime)[0][0])

                lateDynRange = np.abs(10*np.log10(timeWinData[stopIdx])
                                      - 10*np.log10(timeWinData[startIdx]))

                # where returns empty
                if stopIdx == startIdx or (lateDynRange < useDynRange):
                    if not suppressWarnings:
                        print(band, "[Hz] band: SNR for the Lundeby late decay slope too",
                              "low. Skipping!")
                    # c[1] = np.inf
                    c[1] = 0
                    i += 1
                    break

                X = np.ones((stopIdx-startIdx, 2), dtype=np.float32)
                X[:, 1] = timeVecWin[startIdx:stopIdx]
                c = np.linalg.lstsq(X, 10*np.log10(timeWinData[startIdx:stopIdx]),
                                    rcond=-1)[0]

                if (c[1] >= 0):
                    if not suppressWarnings:
                        print(band, "[Hz] band: regression did not work, T -> inf.",
                              "Setting slope to 0!")
                    # c[1] = np.inf
                    c[1] = 0
                    i += 1
                    break

                # 9) find crosspoint
                oldCrossingPoint = crossingPoint
                crossingPoint = (bgNoiseLevel - c[0]) / c[1]

                loopCounter += 1
                if loopCounter > 30:
                    if not suppressWarnings:
                        print(band, "[Hz] band: more than 30 iterations on regression.",
                              "Canceling!")
                    break

            interIdx = crossingPoint * self._fs  # [sample]
            i += i
            if c[1] != 0:
                repeat = False
            if i > 5:
                if not suppressWarnings:
                    print(band, "[Hz] band: too many iterations to find winTimeLength.",
                          "Canceling!")
                return returnTuple
        return c[0], c[1], np.int32(interIdx), BGL

    def _energy_decay_calculation(self, band, timeSignal, bypassLundeby, suppressWarnings=True):
        """Calculate the Energy Decay Curve."""
        if not bypassLundeby:
            lundebyParams = \
                self._Lundeby_correction(band,
                                         timeSignal,
                                         suppressWarnings=suppressWarnings)
            _, c1, interIdx, BGL = lundebyParams
            lateRT = -60/c1 if c1 != 0 else 0
        else:
            interIdx = 0
            lateRT = 1

        if interIdx == 0:
            interIdx = -1

        truncatedTimeSignal = timeSignal[:interIdx]
        truncatedTimeVector = self._timeVector[:interIdx]

        if lateRT != 0.0:
            if not bypassLundeby:
                C = self._fs*BGL*lateRT/(6*np.log(10))
            else:
                C = 0
            sqrInv = truncatedTimeSignal[::-1]**2
            energyDecayFull = np.cumsum(sqrInv)[::-1] + C
            energyDecay = energyDecayFull/energyDecayFull[0]
        else:
            if not suppressWarnings:
                print(band, "[Hz] band: could not estimate C factor")
            C = 0
            energyDecay = np.zeros(truncatedTimeVector.size)
        return (energyDecay, truncatedTimeVector, lundebyParams)

    def _cumulative_integration(self, bypassLundeby,
                                plotLundebyResults,
                                suppressWarnings=True):
        """Cumulative integration with proper corrections."""
        numBands = self.bands.size
        listEDC = []
        for ch in range(numBands):
            band = self.bands[ch]
            timeSignal = self._hSignal[:, ch]
            energyDecay, energyVector, lundebyParams = \
                self._energy_decay_calculation(band,
                                               timeSignal,
                                               bypassLundeby,
                                               suppressWarnings=suppressWarnings)
            listEDC.append((energyDecay, energyVector))
            if plotLundebyResults:
                c0, c1, interIdx, BGL = lundebyParams
                _, ax = plt.subplots(
                    num='{0:.0f} [Hz]'.format(band), figsize=(13, 8))

                line = c1*self._timeVector + c0
                ax.plot(self._timeVector, 10 *
                        np.log10(timeSignal**2), label='IR')
                ax.axhline(y=10*np.log10(BGL), color='#1f77b4',
                           label='BG Noise', c='red')
                ax.plot(self._timeVector, line, label='Late slope', c='white')
                ax.axvline(x=interIdx/self._fs,
                           label='Truncation point', c='green')
                ax.set_xlabel('Time [s]')
                ax.set_ylabel('Amplitude [dBFS]')
                ax.set_title('{0:.0f} [Hz]'.format(band))
                ax.set_xlim([self._timeVector[0], self._timeVector[-1]])
                ax.legend(loc='best', shadow=True, fontsize='x-large')
                ax.grid(True, lw=1, ls='--', c='.75')
                plt.tight_layout()
                plt.show()
        return listEDC

    def _reverb_time_regression(self, energyDecay, energyVector, upperLim, lowerLim):
        """Interpolate the EDT to get the reverberation time."""
        if not np.any(energyDecay):
            return 0
        first = np.where(10*np.log10(energyDecay) >= upperLim)[0][-1]
        last = np.where(10*np.log10(energyDecay) >= lowerLim)[0][-1]
        if last <= first:
            # return np.nan
            return 0
        X = np.ones((last-first, 2))
        X[:, 1] = energyVector[first:last]
        c = np.linalg.lstsq(
            X, 10*np.log10(energyDecay[first:last]), rcond=-1)[0]
        return -60/c[1]

    def reverberation_time(self, decay, listEDC):
        """Call the reverberation time regression."""
        try:
            decay = int(decay)
            y1 = -5
            y2 = y1 - decay
        except ValueError:
            if decay in ['EDT', 'edt']:
                y1 = 0
                y2 = -10
            else:
                raise ValueError("Decay must be either 'EDT' or an integer \
                                corresponding to the amount of energy decayed to \
                                evaluate, e.g. (decay='20' | 20).")
        RT = []
        for ED in listEDC:
            edc, edv = ED
            RT.append(np.round(self._reverb_time_regression(edc, edv, y1, y2), 2))
        return RT

    def clarity(self, listEDC, t=50):
        """
        Calculate the clarity from impulse response

        Parameters
        ----------
        listEDC : list
            List of early decay times.
        t : int, optional
            t is the defined shift from early to late reflections (is often 50 ms or 80 ms)(ms)
            Default is 50

        Returns
        -------
        list
            Clarity in dB.
        """
        C = []
        for ED in listEDC:
            edc, edv = ED
            index_lim = np.where(edv <= t/1000)[0][-1]
            C_t = 10 * np.log10(np.sum(edc[0:index_lim] ** 2, axis=0) /
                                np.sum(edc[index_lim:] ** 2, axis=0))
            C.append(np.round(C_t, 2))
        return C

    def definition(self, listEDC, t=50):
        """
        Calculate the defintion from impulse response.

        Parameters
        ----------
        listEDC : list
            List of early decay times.
        t : int, optional
            t is the defined shift from early to late reflections (is often 50 ms)(ms)
            Default is 50

        Returns
        -------
        list
            Defintion in percentage.
        """
        D = []
        for ED in listEDC:
            edc, edv = ED
            index_lim = np.where(edv <= t/1000)[0][-1]
            D_t = 100*(np.sum(edc[0:index_lim] ** 2, axis=0) /
                       np.sum(edc ** 2, axis=0))
            D.append(np.round(D_t, 2))
        return D

    def plot_RT(self, saveFig: bool = False, figFormat: str = 'pdf', figName=None):
        """
        Method that generates a figure with the reverberation time parameters obtained
        over the frequency spectrum.

        Parameters
        ----------
        saveFig : bool, optional
            Option to save the generated figure.
            -> True to save the figure in the directory.
            -> False not to save.
            Default is False
        figFormat : str, optional
            Format to save the figure, it can be 'pdf', 'png', 'jpg' or 'jpeg'.
            Default is 'pdf'.
        figName : str, optional
            Name in which you want to save the figure in your directory, if `figName`
            is not defined (None) the default name will be 'Reverberation time'.
            Default is None.
        """
        figFormat = figFormat.lower()
        bandsLabel = []
        for i in range(self.bands.size):
            if self.bands[i] >= 1000:
                bandsLabel.append(
                    str(np.round(self.bands[i]/1000, 1)) + " k")
            else:
                bandsLabel.append(str(np.round(self.bands[i], 0)))
        x = np.arange(len(bandsLabel))
        width = 0.2
        fig, ax = plt.subplots(
            num='Reverberation time: EDT, RT15, RT20, RT30', figsize=(13, 8))
        bar1 = ax.bar(x - 2*width, self.results['EDT'], width, label='EDT')
        bar2 = ax.bar(
            x - width, self.results['RT15'], width, label=r'RT$_{15}$')
        bar3 = ax.bar(x, self.results['RT20'], width, label=r'RT$_{20}$')
        bar4 = ax.bar(
            x + width, self.results['RT30'], width, label=r'RT$_{30}$')
        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel('Time [s]')
        ax.set_title('Reverberation time')
        ax.set_xticks(x-width/2)
        ax.set_xticklabels(bandsLabel)
        ax.legend(loc='best', shadow=True, fontsize='x-large')
        ax.grid(True, lw=1, ls='--', c='.75')

        def insertLabel(bar):
            """Attach a text label above each bar in *bar*, displaying its height."""
            if self._filter.b == 1:
                rotation = 45
            else:
                rotation = 90
            for rect in bar:
                height = rect.get_height()
                if height < 0:
                    # vertical offset
                    voffset = -25
                else:
                    voffset = 3
                ax.annotate('{}'.format(np.round(height, 1)),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, voffset),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', color="white", weight='bold', rotation=rotation)
        insertLabel(bar1)
        insertLabel(bar2)
        insertLabel(bar3)
        insertLabel(bar4)
        fig.tight_layout()
        if saveFig:
            formats = ['pdf', 'png', 'jpg', 'jpeg']
            if figName == None:
                figName = "Reverberation time"
            if not figFormat in formats:
                figFormat = 'pdf'
            plt.savefig(fname=figName+"."+figFormat,
                        bbox_inches='tight', pad_inches=0)
        plt.show()

    def plot_definition(self, saveFig: bool = False, figFormat: str = 'pdf', figName=None):
        """
        Method that generates a figure with the definition D50 and D80 obtained
        over the frequency spectrum.

        Parameters
        ----------
        saveFig : bool, optional
            Option to save the generated figure.
            -> True to save the figure in the directory.
            -> False not to save.
            Default is False
        figFormat : str, optional
            Format to save the figure, it can be 'pdf', 'png', 'jpg' or 'jpeg'.
            Default is 'pdf'.
        figName : str, optional
            Name in which you want to save the figure in your directory, if `figName`
            is not defined (None) the default name will be 'Definition'.
            Default is None.
        """
        figFormat = figFormat.lower()
        bandsLabel = []
        for i in range(self.bands.size):
            if self.bands[i] >= 1000:
                bandsLabel.append(
                    str(np.round(self.bands[i]/1000, 1)) + " k")
            else:
                bandsLabel.append(str(np.round(self.bands[i], 0)))
        x = np.arange(len(bandsLabel))
        width = 0.3
        fig, ax = plt.subplots(
            num='Definition: D50 and D80', figsize=(13, 8))
        bar1 = ax.bar(
            x - width/2, self.results['D50'], width, label=r'D$_{50}$')
        bar2 = ax.bar(
            x + width/2, self.results['D80'], width, label=r'D$_{80}$')
        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel('Deinition [%]')
        ax.set_title('Definition')
        ax.set_xticks(x)
        ax.set_xticklabels(bandsLabel)
        ax.legend(loc='best', shadow=True, fontsize='x-large')
        ax.grid(True, lw=1, ls='--', c='.75')

        def insertLabel(bar):
            """Attach a text label above each bar in *bar*, displaying its height."""
            if self._filter.b == 1:
                rotation = 45
            else:
                rotation = 90
            for rect in bar:
                height = rect.get_height()
                if height < 0:
                    # vertical offset
                    voffset = -25
                else:
                    voffset = 3
                ax.annotate('{}'.format(np.round(height, 1)),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, voffset),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', color="white", weight='bold', rotation=rotation)
        insertLabel(bar1)
        insertLabel(bar2)
        fig.tight_layout()
        if saveFig:
            formats = ['pdf', 'png', 'jpg', 'jpeg']
            if figName == None:
                figName = "Definition"
            if not figFormat in formats:
                figFormat = 'pdf'
            plt.savefig(fname=figName+"."+figFormat,
                        bbox_inches='tight', pad_inches=0)
        plt.show()

    def plot_clarity(self, saveFig: bool = False, figFormat: str = 'pdf', figName=None):
        """
        Method that generates a figure with the clarity C50 and C80 obtained
        over the frequency spectrum.

        Parameters
        ----------
        saveFig : bool, optional
            Option to save the generated figure.
            -> True to save the figure in the directory.
            -> False not to save.
            Default is False
        figFormat : str, optional
            Format to save the figure, it can be 'pdf', 'png', 'jpg' or 'jpeg'.
            Default is 'pdf'.
        figName : str, optional
            Name in which you want to save the figure in your directory, if `figName`
            is not defined (None) the default name will be 'Clarity'.
            Default is None.
        """
        figFormat = figFormat.lower()
        bandsLabel = []
        for i in range(self.bands.size):
            if self.bands[i] >= 1000:
                bandsLabel.append(
                    str(np.round(self.bands[i]/1000, 1)) + " k")
            else:
                bandsLabel.append(str(np.round(self.bands[i], 0)))
        x = np.arange(len(bandsLabel))
        width = 0.3
        fig, ax = plt.subplots(
            num='Clarity: C50 and C80', figsize=(13, 8))
        bar1 = ax.bar(
            x - width/2, self.results['C50'], width, label=r'C$_{50}$')
        bar2 = ax.bar(
            x + width/2, self.results['C80'], width, label=r'C$_{80}$')
        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel('Clarity [dB]')
        ax.set_title('Clarity')
        ax.set_xticks(x)
        ax.set_xticklabels(bandsLabel)
        ax.legend(loc='best', shadow=True, fontsize='x-large')
        ax.grid(True, lw=1, ls='--', c='.75')

        def insertLabel(bar):
            """Attach a text label above each bar in *bar*, displaying its height."""
            if self._filter.b == 1:
                rotation = 45
            else:
                rotation = 90
            for rect in bar:
                height = rect.get_height()
                if height < 0:
                    # vertical offset
                    voffset = -25
                else:
                    voffset = 3
                ax.annotate('{}'.format(np.round(height, 1)),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, voffset),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', color="white", weight='bold', rotation=rotation)
        insertLabel(bar1)
        insertLabel(bar2)
        fig.tight_layout()
        if saveFig:
            formats = ['pdf', 'png', 'jpg', 'jpeg']
            if figName == None:
                figName = "Clarity"
            if not figFormat in formats:
                figFormat = 'pdf'
            plt.savefig(fname=figName+"."+figFormat,
                        bbox_inches='tight', pad_inches=0)
        plt.show()


# %% Example
if __name__ == '__main__':
    ################# Configuring input parameters #################
    # Load the impulse response into a vector of type numpy.ndarray
    IR = np.load('ImpulseResponse.npy')
    # Sampling rate
    fs = 48000
    # Initial frequency of octave band
    fstart = 63
    # Final frequency of octave band
    fend = 8000
    # Octave band filter fraction
    b = 1
    # Key for use Lundeby method
    bypassLundeby = False
    # Key to plot the decay curve and Lundeby parameters
    plotLundebyResults = False
    # Key to not suppress warning messages
    suppressWarnings = False
    # Final cut-off time in seconds for the impulsive
    # response in the background noise level
    IREndManualCut = None

    ######### Applying input parameters in the room class #########
    # Instantiate the room class with the input parameters
    roomsParams = rooms(IR=IR,
                        fs=fs,
                        fstart=fstart,
                        fend=fend,
                        b=b,
                        bypassLundeby=bypassLundeby,
                        plotLundebyResults=plotLundebyResults,
                        suppressWarnings=suppressWarnings,
                        IREndManualCut=IREndManualCut)

    ###### Getting the parameters by the `results` attribute #######
    # Early decay time
    EDT = roomsParams.results['EDT']
    print("EDT: ", EDT)
    # Reverberation time RT15
    RT15 = roomsParams.results['RT15']
    print("RT15: ", RT15)
    # Reverberation time RT20
    RT20 = roomsParams.results['RT20']
    print("RT20: ", RT20)
    # Reverberation time RT30
    RT30 = roomsParams.results['RT30']
    print("RT30: ", RT30)
    # Definition D50
    D50 = roomsParams.results['D50']
    print("D50: ", D50)
    # Definition D80
    D80 = roomsParams.results['D80']
    print("D80: ", D80)
    # Clarity C50
    C50 = roomsParams.results['C50']
    print("C50: ", C50)
    # Clarity C80
    C80 = roomsParams.results['C80']
    print("C80: ", C80)

    ############# View the reverberation time parameters ############
    roomsParams.plot_RT()
    roomsParams.plot_definition()
    roomsParams.plot_clarity()
