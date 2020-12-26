# PySLM
Pythonic Sound Level Meter is a package that contains software for real-time measurement and processing of a sound level meter. There are currently two versions: *Advanced Frequency Analyzer* and *Data Logger*.

The version *Advanced Frequency Analyzer* contains analysis of sound levels in frequency bands and also has a template for measuring and calculating the reverberation time of rooms by the interrupted noise method, proposed by ISO 3382 "*Acoustics - Measurement of room acoustic parameters*". Broadband and time and frequency weighting filters follow the design established by IEC 61620-1:2014 standards "*Electroacoustics - Octave-Band and Fractional-Octave-Band Filters - Part 1: Specifications*" and IEC 61672-1 "*Electroacoustics - Sound level meters - Part 1: Specifications*", in addition to other current standards.

The *Data Logger* version is a simplified version of the *Advanced Frequency Analyzer* version, containing only global levels over time (that is, without analysis in octave bands and without the reverb time template). It is the most suitable version for low performance computers or systems.


## Usage
To start, you can try to run the Advanced Frequency Analyzer version:

    >>> import pyslm
    >>> pyslm.AdvFreqAnalyzer()
    
Or, try running the Data Logger version:

    >>> import pyslm
    >>> pyslm.DataLogger()

## Installation

    >>> pip install git+https://github.com/leonardojacomussi/PySLM@main

## Dependencies
To install dependencies on an embedded system like the Raspberry Pi 4B or Asus Tinker Board and create your own prototype, access this repository for more information.

- Numpy;
- Scipy;
- Matplotlib;
- Sounddevice;
- pyqtgraph;
- PyQt5;
- H5py.

# Contact
- Author: Leonardo Jacomussi
  - [LinkedIn][LinkedIn_Leo]
  - [ResearchGate][ResearchGate_Leo]

# See more
[Dependencies to be installed in embedded systems][sound-level-meter]

[*Raspberry Pi: A Low-cost Embedded System for Sound Pressure Level Measurement*][ArtigoInternoise]

[*Tutorial: configuração de dispositivos de áudio no Raspberry Pi – Parte 1*][Artigo_acustica1]

[*Tutorial: configuração de dispositivos de áudio no Raspberry Pi – Parte 2*][Artigo_acustica2]



[sound-level-meter]: <https://github.com/leonardojacomussi/Sound-Level-Meter>
[ArtigoInternoise]: <https://www.researchgate.net/publication/344435460_Raspberry_Pi_A_Low-cost_Embedded_System_for_Sound_Pressure_Level_Measurement>
[Artigo_acustica1]: <https://www.researchgate.net/publication/345948469_Tutorial_configuracao_de_dispositivos_de_audio_no_Raspberry_Pi_-_Parte_1>
[Artigo_acustica2]: <https://www.researchgate.net/publication/345948561_Tutorial_configuracao_de_dispositivos_de_audio_no_Raspberry_Pi_-_Parte_2>
[LinkedIn_Leo]: <https://www.linkedin.com/in/leonardo-jacomussi-6549671a2>
[ResearchGate_Leo]: <https://www.researchgate.net/profile/Leonardo_Jacomussi_Pereira_De_Araujo>
