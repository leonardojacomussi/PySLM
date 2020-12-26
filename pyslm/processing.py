from scipy import interpolate as interp
import multiprocessing as mp
import threading as thd
import numpy as np
import pyslm

class parallelprocess(mp.Process):
    def __init__(self, inData, isPlayed, params):
        # Inheriting the class multiprocessing.Process()
        mp.Process.__init__(self)
        # Other initializations for event flags
        self.params = params
        self.inData = inData
        self.isPlayed = isPlayed
        self.results = mp.Queue(self.params['numSamples']//2)
        # Checking software version parameters
        if self.params['version'] == 'AdvFreqAnalyzer':
            # Configuring filters
            self._set_band_filter()
            # Set parameters
            self.leq_bands_sliding = np.zeros(shape=self.bandfilter.fnom.shape)
            self.Leq_bands = np.empty(shape=self.bandfilter.fnom.shape)
            self.L_max_bands = np.ones(shape=self.bandfilter.fnom.shape) * -10e3
            self.L_min_bands = np.ones(shape=self.bandfilter.fnom.shape) * 10e3
        # Set parameters
        self.time_interval = 1
        self.leq_global_sliding = 0
        self.lAeq_global_sliding = 0
        self.sel_global_sliding = self.params['tau']
        self.Leq_global = 0
        self.Lglobal = np.array([])
        self.Lpeak = 0
        # Set filters
        self.weightingfilter = pyslm.weighting(fs=self.params['fs'],
                                         tau=self.params['tau'],
                                         kind=self.params['fweighting'])
        self.weightingPeak = pyslm.weighting(fs=self.params['fs'],
                                         tau=self.params['tau'],
                                         kind='C')
        self.weightingSEL = pyslm.weighting(fs=self.params['fs'],
                                         tau=self.params['tau'],
                                         kind='A')
        # Other variables
        self.FC = float()
        self.idMax = None
        self.refPressure = 2e-05
        if self.params['applyMicCorr'] or self.params['applyAdcCorr']:
            if params['micCorr'] is not None or params['micCorr'] is not None:
                self.corr = True
            else:
                self.corr = False
        else:
            self.corr = False
            pass
        # The multiprocessing class needs a run () method
        if self.params['template'] == 'stand-by':
            if self.params['version'] == 'AdvFreqAnalyzer':
                self.run = self.stand_by
            elif self.params['version'] == 'DataLogger':
                self.run = self.stand_by_datalogger
            else:
                pass
        elif self.params['template'] == 'spl':
            self.run = self.datalogger
        elif self.params['template'] ==  'frequencyAnalyzer':
            self.run = self.frequencyAnalyzer
        elif self.params['template'] == 'reverberationTime':
            self.run = self.reverberationTime
        elif self.params['template'] == 'calibration':
            self.run = self.calibration
        else:
            pass
    

    def stand_by(self):
        """
        Description:
        ------------
        Function that receives the sound pressure measured by
        the microphone in Pascal and returns the level of global
        sound pressure and in frequency bands.

        Processing steps:
        -----------------
            (1) Apply spectral correction if correction files exist
            (2) Frequency weighting filter (A, C and Z)
            (3) Filter in octave bands (1/1 or 1/3)
            (5) Sound level by frequency bands
            (4) Time weight filter (Impulse, Fast and Slow)
            (6) Global sound level

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        Lp_global : float
            Global sound pressure level of the measured signal
        Lp_bands : np.ndarray
            Sound pressure level by bands
        """
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.inData.empty():
                    rawData = self.inData.get_nowait()
                    # Applying calibration factor
                    rawData = rawData * self.params['calibFactor']
                    # Getting global and band levels
                    signal = rawData[:, 0]
                    # 1) Apply spectral correction if correction files exist
                    if self.corr:
                        signal = self._apply_correction(signal=signal, domain='time')
                    # 2) Applying frequency weighting filter
                    signal_freq_weighting = self.weightingfilter.frequency(
                        signal=signal)
                    # 3) Applying octave band filter
                    filteredSignal = self.bandfilter.filter(data=signal_freq_weighting)
                    # 4) Calculating sound pressure level by bands
                    Lp_bands = np.round(10 * \
                        np.log10(rms(a=filteredSignal**2, #signal_time_weighting,
                                        axis=0)**2/self.refPressure**2), 2)
                    # 5) Applying time weighting filter
                    signal_time_weighting = self.weightingfilter.time(
                        signal=signal_freq_weighting**2, reshape=False)
                    # 6) Calculating overall sound pressure level
                    Lp_global = np.round(10 * np.log10(rms(a=signal_time_weighting, axis=0)**2/self.refPressure**2), 2)
                    # Queuing results
                    self.results.put_nowait({'Lp_global': Lp_global,
                                             'Lp_bands': Lp_bands,
                                             'strBands': self.strBands,
                                             'x_axis': self.x_axis,
                                             'bands': self.bands})
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("parallelprocess.run(): ", E, "\n")
        return

    def stand_by_datalogger(self):
        """
        Description:
        ------------
        Function that receives the sound pressure measured by
        the microphone in Pascal and returns the level of global
        sound pressure and in frequency bands.

        Processing steps:
        -----------------
            (1) Apply spectral correction if correction files exist
            (2) Frequency weighting filter (A, C and Z)
            (3) Time weight filter (Impulse, Fast and Slow)
            (4) Global sound level

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        Lp_global : float
            Global sound pressure level of the measured signal
        Lp_bands : np.ndarray
            Sound pressure level by bands
        """
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.inData.empty():
                    rawData = self.inData.get_nowait()
                    # Applying calibration factor
                    rawData = rawData * self.params['calibFactor']
                    # Getting global and band levels
                    signal = rawData[:, 0]
                    # 1) Apply spectral correction if correction files exist
                    if self.corr:
                        signal = self._apply_correction(signal=signal, domain='time')
                    # 2) Applying frequency weighting filter
                    signal_freq_weighting = self.weightingfilter.frequency(
                        signal=signal)
                    # 3) Applying time weighting filter
                    signal_time_weighting = self.weightingfilter.time(
                        signal=signal_freq_weighting**2, reshape=False)
                    # 4) Calculating overall sound pressure level
                    Lp_global = np.round(10 * np.log10(rms(a=signal_time_weighting, axis=0)**2/self.refPressure**2), 2)
                    # Queuing results
                    self.results.put_nowait({'Lp_global': Lp_global})
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("parallelprocess.run(): ", E, "\n")
        return

    def datalogger (self):
        """
        Description:
        ------------
        Function that receives the sound pressure measured by
        the microphone in Pascal and returns the level of global
        sound pressure.

        Processing steps:
        -----------------
            (1) Apply spectral correction if correction files exist
            (2) Frequency weighting filter (A, C and Z)
            (4) Time weight filter (Impulse, Fast and Slow)
            (5) Global sound level
            (6) Peak sound level
            (7) Calculating equivalent continuous sound level

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        Lp_global : float
            Global sound pressure level of the measured signal
        """
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.inData.empty():
                    rawData, _ = self.inData.get_nowait()
                    # Applying calibration factor
                    rawData = rawData * self.params['calibFactor']
                    # Getting global and band levels
                    signal = rawData[:, 0]
                    # 1) Apply spectral correction if correction files exist
                    if self.corr:
                        signal = self._apply_correction(signal=signal, domain='time')
                    # 2) Applying frequency weighting filter
                    signal_freq_weighting = self.weightingfilter.frequency(
                        signal=signal)
                    # 3) Applying time weighting filter
                    signal_time_weighting = self.weightingfilter.time(
                        signal=signal_freq_weighting**2, reshape=False)
                    # 4) Calculating overall sound pressure level
                    Lp_global = np.round(10*np.log10(rms(a=signal_time_weighting, axis=0)**2/self.refPressure**2), 2)
                    self.Lglobal = np.append(self.Lglobal, Lp_global)
                    # 5) Peak sound level
                    if self.time_interval > 1:
                        C_weighting_Peak = self.weightingPeak.frequency(signal=signal)
                        C_Peak = np.max(np.abs(C_weighting_Peak))
                        Lpeak = np.round(10*np.log10(C_Peak**2/self.refPressure**2), 2)
                        if Lpeak > self.Lpeak:
                            self.Lpeak = Lpeak
                        else:
                            pass
                    else:
                        pass
                    # 6) Calculating equivalent continuous sound level
                    self.leq_global_sliding += 10**(Lp_global/10)
                    self.Leq_global = np.round(10*np.log10(1/self.time_interval * self.leq_global_sliding), 2)
                    # 7) Sound Exposure Level A-weighted
                    signal_freq_weighting_SEL = self.weightingSEL.frequency(signal=signal)
                    signal_time_weighting_SEL = self.weightingSEL.time(signal=signal_freq_weighting_SEL**2, reshape=False)
                    self.lAeq_global_sliding += rms(a=signal_time_weighting_SEL, axis=0)**2/self.refPressure**2
                    LAeq_global = np.round(10*np.log10(1/self.time_interval * self.lAeq_global_sliding), 2)
                    SEL = np.round(LAeq_global + 10*np.log10(self.sel_global_sliding), 2)
                    self.sel_global_sliding += self.params['tau']
                    self.time_interval += 1
                    # Queuing results
                    self.results.put_nowait({'Lp_global': Lp_global,
                                             'Leq_global': self.Leq_global,
                                             'Lpeak': self.Lpeak,
                                             'Lglobal': self.Lglobal,
                                             'SEL': SEL,
                                             'signal': rawData})
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("parallelprocess.run(): ", E, "\n")
        return



    def frequencyAnalyzer(self):
        """
        Description:
        ------------
        Function that receives the sound pressure measured by
        the microphone in Pascal and returns the level of global
        sound pressure and in frequency bands.

        Processing steps:
        -----------------
            (1) Apply spectral correction if correction files exist
            (2) Frequency weighting filter (A, C and Z)
            (3) Filter in octave bands (1/1 or 1/3)
            (4) Sound level by frequency bands
            (5) Time weight filter (Impulse, Fast and Slow)
            (6) Global sound level
            (7) Peak sound level
            (8) Calculating equivalent continuous sound level

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        Lp_global : float
            Global sound pressure level of the measured signal
        Lp_bands : np.ndarray
            Sound pressure level by bands
        """
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.inData.empty():
                    rawData, _ = self.inData.get_nowait()
                    # Applying calibration factor
                    rawData = rawData * self.params['calibFactor']
                    # Getting global and band levels
                    signal = rawData[:, 0]
                    # 1) Apply spectral correction if correction files exist
                    if self.corr:
                        signal = self._apply_correction(signal=signal, domain='time')
                    # 2) Applying frequency weighting filter
                    signal_freq_weighting = self.weightingfilter.frequency(
                        signal=signal)
                    # 3) Applying octave band filter
                    filteredSignal = self.bandfilter.filter(data=signal_freq_weighting)
                    # 4) Calculating sound pressure level by bands
                    Lp_bands = np.round(10*np.log10(rms(a=filteredSignal**2,  axis=0)**2/self.refPressure**2), 2)
                    for i in range(self.bands.size):
                        if Lp_bands[i] > self.L_max_bands[i]:
                            self.L_max_bands[i] = Lp_bands[i]
                        if Lp_bands[i] < self.L_min_bands[i]:
                            self.L_min_bands[i] = Lp_bands[i]
                    # 5) Applying time weighting filter
                    signal_time_weighting = self.weightingfilter.time(
                        signal=signal_freq_weighting**2, reshape=False)
                    # 6) Calculating overall sound pressure level
                    Lp_global = np.round(10*np.log10(rms(a=signal_time_weighting, axis=0)**2/self.refPressure**2), 2)
                    self.Lglobal = np.append(self.Lglobal, Lp_global)
                    # 7) Peak sound level
                    if self.time_interval > 1:
                        C_weighting_Peak = self.weightingPeak.frequency(signal=signal)
                        C_Peak = np.max(np.abs(C_weighting_Peak))
                        Lpeak = np.round(10*np.log10(C_Peak**2/self.refPressure**2), 2)
                        if Lpeak > self.Lpeak:
                            self.Lpeak = Lpeak
                        else:
                            pass
                    else:
                        pass
                    # 8) Calculating equivalent continuous sound level
                    self.leq_bands_sliding += 10**(Lp_bands/10)
                    self.leq_global_sliding += 10**(Lp_global/10)
                    self.Leq_bands = np.round(10*np.log10(1/self.time_interval * self.leq_bands_sliding), 2)
                    self.Leq_global = np.round(10*np.log10(1/self.time_interval * self.leq_global_sliding), 2)
                    # 9) Sound Exposure Level
                    # 7) Sound Exposure Level A-weighted
                    signal_freq_weighting_SEL = self.weightingSEL.frequency(signal=signal)
                    signal_time_weighting_SEL = self.weightingSEL.time(signal=signal_freq_weighting_SEL**2, reshape=False)
                    self.lAeq_global_sliding += rms(a=signal_time_weighting_SEL, axis=0)**2/self.refPressure**2
                    LAeq_global = np.round(10*np.log10(1/self.time_interval * self.lAeq_global_sliding), 2)
                    SEL = np.round(LAeq_global + 10*np.log10(self.sel_global_sliding), 2)
                    self.sel_global_sliding += self.params['tau']
                    self.time_interval += 1
                    # Queuing results
                    self.results.put_nowait({'Lp_global': Lp_global,
                                             'Lp_bands': Lp_bands,
                                             'L_max_bands': self.L_max_bands,
                                             'L_min_bands': self.L_min_bands,
                                             'Leq_bands': self.Leq_bands,
                                             'Leq_global': self.Leq_global,
                                             'Lpeak': self.Lpeak,
                                             'Lglobal': self.Lglobal,
                                             'SEL': SEL,
                                             'signal': rawData,
                                             'strBands': self.strBands,
                                             'x_axis': self.x_axis,
                                             'bands': self.bands})
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("parallelprocess.run(): ", E, "\n")
        return

    def reverberationTime(self):
        """
        Description:
        ------------
        Function that receives the sound pressure measured by
        the microphone in Pascal and returns the level of global
        sound pressure and in frequency bands.

        Processing steps:
        -----------------
            (1) Apply spectral correction if correction files exist
            (2) Frequency weighting filter (A, C and Z)
            (3) Filter in octave bands (1/1 or 1/3)
            (5) Sound level by frequency bands
            (4) Time weight filter (Impulse, Fast and Slow)
            (6) Global sound level

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        Lp_global : float
            Global sound pressure level of the measured signal
        Lp_bands : np.ndarray
            Sound pressure level by bands
        """
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.inData.empty():
                    rawData, framesRead, countDecay = self.inData.get_nowait()
                    # Applying calibration factor
                    rawData = rawData * self.params['calibFactor']
                    # Getting global and band levels
                    signal = rawData[:, 0]
                    # 1) Apply spectral correction if correction files exist
                    if self.corr:
                        signal = self._apply_correction(signal=signal, domain='time')
                    # 2) Applying frequency weighting filter
                    signal_freq_weighting = self.weightingfilter.frequency(
                        signal=signal)
                    # 3) Applying octave band filter
                    filteredSignal = self.bandfilter.filter(data=signal_freq_weighting)
                    # 4) Calculating sound pressure level by bands
                    Lp_bands = np.round(10 * \
                        np.log10(rms(a=filteredSignal**2, #signal_time_weighting,
                                        axis=0)**2/self.refPressure**2), 2)
                    # 5) Applying time weighting filter
                    signal_time_weighting = self.weightingfilter.time(
                        signal=signal_freq_weighting**2, reshape=False)
                    # 6) Calculating overall sound pressure level
                    Lp_global = np.round(10 * np.log10(rms(a=signal_time_weighting, axis=0)**2/self.refPressure**2), 2)
                    # Queuing results
                    self.results.put_nowait({'Lp_global': Lp_global,
                                             'Lp_bands': Lp_bands,
                                             'strBands': self.strBands,
                                             'x_axis': self.x_axis,
                                             'signal': rawData,
                                             'framesRead': framesRead,
                                             'countDecay': countDecay,
                                             'bands': self.bands})
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("parallelprocess.run(): ", E, "\n")
        return

    def calibration(self):
        """
        Description:
        ------------
        Function that performs the transformation of the Fourier, returning the vectors
        of complex amplitude and frequency to display on the calibration screen.

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        freqSignal : np.ndarray
            Complex amplitude vector [Pa]
        freqVector : np.ndarray
            Frequency vector [Hz]
        """
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.inData.empty():
                    self._inData, framesRead = self.inData.get_nowait()
                    # Getting global and band levels
                    signal = self._inData[:, 0]
                    # 1) Apply spectral correction if correction files exist
                    if self.corr:
                        freqSignal = self._apply_correction(
                            signal=signal, domain='freq')
                    else:
                        freqSignal = np.fft.rfft(signal, axis=0, norm=None)
                    numSamples = len(signal)
                    freqSignal /= 2**0.5
                    freqSignal /= len(freqSignal)
                    freqVector = np.linspace(0, (numSamples - 1) *
                                            self.params['fs'] /
                                            (2*numSamples),
                                            (int(numSamples/2)+1)
                                            if numSamples % 2 == 0
                                            else int((numSamples+1)/2))
                    a = np.where(freqVector >= self.params['fCalib'] - 50)[0][0]
                    b = np.where(freqVector <= self.params['fCalib'] + 50)[0][-1]
                    sensitivity = np.abs(freqSignal[a:b]).max()
                    if 20 * np.log10(sensitivity/self.refPressure) > 104:
                        FC = 10/sensitivity
                    else:
                        FC = 1/sensitivity
                    with np.errstate(divide='ignore'):
                        SPL = 20 * np.log10(np.abs(freqSignal)/self.refPressure)
                        sensitivity = np.round(sensitivity, 2)
                        correction = np.round(np.abs(10*np.log10(sensitivity)) -
                                            np.abs(10*np.log10(1/self.params['calibFactor'])), 2)
                        idMax = np.where(SPL == SPL[a:b].max())[0][0]
                        SPLmax = np.round(SPL[idMax], 2)
                        freqmax = np.round(freqVector[idMax], 2)
                    # Queuing results
                    results = {}
                    if self.params['version'] == 'AdvFreqAnalyzer':
                        results['SPL'] = SPL
                        results['freqVector'] = freqVector
                    results['SPLmax'] = SPLmax
                    results['freqmax'] = freqmax
                    results['sensitivity'] = sensitivity*1000
                    results['correction'] = correction
                    results['FC'] = FC
                    results['signal'] = self._inData
                    results['framesRead'] = framesRead
                    self.results.put_nowait(results)
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("parallelprocess.run(): ", E, "\n")
        return

    def _set_band_filter(self):
        try:
            # OctaFilter frequency filter
            self.bandfilter = pyslm.OctFilter(fstart=self.params['fstart'],
                                        fend=self.params['fend'],
                                        b=self.params['b'],
                                        fs=self.params['fs'])

            # Nominal frequencies used on the "x" axis of the plots
            self.bands = self.bandfilter.fnom
            self.x_axis = np.asarray(range(self.bands.size), dtype=np.int32)
            freq = {31.5: '31.5', 63. :'63', 125.: '125', 250.: '250', 500.: '500',
                   1000.: '1k', 2000.: '2k', 4000.: '4k', 8000.: '8k', 16000.: '16k'}
            self.strBands = list()
            for i in range(self.bands.size):
                if self.bands[i] in freq.keys():
                    self.strBands.append((i, freq[self.bands[i]]))
                else:
                    self.strBands.append((i, ''))
        except Exception as E:
            print("parallelprocess._set_band_filter(): ", E, "\n")

    def _apply_correction(self, signal: np.ndarray, domain: str = 'time'):
        try:
            with np.errstate(divide='ignore'):
                freqSignal = np.fft.rfft(signal, axis=0, norm=None)
                MagfreqSignal = 20 * \
                    np.log10(np.abs(freqSignal))
                correctedMagfreqSignal = MagfreqSignal
                # Carregando dados do microfone
                if self.params['micCorr'] is not None and self.params['applyMicCorr']:
                    # Aplica correcao na magnitude
                    correctedMagfreqSignal -= self.params['micCorr']

                # Carregando dados do ADC
                if self.params['adcCorr'] is not None and self.params['applyAdcCorr']:
                    # Aplica correcao na magnitude
                    correctedMagfreqSignal -= self.params['adcCorr']
                # Retorna ao vetor de amplitude complexa com magnitude e fase
                correctedfreqSignal = 10**(correctedMagfreqSignal /
                                        20)
                r = correctedfreqSignal
                teta = np.angle(freqSignal)
                correctedfreqSignal = r*(np.cos(teta) + np.sin(teta)*1j)

                if domain.lower() == 'time':
                    # Transforma em SignalObj para obter o sinal no tempo (ifft)
                    correctedSignal = np.fft.irfft(a=correctedfreqSignal)# * self.window
                elif domain.lower() == 'freq':
                    correctedSignal = correctedfreqSignal
                else:
                    AttributeError("Unsupported domain, please try domain = 'freq'" +
                                " if the `signal` parameter is the signal power spectrum," +
                                " or try domain = 'time' if the` signal` parameter is the signal" +
                                " measured in the time domain.")
        except Exception as E:
            print("parallelprocess._apply_correction(): ", E, "\n")
        return correctedSignal


class finalprocessing(object):
    def __init__(self, inData, params, bandfilter, weightingfilter):
        self.params = params
        self.inData = inData
        self.bandfilter = bandfilter
        self.weightingfilter = weightingfilter
        self.refPressure = 2e-05
        if self.params['template'] in ['spl', 'frequencyAnalyzer']:
            self.results = self.statisticallevels()
        elif self.params['template'] == 'reverberationTime':
            self.results = self.reverberationTime()
        elif self.params['template'] == 'calibration':
            self.results = self.calibration()
        else:
            AttributeError("Template %s not supported, please try 'frequencyAnalyzer', " +
                           "'reverberationTime' or 'calibration'." % self.params['template'])

    def statisticallevels(self):
        """
        Description:
        ------------
        Function that returns the statistical levels L10, L50 and 690.

        Parameters
        ----------
        Leq : np.ndarray
            Vector containing Leq values recorded during measurement

        Returns
        -------
        StatisticalLevels : dict
            Statistical levels (L10, L50 and L90) based on the Leq levels
            recorded during the measurement.
        """
        try:
            Leq = self.inData
            L10 = np.round(np.percentile(Leq, 90), 2)
            L50 = np.round(np.percentile(Leq, 50), 2)
            L90 = np.round(np.percentile(Leq, 10), 2)


            StatisticalLevels = {'L10': L10,
                                 'L50': L50,
                                 'L90': L90}
        except Exception as E:
            print("finalprocessing.StatisticalLevels(): ", E, "\n")
        return StatisticalLevels

    def reverberationTime(self):
        try:
            # Load the impulse response into a vector of type numpy.ndarray
            IR = self.inData
            # Sampling rate
            fs = self.params['fs']
            # Initial frequency of octave band
            fstart = self.params['fstart']
            # Final frequency of octave band
            fend = self.params['fend']
            # Octave band filter fraction
            b = self.params['b']
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
            roomsParams = pyslm.rooms(IR=IR,
                                fs=fs,
                                fstart=fstart,
                                fend=fend,
                                b=b,
                                bypassLundeby=bypassLundeby,
                                plotLundebyResults=plotLundebyResults,
                                suppressWarnings=suppressWarnings,
                                IREndManualCut=IREndManualCut)
        except Exception as E:
            print("finalprocessing.reverberationTime(): ", E, "\n")
        return roomsParams.results

    def calibration(self):
        """
        Description:
        ------------
        Function that performs the transformation of the Fourier, returning the vectors
        of complex amplitude and frequency to display on the calibration screen.

        Parameters
        ----------
        signal : np.ndarray
            Signal measured by the microphone [Pa]

        Returns
        -------
        freqSignal : np.ndarray
            Complex amplitude vector [Pa]
        freqVector : np.ndarray
            Frequency vector [Hz]
        """
        try:
            signal = self.inData
            numSamples = len(signal)
            freqSignal = np.fft.rfft(signal, axis=0, norm=None)
            freqSignal /= 2**0.5
            freqSignal /= len(freqSignal)
            freqVector = np.linspace(0, (numSamples - 1) *
                                     self.params['fs'] /
                                     (2*numSamples),
                                     (int(numSamples/2)+1)
                                     if numSamples % 2 == 0
                                     else int((numSamples+1)/2))
            a = np.where(freqVector >= self.params['fCalib'] - 50)[0][0]
            b = np.where(freqVector <= self.params['fCalib'] + 50)[0][-1]
            with np.errstate(divide='ignore'):
                sensitivity = np.abs(freqSignal[a:b]).max()
                if 20 * np.log10(sensitivity/self.refPressure) > 104:
                    FC = 10/sensitivity
                else:
                    FC = 1/sensitivity
                SPL = 20 * np.log10(np.abs(freqSignal)/self.refPressure)
                sensitivity = np.round(sensitivity, 2)
                correction = np.round(np.abs(10*np.log10(sensitivity)) -
                                    np.abs(10*np.log10(1/self.params['calibFactor'])), 2)
                idMax = np.where(SPL == SPL[a:b].max())[0][0]
                SPLmax = np.round(SPL[idMax], 2)
                freqmax = np.round(freqVector[idMax], 2)
            results = {}
            if self.params['version'] == 'AdvFreqAnalyzer':
                results['SPL'] = SPL
                results['freqVector'] = freqVector
            results['SPLmax'] = SPLmax
            results['freqmax'] = freqmax
            results['sensitivity'] = sensitivity*1000
            results['correction'] = correction
            results['FC'] = FC
        except Exception as E:
            print("finalprocessing.calibration(): ", E, "\n")
        return results


def ImpulseResponse(signal: np.ndarray, fs: int, excitTime: int, numDecay: int, scapeTime: int, method: str, excitation: {None, np.ndarray} = None):
    if numDecay > 1:
        if signal.shape[-1] > signal.shape[0]:
            signal = signal.transpose()
        else:
            pass
        signal = np.mean(a=signal, axis=1)
    else:
        signal = signal[:,0]
    if method in ['pinkNoise', 'whiteNoise']:
        time = np.arange(0, signal.size/fs, 1/fs)
        cutPoint = np.where(time >= scapeTime + excitTime)[0][0]
        signal = signal[cutPoint:]
        square = signal**2
        maxPoint = np.where(square == square.max())[0][0]
        impulseResponse = signal[maxPoint:]
    else:
        if signal.size > excitation.size:
            size = signal.size - excitation.size
            zeros = np.zeros(shape=(size))
            excitation = np.concatenate((excitation, zeros), axis=0)
        elif excitation.size > signal.size:
            size = excitation.size - signal.size
            zeros = np.zeros(shape=(size))
            excitation = np.concatenate((signal, zeros), axis=0)
        else:
            pass
        time = np.arange(0, signal.size/fs, 1/fs)
        cutPoint = np.where(time >= scapeTime)[0][0]
        signal = signal[cutPoint:]
        excitation = excitation[cutPoint:]
        freqSignal = np.fft.rfft(signal, axis=0, norm=None)
        freqExcitation = np.fft.rfft(excitation, axis=0, norm=None)
        freqIR = freqSignal/freqExcitation
        impulseResponse = np.fft.irfft(a=freqIR)
        square = impulseResponse**2
        maxPoint = np.where(square == square.max())[0][0]
        impulseResponse = impulseResponse[maxPoint:]
    # print('Shape is: ', signal.shape)
    return impulseResponse

def rms(a, axis):
    """
    Function that calculates the root mean square of the sound pressure.

    Args:
        a : np.ndarray
        Quadratic sound pressure (e.g. pressure**2)
        axis : int
        Vector calculation axis

    Returns:
        np.ndarray or int
        
    """
    return np.sqrt(np.mean(a=a, axis=axis))

def apply_correction(signal: np.ndarray, fs: int, micCorr: {None, np.ndarray},
                     adcCorr: {None, np.ndarray}, applyMicCorr: bool, applyAdcCorr: bool):
    try:
        refPressure = 2e-05
        freqSignal = np.fft.rfft(signal, axis=0, norm=None)
        freqVector = np.linspace(0, (signal.size - 1) *
                                fs / (2*signal.size),
                                (int(signal.size/2)+1)
                                if signal.size % 2 == 0
                                else int((signal.size+1)/2))
        MagfreqSignal = 20 * \
            np.log10(np.abs(freqSignal)/refPressure)
        correctedMagfreqSignal = MagfreqSignal
        # Carregando dados do microfone
        if micCorr is not None and applyMicCorr:
            freq = micCorr[:, 0]
            mag = micCorr[:, 1]
            # Microphone response interpolation
            interp_func = interp.interp1d(
                freq, mag, fill_value='extrapolate')
            mag_interp = interp_func(freqVector)
            # Aplica correcao na magnitude
            correctedMagfreqSignal -= mag_interp

        # Carregando dados do ADC
        if adcCorr is not None and applyAdcCorr:
            freq = adcCorr[:, 0]
            mag = adcCorr[:, 1]
            # Response interpolation of the digital analog converter
            interp_func = interp.interp1d(
                freq, mag, fill_value='extrapolate')
            mag_interp = interp_func(freqVector)
            # Aplica correcao na magnitude
            correctedMagfreqSignal -= mag_interp
        # Retorna ao vetor de amplitude complexa com magnitude e fase
        correctedfreqSignal = 10**(correctedMagfreqSignal /
                                    20) * refPressure
        r = correctedfreqSignal
        teta = np.angle(freqSignal)
        correctedfreqSignal = r*(np.cos(teta) + np.sin(teta)*1j)
        correctedSignal = np.fft.irfft(a=correctedfreqSignal)
    except Exception as E:
        print("apply_correction(): ", E, "\n")
    return correctedSignal
