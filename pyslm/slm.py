from PyQt5 import QtCore, QtGui, QtWidgets
from typing import Callable, Tuple
import threading as thd
import numpy as np
import platform
import datetime
import pyslm
import time
import sys
import os


path_icons = os.path.join(os.path.dirname(os.path.realpath(pyslm.__file__)), 'Icons')

if sys.platform == 'win32' or sys.platform == 'win64':
    import ctypes
    myappid = u'PySLM.version.0.2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
else:
    pass

class setSLM(QtWidgets.QMainWindow, pyslm.guiSLM):
    def __init__(self, parent=None):
        super(setSLM, self).__init__(parent)
        self.setupUi(self)
        self.btnNewproject.clicked.connect(self.btnNewproject_Action)
        self.btnSetup.clicked.connect(self.btnSetup_Action)
        self.btnCalibrate.clicked.connect(self.btnCalibrate_Action)
        self.btnInfo.clicked.connect(self.btnInfo_Action)
        self.btnQuit.clicked.connect(self.btnQuit_Action)
        self.btnPlay.clicked.connect(self.btnPlay_Action)
        self.btnStop.clicked.connect(self.btnStop_Action)
        self.btnDelete.clicked.connect(self.btnDelete_Action)
        self.btnSave.clicked.connect(self.btnSave_Action)
        self.parameters = pyslm.parameters.load()
        self.parameters['version'] = 'AdvFreqAnalyzer'
        pyslm.parameters.update(self.parameters)
        self.parameters = pyslm.parameters.load()
        self.timeStamp = {}
        self.set_standby()
        self.isOpenWindow = True
        self.gettingDataTime = thd.Thread(target=self.datatime)
        self.gettingDataTime.start()
        self._setStringsGUI()
        self.show()
        
    def set_standby(self) -> Callable:
        try:
            self.btnPlay.setEnabled(True)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play.ico")))
            self.btnStop.setEnabled(False)
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_noclick.ico")))
            self.btnNewproject.setEnabled(True)
            self.btnNewproject.setIcon(QtGui.QIcon(os.path.join(path_icons, "NewProject.ico")))
            self.btnSetup.setEnabled(True)
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup.ico")))
            self.btnCalibrate.setEnabled(True)
            self.btnCalibrate.setIcon(QtGui.QIcon(os.path.join(path_icons, "Calibrate.ico")))
            self.btnInfo.setEnabled(True)
            self.btnInfo.setIcon(QtGui.QIcon(os.path.join(path_icons, "info.ico")))
            self.btnSave.setEnabled(False)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_noclick.ico")))
            self.btnDelete.setEnabled(False)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_noclick.ico")))
            self.manager = pyslm.StreamManager(
                version = 'AdvFreqAnalyzer',
                path = os.path.join(
                    self.parameters['pathProject'],
                    self.parameters['currentProject']
                    ),
                device = self.parameters['device'],
                fs = self.parameters['fs'],
                inCh = self.parameters['inCh'],
                outCh = self.parameters['outCh'],
                tau = self.parameters['tau'],
                fstart = self.parameters['fstart'],
                fend = self.parameters['fend'],
                b = self.parameters['b'],
                fweighting = self.parameters['fweighting'],
                duration = self.parameters['duration'],
                excitTime = self.parameters['excitTime'],
                scapeTime = self.parameters['scapeTime'],
                decayTime = self.parameters['decayTime'],
                template = 'stand-by',
                method = self.parameters['method'],
                numDecay = self.parameters['numDecay'],
                TLevel  =  self.parameters['TLevel'],
                fCalib = self.parameters['fCalib'],
                pCalib = self.parameters['pCalib'],
                calibFactor = self.parameters['calibFactor'],
                micCorr = self.parameters['micCorr'],
                applyMicCorr = False,
                adcCorr = self.parameters['adcCorr'],
                applyAdcCorr = False,
                saveRawData = False
                )
            self.manager.play()
            self.manager.realtime_data.connect(self.update_standby)
            self.ax = self.measurementViewer.getAxis('bottom')
        except Exception as E:
            print("setSLM.set_standby(): ", E, "\n")
        return

    @QtCore.pyqtSlot(dict)
    def update_standby(self, results: dict) -> Callable:
        try:
            Lp_global = results['Lp_global']
            Lp_bands = results['Lp_bands']
            strBands = results['strBands']
            x_axis = results['x_axis']
            self.ax.setTicks([strBands])
            self.value_Leq.setText(str(Lp_global))
            self.plotBar.setOpts(
                x = x_axis,
                height = Lp_bands,
                width = 0.6,
                brush = (120, 145, 255)
                )
        except Exception as E:
            print("setSLM.update_standby(): ", E, "\n")
        return


    def stop_strem(self) -> Callable:
        try:
            self.manager.stop()
        except Exception as E:
            print("setSLM.stop_strem(): ", E, "\n")
        return


    def set_frequencyAnalyzer(self) -> Callable:
        try:
            self.manager = pyslm.StreamManager(
                version = 'AdvFreqAnalyzer',
                path = os.path.join(
                    self.parameters['pathProject'],
                    self.parameters['currentProject']
                    ),
                device = self.parameters['device'],
                fs = self.parameters['fs'],
                inCh = self.parameters['inCh'],
                outCh = self.parameters['outCh'],
                tau = self.parameters['tau'],
                fstart = self.parameters['fstart'],
                fend = self.parameters['fend'],
                b = self.parameters['b'],
                fweighting = self.parameters['fweighting'],
                duration = self.parameters['duration'],
                excitTime = self.parameters['excitTime'],
                scapeTime = self.parameters['scapeTime'],
                decayTime = self.parameters['decayTime'],
                template = self.parameters['template'],
                method = self.parameters['method'],
                numDecay = self.parameters['numDecay'],
                TLevel  =  self.parameters['TLevel'],
                fCalib = self.parameters['fCalib'],
                pCalib = self.parameters['pCalib'],
                calibFactor = self.parameters['calibFactor'],
                micCorr = self.parameters['micCorr'],
                applyMicCorr = self.parameters['applyMicCorr'],
                adcCorr = self.parameters['adcCorr'],
                applyAdcCorr = self.parameters['applyAdcCorr'],
                saveRawData = self.parameters['saveRawData']
                )
            self.manager.play()
            now = datetime.datetime.now()
            self.timeStamp['play'] = now.strftime("%d/%m/%Y - %H:%M:%S")
            self.manager.realtime_data.connect(self.update_frequencyAnalyzer)
            self.manager.fullresults_data.connect(self.full_frequencyAnalyzer)
            self.manager.callstop.connect(self.callOverlay)
            self.ax = self.measurementViewer.getAxis('bottom')
        except Exception as E:
            print("setSLM.set_frequencyAnalyzer(): ", E, "\n")
        return


    @QtCore.pyqtSlot()
    def callOverlay(self) -> Callable:
        try:
            now = datetime.datetime.now()
            self.timeStamp['stop'] = now.strftime("%d/%m/%Y - %H:%M:%S")
            self.overlay = pyslm.Overlay(self.centralWidget())
            self.overlay.hide()
            self.overlay.setMinimumSize(QtCore.QSize(800,430))
            # self.overlay.resize(800, 430)
            self.overlay.show()
        except Exception as E:
            print("setSLM.callOverlay(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def update_frequencyAnalyzer(self, results: dict) -> Callable:
        try:
            Lp_global = results['Lp_global']
            Lp_bands = results['Lp_bands']
            strBands = results['strBands']
            x_axis = results['x_axis']
            countdown = int(self.manager.duration - self.manager.framesRead/self.manager.fs)
            if countdown > 0:
                self.lbl_Durationinfo.setText(self.seconds2HMS(countdown))
                self.ax.setTicks([strBands])
                self.value_Leq.setText(str(Lp_global))
                self.plotBar.setOpts(
                    x = x_axis,
                    height = Lp_bands,
                    width = 0.6,
                    brush = (120, 145, 255)
                    )
        except Exception as E:
            print("setSLM.update_frequencyAnalyzer(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def full_frequencyAnalyzer(self, results: dict) -> Callable:
        try:
            self.results = results
            if self.parameters['tau'] == 0.035:
                tweighting = 'I'
            elif self.parameters['tau'] == 0.125:
                tweighting = 'F'
            else:
                tweighting = 'S'
            _translate = QtCore.QCoreApplication.translate
            self.lbl_Leq.setText(_translate("gui_SLM",
                "<html><head/><body><p>L<span style=\" vertical-align:sub;\">"+\
                self.parameters['fweighting']+"eq,"+tweighting+"</span></p></body></html>"))
            self.overlay.close_overlay = True
            self.lbl_Durationinfo.setText('00:00:00')
            Leq_global = results['Leq_global']
            Leq_bands = results['Leq_bands']
            Lmax = results['Lmax']
            Lmin = results['Lmin']
            LAE = results['SEL']
            Lpeak = results['Lpeak']
            L10 = results['L10']
            L90 = results['L90']
            # print('\n\n\nL50: ', results['L50'])
            strBands = self.manager.parallelProcess.strBands
            x_axis = self.manager.parallelProcess.x_axis
            self.ax.setTicks([strBands])
            self.plotBar.setOpts(x=x_axis, height=Leq_bands, width=0.6,brush=(120, 145, 255))
            # Set values of parameters
            self.value_Leq.setText(str(Leq_global))
            self.value_Lmax.setText(str(Lmax))
            self.value_Lmin.setText(str(Lmin))
            self.value_Lpeak.setText(str(Lpeak))
            self.value_LAE.setText(str(LAE))
            self.value_L10.setText(str(L10))
            self.value_L90.setText(str(L90))
            # Set buttons
            self.btnSave.setEnabled(True)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save.ico")))
            self.btnDelete.setEnabled(True)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete.ico")))
            self.btnPlay.setEnabled(False)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_noclick.ico")))
            self.btnStop.setEnabled(False)
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_noclick.ico")))
            self.btnNewproject.setEnabled(False)
            self.btnNewproject.setIcon(QtGui.QIcon(os.path.join(path_icons, "NewProject_noclick.ico")))
            self.btnSetup.setEnabled(False)
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_noclick.ico")))
            self.btnCalibrate.setEnabled(False)
            self.btnCalibrate.setIcon(QtGui.QIcon(os.path.join(path_icons, "Calibrate_noclick.ico")))
            self.btnInfo.setEnabled(False)
            self.btnInfo.setIcon(QtGui.QIcon(os.path.join(path_icons, "info_noclick.ico")))
        except Exception as E:
            print("setSLM.full_frequencyAnalyzer(): ", E, "\n")
        return


    def set_reverberationTime(self) -> Callable:
        try:
            self.manager = pyslm.StreamManager(
                version = 'AdvFreqAnalyzer',
                path = os.path.join(
                    self.parameters['pathProject'],
                    self.parameters['currentProject']
                    ),
                device = self.parameters['device'],
                fs = self.parameters['fs'],
                inCh = self.parameters['inCh'],
                outCh = self.parameters['outCh'],
                tau = self.parameters['tau'],
                fstart = self.parameters['fstart'],
                fend = self.parameters['fend'],
                b = self.parameters['b'],
                fweighting = self.parameters['fweighting'],
                duration = self.parameters['duration'],
                excitTime = self.parameters['excitTime'],
                scapeTime = self.parameters['scapeTime'],
                decayTime = self.parameters['decayTime'],
                template = self.parameters['template'],
                method = self.parameters['method'],
                numDecay = self.parameters['numDecay'],
                TLevel  =  self.parameters['TLevel'],
                fCalib = self.parameters['fCalib'],
                pCalib = self.parameters['pCalib'],
                calibFactor = self.parameters['calibFactor'],
                micCorr = self.parameters['micCorr'],
                applyMicCorr = self.parameters['applyMicCorr'],
                adcCorr = self.parameters['adcCorr'],
                applyAdcCorr = self.parameters['applyAdcCorr'],
                saveRawData = self.parameters['saveRawData']
                )
            self.tauConter = self.manager.tau
            self.manager.play()
            now = datetime.datetime.now()
            self.timeStamp['play'] = now.strftime("%d/%m/%Y - %H:%M:%S")
            self.manager.realtime_data.connect(self.update_reverberationTime)
            self.manager.fullresults_data.connect(self.full_reverberationTime)
            self.manager.callstop.connect(self.callOverlay)
            self.ax = self.measurementViewer.getAxis('bottom')
        except Exception as E:
            print("setSLM.set_reverberationTime(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def update_reverberationTime(self, results: dict) -> Callable:
        try:
            Lp_global = results['Lp_global']
            Lp_bands = results['Lp_bands']
            strBands = results['strBands']
            x_axis = results['x_axis']
            self.tauConter += self.manager.tau
            countdown = int((self.manager.numSamples * self.manager.numDecay)/self.manager.fs - self.tauConter)
            if countdown > 0:
                self.lbl_Durationinfo.setText(self.seconds2HMS(countdown))
                self.ax.setTicks([strBands])
                self.value_Leq.setText(str(Lp_global))
                self.plotBar.setOpts(
                    x = x_axis,
                    height = Lp_bands,
                    width = 0.6,
                    brush = (120, 145, 255)
                    )
        except Exception as E:
            print("setSLM.update_reverberationTime(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def full_reverberationTime(self, results: dict) -> Callable:
        try:
            self.results = results
            _translate = QtCore.QCoreApplication.translate
            id500 = np.where(results['freq'] == 500)[0][0]
            self.overlay.close_overlay = True
            self.lbl_Durationinfo.setText('00:00:00')
            EDT = results['EDT']
            RT15 = results['RT15']
            RT20 = results['RT20']
            RT30 = results['RT30']
            D50 = results['D50']
            D80 = results['D80']
            # C50 = results['C50']
            C80 = results['C80']
            strBands = self.manager.parallelProcess.strBands
            x_axis = self.manager.parallelProcess.x_axis
            self.ax.setTicks([strBands])
            self.measurementViewer.setLabel('left', "T20 s")
            self.measurementViewer.setYRange(np.asarray(RT20).min() - 2, np.asarray(RT20).max() + 2)
            self.plotBar.setOpts(x=x_axis, height=RT20, width=0.6,brush=(120, 145, 255))
            # Set values of parameters
            self.lbl_Leq.setText(_translate("gui_SLM",
                "<html><head/><body><p>T20<span style=\" vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_Leq.setText(_translate("gui_SLM", "s"))
            self.value_Leq.setText(str(RT20[id500]))
            self.lbl_Lmax.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">EDT</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_Lmax.setText(_translate("gui_SLM", "s"))
            self.value_Lmax.setText(str(EDT[id500]))
            self.lbl_Lmin.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">T15</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_Lmin.setText(_translate("gui_SLM","s"))
            self.value_Lmin.setText(str(RT15[id500]))
            self.lbl_Lpeak.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">T30</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_Lpeak.setText(_translate("gui_SLM", "s"))
            self.value_Lpeak.setText(str(RT30[id500]))
            self.lbl_LAE.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">D50</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_LAE.setText(_translate("gui_SLM", "%"))
            self.value_LAE.setText(str(D50[id500]))
            self.lbl_L10.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">D80</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_L10.setText(_translate("gui_SLM", "%"))
            self.value_L10.setText(str(D80[id500]))
            self.lbl_L90.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">C80</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
            self.unity_L90.setText(_translate("gui_SLM", "dB"))
            self.value_L90.setText(str(C80[id500]))
            # Set buttons
            self.btnSave.setEnabled(True)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save.ico")))
            self.btnDelete.setEnabled(True)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete.ico")))
            self.btnPlay.setEnabled(False)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_noclick.ico")))
            self.btnStop.setEnabled(False)
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_noclick.ico")))
            self.btnNewproject.setEnabled(False)
            self.btnNewproject.setIcon(QtGui.QIcon(os.path.join(path_icons, "NewProject_noclick.ico")))
            self.btnSetup.setEnabled(False)
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_noclick.ico")))
            self.btnCalibrate.setEnabled(False)
            self.btnCalibrate.setIcon(QtGui.QIcon(os.path.join(path_icons, "Calibrate_noclick.ico")))
            self.btnInfo.setEnabled(False)
            self.btnInfo.setIcon(QtGui.QIcon(os.path.join(path_icons, "info_noclick.ico")))
        except Exception as E:
            print("setSLM.full_reverberationTime(): ", E, "\n")
        return


    def datatime(self) -> Callable:
        try:
            while self.isOpenWindow:
                self.now = datetime.datetime.now()
                self.lblDateinfo.setText(self.now.strftime("%d/%m/%Y - %H:%M:%S"))
                time.sleep(1)
            else:
                pass
        except Exception as E:
            print("setSLM.datatime(): ", E, "\n")
        return


    def btnPlay_Action(self):
        try:
            if self.manager.template != 'stand-by':
                self.manager.pause()
                if self.manager.isPaused.is_set():
                    self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Pause_click.ico")))
                else:
                    self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_click.ico")))
            else:
                self.stop_strem()
                if self.parameters['template'] == 'frequencyAnalyzer':
                    self.set_frequencyAnalyzer()
                elif self.parameters['template'] == 'reverberationTime':
                    self.set_reverberationTime()
                else:
                    self.set_standby()
                self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_click.ico")))
                self.btnStop.setEnabled(True)
                self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop.ico")))
                self.btnNewproject.setEnabled(False)
                self.btnNewproject.setIcon(QtGui.QIcon(os.path.join(path_icons, "NewProject_noclick.ico")))
                self.btnSetup.setEnabled(False)
                self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_noclick.ico")))
                self.btnCalibrate.setEnabled(False)
                self.btnCalibrate.setIcon(QtGui.QIcon(os.path.join(path_icons, "Calibrate_noclick.ico")))
                self.btnInfo.setEnabled(False)
                self.btnInfo.setIcon(QtGui.QIcon(os.path.join(path_icons, "info_noclick.ico")))
                self.btnSave.setEnabled(False)
                self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_noclick.ico")))
                self.btnDelete.setEnabled(False)
                self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_noclick.ico")))
        except Exception as E:
            print("setSLM.btnPlay_Action(): ", E, "\n")
        return


    def btnStop_Action(self) -> Callable:
        try:
            self.stop_strem()
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_click.ico")))
            self.btnPlay.setEnabled(False)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_noclick.ico")))
            self.btnSave.setEnabled(True)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save.ico")))
            self.btnDelete.setEnabled(True)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete.ico")))
        except Exception as E:
            print("setSLM.btnStop_Action(): ", E, "\n")
        return


    def btnSave_Action(self) -> Callable:
        try:
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_click.ico")))
            pyslm.save(
                params = self.parameters,
                results = self.results,
                timestamp = self.timeStamp,
                file_name = self.file_name
                )
            if self.parameters['saveRawData']:
                os.remove(self.file_name)
            self._setStringsGUI()
            self.set_standby()
        except Exception as E:
            print("setSLM.btnSave_Action(): ", E, "\n")
        return


    def btnDelete_Action(self) -> Callable:
        try:
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_click.ico")))
            if self.parameters['saveRawData']:
                os.remove(self.manager.recorderRawData.fname)
            else:
                if self.manager.template == 'reverberationTime':
                    print('Implement save function in Excel.')
                else:
                    print('Implement save function in Excel.')
            self._setStringsGUI()
            self.set_standby()
        except Exception as E:
            print("setSLM.btnDelete_Action(): ", E, "\n")
        return


    def btnNewproject_Action(self) -> Callable:
        try:
            self.btnNewproject.setIcon(QtGui.QIcon(os.path.join(path_icons, "NewProject_click.ico")))
            self.stop_strem()
            dlgNewProject = pyslm.setSetup()
            dlgNewProject.tabSettings.setCurrentWidget(dlgNewProject.tabSettings.findChild(QtWidgets.QWidget, 'Projects'))
            dlgNewProject.exec_()
            if not dlgNewProject.isActiveWindow():
                self.parameters = pyslm.parameters.load()
                self._setStringsGUI()
                self.set_standby()
        except Exception as E:
            print("setSLM.btnNewproject_Action(): ", E, "\n")
        return


    def btnSetup_Action(self) -> Callable:
        try:
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_click.ico")))
            self.stop_strem()
            dlgSetup = pyslm.setSetup()
            dlgSetup.tabSettings.setCurrentWidget(dlgSetup.tabSettings.findChild(QtWidgets.QWidget, 'Measurement'))
            dlgSetup.exec_()
            if not dlgSetup.isActiveWindow():
                self.parameters = pyslm.parameters.load()
                self._setStringsGUI()
                self.set_standby()
        except Exception as E:
            print("setSLM.btnSetup_Action(): ", E, "\n")
        return


    def btnCalibrate_Action(self) -> Callable:
        try:
            self.btnCalibrate.setIcon(QtGui.QIcon(os.path.join(path_icons, "Calibrate_click.ico")))
            self.stop_strem()
            dlgCalib = pyslm.setSetup()
            dlgCalib.tabSettings.setCurrentWidget(dlgCalib.tabSettings.findChild(QtWidgets.QWidget, 'Calibration'))
            dlgCalib.exec_()
            dlgCalib.setMinimumSize(QtCore.QSize(800,430))
            dlgCalib.setMaximumWidth(800)
            dlgCalib.setMinimumHeight(430)
            if not dlgCalib.isActiveWindow():
                self.parameters = pyslm.parameters.load()
                self._setStringsGUI()
                self.set_standby()
        except Exception as E:
            print("setSLM.btnCalibrate_Action(): ", E, "\n")
        return


    def btnInfo_Action(self) -> Callable:
        try:
            self.btnInfo.setIcon(QtGui.QIcon(os.path.join(path_icons, "info_click.ico")))
            self.stop_strem()
            dlgAbout = pyslm.setSetup()
            dlgAbout.tabSettings.setCurrentWidget(dlgAbout.tabSettings.findChild(QtWidgets.QWidget, 'About'))
            dlgAbout.exec_()
            if not dlgAbout.isActiveWindow():
                self.parameters = pyslm.parameters.load()
                self._setStringsGUI()
                self.set_standby()
        except Exception as E:
            print("setSLM.btnInfo_Action(): ", E, "\n")
        return
    

    def btnQuit_Action(self) -> Callable:
        try:
            self.stop_strem()
            self.isOpenWindow = False
            self.gettingDataTime.join()
            self.gettingDataTime._stop()
            self.gettingDataTime._delete()
            self.close()
        except Exception as E:
            print("setSLM.btnQuit_Action(): ", E, "\n")
        return


    def _counterFile(self) -> Tuple[str, str]:
        try:
            today = datetime.datetime.now()
            today = today.strftime("%d-%m-%Y")
            path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject'])
            if platform.system().lower() == 'windows':
                bar = '\\'
            else:
                bar = '/'
            if self.parameters['template'] == 'frequencyAnalyzer': 
                name_date = '{} SPL measurement '.format(today)
            else:
                name_date = '{} RT measurement '.format(today)
            if not os.path.isdir(path):
                os.mkdir(path)
            fname = path + bar + name_date + '001.xlsx'
            count = 2
            if os.path.isfile(fname):
                new_name = fname
                while os.path.isfile(new_name):
                    new_name = new_name.replace('.xlsx', '')
                    new_name = new_name[:-3] + '%03i.xlsx' % count
                    count += 1
            else:
                new_name = fname
            new_name = new_name.replace('.xlsx', '')
            name = new_name[:-3]
            count = int(new_name[-3:])
        except Exception as E:
            print("setSLM._counterFile(): ", E, "\n")
        return str(count), "%s(raw data) %03i.h5"%(name, count)


    def seconds2HMS(self, seconds: int) -> str:
        try:
            M, S = divmod(seconds, 60) 
            H, M = divmod(M, 60)
        except Exception as E:
            print("setSLM.seconds2HMS(): ", E, "\n")
        return "%02d:%02d:%02d" % (H, M, S)
    

    def _setStringsGUI(self) -> Callable:
        try:
            fweighting = self.parameters['fweighting']
            if self.parameters['tau'] == 0.035:
                tweighting = 'I'
            elif self.parameters['tau'] == 0.125:
                tweighting = 'F'
            else:
                tweighting = 'S'
            if self.parameters['template'] == 'frequencyAnalyzer':
                template = 'Adv. Frequency Analyzer'
                duration = self.parameters['duration']
            else:
                template = 'Reverberation time'
                duration = (self.parameters['excitTime'] +\
                    self.parameters['scapeTime'] +\
                    self.parameters['decayTime']) *\
                    self.parameters['numDecay']
            duration = self.seconds2HMS(duration)
            projectName = self.parameters['currentProject']
            counter, self.file_name = self._counterFile()
            self.measurementViewer.setLabel('left', "SPL dB")
            self.measurementViewer.setYRange(-10,115)
            _translate = QtCore.QCoreApplication.translate
            self.lbl_Durationinfo.setText(_translate("gui_SLM", duration))
            self.lbl_Projectinfo.setText(_translate("gui_SLM",
                "<html><head/><body><p align=\"center\">"+projectName+" - Measurement " + counter + "</p></body></html>"))
            self.lblDateinfo.setText(_translate("gui_SLM", "DD/MM/AA - Hr:Min:Sec"))
            self.lblTemplateInfo.setText(_translate("gui_SLM",
                "<html><head/><body><p align=\"center\">"+template+"</p></body></html>"))
            self.lbl_L90.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">90</span></p></body></html>"))
            self.lbl_Lmin.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">"+fweighting+"min,"+tweighting+"</span></p></body></html>"))
            self.unity_L10.setText(_translate("gui_SLM", " dB"))
            self.value_Lmax.setText(_translate("gui_SLM", "--.--"))
            self.unity_L90.setText(_translate("gui_SLM", " dB"))
            self.value_LAE.setText(_translate("gui_SLM", "--.--"))
            self.value_Leq.setText(_translate("gui_SLM", "--.--"))
            self.unity_Lpeak.setText(_translate("gui_SLM", " dB"))
            self.lbl_Lpeak.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">Cpeak</span></p></body></html>"))
            self.lbl_Leq.setText(_translate("gui_SLM",
                "<html><head/><body><p>L<span style=\" vertical-align:sub;\">"+fweighting+","+tweighting+"</span></p></body></html>"))
            self.value_L90.setText(_translate("gui_SLM", "--.--"))
            self.value_Lpeak.setText(_translate("gui_SLM", "--.--"))
            self.unity_LAE.setText(_translate("gui_SLM", " dB"))
            self.unity_Leq.setText(_translate("gui_SLM", "dB"))
            self.lbl_Lmax.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">"+fweighting+"max,"+tweighting+"</span></p></body></html>"))
            self.lbl_L10.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">10</span></p></body></html>"))
            self.value_Lmin.setText(_translate("gui_SLM", "--.--"))
            self.lbl_LAE.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">AE</span></p></body></html>"))
            self.value_L10.setText(_translate("gui_SLM", "--.--"))
            self.unity_Lmin.setText(_translate("gui_SLM", " dB"))
            self.unity_Lmax.setText(_translate("gui_SLM", " dB"))
        except Exception as E:
            print("setSLM._setStringsGUI(): ", E, "\n")
        return


