import pandas as pd
import requests
import os, json
import pathlib, datetime

pd.set_option('display.unicode.east_asian_width',True)
pd.set_option('display.unicode.ambiguous_as_wide',True)

class getlist():
    def __init__(self, outname):
        self.outname = outname
        self.srcurl = 'https://pm25.lass-net.org/AirBox/detail.php?city=taichung19'
        self.__get__()

    def __get__(self):
        data = pd.read_html(requests.get(self.srcurl).text)[0].droplevel(0,axis=1).set_index('#')
        data = data.dropna(subset=['Score'])

        name = self.outname
        if not os.path.isfile(name):
            data.to_excel(name, index=False)
        self.data = data
        

class download():
    def __init__(self, name):
        self.name = name
        self.__read__()
        self.__download__()

    def __read__(self):
        self.df = pd.read_excel(self.name)
        self.id = self.df['Site ID']
        
    def __download__(self):
        url = 'https://pm25.lass-net.org/data/history.php?device_id=ID'
        for i, id in self.id.items():
            site = self.df.loc[i, 'Site']
            time = datetime.datetime.today().strftime('%Y%m%d') 
            outname = f'data/datalist/{id}/{time}.xlsx' 
            pathlib.Path(os.path.dirname(outname)).mkdir(parents=True, exist_ok=True)

            if os.path.isfile(outname):
                print(f' >> {id} 檔案已存在')
                continue

            #if i >=1: continue
            data = requests.get(url.replace('ID', id)).text
            try:
                data = json.loads(data)['feeds']
            except:
                data = []

            if data == []: 
                print('沒有數據可下載')
                continue

            print(f'處理 {id} {name}')
            data = data[0]['AirBox']

            DATA = []
            for idata in data:
                DATA.append(pd.DataFrame(idata).T)
                
            DATA = pd.concat(DATA)                
            DATA.index = pd.to_datetime(DATA.index.str.replace('[TZ]',' '))
            DATA = DATA[['s_d0','s_d1','s_d2','s_g1','s_h0', 's_t0']]
            DATA = DATA.astype(float)
            DATA['time'] = DATA.index.strftime('%Y-%m-%d %H:00:00')
            DATA = DATA.pivot_table(index='time', aggfunc='mean')
            DATA.columns = pd.MultiIndex.from_product([[id], [site], DATA.columns])
            DATA.index = pd.to_datetime(DATA.index)
           
            if not os.path.isfile(outname):
                DATA.to_excel(outname)

            self.data = data
            self.DATA = DATA
if __name__ == '__main__':
    name = 'data/airbox_info.xlsx'
    g = getlist(name)
    d = download(name)
    
