from A01_share import CTSP, EPA
import seaborn as sns
import os, re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import seaborn as sns

import matplotlib.dates as mdates

from merge_figure import merge

plt.ion()
plt.close('all')

pd.set_option('display.unicode.east_asian_width',True)
pd.set_option('display.unicode.ambiguous_as_wide',True)

class pathlist():
    def __init__(self):
        path = {}
        path['base'] = os.path.dirname(__file__)
        path['data'] = os.path.join(path['base'], 'data')
        path['list'] = os.path.join(path['base'], 'data', 'datalist')
        self.PATH = path
        self.path = pd.Series(path)


class StaInfo(pathlist):
    def __init__(self):
        super(StaInfo, self).__init__()
        self.info = self.proc()

    def proc(self):
        fn = os.path.join(self.path.data, 'airbox_info.xlsx')
        info = pd.read_excel(fn)[['Site ID', 'Real Address', 'Real GPS']].astype(str)
        info = info.applymap(lambda i: re.sub('巿', '市', i))
        info = info[info['Real Address'].str.contains('區')]
        info['Address'] = info['Real Address'].apply(lambda i : i.split('--')[1])
        info['name'   ] = info['Real Address'].apply(lambda i : i.split('--')[0])
        info['region' ] = info['Address'].apply(lambda i: re.match('.{0,1}臺中市(.*區)', i).groups()[0])
        gps = pd.DataFrame(list(info['Real GPS'].str.split(', ')), index=info.index, columns=['lon', 'lat'])
        info = pd.concat([info, gps], axis=1)
        info = info[['Site ID', 'region', 'name', 'Address', 'lon', 'lat']]
        info = info.rename({'Site ID': 'id'}, axis=1)
        info = info.sort_values(by='region')
        info = info.applymap(lambda i: re.sub('南屯區南屯區', '南屯區', i))
        info.lon = info.lon.astype(float)
        info.lat = info.lat.astype(float)
        return info
       
    def selRegion(self, region):
        info = self.info 
        region = '|'.join(region)
        info = info[info['Address'].str.contains(region)]
        return info

    def byRegion(self):
        info = self.info
        count = info.pivot_table(index='region', aggfunc='count')[['Address']]
        count = count.rename({'Address': '數量'}, axis=1)
        self.count = count
        return count

class dataproc(StaInfo):
    def __init__(self, region):
        super(dataproc, self).__init__()
        self.run(region)

    def run(self, region):
        info = self.selRegion(region)
        print(f' >> 找到 {len(info)} 個測站')
        data = [] 
        data = pd.DataFrame()
        for staid in info.id[:]:
            sta = os.path.join(self.path.list, staid)
            if not os.path.isdir(sta):
                print(f'{sta} does not exist')
            region = info[info.id==staid].iloc[0, 1]
            staname = info[info.id==staid].iloc[0, 2]
            print(f'    >> 測站ID：{staid}, 測站名稱：{staname}, 行政區：{region}')

            files = [os.path.join(sta, i) for i in os.listdir(sta) if 'xls' in i and re.match('^\d.*xlsx',i)]
            dfm = []
            for ifile in files:
                df = pd.read_excel(ifile, header=[0,1,2,3])
                df = df.droplevel([0,1,3], axis=1)
                df = df.rename({'Unnamed: 0_level_2': 'datetime'}, axis=1).set_index('datetime')[['s_d0']]
                df.columns = pd.MultiIndex.from_product([[region],[staname]])
                dfm.append(df)
            dfm = pd.concat(dfm)
            dfm = dfm[~dfm.index.duplicated()] 
            data = pd.concat([data, dfm], axis=1)
        self.dfm = dfm
        data.index = data.index + pd.Timedelta(hours=8)
        self.data = data
        data.to_excel(os.path.join(self.path.data, 'organized', f'data_to_{today}.xlsx'))

