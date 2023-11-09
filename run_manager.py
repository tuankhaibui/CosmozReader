import struct,datetime,sys,os, glob

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

class RunManager():
    def __init__(self):
        self.runnumber = []
        
        self.detector = []
        self.runtype = []
        self.source = []
        self.duration = []
        
        self.unixtime_start = []
        self.unixtime_stop = []
        self.n_boards = []

        self.header_magic_ref = '0x21c5'
        self.magic_number_ref = '0xc0c5'
        self.rawdata_dir = r'/mnt/c/Users/tuank/OneDrive - kekdx/LowMassDM/KamiokaCryo/BKG_MiniLAND_rawdata/'
        self.runlog = 'run_log'
    
    def GetRunList_FromDir(self):
        print(f'get run list from rawdata dir {self.rawdata_dir}')
        self.filename = glob.glob(self.rawdata_dir+'run*.dat')
        runnumber = []
        for filename in self.filename:
            runnumber += [int(filename.split(f'{self.rawdata_dir}run')[1].split('.dat')[0])]
        return np.array(runnumber, dtype=np.int64)
    
    def GetRunList_FromLog(self):
        print(f'get run list from log file {self.runlog}')
        logfile = open(self.runlog, 'r')
        lines = logfile.readlines()
        lines = lines[13:]
        
        runnumber = []
        for i,line in enumerate(lines):
            runnumber += [int(line.split(':')[0].split('run')[-1])]
        logfile.close()
        return np.array(runnumber, dtype=np.int64)
    
    def GetFullRunList(self):
        print('*** merge full run list')
        runlist1 = self.GetRunList_FromDir()
        runlist2 = self.GetRunList_FromLog()
        self.runnumber = np.unique(np.concatenate((runlist1, runlist2), axis=0))

    def _GetRunInfo_(self, filename):
        cz_file = open(filename,'rb')
        file_header =cz_file.read(1024)
        header_magic =  hex(int(file_header[1] << 8)+ int(file_header[0]))
        if header_magic != self.header_magic_ref:
            print(f'wrong header magic: {header_magic} (should be {self.header_magic_ref})')
            sys.exit()
        
        file_hdata =cz_file.read(128)
        magic_number_data = hex(int(file_hdata[1] << 8)+ int(file_hdata[0]))
        if magic_number_data != self.magic_number_ref:
            print(f'wrong magic_number: {magic_number_data} (should be {self.magic_number_ref})')
            sys.exit()
        
        cz_file.close()
        return file_header, file_hdata

    def GetRunInfo(self):
        print('*** get run info from rawdata')
        print(self.filename)
        unixtime_start = []
        unixtime_stop = []
        n_boards = []
        for runnumber in self.runnumber:
            filename = self.rawdata_dir+f'run{runnumber:03d}.dat'
            
            if os.path.exists(filename)==False:
                unixtime_start += ['NaT']
                unixtime_stop += ['NaT']
                n_boards += ['NaN']
                continue
            
            print(f'get headers from {filename}')
            file_header, file_hdata = self._GetRunInfo_(filename)
            unixtime_start += [datetime.datetime.fromtimestamp(int(file_header[11] << 24) + int(file_header[10] << 16) + int(file_header[9] << 8)  + int(file_header[8]))]
            unixtime_stop  += [datetime.datetime.fromtimestamp(int(file_header[15] << 24) + int(file_header[14] << 16) + int(file_header[13] << 8)  + int(file_header[12]))]
            n_boards += [file_header[7]]
            # want some more info?
            # self.fpga_timestamp = int(file_hdata[7] << 40) + int(file_hdata[6] << 32) + int(file_hdata[5] << 24) + int(file_hdata[4] << 16) + int(file_hdata[3] << 8)+ int(file_hdata[2])
            # self.data_length = int(file_hdata[9] << 8)  + int(file_hdata[8] )
            # self.eventcount = int(file_hdata[95] << 24) + int(file_hdata[94] << 16) + int(file_hdata[93] << 8)  + int(file_hdata[92] )
            # self.ch1_pedestal = int(file_hdata[21] << 8)+ int(file_hdata[20])
            # self.ch2_pedestal = int(file_hdata[23] << 8)+ int(file_hdata[22])
            # self.ch3_pedestal = int(file_hdata[25] << 8)+ int(file_hdata[24])
            # self.ch4_pedestal = int(file_hdata[27] << 8)+ int(file_hdata[26])
        print('*** store unixtime_start, unixtime_stop, and n_boards')
        print('*** other info (fpga_timestamp, data_length, eventcount, pedestals): can be added from GetRunInfo() in run_manager.py')
        self.unixtime_start = np.array(unixtime_start, dtype=np.datetime64)
        self.unixtime_stop = np.array(unixtime_stop, dtype=np.datetime64)
        self.n_boards = np.array(n_boards, dtype=np.float64)

        # print(self.unixtime_start)
        print('unixtime_start is ')
        print(unixtime_start)

    def ReadLogBook(self):
        print(f'*** now check info (detector, runtype, source, note) from logfile {self.runlog}')
        logfile = open(self.runlog, 'r')
        lines = logfile.readlines()
        lines = lines[13:]
        
        runid = []
        detector = []
        runtype = []
        source = []
        duration = []
        note = []
        for i,line in enumerate(lines):
            runid += [int(line.split(':')[0].split('run')[-1])]
            detector += [line.split(':')[-1].split(', ')[0]]
            runtype += [line.split(', ')[1]]
            source += [line.split(', ')[2]]
            duration += [int(line.split('length ')[1].split('s')[0])]
            str_ = line.split(', ')[4:]
            if str_:
                str_[-1] = str_[-1][:-1]
                str_ = ', '.join(str_)
                note += [str_]
            else:
                note += ['NaN']
        df = pd.DataFrame(list(zip(runid,
                                   detector,
                                   runtype,
                                   source, 
                                   duration, 
                                   note
                                  )),
                          columns =['runnumber',
                                    'detector',
                                    'runtype',
                                    'source', 
                                    'duration [s]', 
                                    'note', 
                                   ])
        return df
    
    def MakeDataFrame(self):
        self.detector = np.full(self.runnumber.shape, float("NaN"))
        self.runtype  = np.full(self.runnumber.shape, float("NaN"))
        self.source   = np.full(self.runnumber.shape, float("NaN"))
        self.duration = np.full(self.runnumber.shape, float("NaN"))
        self.note     = np.full(self.runnumber.shape, float("NaN"))
        
        df = pd.DataFrame({'runnumber': self.runnumber, 
                           'detector' : self.detector,
                           'runtype'  : self.runtype,
                           'source'   : self.source,
                           # 'duration [s]' : self.duration,
                           'note'     : self.note,
                          })
        
        _df = self.ReadLogBook()
        for i in range(len(_df)):
            index = df.index[df.runnumber==_df.runnumber[i]].to_list()[0]
            df.loc[index] = _df.iloc[i]
        
        df['unixtime_start'] = self.unixtime_start
        df['unixtime_stop'] = self.unixtime_stop

        for i in range(len(df)):
            if pd.isnull(df['unixtime_start'][i])==False:
                self.duration[i] = (df['unixtime_stop'][i].to_pydatetime() - df['unixtime_start'][i].to_pydatetime()).total_seconds()
            else:
                self.duration[i] = float('NaN')
        df['duration [s]'] = self.duration
        df['n_boards'] = self.n_boards
        
        return df

def main():
    runmanager = RunManager()
    runmanager.GetFullRunList()
    runmanager.GetRunInfo()
    df = runmanager.MakeDataFrame()
    pkldata_dir = './'
    pkl_name = pkldata_dir + f'run_summary.pkl' 
    df.to_pickle(pkl_name)
    print(f'run summary is stored at {pkl_name}')

if __name__ == "__main__":
    main()