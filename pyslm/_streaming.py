# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 16:52:22 2020

@author: leonardojacomussi
"""
from scipy import interpolate as interp
import multiprocessing as mp
from time import sleep, time
from PyQt5 import QtCore
import sounddevice as sd
import threading as thd
import numpy as np
import h5py
import os
import pyslm

class StreamManager(QtCore.QObject):
    realtime_data = QtCore.pyqtSignal(dict)
    fullresults_data = QtCore.pyqtSignal(dict)
    callstop = QtCore.pyqtSignal()
    def __init__(self, path: str, device: list, fs: int, inCh: list, outCh: list,
                 tau: float, fstart: float, fend: float, b: int, fweighting: str,
                 duration: int, excitTime: int, scapeTime: int, decayTime: int, TLevel: int,
                 template: str, method: str, numDecay: int, fCalib: float, pCalib: float, calibFactor: float,
                 corrMic: {np.ndarray, None}, applyMicCorr: bool, corrADC: {np.ndarray, None}, applyAdcCorr: bool, saveRawData: bool):
        # inicio = time()
        super(StreamManager, self).__init__(None)
        ######## __init__ variables ########
        if path == None:
            self.path = os.getcwd()
        else: 
            self.path = path
        self.device = device
        self.fs = fs
        self.inCh = inCh
        self.outCh = outCh
        self.tau = tau
        self.fstart = fstart
        self.fend = fend
        self.b = b
        self.fweighting = fweighting
        self.duration = duration
        self.excitTime = excitTime
        self.scapeTime = scapeTime
        self.decayTime = decayTime
        self.TLevel = TLevel
        self.template = template
        self.method = method
        self.numDecay = numDecay
        self.fCalib = fCalib
        self.pCalib = pCalib
        self.calibFactor = calibFactor
        self.corrMic = corrMic
        self.applyMicCorr = applyMicCorr
        self.corrADC = corrADC
        self.applyAdcCorr = applyAdcCorr
        self.saveRawData = saveRawData
        ######## others parameters ########
        self._set_parameters()
        # fim = time()
        # print('TIME -> StreamManager.__init__: {} s.'.format(fim-inicio))
        return

    def play(self):
        try:
            if self.template in ['frequencyAnalyzer', 'calibration']:
                self.Record()
            elif self.template == 'reverberationTime':
                if self.method == 'impulse':
                    self.Record()
                else:
                    self.PlayRecord()
            elif self.template == 'stand-by':
                self.stand_by()
            else:
                pass
        except Exception as E:
            print("StreamManager.play(): ", E, "\n")
        return

    def pause(self):
        try:
            if self.isPaused.is_set():
                self.isPaused.clear()
            else:
                self.isPaused.set()
        except Exception as E:
            print("StreamManager.pause(): ", E, "\n")
        return

    def stop(self):
        try:
            if self.template in ['frequencyAnalyzer', 'reverberationTime']:
                self.callstop.emit()
            else:
                pass
            if self.stream.active:
                self.stream.close()
            else:
                pass
            self.isPlayed.clear()
            self.isPaused.clear()
            self.isStopped.set()
            # Waiting for termination of unfinished
            # processes and threads
            while(self.gettingResults.is_alive() and\
                  self.parallelProcess.is_alive() and\
                  self.threadStream.is_alive()):
                sleep(.1)
            # Threads of stream
            try:
                self.threadStream.join()
                self.threadStream._stop()
                self.threadStream._delete()
            except Exception:
                pass
            # Threads of pull results
            try:
                self.gettingResults.join()
                self.gettingResults._stop()
                self.gettingResults._delete()
            except Exception:
                pass
            # Process of parallel processing
            try:
                self.parallelProcess.join()
                self.parallelProcess.close()
            except Exception:
                pass
            # Shutting down database
            if self.recorderRawData is not None and self.saveRawData:
                if self.template == 'reverberationTime':
                    self.recorderRawData.add(self.send_to_disk)
                elif self.template == 'calibration':
                    self.recorderRawData.add(self.send_to_disk[self.cutSamples:self.framesRead,:])
                else:
                    pass
                self.recorderRawData.close()
            self.fullresults()
        except Exception as E:
            print("StreamManager.stop(): ", E, "\n")
        return

    def stand_by(self):
        try:
            self._setstream(streamType=sd.InputStream,
                        callback=self._standby_callback)
        except Exception as E:
            print("StreamManager.stand_by(): ", E, "\n")
        return

    def Record(self):
        try:
            self._setstream(streamType=sd.InputStream, callback=self._input_callback)
        except Exception as E:
            print("StreamManager.Record(): ", E, "\n")
        return

    def PlayRecord(self):
        try:
            self._setstream(streamType=sd.Stream, callback=self._stream_callback)
        except Exception as E:
            print("StreamManager.PlayRecord(): ", E, "\n")
        return

    def _setstream(self, streamType, callback):
        try:
            # inicio = time()
            self.stream = streamType(samplerate=self.fs,
                                     blocksize=self.frameSize,
                                     device=self.device,
                                     channels=self.numChannels[0],
                                     dtype='float32',
                                     callback=callback)
            self.isPaused.clear()
            self.isStopped.clear()
            self.isPlayed.set()
            self.parallelProcess = pyslm.parallelprocess(self.inData, self.isPlayed, self.params)
            self.parallelProcess.start()
            self.gettingResults = thd.Thread(target=self.realtime)
            self.gettingResults.start()
            self.threadStream = thd.Thread(target=self.runner)
            self.threadStream.start()
            # self.runner()
            # fim = time()
            # print('TIME -> StreamManager.run: {} s.\n'.format(fim-inicio))
        except Exception as E:
            print("StreamManager._setstream(): ", E, "\n")
        return

    def runner(self):
        try:
            with self.stream:
                self.isStopped.wait()
        except Exception as E:
            print("StreamManager.runner(): ", E, "\n")
        return

    def _set_parameters(self):
        try:
            # Events
            self.isPlayed = mp.Event()
            self.isPaused = mp.Event()
            self.isStopped = mp.Event()
            # Others variables
            self.recorderRawData = None
            self.recordedSignal = None
            self.cutSamples = int(0.15*self.fs)
            self.frameSize = int(self.tau * self.fs)
            self.numChannels = [len(self.inCh), len(self.outCh)]
            if self.template == 'frequencyAnalyzer':
                self.numSamples = int(self.duration * self.fs) + self.cutSamples
                if self.saveRawData:
                    self.recorderRawData = pyslm.storage(buffer_size=int(self.fs*180),
                                                   shape=(self.numSamples, 1),
                                                   path=self.path, kind='SPL')
                self.excitation = None
            elif self.template == 'reverberationTime':
                self.numSamples = int((self.excitTime + self.scapeTime +\
                                    self.decayTime) * self.fs) #+ self.cutSamples
                self.send_to_disk = np.empty(shape=(self.numSamples, self.numDecay),
                                            dtype = 'float32')
                if self.saveRawData:
                    self.recorderRawData = pyslm.storage(buffer_size=int(self.fs*30),
                                                    shape=(self.numSamples, self.numDecay),
                                                    path=self.path, kind='TR')

                self._set_excitation()
            elif self.template == 'calibration':
                self.numSamples = int(self.duration * self.fs) + self.cutSamples
                self.excitation = None
                self.send_to_disk = np.empty(shape=(self.numSamples+self.fs, 1), dtype = 'float32')
                if self.saveRawData:
                    self.recorderRawData = pyslm.storage(buffer_size=int(self.fs*30),
                                                    shape=(self.numSamples, 1),
                                                    path=self.path, kind='CAL')
            else:
                self.numSamples = int(self.duration * self.fs) + self.cutSamples
                self.excitation = None
            # Queue
            self.inData = mp.Queue(self.numSamples//2)
            # Counters
            self.countDecay = 0
            self.framesRead = 0
            self.countDn = self.numSamples
            self.counters = mp.Queue(self.numSamples//2)
            self.params = {'device':       self.device,
                        'fs':           self.fs,
                        'inCh':         self.inCh,
                        'outCh':        self.outCh,
                        'tau':          self.tau,
                        'fstart':       self.fstart,
                        'fend':         self.fend,
                        'b':            self.b,
                        'fweighting':   self.fweighting,
                        'duration':     self.duration,
                        'excitTime':    self.excitTime,
                        'scapeTime':    self.scapeTime,
                        'decayTime':    self.decayTime,
                        'template':     self.template,
                        'method':       self.method,
                        'numDecay':     self.numDecay,
                        'fCalib':       self.fCalib,
                        'pCalib':       self.pCalib,
                        'numChannels':  self.numChannels,
                        'numSamples':   self.numSamples,
                        'frameSize':    self.frameSize,
                        'applyMicCorr': self.applyMicCorr,
                        'applyAdcCorr': self.applyAdcCorr,
                        'calibFactor':  self.calibFactor}

            if self.applyMicCorr:
                if type(self.corrMic) == np.ndarray:
                    try:
                        freqVector = np.linspace(0, (self.frameSize - 1) *
                                                self.fs / (2*self.frameSize),
                                                (int(self.frameSize/2)+1)
                                                if self.frameSize % 2 == 0
                                                else int((self.frameSize+1)/2))
                        freq = self.corrMic[:, 0]
                        mag = self.corrMic[:, 1]
                        # Interpolacao da resposta do microfone
                        interp_func = interp.interp1d(
                            freq, mag, fill_value='extrapolate')
                        mag_interp = interp_func(freqVector)
                        mag_interp = mag_interp[~np.isnan(mag_interp)]
                        self.params['corrMic'] = mag_interp
                    except:
                        self.params['corrMic'] = None
                else:
                    self.params['corrMic'] = None
            else:
                self.params['corrMic'] = None

            if self.applyAdcCorr:
                if type(self.corrADC) == np.ndarray:
                    try:
                        freqVector = np.linspace(0, (self.frameSize - 1) *
                                                self.fs / (2*self.frameSize),
                                                (int(self.frameSize/2)+1)
                                                if self.frameSize % 2 == 0
                                                else int((self.frameSize+1)/2))
                        freq = self.corrADC[:, 0]
                        mag = self.corrADC[:, 1]
                        # Interpolacao da resposta do microfone
                        interp_func = interp.interp1d(
                            freq, mag, fill_value='extrapolate')
                        mag_interp = interp_func(freqVector)
                        mag_interp = mag_interp[~np.isnan(mag_interp)]
                        self.params['corrADC'] = mag_interp
                    except:
                        self.params['corrADC'] = None
                else:
                    self.params['corrADC'] = None
            else:
                self.params['corrADC'] = None
        except Exception as E:
            print("StreamManager._set_parameters(): ", E, "\n")
        return

    def _set_excitation(self):
        try:
            if self.method == 'sweepExponential':
                # fftDegree = np.log2(self.fs*self.excitTime)
                excitation = pyslm.sweep(fstart=self.fstart,
                                        fend=self.fend,
                                        fs=self.fs,
                                        duration=self.excitTime,
                                        startMargin=0,
                                        stopMargin=0)
                initial_zeros = np.zeros(shape=(int(self.fs*self.scapeTime)))
                final_zeros = np.zeros(shape=(int(self.fs*self.decayTime)))
                self.excitation = np.concatenate((initial_zeros, excitation, final_zeros), axis=0)

            elif self.method == 'pinkNoise':
                # fftDegree = np.log2(self.fs*self.excitTime)
                self.excitation = pyslm.noise(kind="pink",
                                        fs=self.fs,
                                        duration=self.excitTime,
                                        startMargin=self.scapeTime,
                                        stopMargin=self.decayTime)

            elif self.method == 'whiteNoise':
                # fftDegree = np.log2(self.fs*self.excitTime)
                self.excitation = pyslm.noise(kind="white",
                                        fs=self.fs,
                                        duration=self.excitTime,
                                        startMargin=self.scapeTime,
                                        stopMargin=self.decayTime)
        except Exception as E:
            print("StreamManager._set_excitation(): ", E, "\n")
        return

    def _standby_callback(self, indata: np.ndarray, frames: int,
                          times: type, status: sd.CallbackFlags):
        try:
            if self.isStopped.is_set():
                self.stop()
            elif indata.any():
                # Enviando os dados para um fila Queue()
                self.inData.put_nowait(indata.copy())
            else:
                pass
        except Exception as E:
            print("StreamManager._standby_callback(): ", E, "\n")
        return

    def _input_callback(self, indata: np.ndarray, frames: int,
                        times: type, status: sd.CallbackFlags):
        try:
            # Verificando se a stream está em stand-by
            if self.isPaused.is_set():
                pass
            # Verificando condições de parada
            elif self.isStopped.is_set():
                self.stop()
            elif self.framesRead >= self.numSamples or self.countDn < self.frameSize:
                self.stop()
            else:
                if indata.any():
                    # Enviando os dados para um fila Queue() de processamento
                    self.inData.put_nowait((indata.copy(), self.framesRead))
                    # Iterando quantidade de frames já armazenados
                    self.framesRead += self.frameSize
                    # Iterando contagem regressiva para tamanho do sinal de
                    # medição esperado em samples
                    self.countDn = self.numSamples - self.framesRead
                else:
                    pass
        except Exception as E:
            print("StreamManager._input_callback(): ", E, "\n")
        return

    def _stream_callback(self, indata: np.ndarray, outdata: np.ndarray,
                         frames: int, times: type, status: sd.CallbackFlags):
        try:
            # Verificando se a stream está em stand-by
            if self.isPaused.is_set():
                pass
            # Verificando condições de parada
            elif self.isStopped.is_set():
                self.stop()
            elif self.framesRead >= self.numSamples or self.countDn <= self.frameSize:
                self.countDecay += 1
                if self.countDecay >= self.numDecay:
                    self.stop()
                else:
                    self.framesRead = 0
                    self.countDn = self.numSamples
            else:
                if indata.any():
                    # and self.excitation[self.framesRead:self.framesRead+self.frameSize,:].any():
                    if self.excitation[self.framesRead:self.framesRead+self.frameSize].size >= self.frameSize:
                        # Enviando os dados para um fila Queue() de processamento
                        self.inData.put_nowait((indata.copy(), self.framesRead, self.countDecay))
                        # Enviando sinal de excitação para reprodução
                        for i in range(self.numChannels[0]):
                            outdata[:, i]\
                                = self.excitation[self.framesRead:self.framesRead+self.frameSize]
                    # print(self.excitation.shape)
                    # Iterando quantidade de frames já armazenados
                    self.framesRead += self.frameSize
                    # Iterando contagem regressiva para tamanho do sinal de
                    # medição esperado em samples
                    self.countDn = self.numSamples - self.framesRead
                else:
                    pass
        except Exception as E:
            print("StreamManager._stream_callback(): ", E, "\n")
        return

    def realtime(self):
        try:
            while not self.isPlayed.is_set():
                continue
            while self.isPlayed.is_set():
                if not self.parallelProcess.results.empty():
                    if self.template == 'stand-by':
                        results = self.parallelProcess.results.get_nowait()
                        self.realtime_data.emit(results)
                    elif self.template == 'frequencyAnalyzer':
                        results = self.parallelProcess.results.get_nowait()
                        self.realtime_data.emit(results)
                        signal = results['signal']
                        self.Leq_bands = results['Leq_bands']
                        self.Leq_global = results['Leq_global']
                        self.Lpeak = results['Lpeak']
                        self.Lglobal = results['Lglobal']
                        self.SEL = results['SEL']
                        if self.saveRawData:
                            self.recorderRawData.add(signal)
                        # print(f'SPL: {SPLglobal:.2f} dB | ' +
                        #       f' PID Process: {self.parallelProcess.pid:01d} | PID Main: ' +
                        #       f'{mp.current_process().pid:01d} | PID Stream: ' + 
                        #       f'{self.threadStream.pid:01d}'.replace(".", ","))
                    elif self.template == 'reverberationTime':
                        results = self.parallelProcess.results.get_nowait()
                        self.realtime_data.emit(results)
                        signal = results['signal']
                        framesRead = results['framesRead']
                        countDecay = results['countDecay']
                        self.send_to_disk[framesRead:framesRead+self.frameSize, countDecay] = signal[:,0]
                        # print(f'SPL: {np.round(SPLglobal, 2):.2f} dB | ' +
                        #       f' PID Process: {self.parallelProcess.pid:01d} | PID Main: ' +
                        #       f'{mp.current_process().pid:01d}'.replace(".", ","))
                    elif self.template == 'calibration':
                        results = self.parallelProcess.results.get_nowait()
                        self.realtime_data.emit(results)
                        signal = results['signal']
                        framesRead = results['framesRead']
                        self.send_to_disk[framesRead:framesRead+self.frameSize] = signal
                        # print(f'SPLmax: {SPLmax:.2f} dB | ' +
                        #       f'freqmax: {freqmax:.2f} Hz | ' +
                        #       f'PID Process: {self.parallelProcess.pid:01d} | PID Main: ' +
                        #       f'{mp.current_process().pid:01d}'.replace(".", ","))
                else:
                    if self.isPlayed.is_set():
                        continue
                    else:
                        break
            else:
                pass
        except Exception as E:
            print("StreamManager.realtime(): ", E, "\n")

    def fullresults(self):
        try:
            # print('\n\nFULLRESULTS')
            # inicio = time()
            if self.template == 'frequencyAnalyzer':
                process = pyslm.finalprocessing(inData=self.Lglobal, params=self.params, bandfilter=None, weightingfilter=None)
                process.results['Leq_bands'] = self.Leq_bands
                process.results['Leq_global'] = self.Leq_global
                process.results['Lpeak'] = self.Lpeak
                process.results['Lglobal'] = self.Lglobal
                process.results['Lmax'] = self.Lglobal.max()
                process.results['Lmin'] = self.Lglobal.min()
                process.results['SEL'] = self.SEL
                self.fullresults_data.emit(process.results)
            elif self.template == 'reverberationTime':
                self.IR = pyslm.ImpulseResponse(signal=self.send_to_disk, fs=self.fs, numDecay=self.numDecay, scapeTime=self.scapeTime,
                                          method=self.method, excitation=self.excitation)
                process = pyslm.finalprocessing(inData=self.IR, params=self.params,
                                          bandfilter=self.parallelProcess.bandfilter,
                                          weightingfilter=self.parallelProcess.weightingfilter)
                self.fullresults_data.emit(process.results)
                self.RT20 = process.results['RT20']
                # print(self.RT20)
            elif self.template == 'calibration':
                self.send_to_disk = self.send_to_disk[self.cutSamples:self.framesRead,0]
                process = pyslm.finalprocessing(inData=self.send_to_disk, params=self.params,
                                          bandfilter=self.parallelProcess.bandfilter,
                                          weightingfilter=self.parallelProcess.weightingfilter)
                self.fullresults_data.emit(process.results)
            # fim = time()
            # print('\nTIME -> StreamManager.fullresults: {} s.\n'.format(fim-inicio))
        except Exception as E:
            print("StreamManager.fullresults(): ", E, "\n")
        return


# %% Apenas para testes
if __name__ == '__main__':
    micData = np.loadtxt(fname='Files\\microphoneFRF.txt')
    adcData = np.loadtxt(fname='Files\\adcFRF.txt')
    demo = StreamManager(path = None,
                     device=[1, 3],
                     fs=44100,
                     inCh=[1],
                     outCh=[1, 2],
                     tau=0.125,
                     fstart=63.0,
                     fend=8000.0,
                     b=1,
                     fweighting='Z',
                     duration=180,
                     excitTime=5,
                     scapeTime=2,
                     decayTime=5,
                     # 'calibration', 'stand-by', 'reverberationTime', 'frequencyAnalyzer'
                     template='reverberationTime',
                     method='pinkNoise',  # 'pinkNoise', 'whiteNoise', 'sweepExponential'
                     numDecay=2,
                     TLevel = 76,
                     fCalib=1000.0,
                     pCalib=94.0,
                     calibFactor = 1.0,
                     corrMic=None,
                     applyMicCorr=False,
                     corrADC=None,
                     applyAdcCorr=False,
                     saveRawData=True)
    demo.play()
    sleep(.5)
    while not demo.isStopped.is_set():
        continue
    while demo.parallelProcess.results.empty():
        continue
    print("\n\n\n************* End of stream *************")