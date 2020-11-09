
from PySide2 import QtCore, QtGui, QtWidgets
from datetime import datetime, date
import pyqtgraph, sys, os
import threading as thd
from time import sleep
import numpy as np
import platform
import math
import h5py
import pyslm


path_icons = os.path.join(os.path.dirname(os.path.realpath(pyslm.__file__)), 'Icons')

if sys.platform == 'win32' or sys.platform == 'win64':
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version'  # arbitrary string
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
        self.set_standby()
        self.isOpenWindow = True
        self.gettingDataTime = thd.Thread(target=self.datatime)
        self.gettingDataTime.start()
        self._setStringsGUI()
        self.show()
        
        

    def set_standby(self):
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
        self.manager = pyslm.StreamManager(path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject']),
                                device=self.parameters['device'],
                                fs=self.parameters['fs'],
                                inCh=self.parameters['inCh'],
                                outCh=self.parameters['outCh'],
                                tau=self.parameters['tau'],
                                fstart=self.parameters['fstart'],
                                fend=self.parameters['fend'],
                                b=self.parameters['b'],
                                fweighting=self.parameters['fweighting'],
                                duration=self.parameters['duration'],
                                excitTime=self.parameters['excitTime'],
                                scapeTime=self.parameters['scapeTime'],
                                decayTime=self.parameters['decayTime'],
                                template='stand-by',
                                method=self.parameters['method'],
                                numDecay=self.parameters['numDecay'],
                                TLevel = self.parameters['TLevel'],
                                fCalib=self.parameters['fCalib'],
                                pCalib=self.parameters['pCalib'],
                                calibFactor=self.parameters['calibFactor'],
                                corrMic=self.parameters['micCorr'],
                                applyMicCorr=False,
                                corrADC=self.parameters['adcCorr'],
                                applyAdcCorr=False,
                                saveRawData=False)
        self.manager.play()
        self.manager.realtime_data.connect(self.update_standby)
        self.ax = self.measurementViewer.getAxis('bottom')
        return

    @QtCore.Slot(dict)
    def update_standby(self, results):
        Lp_global = results['Lp_global']
        Lp_bands = results['Lp_bands']
        strBands = results['strBands']
        x_axis = results['x_axis']
        self.ax.setTicks([strBands])
        self.value_Leq.setText(str(Lp_global))
        self.plotBar.setOpts(x=x_axis, height=Lp_bands, width=0.6,brush=(120, 145, 255))
        return

    def stop_strem(self):
        self.manager.stop()
        return

    def set_frequencyAnalyzer(self):
        self.manager = pyslm.StreamManager(path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject']),
                                device=self.parameters['device'],
                                fs=self.parameters['fs'],
                                inCh=self.parameters['inCh'],
                                outCh=self.parameters['outCh'],
                                tau=self.parameters['tau'],
                                fstart=self.parameters['fstart'],
                                fend=self.parameters['fend'],
                                b=self.parameters['b'],
                                fweighting=self.parameters['fweighting'],
                                duration=self.parameters['duration'],
                                excitTime=self.parameters['excitTime'],
                                scapeTime=self.parameters['scapeTime'],
                                decayTime=self.parameters['decayTime'],
                                template=self.parameters['template'],
                                method=self.parameters['method'],
                                numDecay=self.parameters['numDecay'],
                                TLevel = self.parameters['TLevel'],
                                fCalib=self.parameters['fCalib'],
                                pCalib=self.parameters['pCalib'],
                                calibFactor=self.parameters['calibFactor'],
                                corrMic=self.parameters['micCorr'],
                                applyMicCorr=self.parameters['applyMicCorr'],
                                corrADC=self.parameters['adcCorr'],
                                applyAdcCorr=self.parameters['applyAdcCorr'],
                                saveRawData=self.parameters['saveRawData'])
        self.manager.play()
        self.manager.realtime_data.connect(self.update_frequencyAnalyzer)
        self.manager.fullresults_data.connect(self.full_frequencyAnalyzer)
        self.manager.callstop.connect(self.callOverlay)
        self.ax = self.measurementViewer.getAxis('bottom')
        return

    @QtCore.Slot()
    def callOverlay(self):
        self.overlay = pyslm.Overlay(self.centralWidget())
        self.overlay.hide()
        self.overlay.setMinimumSize(QtCore.QSize(800,430))
        # self.overlay.resize(800, 430)
        self.overlay.show()
        return

    @QtCore.Slot(dict)
    def update_frequencyAnalyzer(self, results):
        Lp_global = results['Lp_global']
        Lp_bands = results['Lp_bands']
        strBands = results['strBands']
        x_axis = results['x_axis']
        countdown = int(self.manager.duration - self.manager.framesRead/self.manager.fs)
        if countdown > 0:
            self.lbl_Durationinfo.setText(self.seconds2HMN(countdown))
            self.ax.setTicks([strBands])
            self.value_Leq.setText(str(Lp_global))
            self.plotBar.setOpts(x=x_axis, height=Lp_bands, width=0.6,brush=(120, 145, 255))
        return

    @QtCore.Slot(dict)
    def full_frequencyAnalyzer(self, results):
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
        return


    def set_reverberationTime(self):
        self.manager = pyslm.StreamManager(path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject']),
                                device=self.parameters['device'],
                                fs=self.parameters['fs'],
                                inCh=self.parameters['inCh'],
                                outCh=self.parameters['outCh'],
                                tau=self.parameters['tau'],
                                fstart=self.parameters['fstart'],
                                fend=self.parameters['fend'],
                                b=self.parameters['b'],
                                fweighting=self.parameters['fweighting'],
                                duration=self.parameters['duration'],
                                excitTime=self.parameters['excitTime'],
                                scapeTime=self.parameters['scapeTime'],
                                decayTime=self.parameters['decayTime'],
                                template=self.parameters['template'],
                                method=self.parameters['method'],
                                numDecay=self.parameters['numDecay'],
                                TLevel = self.parameters['TLevel'],
                                fCalib=self.parameters['fCalib'],
                                pCalib=self.parameters['pCalib'],
                                calibFactor=self.parameters['calibFactor'],
                                corrMic=self.parameters['micCorr'],
                                applyMicCorr=self.parameters['applyMicCorr'],
                                corrADC=self.parameters['adcCorr'],
                                applyAdcCorr=self.parameters['applyAdcCorr'],
                                saveRawData=self.parameters['saveRawData'])
        self.tauConter = self.manager.tau
        self.manager.play()
        self.manager.realtime_data.connect(self.update_reverberationTime)
        self.manager.fullresults_data.connect(self.full_reverberationTime)
        self.manager.callstop.connect(self.callOverlay)
        self.ax = self.measurementViewer.getAxis('bottom')
        return

    @QtCore.Slot(dict)
    def update_reverberationTime(self, results):
        Lp_global = results['Lp_global']
        Lp_bands = results['Lp_bands']
        strBands = results['strBands']
        x_axis = results['x_axis']
        self.tauConter += self.manager.tau
        countdown = int((self.manager.numSamples * self.manager.numDecay)/self.manager.fs - self.tauConter)
        if countdown > 0:
            self.lbl_Durationinfo.setText(self.seconds2HMN(countdown))
            self.ax.setTicks([strBands])
            self.value_Leq.setText(str(Lp_global))
            self.plotBar.setOpts(x=x_axis, height=Lp_bands, width=0.6,brush=(120, 145, 255))
        return

    @QtCore.Slot(dict)
    def full_reverberationTime(self, results):
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
        self.measurementViewer.setLabel('left', "T20 dB")
        self.plotBar.setOpts(x=x_axis, height=RT20, width=0.6,brush=(120, 145, 255))
        # Set values of parameters
        self.lbl_Leq.setText(_translate("gui_SLM", "<html><head/><body><p>T20<span style=\" vertical-align:sub;\">500Hz</span></p></body></html>"))
        self.unity_Leq.setText(_translate("gui_SLM", "s"))
        self.value_Leq.setText(str(RT20[id500]))
        self.lbl_Lmax.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">EDT</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
        self.unity_Lmax.setText(_translate("gui_SLM", "s"))
        self.value_Lmax.setText(str(EDT[id500]))
        self.lbl_Lmin.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">T15</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
        self.unity_Lmin.setText(_translate("gui_SLM", "s"))
        self.value_Lmin.setText(str(RT15[id500]))
        self.lbl_Lpeak.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">T30</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
        self.unity_Lpeak.setText(_translate("gui_SLM", "s"))
        self.value_Lpeak.setText(str(RT30[id500]))
        self.lbl_LAE.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">D50</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
        self.unity_LAE.setText(_translate("gui_SLM", "%"))
        self.value_LAE.setText(str(D50[id500]))
        self.lbl_L10.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">D80</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
        self.unity_L10.setText(_translate("gui_SLM", "%"))
        self.value_L10.setText(str(D80[id500]))
        self.lbl_L90.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">C80</span><span style=\" font-size:14pt; vertical-align:sub;\">500Hz</span></p></body></html>"))
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
        return

    def datatime(self):
        while self.isOpenWindow:
            self.now = datetime.now()
            self.lblDateinfo.setText(self.now.strftime("%d/%m/%Y - %H:%M:%S"))
            sleep(1.0)
        else:
            pass
        return

    def btnPlay_Action(self):
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
        return

    def btnStop_Action(self):
        self.stop_strem()
        self.btnStop.setIcon(QtGui.QIcon(os.path.join(path_icons, "Stop_click.ico")))
        self.btnPlay.setEnabled(False)
        self.btnPlay.setIcon(QtGui.QIcon(os.path.join(path_icons, "Play_noclick.ico")))
        self.btnSave.setEnabled(True)
        self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save.ico")))
        self.btnDelete.setEnabled(True)
        self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete.ico")))
        return

    def btnSave_Action(self):
        self.btnSave.setIcon(QtGui.QIcon(os.path.join(path_icons, "Save_click.ico")))
        if self.parameters['saveRawData'] == False:
            os.remove(self.manager.recorderRawData.fname)
        if self.manager.template == 'reverberationTime':
            print('Implementar saver do Excel!')
        else:
            print('Implementar saver do Excel!')
        self._setStringsGUI()
        self.set_standby()
        return

    def btnDelete_Action(self):
        self.btnDelete.setIcon(QtGui.QIcon(os.path.join(path_icons, "Delete_click.ico")))
        if self.parameters['saveRawData']:
            os.remove(self.manager.recorderRawData.fname)
        self._setStringsGUI()
        self.set_standby()
        return

    def btnNewproject_Action(self):
        self.btnNewproject.setIcon(QtGui.QIcon(os.path.join(path_icons, "NewProject_click.ico")))
        self.stop_strem()
        dlgNewProject = pyslm.setSetup()
        dlgNewProject.tabSettings.setCurrentWidget(dlgNewProject.tabSettings.findChild(QtWidgets.QWidget, 'Projects'))
        dlgNewProject.exec_()
        if not dlgNewProject.isActiveWindow():
            self.parameters = pyslm.parameters.load()
            self._setStringsGUI()
            self.set_standby()
        return

    def btnSetup_Action(self):
        self.btnSetup.setIcon(QtGui.QIcon(os.path.join(path_icons, "Setup_click.ico")))
        self.stop_strem()
        dlgSetup = pyslm.setSetup()
        dlgSetup.tabSettings.setCurrentWidget(dlgSetup.tabSettings.findChild(QtWidgets.QWidget, 'Measurement'))
        dlgSetup.exec_()
        if not dlgSetup.isActiveWindow():
            self.parameters = pyslm.parameters.load()
            self._setStringsGUI()
            self.set_standby()
        return

    def btnCalibrate_Action(self):
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
        return

    def btnInfo_Action(self):
        self.btnInfo.setIcon(QtGui.QIcon(os.path.join(path_icons, "info_click.ico")))
        self.stop_strem()
        dlgAbout = pyslm.setSetup()
        dlgAbout.tabSettings.setCurrentWidget(dlgAbout.tabSettings.findChild(QtWidgets.QWidget, 'About'))
        dlgAbout.exec_()
        if not dlgAbout.isActiveWindow():
            self.parameters = pyslm.parameters.load()
            self._setStringsGUI()
            self.set_standby()
        return
    
    def btnQuit_Action(self):
        self.stop_strem()
        self.isOpenWindow = False
        self.gettingDataTime.join()
        self.gettingDataTime._stop()
        self.gettingDataTime._delete()
        self.close()
        return

    def _counterFile(self):
        path = os.path.join(self.parameters['pathProject'], self.parameters['currentProject'])
        if platform.system().lower() == 'windows':
            bar = '\\'
        else:
            bar = '/'
        if self.parameters['template'] == 'frequencyAnalyzer': 
            name_date = '{} SPL - RAW DATA - measurement '.format(
                str(date.today()))
        elif self.parameters['template'] == 'calibration':
            name_date = '{} CAL - RAW DATA - measurement '.format(
                str(date.today()))
        else:
            name_date = '{} RT - RAW DATA - measurement '.format(
                str(date.today()))
        if not os.path.isdir(path):
            os.mkdir(path)
        fname = path + bar + name_date + '001.h5'
        count = 2
        if os.path.isfile(fname):
            new_name = fname
            while os.path.isfile(new_name):
                new_name = new_name.replace('.h5', '')
                idx = len(new_name)
                new_name = new_name[0:idx-3] + '%03i.h5' % count
                count += 1
        else:
            new_name = fname
        return count - 1

    def seconds2HMN(self, seconds): 
        M, S = divmod(seconds, 60) 
        H, M = divmod(M, 60)
        return "%02d:%02d:%02d" % (H, M, S)
    
    def _setStringsGUI(self):
        fweighting = self.parameters['fweighting']
        if self.parameters['tau'] == 0.035:
            tweighting = 'I'
        elif self.parameters['tau'] == 0.125:
            tweighting = 'F'
        else:
            tweighting = 'S'
        if self.parameters['template'] == 'frequencyAnalyzer':
            template = 'Frequency Analyzer Adv.'
            duration = self.parameters['duration']
        else:
            template = 'Reverberation time'
            duration = (self.parameters['excitTime'] + self.parameters['scapeTime'] + self.parameters['decayTime']) * self.parameters['numDecay']
        duration = self.seconds2HMN(duration)
        projectName = self.parameters['currentProject']
        counter = str(self._counterFile())
        if self.manager.template in ['frequencyAnalyzer', 'stand-by']:
            self.measurementViewer.setLabel('left', "SPL dB")
            _translate = QtCore.QCoreApplication.translate
            self.lbl_Durationinfo.setText(_translate("gui_SLM", duration))
            self.lbl_Projectinfo.setText(_translate("gui_SLM", "<html><head/><body><p align=\"center\">"+projectName+" - Measurement " + counter + "</p></body></html>"))
            self.lblDateinfo.setText(_translate("gui_SLM", "DD/MM/AA - Hr:Min:Sec"))
            self.lblTemplateInfo.setText(_translate("gui_SLM", "<html><head/><body><p align=\"center\">"+template+"</p></body></html>"))
            self.lbl_L90.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">90</span></p></body></html>"))
            self.lbl_Lmin.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">"+fweighting+"min,"+tweighting+"</span></p></body></html>"))
            self.unity_L10.setText(_translate("gui_SLM", " dB"))
            self.value_Lmax.setText(_translate("gui_SLM", "--.--"))
            self.unity_L90.setText(_translate("gui_SLM", " dB"))
            self.value_LAE.setText(_translate("gui_SLM", "--.--"))
            self.value_Leq.setText(_translate("gui_SLM", "--.--"))
            self.unity_Lpeak.setText(_translate("gui_SLM", " dB"))
            self.lbl_Lpeak.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">peak</span></p></body></html>"))
            self.lbl_Leq.setText(_translate("gui_SLM", "<html><head/><body><p>L<span style=\" vertical-align:sub;\">"+fweighting+","+tweighting+"</span></p></body></html>"))
            self.value_L90.setText(_translate("gui_SLM", "--.--"))
            self.value_Lpeak.setText(_translate("gui_SLM", "--.--"))
            self.unity_LAE.setText(_translate("gui_SLM", " dB"))
            self.unity_Leq.setText(_translate("gui_SLM", "dB"))
            self.lbl_Lmax.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">"+fweighting+"max,"+tweighting+"</span></p></body></html>"))
            self.lbl_L10.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">10</span></p></body></html>"))
            self.value_Lmin.setText(_translate("gui_SLM", "--.--"))
            self.lbl_LAE.setText(_translate("gui_SLM", "<html><head/><body><p><span style=\" font-size:14pt;\">L</span><span style=\" font-size:14pt; vertical-align:sub;\">AE</span></p></body></html>"))
            self.value_L10.setText(_translate("gui_SLM", "--.--"))
            self.unity_Lmin.setText(_translate("gui_SLM", " dB"))
            self.unity_Lmax.setText(_translate("gui_SLM", " dB"))
        return

#%%
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    startSLM = setSLM()
    app.exec_()