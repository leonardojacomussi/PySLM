import soundfile as sf
import numpy as np
import xlsxwriter
import pyslm
import h5py
import os

def save(params: dict, results: dict, timestamp: dict, file_name: str):
    # Saving raw data to a .wav file
    if params['saveRawData']:
        RawData = h5py.File(name=file_name, mode='r')
        audio = np.asarray(RawData.get('recSignal'))
        file_audio = file_name.replace(".h5", ".wav")
        if params['template'] != 'reverberationTime':
            sf.write(file=file_audio, data=audio[int(0.15*params['fs']):results['framesRead']], samplerate=params["fs"])
        else:
            sf.write(file=file_audio, data=audio, samplerate=params["fs"])
    else:
        file_audio = None
    file_name = (file_name.replace("(raw data) ", "")).replace(".h5", ".xlsx")

    if params['version'] == 'AdvFreqAnalyzer':
        if params['template'] != 'reverberationTime':
            # Time vector
            time = np.arange(results['Lglobal'].size) * params['tau']

        # time weighting string
        if params['tau'] == 0.035:
            strTau = 'Impulse'
        elif params['tau'] == 0.125:
            strTau = 'Fast'
        else:
            strTau = 'Slow'
        # Frequencies labels
        freq = {20.: '20', 25.: '25', 31.5: '31.5', 40.: '40', 50.: '50', 63. :'63', 80.: '80', 100.: '100', 125.: '125',
                160.: '160', 200.: '200', 250.: '250', 315.: '315', 400.: '400', 500.: '500', 630.: '630', 800.: '800',
                1000.: '1k', 1250.: '1.25k', 1600.: '1.6k', 2000.: '2k', 2500.: '2.5k', 3150.: '3.15k', 4000.: '4k',
                5000.: '5k', 6300.: '6.3k', 8000.: '8k', 10000.: '10k', 12500.: '12.5k', 16000.: '16k', 20000.: '20k'}
        strBands = list()
        for i in range(results['bands'].size):
            if results['bands'][i] in freq.keys():
                strBands.append(freq[results['bands'][i]])

        # Creating the spreadsheet
        workbook = xlsxwriter.Workbook(file_name)
        bold = workbook.add_format({'bold': True})
        sheetResults = workbook.add_worksheet(name="Results")
        sheetSetup      = workbook.add_worksheet(name="Settings")

        # Formatting templates
        formatSection = workbook.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#7030a0'})
        formatInformationT = workbook.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCCC'})

        # Save data for Adv. Frequency Analyzer template
        if params['template'] == 'frequencyAnalyzer':
            # Measurement parameters (sheet Setup)
            sheetSetup.set_column(0,0,30,bold)
            sheetSetup.merge_range(0,0,0,10, 'Measurement parameters', formatSection)
            sheetSetup.write("A2", "Version of software", bold);              sheetSetup.write("B2", "Advanced Frequency Analyzer")
            sheetSetup.write("A3", "Template", bold);                         sheetSetup.write("B3", "Frequency Analyzer")
            sheetSetup.write("A4", "Frequency range", bold);                  sheetSetup.write("B4", '%.2f Hz to %.2f kHz'%(params['fstart'], np.round(params['fend']/1000, 2)))
            sheetSetup.write("A5", "Octave band", bold);                      sheetSetup.write("B5", '1/%d'%params['b'])
            sheetSetup.write("A6", "Duration", bold);                         sheetSetup.write("B6", seconds2HMS(params['duration']))
            sheetSetup.write("A7", "Frequency weighting", bold);              sheetSetup.write("B7", params['fweighting'])
            sheetSetup.write("A8", "Integration time", bold);                 sheetSetup.write("B8", strTau)
            sheetSetup.write("A9", "Sampling rate", bold);                    sheetSetup.write("B9",'%d Hz'%params['fs'])
            sheetSetup.write("A10", "Microphone sensitivity", bold);          sheetSetup.write("B10", '%.2f mV/Pa'%params['sensitivity'])
            sheetSetup.write("A11", "Correction", bold);                      sheetSetup.write("B11", '%.2f dB'%params['corrFactor'])
            sheetSetup.write("A12", "Adjustment factor", bold);               sheetSetup.write("B12", '%.2f'%params['calibFactor'])
            sheetSetup.write("A13", "Reference pressure", bold);              sheetSetup.write("B13", '%d dB'%params['pCalib'])
            sheetSetup.write("A14", "Reference frequency", bold);             sheetSetup.write("B14", '%d Hz'%params['fCalib'])
            sheetSetup.write("A15", "Raw data", bold);                        sheetSetup.write("B15", str(file_audio))
            sheetSetup.write("A16", "Project", bold);                         sheetSetup.write("B16", params['currentProject'])
            sheetSetup.write("A17", "Project path", bold);                    sheetSetup.write("B17", os.path.join(params['pathProject'], params['currentProject']))
            sheetSetup.write("A18", "Microphone correction file", bold);      sheetSetup.write("B18", params['micCorrFile'])
            sheetSetup.write("A19", "Was the mic correction applied?", bold); sheetSetup.write("B19", 'Yes' if params['applyMicCorr']==True else 'No')
            sheetSetup.write("A20", "ADC correction file", bold);             sheetSetup.write("B20", params['adcCorrFile'])
            sheetSetup.write("A21", "Was the ADC correction applied?", bold); sheetSetup.write("B21", 'Yes' if params['applyAdcCorr']==True else 'No')
            sheetSetup.write("A22", "Start of measurement", bold);            sheetSetup.write("B22", timestamp['play'])
            sheetSetup.write("A23", "End of measurement", bold);              sheetSetup.write("B23", timestamp['stop'])

            # Results (sheet Results) 
            # Frequency Analysis
            if params['b'] == 1:
                sheetResults.merge_range(0,0,0,2*results['bands'].size, 'Frequency Analysis', formatSection)
            else:
                sheetResults.merge_range(0,0,0,results['bands'].size, 'Frequency Analysis', formatSection)
            sheetResults.set_column(0,0,15,bold)
            sheetResults.set_row(0,15,bold)
            sheetResults.write("A2", "Frequency Hz", formatInformationT)
            sheetResults.write("A3", "L{},{},Min       dB".format(params['fweighting'], strTau[0]), formatInformationT)
            sheetResults.write("A4", "L{},{},Max      dB".format(params['fweighting'], strTau[0]), formatInformationT)
            sheetResults.write("A5", "L{}eq,{}           dB".format(params['fweighting'], strTau[0]), formatInformationT)
            for i in range(len(strBands)):
                sheetResults.write(1, i+1, strBands[i])
                sheetResults.write(2, i+1, results['L_min_bands'][i])
                sheetResults.write(3, i+1, results['L_max_bands'][i])
                sheetResults.write(4, i+1, results['Leq_bands'][i])

            # Bar graphs
            plotOctave = workbook.add_chart({'type': 'column'})
            plotOctave.add_series({
                'name': ['Results', 2,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 2,1,2,results['bands'].size]
                })
            plotOctave.add_series({
                'name': ['Results', 3,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 3,1,3,results['bands'].size]
                })
            plotOctave.add_series({
                'name': ['Results', 4,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 4,1,4,results['bands'].size]
                })
            plotOctave.set_title({'name': 'Sound pressure level measured in 1/%d octave bands'%params['b']})
            plotOctave.set_x_axis({'name': 'Frequency Hz'})
            plotOctave.set_y_axis({'name': 'Level dB'})
            # plotOctave.set_style(15)
            if params['b'] == 1:
                sheetResults.insert_chart(5,2, plotOctave, {'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 1.4})
            else:
                sheetResults.insert_chart(5,2, plotOctave, {'x_offset': 0, 'y_offset': 0, 'x_scale': 4, 'y_scale': 1.4})

            # Time Analysis
            # sheetResults.set_column(1,1,15)
            if params['b'] == 1:
                sheetResults.merge_range(27,0,27,2*results['bands'].size, 'Time Analysis', formatSection)
            else:
                sheetResults.merge_range(27,0,27,results['bands'].size, 'Time Analysis', formatSection)
            sheetResults.merge_range(28,0,29,1,"L{},{}".format(params['fweighting'], strTau[0]), formatInformationT)
            sheetResults.write(30, 0, 'Time         s', formatInformationT)
            sheetResults.write_column(31,0, time)
            sheetResults.write(30, 1, 'Level dB', formatInformationT)
            sheetResults.write_column(31,1, results['Lglobal'])
            # Inline graphics
            plotLine = workbook.add_chart({'type': 'line'})
            plotLine.add_series({
                'name': ['Results', 28,0],
                'categories': ['Results', 31, 0, time.size, 0],
                'values': ['Results', 31, 1, time.size, 1]
                })
            plotLine.set_title({'name': 'Sound pressure level measured in {} weighting'.format(strTau)})
            plotLine.set_x_axis({'name': 'Time s'})
            plotLine.set_y_axis({'name': "L{},{} dB".format(params['fweighting'], strTau[0])})
            # plotLine.set_style(10)
            if params['b'] == 1:
                sheetResults.insert_chart(28, 2, plotLine, {'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 1.5})
            else:
                sheetResults.insert_chart(28, 2, plotLine, {'x_offset': 0, 'y_offset': 0, 'x_scale': 4, 'y_scale': 1.5})
            sheetResults.write("K51", "L{}eq,{}".format(params["fweighting"], strTau[0]), formatInformationT)
            sheetResults.write("K52", "{} dB".format(results["Leq_global"]))
            sheetResults.write("M51", "LAE/SEL", formatInformationT)
            sheetResults.write("M52", "{} dB".format(results["SEL"]))
            sheetResults.write("O51", "Lmax", formatInformationT)
            sheetResults.write("O52", "{} dB".format(results["Lmax"]))
            sheetResults.write("Q51", "Lmin", formatInformationT)
            sheetResults.write("Q52", "{} dB".format(results["Lmin"]))
            sheetResults.write("K54", "Lpeak", formatInformationT)
            sheetResults.write("K55", "{} dB".format(results["Lpeak"]))
            sheetResults.write("M54", "L10", formatInformationT)
            sheetResults.write("M55", "{} dB".format(results["L10"]))
            sheetResults.write("O54", "L50", formatInformationT)
            sheetResults.write("O55", "{} dB".format(results["L50"]))
            sheetResults.write("Q54", "L90", formatInformationT)
            sheetResults.write("Q55", "{} dB".format(results["L90"]))

        else: # Reverberation time
            # Excitement signal labels
            if params['method'] == 'pinkNoise':
                method = "Pink noise"
            elif params['method'] == 'whiteNoise':
                method = "White noise"
            elif params['method'] == 'sweepExponential':
                method = "Sweep exponential"
            else:
                method = "Impulse"
            # Measurement parameters (sheet Setup)
            sheetSetup.set_column(0,0,30,bold)
            sheetSetup.merge_range(0,0,0,10, 'Measurement parameters', formatSection)
            sheetSetup.write("A2", "Version of software", bold);              sheetSetup.write("B2", "Advanced Frequency Analyzer")
            sheetSetup.write("A3", "Template", bold);                         sheetSetup.write("B3", "Reverberation time")
            sheetSetup.write("A4", "Frequency range", bold);                  sheetSetup.write("B4", '%.2f Hz to %.2f kHz'%(params['fstart'], np.round(params['fend']/1000, 2)))
            sheetSetup.write("A5", "Frequency weighting", bold);              sheetSetup.write("B5", params['fweighting'])
            sheetSetup.write("A6", "Integration time", bold);                 sheetSetup.write("B6", strTau)
            sheetSetup.write("A7", "Octave band", bold);                      sheetSetup.write("B7", '1/%d'%params['b'])
            sheetSetup.write("A8", "Excitement signal", bold);                sheetSetup.write("B8", method)
            sheetSetup.write("A9", "Excitation time", bold);                  sheetSetup.write("B9", seconds2MS(params['excitTime']))
            sheetSetup.write("A10", "Decay time", bold);                      sheetSetup.write("B10", "%i s" % params['decayTime'])
            sheetSetup.write("A11", "Number of decays", bold);                sheetSetup.write("B11", "%i" % params['numDecay'])
            sheetSetup.write("A12", "Trigger level", bold);                   sheetSetup.write("B12", "%i dB" % params['numDecay'] if method == 'impulse' else "-- dB")
            sheetSetup.write("A13", "Escape time", bold);                     sheetSetup.write("B14", seconds2MS(params['scapeTime']))
            sheetSetup.write("A14", "Sampling rate", bold);                   sheetSetup.write("B14",'%d Hz'%params['fs'])
            sheetSetup.write("A15", "Microphone sensitivity", bold);          sheetSetup.write("B15", '%.2f mV/Pa'%params['sensitivity'])
            sheetSetup.write("A16", "Correction", bold);                      sheetSetup.write("B16", '%.2f dB'%params['corrFactor'])
            sheetSetup.write("A17", "Adjustment factor", bold);               sheetSetup.write("B17", '%.2f'%params['calibFactor'])
            sheetSetup.write("A18", "Reference pressure", bold);              sheetSetup.write("B18", '%d dB'%params['pCalib'])
            sheetSetup.write("A19", "Reference frequency", bold);             sheetSetup.write("B19", '%d Hz'%params['fCalib'])
            sheetSetup.write("A20", "Raw data", bold);                        sheetSetup.write("B20", str(file_audio))
            sheetSetup.write("A21", "Project", bold);                         sheetSetup.write("B21", params['currentProject'])
            sheetSetup.write("A22", "Project path", bold);                    sheetSetup.write("B22", os.path.join(params['pathProject'], params['currentProject']))
            sheetSetup.write("A23", "Microphone correction file", bold);      sheetSetup.write("B23", params['micCorrFile'])
            sheetSetup.write("A24", "Was the mic correction applied?", bold); sheetSetup.write("B24", 'Yes' if params['applyMicCorr']==True else 'No')
            sheetSetup.write("A25", "ADC correction file", bold);             sheetSetup.write("B25", params['adcCorrFile'])
            sheetSetup.write("A26", "Was the ADC correction applied?", bold); sheetSetup.write("B26", 'Yes' if params['applyAdcCorr']==True else 'No')
            sheetSetup.write("A27", "Start of measurement", bold);            sheetSetup.write("B27", timestamp['play'])
            sheetSetup.write("A28", "End of measurement", bold);              sheetSetup.write("B28", timestamp['stop'])

            # Results (sheet Results) 
            # Reverberation time (EDT, T15, T20, T30)
            if params['b'] == 1:
                sheetResults.merge_range(0,0,0,2*results['bands'].size, 'Reverberation time (EDT, T15, T20, T30)', formatSection)
            else:
                sheetResults.merge_range(0,0,0,results['bands'].size, 'Reverberation time (EDT, T15, T20, T30)', formatSection)
            sheetResults.set_column(0,0,15,bold)
            sheetResults.set_row(0,15,bold)
            sheetResults.write("A2", "Frequency Hz", formatInformationT)
            sheetResults.write("A3", "EDT   s", formatInformationT)
            sheetResults.write("A4", "T15   s", formatInformationT)
            sheetResults.write("A5", "T20   s", formatInformationT)
            sheetResults.write("A6", "T30   s", formatInformationT)
            for i in range(len(strBands)):
                sheetResults.write(1, i+1, strBands[i])
                sheetResults.write(2, i+1, results['EDT'][i])
                sheetResults.write(3, i+1, results['RT15'][i])
                sheetResults.write(4, i+1, results['RT20'][i])
                sheetResults.write(5, i+1, results['RT30'][i])

            # Bar graphs
            plotOctave_RT = workbook.add_chart({'type': 'column'})
            plotOctave_RT.add_series({
                'name': ['Results', 2,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 2,1,2,results['bands'].size]
                })
            plotOctave_RT.add_series({
                'name': ['Results', 3,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 3,1,3,results['bands'].size]
                })
            plotOctave_RT.add_series({
                'name': ['Results', 4,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 4,1,4,results['bands'].size]
                })
            plotOctave_RT.add_series({
                'name': ['Results', 5,0],
                'categories': ['Results', 1,1,0,results['bands'].size],
                'values': ['Results', 5,1,5,results['bands'].size]
                })
            plotOctave_RT.set_title({'name': 'Reverberation time measured in 1/%d octave bands'%params['b']})
            plotOctave_RT.set_x_axis({'name': 'Frequency Hz'})
            plotOctave_RT.set_y_axis({'name': 'Time s'})

            # Definition (D50, D80)
            if params['b'] == 1:
                sheetResults.merge_range(27,0,27,2*results['bands'].size, 'Definition (D50, D80)', formatSection)
            else:
                sheetResults.merge_range(27,0,27,results['bands'].size, 'Definition (D50, D80)', formatSection)
            sheetResults.write("A29", "Frequency Hz", formatInformationT)
            sheetResults.write("A30", "D50   %", formatInformationT)
            sheetResults.write("A31", "D80   %", formatInformationT)
            for i in range(len(strBands)):
                sheetResults.write(28, i+1, strBands[i])
                sheetResults.write(29, i+1, results['D50'][i])
                sheetResults.write(30, i+1, results['D80'][i])

            # Bar graphs
            plotOctave_D = workbook.add_chart({'type': 'column'})
            plotOctave_D.add_series({
                'name': ['Results', 29,0],
                'categories': ['Results', 28,1,28,results['bands'].size],
                'values': ['Results', 29,1,29,results['bands'].size]
                })
            plotOctave_D.add_series({
                'name': ['Results', 30,0],
                'categories': ['Results', 28,1,28,results['bands'].size],
                'values': ['Results', 30,1,30,results['bands'].size]
                })
            plotOctave_D.set_title({'name': 'Definition measured in 1/%d octave bands'%params['b']})
            plotOctave_D.set_x_axis({'name': 'Frequency Hz'})
            plotOctave_D.set_y_axis({'name': 'Definition %'})

            # Clarity (C50, C80)
            if params['b'] == 1:
                sheetResults.merge_range(54,0,54,2*results['bands'].size, 'Clarity (C50, C80)', formatSection)
            else:
                sheetResults.merge_range(54,0,54,results['bands'].size, 'Clarity (C50, C80)', formatSection)
            sheetResults.write("A56", "Frequency Hz", formatInformationT)
            sheetResults.write("A57", "C50   dB", formatInformationT)
            sheetResults.write("A58", "C80   dB", formatInformationT)
            for i in range(len(strBands)):
                sheetResults.write(55, i+1, strBands[i])
                sheetResults.write(56, i+1, results['C50'][i])
                sheetResults.write(57, i+1, results['C80'][i])

            # Bar graphs
            plotOctave_C = workbook.add_chart({'type': 'column'})
            plotOctave_C.add_series({
                'name': ['Results', 56,0],
                'categories': ['Results', 55,1,55,results['bands'].size],
                'values': ['Results', 56,1,56,results['bands'].size]
                })
            plotOctave_C.add_series({
                'name': ['Results', 57,0],
                'categories': ['Results', 55,1,55,results['bands'].size],
                'values': ['Results', 57,1,57,results['bands'].size]
                })
            plotOctave_C.set_title({'name': 'Clarity measured in 1/%d octave bands'%params['b']})
            plotOctave_C.set_x_axis({'name': 'Frequency Hz'})
            plotOctave_C.set_y_axis({'name': 'Clarity dB'})
            if params['b'] == 1:
                sheetResults.insert_chart(6,2, plotOctave_RT, {'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 1.4})
                sheetResults.insert_chart(31,2, plotOctave_D, {'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 1.4})
                sheetResults.insert_chart(58,2, plotOctave_C, {'x_offset': 0, 'y_offset': 0, 'x_scale': 2, 'y_scale': 1.4})
            else:
                sheetResults.insert_chart(6,2, plotOctave_RT, {'x_offset': 0, 'y_offset': 0, 'x_scale': 4, 'y_scale': 1.4})
                sheetResults.insert_chart(31,2, plotOctave_D, {'x_offset': 0, 'y_offset': 0, 'x_scale': 4, 'y_scale': 1.4})
                sheetResults.insert_chart(58,2, plotOctave_C, {'x_offset': 0, 'y_offset': 0, 'x_scale': 4, 'y_scale': 1.4})
    else: # DataLogger
        # Time vector
        time = np.arange(results['Lglobal'].size) * params['tau']

        # Time weighting labels
        if params['tau'] == 0.035:
            strTau = 'Impulse'
        elif params['tau'] == 0.125:
            strTau = 'Fast'
        else:
            strTau = 'Slow'

        # Creating the spreadsheet
        workbook = xlsxwriter.Workbook(file_name)
        bold = workbook.add_format({'bold': True})
        sheetResults = workbook.add_worksheet(name="Results")
        sheetSetup      = workbook.add_worksheet(name="Settings")

        # Formatting templates
        formatSection = workbook.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#7030a0'})
        formatInformationT = workbook.add_format({'bold': True, 'border': 4, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCCC'})

        # Measurement parameters (sheet Setup)
        sheetSetup.set_column(0,0,30,bold)
        sheetSetup.merge_range(0,0,0,10, 'Measurement parameters', formatSection)
        sheetSetup.write("A2", "Version of software", bold);              sheetSetup.write("B2", "Data Logger")
        sheetSetup.write("A3", "Template", bold);                         sheetSetup.write("B3", "Sounud Pressure Level")
        sheetSetup.write("A4", "Duration", bold);                         sheetSetup.write("B4", seconds2HMS(params['duration']))
        sheetSetup.write("A5", "Frequency weighting", bold);              sheetSetup.write("B5", params['fweighting'])
        sheetSetup.write("A6", "Integration time", bold);                 sheetSetup.write("B6", strTau)
        sheetSetup.write("A7", "Sampling rate", bold);                    sheetSetup.write("B7",'%d Hz'%params['fs'])
        sheetSetup.write("A8", "Microphone sensitivity", bold);           sheetSetup.write("B8", '%.2f mV/Pa'%params['sensitivity'])
        sheetSetup.write("A9", "Correction", bold);                       sheetSetup.write("B9", '%.2f dB'%params['corrFactor'])
        sheetSetup.write("A10", "Adjustment factor", bold);               sheetSetup.write("B10", '%.2f'%params['calibFactor'])
        sheetSetup.write("A11", "Reference pressure", bold);              sheetSetup.write("B11", '%d dB'%params['pCalib'])
        sheetSetup.write("A12", "Reference frequency", bold);             sheetSetup.write("B12", '%d Hz'%params['fCalib'])
        sheetSetup.write("A13", "Raw data", bold);                        sheetSetup.write("B13", str(file_audio))
        sheetSetup.write("A14", "Project", bold);                         sheetSetup.write("B14", params['currentProject'])
        sheetSetup.write("A15", "Project path", bold);                    sheetSetup.write("B15", os.path.join(params['pathProject'], params['currentProject']))
        sheetSetup.write("A16", "Microphone correction file", bold);      sheetSetup.write("B16", params['micCorrFile'] if params['micCorrFile'] is not None else 'None')
        sheetSetup.write("A17", "Was the mic correction applied?", bold); sheetSetup.write("B17", 'Yes' if params['applyMicCorr']==True else 'No')
        sheetSetup.write("A18", "ADC correction file", bold);             sheetSetup.write("B18", params['adcCorrFile'] if params['adcCorrFile'] is not None else 'None')
        sheetSetup.write("A19", "Was the ADC correction applied?", bold); sheetSetup.write("B19", 'Yes' if params['applyAdcCorr']==True else 'No')
        sheetSetup.write("A20", "Start of measurement", bold);            sheetSetup.write("B20", timestamp['play'])
        sheetSetup.write("A21", "End of measurement", bold);              sheetSetup.write("B21", timestamp['stop'])

        # Time Analysis
        sheetResults.set_column(0,0,15)
        sheetResults.merge_range(0,0,0,31, 'Time Analysis', formatSection)
        sheetResults.merge_range(1,0,2,1,"L{},{}".format(params['fweighting'], strTau[0]), formatInformationT)
        sheetResults.write(3, 0, 'Time         s', formatInformationT)
        sheetResults.write_column(4,0, time)
        sheetResults.write(3, 1, 'Level dB', formatInformationT)
        sheetResults.write_column(4,1, results['Lglobal'])

        # Inline graphics
        plotLine = workbook.add_chart({'type': 'line'})
        plotLine.add_series({
            'name': ['Results', 1,0],
            'categories': ['Results', 4, 0, time.size, 0],
            'values': ['Results', 4, 1, time.size, 1]
            })
        plotLine.set_title({'name': 'Sound pressure level measured in {} weighting'.format(strTau)})
        plotLine.set_x_axis({'name': 'Time s'})
        plotLine.set_y_axis({'name': "L{},{} dB".format(params['fweighting'], strTau[0])})
        # plotLine.set_style(10)
        sheetResults.insert_chart(1, 2, plotLine, {'x_offset': 0, 'y_offset': 0, 'x_scale': 4, 'y_scale': 1.5})
        sheetResults.write("N25", "L{}eq,{}".format(params["fweighting"], strTau[0]), formatInformationT)
        sheetResults.write("N26", "{} dB".format(results["Leq_global"]))
        sheetResults.write("P25", "LAE/SEL", formatInformationT)
        sheetResults.write("P26", "{} dB".format(results["SEL"]))
        sheetResults.write("R25", "Lmax", formatInformationT)
        sheetResults.write("R26", "{} dB".format(results["Lmax"]))
        sheetResults.write("T25", "Lmin", formatInformationT)
        sheetResults.write("T26", "{} dB".format(results["Lmin"]))
        sheetResults.write("N28", "Lpeak", formatInformationT)
        sheetResults.write("N29", "{} dB".format(results["Lpeak"]))
        sheetResults.write("P28", "L10", formatInformationT)
        sheetResults.write("P29", "{} dB".format(results["L10"]))
        sheetResults.write("R28", "L50", formatInformationT)
        sheetResults.write("R29", "{} dB".format(results["L50"]))
        sheetResults.write("T28", "L90", formatInformationT)
        sheetResults.write("T29", "{} dB".format(results["L90"]))
    workbook.close()
    return

def seconds2MS(seconds): 
    M, S = divmod(seconds, 60) 
    _, M = divmod(M, 60)
    return "%02dm%02ds" % (M, S)

def seconds2HMS(seconds): 
    M, S = divmod(seconds, 60) 
    H, M = divmod(M, 60)
    return "%02dh%02dm%02ds" % (H, M, S)