from PyQt5 import QtWidgets
import pyslm
import sys

def AdvFreqAnalyzer():
    application = QtWidgets.QApplication(sys.argv)
    start = pyslm.setSLM()
    print('*************** PySLM.AdvFreqAnalyzer was started! ***************\n')
    sys.exit(application.exec_())
    print('***************** PySLM.AdvFreqAnalyzer has ended! ****************')
    return start

def DataLogger():
    application = QtWidgets.QApplication(sys.argv)
    start = pyslm.setSLM2()
    print('*************** PySLM.DataLogger was started! ***************\n')
    sys.exit(application.exec_())
    print('***************** PySLM.DataLogger has ended! ****************')
    return start

if __name__ == "__main__":
    # DataLogger()
    AdvFreqAnalyzer()