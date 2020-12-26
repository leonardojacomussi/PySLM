import os
import pickle
import numpy as np
import sounddevice as sd
import pyslm

path_code = os.path.dirname(os.path.realpath(pyslm.__file__))

if os.path.isdir(os.path.expanduser("~/Desktop")):
    pathDefault = os.path.expanduser("~/Desktop")
else:
    pathDefault = os.getcwd()

params = {#Measurement
          'version': 'AdvFreqAnalyzer',
          'template':  'frequencyAnalyzer',
          'b': 1,
          'fstart': 63.0,
          'fend': 16000.0,
          'duration': 30,
          'fweighting': 'A',
          'tau': 0.125,
          'method': 'pinkNoise',
          'excitTime': 10,
          'scapeTime': 3,
          'decayTime': 7,
          'numDecay': 3,
          'TLevel': 76,
          #Calibration
          'pCalib': 94,
          'fCalib': 1000,
          'calibFactor': 1.0,
          'corrFactor': 1.0,
          'sensitivity': 1.0,
          #Projects
          'saveRawData': True,
          'currentProject': 'First project',
          'pathProject': pathDefault,
          #Spectrum correction
          'micCorrFile': None,
          'micCorr': None,
          'applyMicCorr': False,
          'adcCorrFile': None,
          'adcCorr': None,
          'applyAdcCorr': False,
          #Device
          'device': [sd.default.device[0], sd.default.device[1]],
          'inCh': [1],
          'outCh': [1],
          'fs': 44100}

def load():
    if not os.path.isfile(os.path.join(path_code, "parameters.pkl")):
        newfile = open(file = os.path.join(path_code, "parameters.pkl"), mode = 'wb')
        pickle.dump(params, newfile)
        newfile.close()
    else:
        pass
    file = open(os.path.join(path_code, "parameters.pkl"), "rb")
    parameters = pickle.load(file)
    file.close()
    return parameters

def update(dictParams):
    newfile = open(file = os.path.join(path_code, "parameters.pkl"), mode = 'wb')
    pickle.dump(dictParams, newfile)
    newfile.close()
    file = open(os.path.join(path_code, "parameters.pkl"), "rb")
    parameters = pickle.load(file)
    file.close()
    return parameters