class setSLM2(QtWidgets.QMainWindow, pyslm.guiSLM2):
    def __init__(self, parent=None):
        super(setSLM2, self).__init__(parent)
        self.setupUi(self)
        self.timeStamp = {}
        self.btnSetup.clicked.connect(self.btnSetup_Action)
        self.btnQuit.clicked.connect(self.btnQuit_Action)
        self.btnPlay.clicked.connect(self.btnPlay_Action)
        self.btnStop.clicked.connect(self.btnStop_Action)
        self.btnDelete.clicked.connect(self.btnDelete_Action)
        self.btnSave.clicked.connect(self.btnSave_Action)
        self.parameters = pyslm.parameters.load()
        self.parameters['version'] = 'DataLogger'
        self.parameters['template'] = 'spl'
        pyslm.parameters.update(self.parameters)
        self.parameters = pyslm.parameters.load()
        self.set_standby()
        self.isOpenWindow = True
        self._setStringsGUI()
        self.show()
        
    def set_standby(self) -> Callable:
        try:
            self.btnPlay.setEnabled(True)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play.ico")))
            self.btnStop.setEnabled(False)
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_noclick.ico")))
            self.btnSetup.setEnabled(True)
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup.ico")))
            self.btnSave.setEnabled(False)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_noclick.ico")))
            self.btnDelete.setEnabled(False)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_noclick.ico")))
            self.manager = pyslm.StreamManager(
                version = 'DataLogger',
                path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject']),
                device = self.parameters['device'],
                fs = self.parameters['fs'],
                inCh = self.parameters['inCh'],
                tau = self.parameters['tau'],
                fweighting = self.parameters['fweighting'],
                duration = self.parameters['duration'],
                template = 'stand-by',
                fCalib = self.parameters['fCalib'],
                pCalib = self.parameters['pCalib'],
                calibFactor = self.parameters['calibFactor'],
                micCorr = self.parameters['micCorr'],
                applyMicCorr = False,
                adcCorr = self.parameters['adcCorr'],
                applyAdcCorr = False,
                saveRawData = False
                )
            self.manager.play()
            self.manager.realtime_data.connect(self.update_standby)
        except Exception as E:
            print("setSLM2.set_standby(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def update_standby(self, results: dict) -> Callable:
        try:
            Lp_global = results['Lp_global']
            self.value_Leq.setText(str(Lp_global))
        except Exception as E:
            print("setSLM2.update_standby(): ", E, "\n")
        return


    def stop_strem(self) -> Callable:
        try:
            self.manager.stop()
        except Exception as E:
            print("setSLM2.stop_strem(): ", E, "\n")
        return


    def set_spl(self) -> Callable:
        try:
            self.manager = pyslm.StreamManager(
                version = 'DataLogger',
                path = os.path.join(
                    self.parameters['pathProject'], 
                    self.parameters['currentProject']
                    ),
                device = self.parameters['device'],
                fs = self.parameters['fs'],
                inCh = self.parameters['inCh'],
                tau = self.parameters['tau'],
                fweighting = self.parameters['fweighting'],
                duration = self.parameters['duration'],
                template = self.parameters['template'],
                fCalib = self.parameters['fCalib'],
                pCalib = self.parameters['pCalib'],
                calibFactor = self.parameters['calibFactor'],
                micCorr = self.parameters['micCorr'],
                applyMicCorr = self.parameters['applyMicCorr'],
                adcCorr = self.parameters['adcCorr'],
                applyAdcCorr = self.parameters['applyAdcCorr'],
                saveRawData = self.parameters['saveRawData']
                )
            self.manager.play()
            now = datetime.datetime.now()
            self.timeStamp['play'] = now.strftime("%d/%m/%Y - %H:%M:%S")
            self.manager.realtime_data.connect(self.update_spl)
            self.manager.fullresults_data.connect(self.full_spl)
            self.manager.callstop.connect(self.callOverlay)
        except Exception as E:
            print("setSLM2.set_spl(): ", E, "\n")
        return


    @QtCore.pyqtSlot()
    def callOverlay(self) -> Callable:
        try:
            now = datetime.datetime.now()
            self.timeStamp['stop'] = now.strftime("%d/%m/%Y - %H:%M:%S")
            self.overlay = pyslm.Overlay(self.centralWidget())
            self.overlay.hide()
            self.overlay.setMinimumSize(QtCore.QSize(480,410))
            # self.overlay.resize(800, 430)
            self.overlay.show()
        except Exception as E:
            print("setSLM2.callOverlay(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def update_spl(self, results: dict) -> Callable:
        try:
            Lp_global = results['Lp_global']
            countdown = int(self.manager.duration - self.manager.framesRead/self.manager.fs)
            if countdown > 0:
                self.lbl_Durationinfo.setText(self.seconds2HMS(countdown))
                self.value_Leq.setText(str(Lp_global))
        except Exception as E:
            print("setSLM2.update_spl(): ", E, "\n")
        return


    @QtCore.pyqtSlot(dict)
    def full_spl(self, results: dict) -> Callable:
        try:
            self.results = results
            if self.parameters['tau'] == 0.035:
                tweighting = 'I'
            elif self.parameters['tau'] == 0.125:
                tweighting = 'F'
            else:
                tweighting = 'S'
            _translate = QtCore.QCoreApplication.translate
            self.lbl_Leq.setText(_translate("gui_SLM",
                "<html><head/><body><p>L<span style=\" vertical-align:sub;\">"+\
                self.parameters['fweighting']+"eq,"+tweighting+"</span></p></body></html>"))
            self.overlay.close_overlay = True
            self.lbl_Durationinfo.setText('00:00:00')
            Leq_global = results['Leq_global']
            Lmax = results['Lmax']
            Lmin = results['Lmin']
            LAE = results['SEL']
            Lpeak = results['Lpeak']
            L10 = results['L10']
            L90 = results['L90']
            # print('\n\n\nL50: ', results['L50'])
            # Set values of parameters
            self.value_Leq.setText(str(Leq_global))
            self.value_Lmax.setText(str(Lmax))
            self.value_Lmin.setText(str(Lmin))
            self.value_Lpeak.setText(str(Lpeak))
            self.value_LAE.setText(str(LAE))
            self.value_L10.setText(str(L10))
            self.value_L90.setText(str(L90))
            # Set buttons
            self.btnSave.setEnabled(True)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save.ico")))
            self.btnDelete.setEnabled(True)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete.ico")))
            self.btnPlay.setEnabled(False)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_noclick.ico")))
            self.btnStop.setEnabled(False)
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_noclick.ico")))
            self.btnSetup.setEnabled(False)
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_noclick.ico")))
        except Exception as E:
            print("setSLM2.full_spl(): ", E, "\n")
        return


    def btnPlay_Action(self) -> Callable:
        try:
            if self.manager.template != 'stand-by':
                self.manager.pause()
                if self.manager.isPaused.is_set():
                    self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Pause_click.ico")))
                else:
                    self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_click.ico")))
            else:
                self.stop_strem()
                if self.parameters['template'] == 'spl':
                    self.set_spl()
                else:
                    self.set_standby()
                self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_click.ico")))
                self.btnStop.setEnabled(True)
                self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop.ico")))
                self.btnSetup.setEnabled(False)
                self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_noclick.ico")))
                self.btnSave.setEnabled(False)
                self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_noclick.ico")))
                self.btnDelete.setEnabled(False)
                self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_noclick.ico")))
        except Exception as E:
            print("setSLM2.btnPlay_Action(): ", E, "\n")
        return


    def btnStop_Action(self) -> Callable:
        try:
            self.stop_strem()
            self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_click.ico")))
            self.btnPlay.setEnabled(False)
            self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_noclick.ico")))
            self.btnSave.setEnabled(True)
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save.ico")))
            self.btnDelete.setEnabled(True)
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete.ico")))
        except Exception as E:
            print("setSLM2.btnStop_Action(): ", E, "\n")
        return


    def btnSave_Action(self) -> Callable:
        try:
            self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_click.ico")))
            pyslm.save(params=self.parameters, results=self.results, timestamp=self.timeStamp, file_name=self.file_name)
            if self.parameters['saveRawData']:
                os.remove(self.file_name)
            self._setStringsGUI()
            self.set_standby()
        except Exception as E:
            print("setSLM2.btnSave_Action(): ", E, "\n")
        return


    def btnDelete_Action(self) -> Callable:
        try:
            self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_click.ico")))
            if self.parameters['saveRawData']:
                os.remove(self.manager.recorderRawData.fname)
            self._setStringsGUI()
            self.set_standby()
        except Exception as E:
            print("setSLM2.btnDelete_Action(): ", E, "\n")
        return


    def btnSetup_Action(self) -> Callable:
        try:
            self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_click.ico")))
            self.stop_strem()
            dlgSetup = pyslm.setSetup2()
            dlgSetup.tabSettings.setCurrentWidget(dlgSetup.tabSettings.findChild(QtWidgets.QWidget, 'Measurement'))
            dlgSetup.exec_()
            if not dlgSetup.isActiveWindow():
                self.parameters = pyslm.parameters.load()
                self._setStringsGUI()
                self.set_standby()
        except Exception as E:
            print("setSLM2.btnSetup_Action(): ", E, "\n")
        return
    

    def btnQuit_Action(self) -> Callable:
        try:
            self.stop_strem()
            self.isOpenWindow = False
            self.close()
        except Exception as E:
            print("setSLM2.btnQuit_Action(): ", E, "\n")
        return


    def _counterFile(self) -> Tuple[str, str]:
        try:
            today = datetime.datetime.now()
            today = today.strftime("%d-%m-%Y")
            path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject'])
            if platform.system().lower() == 'windows':
                bar = '\\'
            else:
                bar = '/'
            name_date = '{} SPL measurement '.format(today)
            if not os.path.isdir(path):
                os.mkdir(path)
            fname = path + bar + name_date + '001.xlsx'
            count = 2
            if os.path.isfile(fname):
                new_name = fname
                while os.path.isfile(new_name):
                    new_name = new_name.replace('.xlsx', '')
                    new_name = new_name[:-3] + '%03i.xlsx' % count
                    count += 1
            else:
                new_name = fname
            new_name = new_name.replace('.xlsx', '')
            name = new_name[:-3]
            count = int(new_name[-3:])
        except Exception as E:
            print("setSLM2._counterFile(): ", E, "\n")
        return str(count), "%s(raw data) %03i.h5"%(name, count)


    def seconds2HMS(self, seconds: int) -> str:
        try:
            M, S = divmod(seconds, 60) 
            H, M = divmod(M, 60)
        except Exception as E:
            print("setSLM2.seconds2HMS(): ", E, "\n")
        return "%02d:%02d:%02d" % (H, M, S)
    

    def _setStringsGUI(self) -> Callable:
        try:
            fweighting = self.parameters['fweighting']
            if self.parameters['tau'] == 0.035:
                tweighting = 'I'
            elif self.parameters['tau'] == 0.125:
                tweighting = 'F'
            else:
                tweighting = 'S'
            duration = self.seconds2HMS(self.parameters['duration'])
            projectName = self.parameters['currentProject']
            counter, self.file_name = self._counterFile()
            _translate = QtCore.QCoreApplication.translate
            self.lbl_Durationinfo.setText(_translate("gui_SLM", duration))
            self.lbl_Projectinfo.setText(_translate("gui_SLM",
                "<html><head/><body><p align=\"center\">"+projectName+" - Measurement " + counter + "</p></body></html>"))
            self.lbl_L90.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">90</span></p></body></html>"))
            self.lbl_Lmin.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">"+fweighting+"min,"+tweighting+"</span></p></body></html>"))
            self.unity_L10.setText(_translate("gui_SLM"," dB"))
            self.value_Lmax.setText(_translate("gui_SLM", "--.--"))
            self.unity_L90.setText(_translate("gui_SLM", " dB"))
            self.value_LAE.setText(_translate("gui_SLM", "--.--"))
            self.value_Leq.setText(_translate("gui_SLM", "--.--"))
            self.unity_Lpeak.setText(_translate("gui_SLM", " dB"))
            self.lbl_Lpeak.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">Cpeak</span></p></body></html>"))
            self.lbl_Leq.setText(_translate("gui_SLM",
                "<html><head/><body><p>L<span style=\" vertical-align:sub;\">"+fweighting+","+tweighting+"</span></p></body></html>"))
            self.value_L90.setText(_translate("gui_SLM", "--.--"))
            self.value_Lpeak.setText(_translate("gui_SLM", "--.--"))
            self.unity_LAE.setText(_translate("gui_SLM", " dB"))
            self.unity_Leq.setText(_translate("gui_SLM", "dB"))
            self.lbl_Lmax.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">"+fweighting+"max,"+tweighting+"</span></p></body></html>"))
            self.lbl_L10.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">10</span></p></body></html>"))
            self.value_Lmin.setText(_translate("gui_SLM", "--.--"))
            self.lbl_LAE.setText(_translate("gui_SLM",
                "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">AE</span></p></body></html>"))
            self.value_L10.setText(_translate("gui_SLM", "--.--"))
            self.unity_Lmin.setText(_translate("gui_SLM", " dB"))
            self.unity_Lmax.setText(_translate("gui_SLM", " dB"))
        except Exception as E:
            print("setSLM2._setStringsGUI(): ", E, "\n")
        return


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    start = pyslm.setSLM()
    app.exec_()