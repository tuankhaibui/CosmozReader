import struct,datetime,sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

__author__ = "Koji Ishidoshiro <koji@awa.tohoku.ac.jp>"
__status__ = "Prototype"
# __version__ = "0.0.1" ### Koji 
# __version__ = "0.0.2" ### Khai Fix some typos
__version__ = "0.1.0" ### Khai added some functions
__date__    = "2022,04,07"



class CZ_handler():
    def __init__(self,filename):
        self.filename = filename
        print(f'now processing {filename}')
        self.run_number = filename.split('run')[1].split('.')[0]
        self.cz_file = open(filename,'rb')
        self.log_file = open('run_log', 'r')
        self.ReadLogBook()
        self.file_header =self.cz_file.read(1024)
        self.header_magic =  hex(int(self.file_header[1] << 8)+ int(self.file_header[0]))        
        self.unixtime_start = datetime.datetime.fromtimestamp(int(self.file_header[11] << 24) + int(self.file_header[10] << 16) + int(self.file_header[9] << 8)  + int(self.file_header[8] ))
        self.unixtime_stop = datetime.datetime.fromtimestamp(int(self.file_header[15] << 24) + int(self.file_header[14] << 16) + int(self.file_header[13] << 8)  + int(self.file_header[12] ))
        self.triginfo = int(self.file_header[27] << 24) + int(self.file_header[26] << 16) + int(self.file_header[25] << 8)  + int(self.file_header[24])
        self.adctrig = int(self.file_header[323] << 24) + int(self.file_header[322] << 16) + int(self.file_header[321] << 8)  + int(self.file_header[320])

        
    def checkMagic(self):
        print ('*********************Mode********************')
        if self.header_magic == '0x20c5': # Magic Number
            print ('Raw data')
        elif self.header_magic == '0x21c5': # Magic Number
            print ('Low rate pulse data')
        else:
            print ('Not CZ file header')
            sys.exit()

    def showHeader(self):
        print ('*********************HEADER********************')
        print ('Magic number = {}'.format(self.header_magic))
        print ('Numer of boards = {}'.format(self.file_header[7]))
        print ('trig info = {}'.format(self.triginfo))
        print ('adc info = {}'.format(self.triginfo))
        print ('Start time {}'.format(self.unixtime_start))
        print ('Stop time  {}'.format(self.unixtime_stop))

    def dataLoad(self):
        self.file_hdata =self.cz_file.read(128)
        self.magic_number_data = hex(int(self.file_hdata[1] << 8)+ int(self.file_hdata[0]))

        if self.magic_number_data != '0xc0c5':
            print ('Data magic number {} should be 0xc0c5'.format(self.magic_number_data))
            sys.exit()
            pass

        self.fpga_timestamp = int(self.file_hdata[7] << 40) + int(self.file_hdata[6] << 32) + int(self.file_hdata[5] << 24) + int(self.file_hdata[4] << 16) + int(self.file_hdata[3] << 8)+ int(self.file_hdata[2])

        
        self.data_length = int(self.file_hdata[9] << 8)  + int(self.file_hdata[8] )
        self.eventcount = int(self.file_hdata[95] << 24) + int(self.file_hdata[94] << 16) + int(self.file_hdata[93] << 8)  + int(self.file_hdata[92] )

        self.ch1_pedestal = int(self.file_hdata[21] << 8)+ int(self.file_hdata[20])
        self.ch2_pedestal = int(self.file_hdata[23] << 8)+ int(self.file_hdata[22])
        self.ch3_pedestal = int(self.file_hdata[25] << 8)+ int(self.file_hdata[24])
        self.ch4_pedestal = int(self.file_hdata[27] << 8)+ int(self.file_hdata[26])

    def showDataHeader(self):
        print ('******************DATA HEADER******************')
        print ('FPGA timestamp = {}'.format(self.fpga_timestamp))
        print ('Data length = {}'.format(self.data_length))
        print ('ch1 pedestal = {}'.format(self.ch1_pedestal))
        print ('ch2 pedestal = {}'.format(self.ch2_pedestal))
        print ('ch3 pedestal = {}'.format(self.ch3_pedestal))
        print ('ch4 pedestal = {}'.format(self.ch4_pedestal))
        print ('eventcount = {}'.format(self.eventcount))

    def setWaveformLength(self,waveformLength):
        self.waveformLength = waveformLength
        
    def waveformLoad(self,waveform_analysis):

        pedestalList = []
        pedestalList2 = []
        eventtimeList = []
        waveformList = []
        lengthList = []
        for n_num in range(self.eventcount):
            if n_num%1000 == 0:
                print(f'loaded {n_num}/{self.eventcount} events [{100*n_num/self.eventcount:2.2f}% in run#{self.run_number}]')
            f_data = 0
            while f_data == 0:
                event_data =self.cz_file.read(2)
                event_header = int(event_data[1]<<8) + int(event_data[0])
                if event_header == 1:
                    f_data = 1
                    pass
            
            event_data =self.cz_file.read(22)
            length = int(event_data[1]<<8) + int(event_data[0])
            eventtime = int(event_data[7]<<40) + int(event_data[6]<<32) + int(event_data[5]<<24) + int(event_data[4]<<16) + int(event_data[3]<<8) + int(event_data[2])
            pulseheight = int(event_data[9]<<8) + int(event_data[8])
            pulsearea = int(event_data[13]<<24) + int(event_data[12]<<16) + int(event_data[11]<<8) + int(event_data[10])
            pedestal = int(event_data[15]<<8) + int(event_data[14])

            waveform = []
            for line in range(length):
                event_data =self.cz_file.read(2)
                #tList.append(line)
                waveform.append(int(event_data[1]<< 8) + int(event_data[0]))
                #vList.append(int(event_data[1]<< 8) + int(event_data[0]))
                pass

            waveform = np.array(waveform)
            pedestal2 = np.mean(waveform[1:15])
            if length == self.waveformLength and waveform_analysis == 1:
            #if waveform_analysis == 1:
                eventtimeList.append(eventtime)
                pedestalList.append(pedestal)
                lengthList.append(length)
                pedestalList2.append(pedestal2)
                # print(eventtime, pedestal, pedestal2)
                if len(waveformList)==0:
                    waveformList = waveform
                else:
                    waveformList = np.vstack([waveformList,waveform])
                    pass
                pass
            else:
                print ('Strange event length: Ev={}'.format(n_num))
            pass


        self.pedestalList = pedestalList
        self.pedestalList2 = pedestalList2
        self.eventtimeList = eventtimeList
        self.waveformList = waveformList
        self.waveformList_org = np.copy(self.waveformList)
        self.lengthList = lengthList
        
    def drawWaveform(self,drawevent):
        if drawevent > self.eventcount:
            print('Draw event number should be smaller than {}'.format(self.eventcount))
        else:
            vList = self.waveformList[drawevent]
            tList = np.arange(1,len(vList),1)
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.plot(tList,vList[1:])
            plt.show()  

    def pedestalSubtraction(self):
        for line in range(len(self.pedestalList)):
            self.waveformList[line]=self.waveformList[line]-self.pedestalList[line]
            
    def makeAmplitude(self):
        ampList = []
        for line in range(len(self.pedestalList)):
            ampList.append(np.max(self.waveformList[line][1:]))
            pass
        self.ampList = np.array(ampList)

    def makeArea(self):
        areaList = []
        for line in range(len(self.pedestalList)):
            areaList.append(np.sum(self.waveformList[line][1:]))
            pass
        self.areaList = np.array(areaList)

    def getAmp(self):
        return self.ampList

        
    def getArea(self):
        return self.areaList

    def getLength(self):
        return self.lengthList

    def getWaveform(self):
        return self.waveformList

    def getPedestal(self):
        return self.pedestalList
            
    def ReadLogBook(self):
        lines = self.log_file.readlines()
        lines = lines[13:]
        runlist = []
        detector = []
        runtype = []
        source = []
        duration = []
        runcheck = -1
        self.source = 'N/A'
        for i,line in enumerate(lines):
            runlist += [line.split(':')[0].split('run')[-1]]
            detector += [line.split(':')[-1].split(', ')[0]]
            runtype += [line.split(':')[-1].split(', ')[1]]
            source += [line.split(':')[-1].split(', ')[2]]
            duration += [line.split(':')[-1].split(', ')[3].split('\n')[0]]
            if line.find(f'run{self.run_number}')!=-1:
                print(f'found {self.run_number} in log book at line #{i+6}')
                self.source = source[-1]
                runcheck = line.find(f'run{self.run_number}')
        if runcheck==-1:
            print(f'cannot find {self.run_number} in log book')

    # def CleanUpWaveform(self):
    #     #FIX ME: could not broadcast input array from shape (210,) into shape (211,)
    #     #the first data of waveform looks like a fault, so delete it
    #     for i,wf in enumerate(self.waveformList): 
    #         print(len(wf))
    #         wf = np.delete(wf, 0)
    #         self.waveformList[i] = np.delete(self.waveformList[i], 0)  #np.copy(wf)
    #         print(len(self.waveformList[i]))
    #     # for i in range(len(self.waveformList)):
    #     #     self.waveformList[i] = np.delete(self.waveformList[i], 0)
    #     #     self.waveformList_org[i] = np.delete(self.waveformList_org[i], 0)
    
    def MakeDataFrame(self):
        # self.CleanUpWaveform()
        df = pd.DataFrame(list(zip(list(np.full(len(self.pedestalList), self.run_number)),
                                   list(np.full(len(self.pedestalList), self.unixtime_start)),
                                   list(np.full(len(self.pedestalList), self.unixtime_stop)),
                                   list(np.full(len(self.pedestalList), self.source)),
                                   list(range(len(self.pedestalList))),
                                   self.eventtimeList,
                                   self.pedestalList,
                                   self.pedestalList2,
                                   self.ampList, 
                                   self.areaList, 
                                   self.waveformList,
                                   self.waveformList_org,
                                  )),
                          columns =['RunNumber',
                                    'UnixTimeStart',
                                    'UnixTimeStop',
                                    'Source', 
                                    'EventID', 
                                    'Timestamp', 
                                    'Pedestal',
                                    'Pedestal2',
                                    'Amplitude', 
                                    'Area', 
                                    'Waveform',
                                    'Waveform_org',
                                   ])
        return df
    
