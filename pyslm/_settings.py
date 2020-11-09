from PySide2 import QtCore, QtGui, QtWidgets
import sounddevice as sd
import threading as thd
from time import sleep
import numpy as np
import pyqtgraph
import os, sys
import pyslm

path_icons = os.path.join(os.path.dirname(os.path.realpath(pyslm.__file__)), 'Icons')

if sys.platform == 'win32' or sys.platform == 'win64':
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
else:
    pass


class setSetup(QtWidgets.QDialog, pyslm.guiSetup):
    def __init__(self, parent=None):
        super(setSetup, self).__init__(parent)
        self.setupUi(self)
        self.restore = False
        self._listNumFreq = [20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0,
                            100.0, 125.0, 160.0, 200.0, 250.0, 4000.0,
                            5000.0, 6300.0, 8000.0, 10000.0, 16000.0, 20000.0]
        self._listStrFreq = ['20 Hz', '25 Hz', '31.5 Hz', '40 Hz', '50 Hz', '63 Hz',
                             '80 Hz', '100 Hz', '125 Hz', '160 Hz', '200 Hz', '250 Hz',
                             '4 kHz', '5 kHz', '6.3 kHz', '8 kHz', '10 kHz', '16 kHz', '20 kHz']
        self._str2numFreq = {}
        self._num2strFreq = {}
        count = 0
        for string in self._listStrFreq:
            self._str2numFreq[string] = self._listNumFreq[count]
            count += 1
        count = 0
        for number in self._listNumFreq:
            self._num2strFreq[number] = self._listStrFreq[count]
            count += 1
        self.newParams = pyslm.parameters.load()
        self.currentParams = pyslm.parameters.load()
        self.plotMic = None
        self.plotADC = None
        self._setTabMeasurement()
        self._setTabCalibration()
        self._setTabProjects()
        self._setTabSpectrumCorretion()
        self._setTabDevice()
        self.changedParams()
        self.btnClose.clicked.connect(self.btnClose_Action)
        self.btnApply.clicked.connect(self.btnApply_Action)
        self.btnRestore.clicked.connect(self.btnRestore_Action)

    def _restore(self):
        self.newParams = self.currentParams.copy()
        self.compensationView.plotItem.clear()
        self.plotMic = None
        self.plotADC = None
        self._setTabMeasurement()
        self._setTabCalibration()
        self._setTabProjects()
        self._setTabSpectrumCorretion()
        self._setTabDevice()
        self.changedParams()
        return

    def _setTabMeasurement(self):
        # Set current template
        if self.newParams['template'] == 'frequencyAnalyzer':
            self.inTemplate.setCurrentIndex(0)
        else:
            self.inTemplate.setCurrentIndex(1)
        # Set current bandwidth
        if self.newParams['b'] == 1:
            self.inBandwidth.setCurrentIndex(0)
        else:
            self.inBandwidth.setCurrentIndex(1)
        methods = {'sweepExponential': 'Exponential sweep',
                   'whiteNoise': 'White noise',
                   'pinkNoise': 'Pink noise',
                   'impulse': 'Impulse'}
        self.inMethod.setCurrentText(methods[self.newParams['method']])
        self._listParamsTabMeasurement()
        self._setfrequencyLimits()
        self._setMethod()
        # Set frequency weighting
        self.inFreqWeighting.setCurrentText(self.newParams['fweighting'])
        # Set time weighting
        TimeWeighting = {0.035: 'Impulse', 0.125: 'Fast', 1.0: 'Slow'}
        self.inTimeWeighting.setCurrentText(TimeWeighting[self.newParams['tau']])
        # Set duration
        h, m, s = self.seconds2HMN(self.newParams['duration'])
        self.inHour.setCurrentText(h)
        self.inMin.setCurrentText(m)
        self.inSec.setCurrentText(s)
        # Set excitation time
        _, m, s = self.seconds2HMN(self.newParams['excitTime'])
        self.inMinExcit.setCurrentText(m)
        self.inSecExcit.setCurrentText(s)
        # Set escape time
        _, m, s = self.seconds2HMN(self.newParams['scapeTime'])
        self.inMinScape.setCurrentText(m)
        self.inSecScape.setCurrentText(s)
        # Set decay time
        _, _, s = self.seconds2HMN(self.newParams['decayTime'])
        self.inSecDecay.setCurrentText(s)
        # Set number of decay
        self.inNumDecays.setCurrentText('%02d'%self.newParams['numDecay'])
        # Set trigger level
        self.inTriggerLevel.setCurrentText('%02d dB'%self.newParams['TLevel'])
        # Set connections
        self.inTemplate.currentIndexChanged.connect(self._setfrequencyLimits)
        self.inBandwidth.currentIndexChanged.connect(self._setfrequencyLimits)
        self.inBottomFreq.currentIndexChanged.connect(self._setBottomFreq)
        self.inTopFreq.currentIndexChanged.connect(self._setTopFreq)
        self.inHour.currentTextChanged.connect(self._setDuration)
        self.inMin.currentTextChanged.connect(self._setDuration)
        self.inSec.currentTextChanged.connect(self._setDuration)
        self.inFreqWeighting.currentTextChanged.connect(self._setFreqWeighting)
        self.inTimeWeighting.currentTextChanged.connect(self._setTimeWeighting)
        self.inMethod.currentIndexChanged.connect(self._setMethod)
        self.inMinExcit.currentTextChanged.connect(self._setExcitTime)
        self.inSecExcit.currentTextChanged.connect(self._setExcitTime)
        self.inMinScape.currentTextChanged.connect(self._setEscapeTime)
        self.inSecScape.currentTextChanged.connect(self._setEscapeTime)
        self.inSecDecay.currentTextChanged.connect(self._setSecDecay)
        self.inNumDecays.currentTextChanged.connect(self._setNumDecay)
        self.inTriggerLevel.currentTextChanged.connect(self._setTriggerLevel)

    def _setTabCalibration(self):
        self.groupBox_Calibration.setEnabled(False)
        self.groupBox_Calibration.setTitle('')
        self.lbl_NewCorrFactor.setText('')
        self.lbl_NewSensitivity.setText('')
        # Set reference sound pressure
        self.inPressureRef.setCurrentText('%02d dB'%self.newParams['pCalib'])
        # Set reference frequency
        self.inFrequencyRef.setCurrentText('%d Hz'%self.newParams['fCalib'])
        # Set current correction factor
        self.val_CurrentCorrFactor.setText('%.2f dB'%self.newParams['corrFactor'])
        # Set current sensitivity
        self.val_CurrentSensitivity.setText('%.2f mV/Pa'%self.newParams['sensitivity'])
        self.inPressureRef.currentTextChanged.connect(self._setPressureRef)
        self.inFrequencyRef.currentIndexChanged.connect(self._setFrequencyRef)
        self.btnCalibrate.clicked.connect(self.btnCalibrate_Action)
        self.btnAccept.clicked.connect(self.btnAccept_Action)
        self.btnDecline.clicked.connect(self.btnDecline_Action)


    def _setTabSpectrumCorretion(self):
        self.groupBox_CompensationViewer.setEnabled(False)
        if self.currentParams['micCorrFile'] != None:
            _, file_name = os.path.split(self.currentParams['micCorrFile'])
            self.disp_CurrentMicFile.setText(file_name)
            if self.currentParams['applyMicCorr']:
                self.onMicCorr.setChecked(True)
            else:
                self.onMicCorr.setChecked(False)
        else:
            self.disp_CurrentMicFile.setText('No microphone calibration files defined')
            self.onMicCorr.setEnabled(False)
            self.onMicCorr.setChecked(False)
        if self.currentParams['adcCorrFile'] != None:
            _, file_name = os.path.split(self.currentParams['adcCorrFile'])
            self.disp_CurrentADCFile.setText(file_name)
            if self.currentParams['applyAdcCorr']:
                self.onADCCorr.setChecked(True)
            else:
                self.onADCCorr.setChecked(False)
        else:
            self.disp_CurrentADCFile.setText('No ADC calibration file defined')
            self.onADCCorr.setEnabled(False)
            self.onADCCorr.setChecked(False)
        if self.onMicCorr.isChecked():
            if self.plotMic == None:
                pen=pyqtgraph.mkPen(color=(120, 145, 255))
                self.plotMic = pyqtgraph.PlotDataItem(self.currentParams['micCorr'][:, 0],
                                        self.currentParams['micCorr'][:, 1],
                                        pen=pen, clear=True, name='Microphone response')
                self.compensationView.addItem(self.plotMic)
            else:
                self.compensationView.addItem(self.plotMic)
        else:
            if not self.plotMic is None:
                self.compensationView.removeItem(self.plotMic)
            else:
                pass
        if self.onADCCorr.isChecked():
            if self.plotADC == None:
                pen=pyqtgraph.mkPen(color=(222, 28, 74))
                self.plotADC = pyqtgraph.PlotDataItem(self.currentParams['adcCorr'][:, 0],
                                      self.currentParams['adcCorr'][:, 1],
                                      pen=pen, clear=True, name='ADC response')
                self.compensationView.addItem(self.plotADC)
            else:
                self.compensationView.addItem(self.plotADC)
        else:
            if not self.plotADC is None:
                self.compensationView.removeItem(self.plotADC)
            else:
                pass
        # Set connections
        self.btnLoadMicFile.clicked.connect(self._openMicFile)
        self.btnLoadADCFile.clicked.connect(self._openAdcFile)
        self.onMicCorr.clicked.connect(self._setOnMicCorr)
        self.onADCCorr.clicked.connect(self._setOnADCCorr)
        return

    def _openMicFile(self):
        try:
            file = str(QtWidgets.QFileDialog.getOpenFileName(self, "Select microphone calibration file", "", "*.txt"))
            if file == "('', '')":
                Exception
            else:
                pass
            if sys.platform == 'win32' or sys.platform == 'win64':
                file = file.replace('/', '\\')
            file = file[1:].replace(", '*.txt')", "").replace("'", "")
            _, file_name = os.path.split(file)
            # print("Path: {}\nFile: {}\n".format(folder, file_name))
            micData = np.loadtxt(fname=file)
            self.newParams['micCorrFile'] = file
            self.newParams['micCorr'] = micData
            self.onMicCorr.setEnabled(True)
            self.disp_CurrentMicFile.setText(file_name)
            if self.plotMic != None and self.onMicCorr.isChecked():
                self.compensationView.removeItem(self.plotMic)
                self.plotMic = None
                self._setPlotMicCompensation()
            elif self.plotMic != None:
                self.compensationView.removeItem(self.plotMic)
                self.plotMic = None
            self.changedParams()
        except:
            if self.plotMic == None:
                self.newParams['micCorrFile'] = None
                self.newParams['micCorr'] = None
                self.newParams['applyMicCorr'] = False
                self.onMicCorr.setEnabled(False)
                self.onMicCorr.setChecked(False)
                self.disp_CurrentMicFile.setText('No microphone calibration files defined')
            else:
                pass
        return

    def _openAdcFile(self):
        try:
            file = str(QtWidgets.QFileDialog.getOpenFileName(self, "Select ADC calibration file", "", "*.txt"))
            if file == "('', '')":
                Exception
            else:
                pass
            if sys.platform == 'win32' or sys.platform == 'win64':
                file = file.replace('/', '\\')
            file = file[1:].replace(", '*.txt')", "").replace("'", "")
            _, file_name = os.path.split(file)
            # print("Path: {}\nFile: {}\n".format(folder, file_name))
            micADC = np.loadtxt(fname=file)
            self.newParams['adcCorrFile'] = file
            self.newParams['adcCorr'] = micADC
            self.onADCCorr.setEnabled(True)
            self.disp_CurrentADCFile.setText(file_name)
            if self.plotADC != None and self.onADCCorr.isChecked():
                self.compensationView.removeItem(self.plotADC)
                self.plotADC = None
                self._setPlotADCCompensation()
            self.changedParams()
        except:
            if self.plotADC == None:
                self.newParams['adcCorrFile'] = None
                self.newParams['adcCorr'] = None
                self.newParams['applyAdcCorr'] = False
                self.onADCCorr.setEnabled(False)
                self.onADCCorr.setChecked(False)
                self.disp_CurrentADCFile.setText('No ADC calibration file defined')
            else:
                pass
        return

    def _setOnMicCorr(self):
        if self.onMicCorr.isChecked():
            self.newParams['applyMicCorr'] = True
        else:
            self.newParams['applyMicCorr'] = False
        self._setPlotMicCompensation()
        self.changedParams()
        return

    def _setOnADCCorr(self):
        if self.onADCCorr.isChecked():
            self.newParams['applyAdcCorr'] = True
        else:
            self.newParams['applyAdcCorr'] = False
        self._setPlotADCCompensation()
        self.changedParams()
        return

    def _setPlotMicCompensation(self):
        if self.onMicCorr.isChecked():
            if self.plotMic == None:
                pen=pyqtgraph.mkPen(color=(120, 145, 255))
                self.plotMic = pyqtgraph.PlotDataItem(self.newParams['micCorr'][:, 0],
                                        self.newParams['micCorr'][:, 1],
                                        pen=pen, clear=True, name='Microphone response')
                self.compensationView.addItem(self.plotMic)
            else:
                self.compensationView.addItem(self.plotMic)
        else:
            if not self.plotMic is None:
                self.compensationView.removeItem(self.plotMic)
            else:
                pass
        return
            
    def _setPlotADCCompensation(self):
        if self.onADCCorr.isChecked():
            if self.plotADC == None:
                pen=pyqtgraph.mkPen(color=(222, 28, 74))
                self.plotADC = pyqtgraph.PlotDataItem(self.newParams['adcCorr'][:, 0],
                                      self.newParams['adcCorr'][:, 1],
                                      pen=pen, clear=True, name='ADC response')
                self.compensationView.addItem(self.plotADC)
            else:
                self.compensationView.addItem(self.plotADC)
        else:
            if not self.plotADC is None:
                self.compensationView.removeItem(self.plotADC)
            else:
                pass
        return

    def _setTabDevice(self):
        self._listParamsTabDevice()
        self.listInDevices.currentIndexChanged.connect(self._setInputDevice)
        self.listOutDevices.currentIndexChanged.connect(self._setOutputDevice)
        self.inChannels.currentIndexChanged.connect(self._setInChannels)
        self.outChannels.currentTextChanged.connect(self._setOutChannels)
        self.listSampleRate.currentIndexChanged.connect(self._setSampleRate)
        return

    def _setInputDevice(self):
        self.inChannels.clear()
        self.listSampleRate.clear()
        # Query devices
        inputDevices, outputDevices, _ = self._setDevices()
        d = [inputDevices[self.listInDevices.currentIndex()]['id'],
             outputDevices[self.listOutDevices.currentIndex()]['id']]
        self.newParams['device'], self.newParams['fs'] = \
            self._checkParamsDevice(d, self.newParams['fs'])
        # List and set input channels
        for inCh in range(len(inputDevices[self.listInDevices.currentIndex()]['listCha'])):
            self.inChannels.addItem("")
            self.inChannels.setItemText(inCh, str(inCh+1))
        self.inChannels.setCurrentText(str(self.newParams['inCh'][0]))
        # List sample rate
        for fs in range(len(inputDevices[self.listInDevices.currentIndex()]['fs_list'])):
            self.listSampleRate.addItem("")
            self.listSampleRate.setItemText(fs, '%d Hz'%inputDevices[self.listInDevices.currentIndex()]['fs_list'][fs])
        # Set sample rate
        self.listSampleRate.setCurrentText('%d Hz'%self.newParams['fs'])
        self.changedParams()
        return

    def _setOutputDevice(self):
        self.outChannels.clear()
        # Query devices
        inputDevices, outputDevices, _ = self._setDevices()
        d = [inputDevices[self.listInDevices.currentIndex()]['id'],
             outputDevices[self.listOutDevices.currentIndex()]['id']]
        self.newParams['device'], self.newParams['fs'] = \
            self._checkParamsDevice(d, self.newParams['fs'])
        # List and set output channels
        for outCh in range(len(outputDevices[self.listOutDevices.currentIndex()]['listCha'])):
            self.outChannels.addItem("")
            self.outChannels.setItemText(outCh, str(outCh+1))
            if outCh+1 in self.newParams['outCh']:
                self.outChannels.setItemChecked(outCh, True)
            else:
                self.outChannels.setItemChecked(outCh, False)
        self.changedParams()
        return

    def _setInChannels(self):
        if self.inChannels.count() > 0:
            self.newParams['inCh'] = [self.inChannels.currentIndex()+1]
            self.changedParams()
        else:
            pass
        return

    def _setOutChannels(self):
        if self.outChannels.count() > 0:
            outChannels = []
            for outCha in range(self.outChannels.count()):
                if self.outChannels.itemChecked(outCha):
                    outChannels.append(outCha+1)
            if len(outChannels) > 0:
                self.outChannels.setCurrentText(str(outChannels[-1]))
            self.newParams['outCh'] = outChannels
            self.changedParams()
        else:
            pass
        return

    def _setSampleRate(self):
        if self.listSampleRate.count() > 0:
            if self.listSampleRate.currentText() != '':
                self.newParams['fs'] = int(self.listSampleRate.currentText().replace(' Hz', ''))
            self.changedParams()
        else:
            pass
        return

    def _setPressureRef(self):
        self.newParams['pCalib'] = int(self.inPressureRef.currentText().replace(' dB', ''))
        self.changedParams()
        return

    def _setFrequencyRef(self):
        self.newParams['fCalib'] = int(self.inFrequencyRef.currentText().replace(' Hz', ''))
        self.changedParams()
        return
    
    def _setBottomFreq(self):
        if self.inBottomFreq.count() > 0:
            self.newParams['fstart'] = self._str2numFreq[self.inBottomFreq.currentText()]
            self.changedParams()
        else:
            pass
        return
    
    def _setTopFreq(self):
        if self.inTopFreq.count() > 0:
            self.newParams['fend'] = self._str2numFreq[self.inTopFreq.currentText()]
            self.changedParams()
        else:
            pass
        return

    def _setDuration(self):
        hour = int(self.inHour.currentText().replace('h', ''))
        minute = int(self.inMin.currentText().replace('m', ''))
        second = int(self.inSec.currentText().replace('s', ''))
        duration = 3600*hour + 60*minute + second
        if duration < 15:
            duration = 15
            self.inSec.setCurrentText('15s')
        else:
            pass
        self.newParams['duration'] = duration
        self.changedParams()
        return

    def _setExcitTime(self):
        minute = int(self.inMinExcit.currentText().replace('m', ''))
        second = int(self.inSecExcit.currentText().replace('s', ''))
        durationExcit = 60*minute + second
        self.newParams['excitTime'] = durationExcit
        self.changedParams()
        return

    def _setEscapeTime(self):
        minute = int(self.inMinScape.currentText().replace('m', ''))
        second = int(self.inSecScape.currentText().replace('s', ''))
        scapeTime = 60*minute + second
        self.newParams['scapeTime'] = scapeTime
        self.changedParams()
        return

    def _setSecDecay(self):
        decayTime = int(self.inSecScape.currentText().replace('s', ''))
        self.newParams['decayTime'] = decayTime
        self.changedParams()
        return

    def _setNumDecay(self):
        self.newParams['numDecay'] = int(self.inNumDecays.currentText())
        self.changedParams()
        return

    def _setTriggerLevel(self):
        self.newParams['TLevel'] = int(self.inTriggerLevel.currentText().replace(' dB', ''))
        self.changedParams()
        return

    def _setFreqWeighting(self):
        self.newParams['fweighting'] = self.inFreqWeighting.currentText()
        self.changedParams()
        return
    
    def _setTimeWeighting(self):
        TimeWeighting = {'Impulse': 0.035, 'Fast': 0.125, 'Slow': 1.0}
        self.newParams['tau'] = TimeWeighting[self.inTimeWeighting.currentText()]
        self.changedParams()
        return

    def _setMethod(self):
        methods = {'Exponential sweep': 'sweepExponential',
                   'White noise': 'whiteNoise',
                   'Pink noise': 'pinkNoise',
                   'Impulse': 'impulse'}
        if self.inMethod.currentIndex() == 3:
            self.inTriggerLevel.setEnabled(True)
            self.inMinExcit.setEnabled(False)
            self.inSecExcit.setEnabled(False)
            self.inMinScape.setEnabled(False)
            self.inSecScape.setEnabled(False)
            self.inNumDecays.setEnabled(False)
        else:
            self.inTriggerLevel.setEnabled(False)
            self.inMinExcit.setEnabled(True)
            self.inSecExcit.setEnabled(True)
            self.inMinScape.setEnabled(True)
            self.inSecScape.setEnabled(True)
            self.inNumDecays.setEnabled(True)
        self.newParams['method'] = methods[self.inMethod.currentText()]
        self.changedParams()
        return

    def changedParams(self):
        changes = []
        for key in self.newParams.keys():
            if not type(self.newParams[key]) is np.ndarray:
                if self.newParams[key] == self.currentParams[key]:
                    changes.append(True)
                else:
                    changes.append(False)
            elif type(self.newParams[key]) == np.ndarray:
                if np.array_equal(a1=self.newParams[key], a2=self.currentParams[key]):
                    changes.append(True)
                else:
                    changes.append(False)
            else:
                pass

        if not False in changes:
            self.btnApply.setEnabled(False)
            self.btnApply.setText('Apply')
            self.btnRestore.setEnabled(False)
        else:
            self.btnApply.setEnabled(True)
            self.btnApply.setText('Apply*')
            self.btnRestore.setEnabled(True)
        return

    def btnCalibrate_Action(self):
        self.btnCalibrate.setEnabled(False)
        self.btnAccept.setEnabled(False)
        self.btnDecline.setEnabled(False)
        self.groupBox_Calibration.setEnabled(True)
        self.plotCalib = pyqtgraph.PlotCurveItem()
        self.CalibrationView.addItem(self.plotCalib)
        self.stream_calibration = pyslm.StreamManager(path = os.path.join(self.currentParams['pathProject'], self.currentParams['currentProject']),
                                            device=self.currentParams['device'],
                                            fs=self.currentParams['fs'],
                                            inCh=self.currentParams['inCh'],
                                            outCh=self.currentParams['outCh'],
                                            tau=1.0,
                                            fstart=self.currentParams['fstart'],
                                            fend=self.currentParams['fend'],
                                            b=self.currentParams['b'],
                                            fweighting=self.currentParams['fweighting'],
                                            duration=10,
                                            excitTime=self.currentParams['excitTime'],
                                            scapeTime=self.currentParams['scapeTime'],
                                            decayTime=self.currentParams['decayTime'],
                                            template='calibration',
                                            method=self.currentParams['method'],
                                            numDecay=self.currentParams['numDecay'],
                                            TLevel = self.currentParams['TLevel'],
                                            fCalib=self.currentParams['fCalib'],
                                            pCalib=self.currentParams['pCalib'],
                                            calibFactor=self.currentParams['calibFactor'],
                                            corrMic=self.currentParams['micCorr'],
                                            applyMicCorr=self.currentParams['applyMicCorr'],
                                            corrADC=self.currentParams['adcCorr'],
                                            applyAdcCorr=self.currentParams['applyAdcCorr'],
                                            saveRawData=self.currentParams['saveRawData'])
        self.stream_calibration.play()
        self.stream_calibration.realtime_data.connect(self.updateCalibrate)
        self.stream_calibration.fullresults_data.connect(self.fullCalibrate)
        return

    @QtCore.Slot(dict)
    def updateCalibrate(self, results):
        SPL = results['SPL'][1:]
        with np.errstate(divide='ignore'):
            freqVector = np.log10(results['freqVector'][1:])
        framesRead = self.stream_calibration.framesRead
        countdown = int(self.stream_calibration.duration - framesRead/self.stream_calibration.fs)
        if countdown > 0:
            self.groupBox_Calibration.setTitle('Performing calibration, please wait %02ds'%countdown)
            if freqVector.size == SPL.size:
                self.plotCalib.setData(x=freqVector, y=SPL, pen=pyqtgraph.mkPen(color=(120, 145, 255)))
            else:
                pass
        else:
            pass
        return

    @QtCore.Slot(dict)
    def fullCalibrate(self, results):
        self.groupBox_Calibration.setTitle('Performing calibration, please wait 00s')
        SPL = results['SPL']
        with np.errstate(divide='ignore'):
                freqVector = np.log10(results['freqVector'][1:])
        self.sensitivity = results['sensitivity']
        self.correction = results['correction']
        self.FC = results['FC']
        if freqVector.size == SPL.size:
            self.plotCalib.setData(freqVector, SPL)
        else:
            pass
        self.lbl_NewCorrFactor.setText('New correction factor: %.02f dB'%self.correction)
        self.lbl_NewSensitivity.setText('New sensitivity: %.02f mV/Pa'%self.sensitivity)
        self.btnAccept.setEnabled(True)
        self.btnDecline.setEnabled(True)

    def btnAccept_Action(self):
        self.currentParams['corrFactor'] = self.correction
        self.currentParams['sensitivity'] = self.sensitivity
        self.currentParams['calibFactor'] = self.FC
        self.newParams['corrFactor'] = self.correction
        self.newParams['sensitivity'] = self.sensitivity
        self.newParams['calibFactor'] = self.FC
        self.val_CurrentCorrFactor.setText('%.2f dB'%self.newParams['corrFactor'])
        self.val_CurrentSensitivity.setText('%.2f mV/Pa'%self.newParams['sensitivity'])
        pyslm.parameters.update(self.currentParams)
        self.changedParams()
        self.groupBox_Calibration.setEnabled(False)
        self.groupBox_Calibration.setTitle('')
        self.lbl_NewCorrFactor.setText('')
        self.lbl_NewSensitivity.setText('')
        self.btnDecline.setEnabled(False)
        self.btnAccept.setEnabled(False)
        self.btnCalibrate.setEnabled(True)
        self.CalibrationView.removeItem(self.plotCalib)
        return

    def btnDecline_Action(self):
        self.changedParams()
        self.groupBox_Calibration.setEnabled(False)
        self.groupBox_Calibration.setTitle('')
        self.lbl_NewCorrFactor.setText('')
        self.lbl_NewSensitivity.setText('')
        self.btnDecline.setEnabled(False)
        self.btnAccept.setEnabled(False)
        self.btnCalibrate.setEnabled(True)
        self.CalibrationView.removeItem(self.plotCalib)
        return

    def btnClose_Action(self):
        # os.chdir(path_main)
        self.close()
        return

    def btnApply_Action(self):
        self.currentParams = self.newParams.copy()
        self.changedParams()
        pyslm.parameters.update(self.currentParams)
        return
    
    def btnRestore_Action(self):
        self.restore = True
        self._restore()
        self.restore = False
        return

    def findFrequency(self, freq):
        if self.newParams['b'] == 1:
            if self.newParams['template'] == 'frequencyAnalyzer':
                vecfrequency = [31.5, 63.0, 125.0, 250.0, 4000.0, 8000.0, 16000.0]
            else:
                vecfrequency = [63.0, 125.0, 250.0, 4000.0, 8000.0]
            frequency = np.asarray(vecfrequency)
        else:
            if self.newParams['template'] == 'frequencyAnalyzer':
                vecfrequency = self._listNumFreq
            else:
                vecfrequency = self._listNumFreq[4:17]
            frequency = np.asarray(vecfrequency)
        dist = np.sqrt((frequency - freq)**2)
        return vecfrequency[np.argmin(dist)]

    def seconds2HMN(self, seconds): 
        M, S = divmod(seconds, 60) 
        H, M = divmod(M, 60)
        # return "%02d:%02d:%02d" % (H, M, S) 
        return '%02dh'%H, '%02dm'%M, '%02ds'%S

    def _setfrequencyLimits(self):
        self.inBottomFreq.clear()
        self.inTopFreq.clear()
        if self.inTemplate.currentIndex() == 0:
            self.newParams['template'] = 'frequencyAnalyzer'
            self.inHour.setEnabled(True)
            self.inMin.setEnabled(True)
            self.inSec.setEnabled(True)
            self.inFreqWeighting.setEnabled(True)
            self.inTimeWeighting.setEnabled(True)
            self.groupBox_ExcitSignal.setEnabled(False)
            minoctband_third = ['20 Hz', '25 Hz', '31.5 Hz', '40 Hz', '50 Hz', '63 Hz',
                                '80 Hz', '100 Hz', '125 Hz', '160 Hz', '200 Hz', '250 Hz']
            maxoctband_third = ['4 kHz', '5 kHz', '6.3 kHz', '8 kHz', '10 kHz', '16 kHz', '20 kHz']
            minoctband_one = ['31.5 Hz', '63 Hz', '125 Hz', '250 Hz']
            maxoctband_one = ['4 kHz', '8 kHz', '16 kHz']
        else:
            self.newParams['template'] = 'reverberationTime'
            self.inHour.setEnabled(False)
            self.inMin.setEnabled(False)
            self.inSec.setEnabled(False)
            self.inFreqWeighting.setEnabled(False)
            self.inTimeWeighting.setEnabled(False)
            self.inFreqWeighting.setCurrentIndex(2)
            self.groupBox_ExcitSignal.setEnabled(True)
            minoctband_third = ['50 Hz', '63 Hz', '80 Hz', '100 Hz', '125 Hz', '160 Hz', '200 Hz', '250 Hz']
            maxoctband_third = ['4 kHz', '5 kHz', '6.3 kHz', '8 kHz', '10 kHz']
            minoctband_one = ['63 Hz', '125 Hz', '250 Hz']
            maxoctband_one = ['4 kHz', '8 kHz']

        if self.inBandwidth.currentIndex() == 0:
            self.newParams['b'] = 1
            self.inBottomFreq.addItems(minoctband_one)
            self.inTopFreq.addItems(maxoctband_one)
        else:
            self.newParams['b'] = 3
            self.inBottomFreq.addItems(minoctband_third)
            self.inTopFreq.addItems(maxoctband_third)
        if self.restore:
            self.newParams = self.currentParams.copy()
        # Set current bottom frequency
        bottomFreq = self.findFrequency(freq=self.currentParams['fstart'])
        self.inBottomFreq.setCurrentText(self._num2strFreq[bottomFreq])
        # Set current top frequency
        topFreq = self.findFrequency(freq=self.currentParams['fend'])
        self.inTopFreq.setCurrentText(self._num2strFreq[topFreq])
        self.changedParams()
        return

    def _listParamsTabMeasurement(self):
        # Set items Hours
        for h in range(24):
            self.inHour.addItem("")
            self.inHour.setItemText(h, '%02dh'%h)
        # Set items Minutes
        for m in range(60):
            self.inMin.addItem("")
            self.inMin.setItemText(m, '%02dm'%m)
            if m < 6:
                self.inMinExcit.addItem("")
                self.inMinExcit.setItemText(m, '%02dm'%m)
                self.inMinScape.addItem("")
                self.inMinScape.setItemText(m, '%02dm'%m)
        # Set items Seconds
        for s in range(60):
            self.inSec.addItem("")
            self.inSec.setItemText(s, '%02ds'%s)
            if s > 4:
                self.inSecExcit.addItem("")
                self.inSecExcit.setItemText(s-5, '%02ds'%s)
            self.inSecScape.addItem("")
            self.inSecScape.setItemText(s, '%02ds'%s)
        # Set items time decay
        for d in range(21):
            if d > 2:
                self.inSecDecay.addItem("")
                self.inSecDecay.setItemText(d-3, '%02ds'%d)
        # Set items number of decays
        for nd in range(101):
            if nd > 0:
                self.inNumDecays.addItem("")
                self.inNumDecays.setItemText(nd-1, '%02d'%nd)
        # Set items trigger leves
        for t in range(101):
            if t > 39:
                self.inTriggerLevel.addItem("")
                self.inTriggerLevel.setItemText(t-40, '%02d dB'%t)
        return

    def _listParamsTabDevice(self):
        # Query devices
        inputDevices, outputDevices, _ = self._setDevices()
        sd_devices = sd.query_devices()
        self.newParams['device'], self.newParams['fs'] = \
            self._checkParamsDevice(self.newParams['device'], self.newParams['fs'])
        # List input devices
        for dev in range(len(inputDevices)):
            self.listInDevices.addItem("")
            self.listInDevices.setItemText(dev, inputDevices[dev]['name'])
        # Set input device
        self.listInDevices.setCurrentText(sd_devices[self.newParams['device'][0]]['name'])
        # List and set input channels
        for inCh in range(len(inputDevices[self.listInDevices.currentIndex()]['listCha'])):
            self.inChannels.addItem("")
            self.inChannels.setItemText(inCh, str(inCh+1))
        self.inChannels.setCurrentText(str(self.newParams['inCh'][0]))
        # List output devices
        for dev in range(len(outputDevices)):
            self.listOutDevices.addItem("")
            self.listOutDevices.setItemText(dev, outputDevices[dev]['name'])
        # Set output device
        self.listOutDevices.setCurrentText(sd_devices[self.newParams['device'][1]]['name'])
        # List and set output channels
        for outCh in range(len(outputDevices[self.listOutDevices.currentIndex()]['listCha'])):
            self.outChannels.addItem("")
            self.outChannels.setItemText(outCh, str(outCh+1))
            if outCh+1 in self.newParams['outCh']:
                self.outChannels.setItemChecked(outCh, True)
            else:
                self.outChannels.setItemChecked(outCh, False)
        # List sample rate
        for fs in range(len(inputDevices[self.listInDevices.currentIndex()]['fs_list'])):
            self.listSampleRate.addItem("")
            self.listSampleRate.setItemText(fs, '%d Hz'%inputDevices[self.listInDevices.currentIndex()]['fs_list'][fs])
        # Set sample rate
        self.listSampleRate.setCurrentText('%d Hz'%self.newParams['fs'])
        return

    def _checkParamsDevice(self, device, fs):
        # Check input parameters
        inputDevice = device[0]
        outputDevice = device[1]
        try:
            sd.check_input_settings(device=inputDevice, samplerate=fs)
        except:
            sd_devices = sd.query_devices()
            inputDevice = sd.default.device[0]
            fs = int(sd_devices[sd.default.device[0]]['default_samplerate'])
        else:
            pass
        # Check output parameters
        try:
            sd.check_output_settings(device=outputDevice, samplerate=fs)
        except:
            sd_devices = sd.query_devices()
            outputDevice = sd.default.device[1]
        else:
            pass
        return [inputDevice, outputDevice], fs


    def _setDevices(self):
        sd_devices = sd.query_devices()
        def supportedFs(device, kind):
            samplerates = [44100, 48000, 96000, 128000]
            supported_samplerates = []
            for fs in samplerates:
                try:
                    if kind == 'in':
                        sd.check_input_settings(device=device, samplerate=fs)
                    else:
                        sd.check_output_settings(device=device, samplerate=fs)
                except:
                    pass
                else:
                    supported_samplerates.append(fs)
            return supported_samplerates

        def supportedCha(device, kind, numCha):
            supported_channels = []
            for ch in range(numCha+1):
                try:
                    if kind == 'in':
                        sd.check_input_settings(device=device, channels=ch)
                    else:
                        sd.check_output_settings(device=device, channels=ch)
                except:
                    pass
                else:
                    supported_channels.append(ch)
            return supported_channels
        inputDevices = []
        outputDevices = []
        for dev in range(len(sd_devices)):
            if sd_devices[dev]['max_input_channels'] > 0:
                listFs = supportedFs(dev, 'in')
                listCha = supportedCha(dev, 'in', sd_devices[dev]['max_input_channels'])
                inputDevices.append({'name': sd_devices[dev]['name'],
                                    'numCha': sd_devices[dev]['max_input_channels'],
                                    'id': dev,
                                    'fs_default': sd_devices[dev]['default_samplerate'],
                                    'fs_list': listFs,
                                    'listCha': listCha})
            if sd_devices[dev]['max_output_channels'] > 0:
                listFs = supportedFs(dev, 'out')
                listCha = supportedCha(dev, 'out', sd_devices[dev]['max_output_channels'])
                outputDevices.append({'name': sd_devices[dev]['name'],
                                    'numCha': sd_devices[dev]['max_output_channels'],
                                    'id': dev,
                                    'fs_default': sd_devices[dev]['default_samplerate'],
                                    'fs_list': listFs,
                                    'listCha': listCha})
        defaultDevices = {}
        for dev in range(len(inputDevices)):
            if inputDevices[dev]['id'] == sd.default.device[0]:
                defaultDevices['in'] = inputDevices[dev]
        for dev in range(len(outputDevices)):
            if outputDevices[dev]['id'] == sd.default.device[1]:
                defaultDevices['out'] = outputDevices[dev]
        return inputDevices, outputDevices, defaultDevices

    def _setTabProjects(self):
        if not os.path.isdir(self.newParams['pathProject']):
            if os.path.isdir(os.path.expanduser("~/Desktop")):
                self.newParams['pathProject'] = os.path.expanduser("~/Desktop")
            else:
                self.newParams['pathProject'] = os.getcwd()
        self.disp_ProjectsFolder.setText(self.newParams['pathProject'])
        self.disp_CurrentProject.setText(self.newParams['currentProject'])
        os.chdir(self.newParams['pathProject'])
        self.allProjects = os.listdir(".")
        if self.newParams['saveRawData']:
            self.onSaveData.setChecked(True)
        else:
            self.onSaveData.setChecked(False)
        self.onSaveData.toggled.connect(self._setSaveData)
        self.btnChangeProject.clicked.connect(self._setPathProject)
        self.btnCreate.setEnabled(False)
        self.minStr = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p",\
                        "a", "s", "d", "f", "g", "h", "j", "k", "l", "ç",\
                        "z", "x", "c", "v", "b", "n", "m"]
        self.maiStr = list(map(str.upper, self.minStr))
        self.upper = False
        self.vk_a.clicked.connect(self.vk_aAction)
        self.vk_b.clicked.connect(self.vk_bAction)
        self.vk_c.clicked.connect(self.vk_cAction)
        self.vk_d.clicked.connect(self.vk_dAction)
        self.vk_e.clicked.connect(self.vk_eAction)
        self.vk_f.clicked.connect(self.vk_fAction)
        self.vk_g.clicked.connect(self.vk_gAction)
        self.vk_h.clicked.connect(self.vk_hAction)
        self.vk_i.clicked.connect(self.vk_iAction)
        self.vk_j.clicked.connect(self.vk_jAction)
        self.vk_k.clicked.connect(self.vk_kAction)
        self.vk_l.clicked.connect(self.vk_lAction)
        self.vk_m.clicked.connect(self.vk_mAction)
        self.vk_n.clicked.connect(self.vk_nAction)
        self.vk_o.clicked.connect(self.vk_oAction)
        self.vk_p.clicked.connect(self.vk_pAction)
        self.vk_q.clicked.connect(self.vk_qAction)
        self.vk_r.clicked.connect(self.vk_rAction)
        self.vk_s.clicked.connect(self.vk_sAction)
        self.vk_t.clicked.connect(self.vk_tAction)
        self.vk_u.clicked.connect(self.vk_uAction)
        self.vk_v.clicked.connect(self.vk_vAction)
        self.vk_w.clicked.connect(self.vk_wAction)
        self.vk_x.clicked.connect(self.vk_xAction)
        self.vk_y.clicked.connect(self.vk_yAction)
        self.vk_z.clicked.connect(self.vk_zAction)
        self.vk_0.clicked.connect(self.vk_0Action)
        self.vk_1.clicked.connect(self.vk_1Action)
        self.vk_2.clicked.connect(self.vk_2Action)
        self.vk_3.clicked.connect(self.vk_3Action)
        self.vk_4.clicked.connect(self.vk_4Action)
        self.vk_5.clicked.connect(self.vk_5Action)
        self.vk_6.clicked.connect(self.vk_6Action)
        self.vk_7.clicked.connect(self.vk_7Action)
        self.vk_8.clicked.connect(self.vk_8Action)
        self.vk_9.clicked.connect(self.vk_9Action)
        self.vk_underscore.clicked.connect(self.vk_underscoreAction)
        self.delAll.clicked.connect(self.delAllAction)
        self.capsLock.clicked.connect(self.btncapsLock)
        self.space.clicked.connect(self.spaceAction)
        self.backspace.clicked.connect(self.backspaceAction)
        self.btnCancel.clicked.connect(self.btnCancel_Action)
        self.btnCreate.clicked.connect(self.btnCreate_Action)
        self.changedParams()
        return

    def btnCancel_Action(self):
        self.delAllAction()
        return

    def btnCreate_Action(self):
        if not os.path.isdir(os.path.join(self.newParams['pathProject'], self.entryProjectname.toPlainText())):
            self.newParams['currentProject'] = self.entryProjectname.toPlainText()
            os.mkdir(os.path.join(self.newParams['pathProject'], self.entryProjectname.toPlainText()))
        else:
            pass
        self.disp_ProjectsFolder.setText(self.newParams['pathProject'])
        self.disp_CurrentProject.setText(self.newParams['currentProject'])
        self.delAllAction()
        return
        
    def _checkVirtualKeyboard(self):
        if self.entryProjectname.toPlainText() == "":
            self.btnCreate.setEnabled(False)
        elif self.entryProjectname.toPlainText() in self.allProjects:
            self.btnCreate.setEnabled(False)
        else:
            self.btnCreate.setEnabled(True)
        return
            
    def btncapsLock(self):
        self.upper = not self.upper
        if self.upper:
            self.vk_q.setText(self.maiStr[0])
            self.vk_w.setText(self.maiStr[1])
            self.vk_e.setText(self.maiStr[2])
            self.vk_r.setText(self.maiStr[3])
            self.vk_t.setText(self.maiStr[4])
            self.vk_y.setText(self.maiStr[5])
            self.vk_u.setText(self.maiStr[6])
            self.vk_i.setText(self.maiStr[7])
            self.vk_o.setText(self.maiStr[8])
            self.vk_p.setText(self.maiStr[9])
            self.vk_a.setText(self.maiStr[10])
            self.vk_s.setText(self.maiStr[11])
            self.vk_d.setText(self.maiStr[12])
            self.vk_f.setText(self.maiStr[13])
            self.vk_g.setText(self.maiStr[14])
            self.vk_h.setText(self.maiStr[15])
            self.vk_j.setText(self.maiStr[16])
            self.vk_k.setText(self.maiStr[17])
            self.vk_l.setText(self.maiStr[18])
            self.vk_z.setText(self.maiStr[20])
            self.vk_x.setText(self.maiStr[21])
            self.vk_c.setText(self.maiStr[22])
            self.vk_v.setText(self.maiStr[23])
            self.vk_b.setText(self.maiStr[24])
            self.vk_n.setText(self.maiStr[25])
            self.vk_m.setText(self.maiStr[26])
        else:
            self.vk_q.setText(self.minStr[0])
            self.vk_w.setText(self.minStr[1])
            self.vk_e.setText(self.minStr[2])
            self.vk_r.setText(self.minStr[3])
            self.vk_t.setText(self.minStr[4])
            self.vk_y.setText(self.minStr[5])
            self.vk_u.setText(self.minStr[6])
            self.vk_i.setText(self.minStr[7])
            self.vk_o.setText(self.minStr[8])
            self.vk_p.setText(self.minStr[9])
            self.vk_a.setText(self.minStr[10])
            self.vk_s.setText(self.minStr[11])
            self.vk_d.setText(self.minStr[12])
            self.vk_f.setText(self.minStr[13])
            self.vk_g.setText(self.minStr[14])
            self.vk_h.setText(self.minStr[15])
            self.vk_j.setText(self.minStr[16])
            self.vk_k.setText(self.minStr[17])
            self.vk_l.setText(self.minStr[18])
            self.vk_z.setText(self.minStr[20])
            self.vk_x.setText(self.minStr[21])
            self.vk_c.setText(self.minStr[22])
            self.vk_v.setText(self.minStr[23])
            self.vk_b.setText(self.minStr[24])
            self.vk_n.setText(self.minStr[25])
            self.vk_m.setText(self.minStr[26])
        self._checkVirtualKeyboard()
        return

    def vk_aAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_a.text())
        self._checkVirtualKeyboard()
        return

    def vk_bAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_b.text())
        self._checkVirtualKeyboard()
        return

    def vk_cAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_c.text())
        self._checkVirtualKeyboard()
        return

    def vk_dAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_d.text())
        self._checkVirtualKeyboard()
        return

    def vk_eAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_e.text())
        self._checkVirtualKeyboard()
        return

    def vk_fAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_f.text())
        self._checkVirtualKeyboard()
        return

    def vk_gAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_g.text())
        self._checkVirtualKeyboard()
        return

    def vk_hAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_h.text())
        self._checkVirtualKeyboard()
        return

    def vk_iAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_i.text())
        self._checkVirtualKeyboard()
        return

    def vk_jAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_j.text())
        self._checkVirtualKeyboard()
        return

    def vk_kAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_k.text())
        self._checkVirtualKeyboard()
        return

    def vk_lAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_l.text())
        self._checkVirtualKeyboard()
        return

    def vk_mAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_m.text())
        self._checkVirtualKeyboard()
        return

    def vk_nAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_n.text())
        self._checkVirtualKeyboard()
        return

    def vk_oAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_o.text())
        self._checkVirtualKeyboard()
        return

    def vk_pAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_p.text())
        self._checkVirtualKeyboard()
        return

    def vk_qAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_q.text())
        self._checkVirtualKeyboard()
        return

    def vk_rAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_r.text())
        self._checkVirtualKeyboard()
        return

    def vk_sAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_s.text())
        self._checkVirtualKeyboard()
        return

    def vk_tAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_t.text())
        self._checkVirtualKeyboard()
        return

    def vk_uAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_u.text())
        self._checkVirtualKeyboard()
        return

    def vk_vAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_v.text())
        self._checkVirtualKeyboard()
        return

    def vk_wAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_w.text())
        self._checkVirtualKeyboard()
        return

    def vk_xAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_x.text())
        self._checkVirtualKeyboard()
        return

    def vk_yAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_y.text())
        self._checkVirtualKeyboard()
        return

    def vk_zAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_z.text())
        self._checkVirtualKeyboard()
        return

    def spaceAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + ' ')
        self._checkVirtualKeyboard()
        return

    def backspaceAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText()[:-1])
        self._checkVirtualKeyboard()
        return

    def vk_0Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_0.text())
        self._checkVirtualKeyboard()
        return

    def vk_1Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_1.text())
        self._checkVirtualKeyboard()
        return

    def vk_2Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_2.text())
        self._checkVirtualKeyboard()
        return

    def vk_3Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_3.text())
        self._checkVirtualKeyboard()
        return

    def vk_4Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_4.text())
        self._checkVirtualKeyboard()
        return

    def vk_5Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_5.text())
        self._checkVirtualKeyboard()
        return

    def vk_6Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_6.text())
        self._checkVirtualKeyboard()
        return

    def vk_7Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_7.text())
        self._checkVirtualKeyboard()
        return

    def vk_8Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_8.text())
        self._checkVirtualKeyboard()
        return

    def vk_9Action(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + self.vk_9.text())
        self._checkVirtualKeyboard()
        return

    def vk_underscoreAction(self):
        self.entryProjectname.setText(self.entryProjectname.toPlainText() + '_')
        self._checkVirtualKeyboard()
        return

    def delAllAction(self):
        self.entryProjectname.setText('')
        self._checkVirtualKeyboard()
        return

    def _setPathProject(self):
        if os.path.isdir(self.newParams['pathProject']):
            pathDefault = self.newParams['pathProject']
        elif os.path.isdir(os.path.expanduser("~/Desktop")):
            pathDefault = os.path.expanduser("~/Desktop")
        else:
            pathDefault = os.getcwd()
        path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", pathDefault))
        if sys.platform == 'win32' or sys.platform == 'win64':
                path = path.replace('/', '\\')
        projectFolder, currentProject = os.path.split(path)
        self.newParams['pathProject'] = projectFolder
        self.newParams['currentProject'] = currentProject
        self.disp_ProjectsFolder.setText(projectFolder)
        self.disp_CurrentProject.setText(currentProject)
        self.changedParams()
        return

    def _setSaveData(self):
        if self.onSaveData.isChecked():
            self.newParams['saveRawData'] = True
        else:
            self.newParams['saveRawData'] = False
        self.changedParams()
        return



#%%
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dlgSetup = setSetup()
    # dlgSetup.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
    # dlgSetup.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
    dlgSetup.exec_()
    app.exec_()
    app.quit()