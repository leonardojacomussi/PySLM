#%%
from scipy.io import savemat, loadmat
from itertools import count
import sounddevice as sd
from time import sleep
import os, platform

# #%% Função para gerar nomes
path_files = r'C:\Users\Leonardo\Desktop\Medição 11_11_2020'
# /home/pi/Documents/Medição 11_11_2020

def generator(path):
    if platform.system().lower() == 'windows':
        bar = '\\'
    else:
        bar = '/'
    if not os.path.isdir(path):
        os.mkdir(path)
    fname = path + bar + 'measurement ' + '001.mat'
    count = 2
    if os.path.isfile(fname):
        new_name = fname
        while os.path.isfile(new_name):
            new_name = new_name.replace('.mat', '')
            idx = len(new_name)
            new_name = new_name[0:idx-3] + '%03i.mat' % count
            count += 1
    else:
        new_name = fname
    return new_name

#%% Parâmetros de entrada
# # print(sd.query_devices())
# indevice = int(input('\nEscolha o dispositivo de áudio: '))

# dev = sd.query_devices()
# fs = int(dev[indevice]['default_samplerate'])
# [indevice, sd.default.device[1]]

dev = sd.query_devices()
device = sd.default.device
indevice = device[0]
fs = int(dev[indevice]['default_samplerate'])

params = {'device': device,
          'numCha': [1],
          'fs': fs,
          'numSamples': int(fs*10)}

#%% loop de gravação
for i in range(2):
    try:
        rec = sd.rec(frames=params['numSamples'],
                    samplerate=params['fs'],
                    channels=len(params['numCha']),
                    dtype='float32',
                    blocking=True)
        
        params['data'] = rec[:,0]
        file = generator(path_files)
        savemat(file_name=file, mdict=params)
        sleep(2)
        print('Medição {} OK!'.format(i+1))
    except Exception as E:
        print("** Erro na medição {} \n{}".format(i+1, E))
print('\n*** FIM DA MEDIÇÃO ***')

# %% Seção de teste de áudio
# med = loadmat(os.path.join(path_files, 'Measurement 003.mat'))
# sd.play(data=med['data'][0,:], samplerate=med['fs'][0,0], device=sd.default.device, blocking=True)