class plot(StaInfo):
    def __init__(self):
        super(plot, self).__init__()
        data = self.read()
        #self.plotCorr(data)
        data = self.drop(data, drop)
        self.toRegion(data)
        #self.plotavg()
        #self.plotstd()
        #self.pairComp(self.avg)

        self.compareCTSP()
        #self.run_plotComp()
        #self.mergeComp()
        self.scatterComp()


        self.data = data

    def read(self):
        fn = os.path.join(self.path.data, 'organized', f'data_to_{today}.xlsx')
        df = pd.read_excel(fn, index_col=0, header=[0,1])
        self.df = df 
        return df

    def plotCorr(self, data):
        plt.ion()
        corr = data.corr()
        self.corr = corr

    def drop(self, data, drop):
        drop = [f'臺中市立{i} ' for i in drop]
        columns = pd.MultiIndex.from_tuples([i for i in data.columns if i[1] not in drop])
        data = data[columns]
        return data

    def toRegion(self, data):
        index = pd.date_range(data.index[0], data.index[-1], freq='h')
        tmp = pd.DataFrame(index=index)
        data = data.stack().droplevel(1)
        avg = data.pivot_table(index=data.index)
        std = data.pivot_table(index=data.index, aggfunc=np.nanstd)

        avg = pd.concat([avg, tmp], axis=1).fillna(np.inf)
        std = pd.concat([std, tmp], axis=1).fillna(np.inf)

        self.avg = avg 
        self.std = std

    def plotavg(self):
        sns.set(font_scale=1.3, style='whitegrid')
        months = mdates.MonthLocator()  # every month
        mon_fmt = mdates.DateFormatter('%Y/%m')
        days   = mdates.DayLocator([5, 10, 15, 20, 25])  # every month
        day_fmt = mdates.DateFormatter('%m-%d')
        #ax = sns.lineplot(data=data1, dashes=False, palette=('grey',), linewidth=1) 

        avg = pd.concat([self.avg.iloc[:,1:], self.avg.iloc[:,[0]]], axis=1)
        plt.plot(avg) 
        ax = plt.gca()
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_minor_locator(days)
        ax.xaxis.set_major_formatter(mon_fmt)
        ax.xaxis.set_minor_formatter(day_fmt)

        ax.legend(avg.columns, loc='upper left', bbox_to_anchor=[0,1], ncol=6, frameon=False, facecolor=None)
        #ax.grid(grid_linewith=0.4, linestyle='--')
        plt.gcf().set_size_inches([15, 6])
        plt.subplots_adjust(left=0.05)
        plt.subplots_adjust(right=0.95)
        plt.title('各行政區空氣盒子監測之PM2.5平均濃度', fontsize=16)
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

        figName = os.path.join(self.path.base, 'figure', '行政區時序.png')
        plt.savefig(figName, dpi=300)

    def plotstd(self):
        sns.set(font_scale=1.3, style='whitegrid')
        months = mdates.MonthLocator()  # every month
        mon_fmt = mdates.DateFormatter('%Y/%m')
        days   = mdates.DayLocator([5, 10, 15, 20, 25])  # every month
        day_fmt = mdates.DateFormatter('%m-%d')
        #ax = sns.lineplot(data=data1, dashes=False, palette=('grey',), linewidth=1) 
        plt.plot(self.std) 
        ax = plt.gca()
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_minor_locator(days)
        ax.xaxis.set_major_formatter(mon_fmt)
        ax.xaxis.set_minor_formatter(day_fmt)

        ax.legend(self.std.columns, loc='upper left', bbox_to_anchor=[0,1], ncol=6, frameon=False, facecolor=None)
        ax.grid(linewidth=0.4, linestyle='--')
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        plt.gcf().set_size_inches([15, 6])
        plt.subplots_adjust(left=0.05)
        plt.subplots_adjust(right=0.95)
        plt.title('各行政區空氣盒子監測之PM2.5濃度標準差', fontsize=16)

        figName = os.path.join(self.path.base, 'figure', '行政區時序_標準差.png')
        plt.savefig(figName, dpi=300)

    def pairComp(self, data):
        
        data[data==np.inf] = np.nan
        sns.set(font_scale=.7)
        g = sns.pairplot(data.iloc[:,:], plot_kws=dict(s=10, edgecolor="w", linewidth=0.5))
        g.set(xticks=range(0,70,20), yticks=range(0,70,20), xlim=[0, 70], ylim=[0,70])
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        figName = os.path.join(self.path.base, 'figure', '行政區PM25比較.png')
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        plt.gcf().set_size_inches([10, 10])
        plt.savefig(figName, dpi=300)
        
    def compareCTSP(self):
        TS = self.df.index.min()
        TE = self.df.index.max()
        timeseries = pd.date_range(TS, TE, freq='H')

        TS = TS.strftime('%Y-%m')
        TE = TE.strftime('%Y-%m')
        
        c = CTSP([TS, TE], 'hour', ['PM2.5'])
        ctsp = c.data.droplevel(0, axis=1)
        self.ctsp = ctsp
        self.timeseries = timeseries
        ctsp = ctsp.loc[timeseries, :]

        e = EPA('臺中市', station=['忠明', '沙鹿', '西屯'], TimePeriod=[TS, TE], varName=['PM2.5'], freq='hr')
        epa = e.data.droplevel(1, axis=1)
        epa = epa.loc[timeseries, :]
        self.e = e
        self.c = c
        
        self.ctsp = ctsp
        self.epa = epa


    def run_plotComp(self):
        for ista in self.ctsp.columns[:]:
            name = self.c.staNameE2C[ista] 
            self.plotComp(self.ctsp[ista], name)

        for ista in self.epa.columns[:]:
            name = f'環保署{ista}站'
            self.plotComp(self.epa[ista], name)

    def plotComp(self, data, name):
        plt.close('all')
        sns.set(font_scale=1.3, style='whitegrid')
        months = mdates.MonthLocator()  # every month
        mon_fmt = mdates.DateFormatter('%Y/%m')
        days   = mdates.DayLocator([5, 10, 15, 20, 25])  # every month
        day_fmt = mdates.DateFormatter('%m-%d')
        #ax = sns.lineplot(data=data1, dashes=False, palette=('grey',), linewidth=1) 

        plt.plot(self.avg, color=(.7,.7,.7)) 
        plt.plot(data) 
        ax = plt.gca()
        ax.xaxis.set_major_locator(months)
        ax.xaxis.set_minor_locator(days)
        ax.xaxis.set_major_formatter(mon_fmt)
        ax.xaxis.set_minor_formatter(day_fmt)

        #ax.legend(self.avg.columns, loc='upper left', bbox_to_anchor=[0,1], ncol=6, frameon=False, facecolor=None)
        #ax.grid(grid_linewith=0.4, linestyle='--')
        plt.gcf().set_size_inches([15, 6])
        plt.subplots_adjust(left=0.05)
        plt.subplots_adjust(right=0.95)
        plt.title(f'{name} 與 空氣盒子監測之PM2.5平均濃度比較', fontsize=16)
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

        figName = os.path.join(self.path.base, 'figure', f'濃度比較_{name}.png')
        plt.savefig(figName, dpi=300)
        
    def mergeComp(self):
        basepath = os.path.join(self.path.base, 'figure')

        files = [os.path.join(basepath, i) for i in os.listdir(basepath) if '濃度比較' in i and '環保署' not in i and '-' not in i]
        outName = os.path.join(basepath, '濃度比較-中科.png')
        merge(files, (1,4), outName)     

        files = [os.path.join(basepath, i) for i in os.listdir(basepath) if '環保署' in i and '-' not in i]
        outName = os.path.join(basepath, '濃度比較-環保署.png')
        merge(files, (1,3), outName)     


    def scatterComp(self):
        # 西屯
        ctsp = self.ctsp[['GuoAn', 'CP']]
        epa  = self.epa[['西屯']]
        box  = self.avg[['西屯區']]
        xitun = pd.concat([ctsp, epa, box], axis=1)
        xitun = xitun.rename({'GuoAn': '中科-國安', 'CP': '中科-都公', '西屯':'環保署-西屯站', '西屯區': '空氣盒子-西屯區'}, axis=1)
        self.xitun = xitun 

        xitun[xitun==np.inf] = np.nan

        sns.set(font_scale=.7)
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        g = sns.pairplot(xitun.iloc[:,:], plot_kws=dict(s=10, edgecolor="w", linewidth=0.5))
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        g.set(xticks=range(0,70,20), yticks=range(0,70,20), xlim=[0, 70], ylim=[0,70])
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        figName = os.path.join(self.path.base, 'figure', '西屯區-PM25比較.png')
        plt.gcf().set_size_inches([10, 10])

        def line(*kws, **kwargs):
            plt.gca().plot(range(70), range(70) , color=(.5,.5,.5), marker=None, linestyle='--', linewidth=0.5)

        def hide_current_axis(*args, **kwds):
            plt.gca().set_visible(False)

        g.map_offdiag(line)
        #g.map_upper(hide_current_axis)

        plt.savefig(figName, dpi=300)


        # 大雅
        ctsp = self.ctsp[['NEHS', 'YangMing']]
        epa  = self.epa[['西屯']]
        box  = self.avg[['大雅區']]
        xitun = pd.concat([ctsp, epa, box], axis=1)
        xitun = xitun.rename({'YangMing': '中科-陽明', 'NEHS': '中科-實中', '西屯':'環保署-西屯站', '大雅區': '空氣盒子-大雅區'}, axis=1)
        self.xitun = xitun 

        xitun[xitun==np.inf] = np.nan

        sns.set(font_scale=.7)
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        g = sns.pairplot(xitun.iloc[:,:], plot_kws=dict(s=10, edgecolor="w", linewidth=0.5))
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        g.set(xticks=range(0,70,20), yticks=range(0,70,20), xlim=[0, 70], ylim=[0,70])
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        figName = os.path.join(self.path.base, 'figure', '大雅區-PM25比較.png')
        plt.gcf().set_size_inches([10, 10])

        def line(*kws, **kwargs):
            plt.gca().plot(range(70), range(70) , color=(.5,.5,.5), marker=None, linestyle='--', linewidth=0.5)

        def hide_current_axis(*args, **kwds):
            plt.gca().set_visible(False)

        g.map_offdiag(line)
        #g.map_upper(hide_current_axis)

        plt.savefig(figName, dpi=300)

