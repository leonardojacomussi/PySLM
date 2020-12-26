import numpy as np
import platform
import datetime
import h5py
import os

"""
Reference:
----------
[1] https://sigmoidal.ai/hdf5-armazenamento-para-deep-learning/
[2] https://www.christopherlovell.co.uk/blog/2016/04/27/h5py-intro.html
"""


class storage(object):
    def __init__(self, buffer_size: int, shape: tuple, path: str, kind: str = 'SPL'):
        today = datetime.datetime.now()
        today = today.strftime("%d-%m-%Y")
        if platform.system().lower() == 'windows':
            bar = '\\'
        else:
            bar = '/'
        if kind.upper() == 'SPL':
            name_date = '{} SPL measurement '.format(today)
        else:
            name_date = '{} RT measurement '.format(today)
        if not os.path.isdir(path):
            os.mkdir(path)
        self.fname = path + bar + name_date + '001.xlsx'
        _, self.fname = self.counter(self.fname)
        self.dataBase = h5py.File(self.fname, 'w')
        self.data = self.dataBase.create_dataset(
            "recSignal", shape=shape, dtype='float')
        # Definir o buffer e índice da próxima linha disponível
        self.buffer_size = buffer_size
        self.buffer = {"signal": []}
        self.idx = 0

    def add(self, frameData):
        self.buffer["signal"].extend(frameData)
        if len(self.buffer["signal"]) >= self.buffer_size:
            self.flush()
        return

    def flush(self):
        """Reseta o buffer e escreve os dados no disco."""
        i = self.idx + len(self.buffer["signal"])
        self.data[self.idx:i] = self.buffer["signal"]
        self.idx = i
        self.buffer = {"signal": []}
        return

    def close(self):
        if len(self.buffer["signal"]) > 0:
            self.flush()
        self.dataBase.close()
        return

    def counter(self, fname: str):
        if os.path.isfile(fname):
            new_name = fname
            count = 1
            while os.path.isfile(new_name):
                new_name = new_name.replace('.xlsx', '')
                new_name = new_name[:-3] + '%03i.xlsx' % count
                count += 1
        else:
            new_name = fname
        new_name = new_name.replace('.xlsx', '')
        name = new_name[:-3]
        count = int(new_name[-3:])
        return str(count), "%s(raw data) %03i.h5"%(name, count)


# %%
if __name__ == '__main__':
    from time import sleep
    fs = 48000
    duration = 15
    path = os.getcwd()
    numSamples = int(fs*duration)
    shape = (numSamples, 1)
    array = np.random.random(size=shape)
    database = storage(buffer_size=fs*60, shape=shape, path=path, kind='SPL')
    # range(start, stop, step)
    count = 0
    for i in range(0, numSamples, fs):
        database.add(array[i: i+fs])
        if count > 300:
            count = 0
            sleep(1)
        count += fs*5
    database.close()

    data = h5py.File(database.fname, 'r')
    load_array = np.asarray(data.get("recSignal"))
    print(np.sum(array - load_array))
    data.close()
