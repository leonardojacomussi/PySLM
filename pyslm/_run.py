from PyQt5 import QtWidgets
import pyslm
import sys

def run():
    application = QtWidgets.QApplication(sys.argv)
    pyslm.setSLM()
    print('*************** PySLM was started! ***************\n')
    sys.exit(application.exec_())
    print('***************** PySLM has ended! ****************')
    return

if __name__ == "__main__":
    run()