if __name__ == '__main__':
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    #today = '2020-10-14'
    region = ['梧棲區', '沙鹿區', '大雅區', '潭子區', '北屯區', '西屯區', '南屯區', '大肚區', '中區', '北區', '西區', '東區', '龍井區']
    drop = ['惠文高中', '篤行國小', '西苑高中', '龍山國小', '北勢國小']
    #Info = StaInfo()
    #info = Info.selRegion(region)
    #table = Info.byRegion()
    #d = dataproc(region)
    p = plot()




#airbox = pd.read_excel('data/organized/average_2020_10_06.xls', index_col=0)[['s_d0', 'region']]
#airbox = airbox.reset_index().pivot(index='datetime', columns='region', values='s_d0')
#airbox.index= airbox.index + pd.Timedelta(hours=8)
#TS = airbox.index.min().strftime('%Y-%m-%d')
#TE = (airbox.index.max() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
#
#c = CTSP([TS, TE], 'hour', ['PM2.5'])
#ctsp = c.data.droplevel(0, axis=1)
#data = pd.concat([airbox, ctsp], axis=1)
#data = data.fillna(np.inf)
#
#
#
#data1 = data.iloc[:,:-4]
#data2 = data.iloc[:,-4]
#data3 = data.iloc[:,-3]
#data4 = data.iloc[:,-2]
#data5 = data.iloc[:,-1]
#plt.ion()
#ax1 = sns.lineplot(data=data1, dashes=False, palette=('grey',), linewidth=1)
#ax1.get_legend().remove()
#plt.plot(data2)