if __name__ == '__main__':
    filename = "data/run017.dat"
    CZ=CZ_handler(filename)
    #CZ.checkMagic()
    CZ.showHeader()
    CZ.dataLoad()
    #CZ.showDataHeader()
    CZ.waveformLoad()
    CZ.pedestalSbtraction()
    CZ.makeArea()
    areaList1 = CZ.getArea()
    #CZ.DrawWaveform(1)

    filename = "data/run003.dat"
    CZ=CZ_handler(filename)
    #CZ.checkMagic()
    CZ.showHeader()
    CZ.dataLoad()
    #CZ.showDataHeader()
    CZ.waveformLoad()
    CZ.pedestalSbtraction()
    CZ.makeArea()
    areaList2 = CZ.getArea()
    #CZ.DrawWaveform(1)

    filename = "data/run004.dat"
    CZ=CZ_handler(filename)
    #CZ.checkMagic()
    CZ.showHeader()
    CZ.dataLoad()
    #CZ.showDataHeader()
    CZ.waveformLoad()
    CZ.pedestalSbtraction()
    CZ.makeArea()
    areaList3 = CZ.getArea()
    #CZ.DrawWaveform(1)

    a1_hist, a_bins = np.histogram(areaList1,range=(0,600000),bins=100)
    a2_hist, a_bins = np.histogram(areaList2,range=(0,600000),bins=100)
    a3_hist, a_bins = np.histogram(areaList3,range=(0,600000),bins=100)

    X = []
    for i in range(1, len(a_bins)):
        X.append((a_bins[i-1]+a_bins[i])/2)
        pass
    
    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.plot(X,a1_hist/6,label="BG")
    ax.plot(X,a2_hist,label="252Cf")
    ax.plot(X,a2_hist - a1_hist/6, label="252Cf - BG")
    plt.legend()
    ax = fig.add_subplot(212)
    ax.plot(X,a1_hist/6,label="BG")
    ax.plot(X,a3_hist,label="60Co")
    ax.plot(X,a3_hist - a1_hist/6, label="60Co - BG")
    plt.legend()
    

    plt.show()