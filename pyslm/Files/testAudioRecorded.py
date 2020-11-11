import sounddevice as sd
import numpy as np
import h5py

file = r'C:\Users\Leonardo\Desktop\First project\2020-11-08 SPL - RAW DATA - measurement 001.h5'
data = h5py.File(name=file, mode='r')
audio = np.asarray(data.get('recSignal'))

sd.play(data=audio, samplerate=44100, device=[1,3], blocking=True)