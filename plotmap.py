import json
import folium
import shapefile
import pandas as pd
from folium.features import DivIcon



rdBound = lambda filename: json.loads(open(filename , 'r').read())

def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'W' or direction == 'S':
        dd *= -1
    return dd

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

def parse_dms(dms):
    parts = re.split('[^\d\w]+', dms)
    lat = dms2dd(parts[0], parts[1], parts[2], parts[3])

    return (lat)

def shp2json(filename='TW_shpfile/TOWN_MOI_1081121.shp'):
    reader = shapefile.Reader(filename)
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]
    buffer = []
    for sr in reader.shapeRecords():
        if sr.record[2] != '臺中市':
            continue
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buffer.append(dict(type='Feature', \
        geometry=geom, properties=atr))

    # write the GeoJSON file
    outname = filename.replace('.shp', '.json')
    geojson = open(outname, 'w')
    geojson.write(json.dumps({'type': 'FeatureCollection', 'features': buffer}, indent=2) + '\n')
    geojson.close()

def selectRegion(filename='TW_shpfile/TOWN_MOI_1081121.json'):
    bnd = rdBound(filename)
    #bnd['features'] = [j for j in bnd['features'] if  j['properties']['COUNTYNAME']=='臺中市']



if __name__ == '__main__':
    #shp2json()
    f = rdBound('TW_shpfile/TOWN_MOI_1081121.json')
    data = pd.DataFrame([(   f['features'][i]['properties']['TOWNCODE'],  
                             f['features'][i]['properties']['COUNTYNAME'],
                             f['features'][i]['properties']['TOWNNAME']
                         ) for i in range(len(f['features']))],
                        columns = ['TOWNCODE', 'COUNTYNAME', 'TOWNNAME'])

    staname = pd.read_excel('data/airbox_info_organized.xlsx')

    ctsp = pd.read_excel('data/中科測站.xlsx')
    ctsp['lon'] = ctsp.lon.apply(lambda i: dms2dd(i.split()[0], i.split()[1], i.split()[2], 'E'))
    ctsp['lat'] = ctsp.lat.apply(lambda i: dms2dd(i.split()[0], i.split()[1], i.split()[2], 'N'))

    epa = pd.read_excel('data/epa_station.xlsx')


    city = pd.read_excel('data/city_lonlat_taichung.xlsx')
    #city['lon'] = city.lon.apply(lambda i: dms2dd(i.split()[0], i.split()[1], i.split()[2], 'E'))
    #city['lat'] = city.lat.apply(lambda i: dms2dd(i.split()[0], i.split()[1], i.split()[2], 'N'))

    mapfile = 'TW_shpfile/TOWN_MOI_1081121.json'
    myMap = folium.Map([24.170188, 120.755415], zoom_start=12, tiles='Stamen Terrain', right='0%')
    a = folium.Choropleth(  geo_data=mapfile, fill_color='BuPu', fill_opacity=0.2, line_opacity=0.9,line_color='brown', line_weight=2)
    a.add_to(myMap)



    for i,j in epa.iterrows():
        region = f'環保署{j["station"]}站'
        folium.Marker( location = [j['lat'], j['lon']], 
                        icon = DivIcon(
                            icon_size = (150,36),
                            icon_anchor =(7,20),
                            html=f'<div style="font-size: 20pt; color : cyan">◇</div>'),
                            tooltip= region, 
                         ).add_to(myMap)

    for i,j in ctsp.iterrows():
        region = j['station']
        folium.Marker( location = [j['lat'], j['lon']], 
                        icon = DivIcon(
                            icon_size = (150,36),
                            icon_anchor =(7,20),
                            html=f'<div style="font-size: 20pt; color : red">△</div>'),
                            tooltip= j['station'], 
                         ).add_to(myMap)

    for i,j in city.iterrows():
        region = j['region']
        folium.Marker( location = [j['lat'], j['lon']], 
                        icon = DivIcon(
                            icon_size = (150,36),
                            icon_anchor =(7,20),
                            html=f'<div style="font-size: 12pt; color : blue">{region}</div>'),
                         ).add_to(myMap)

    region = ['梧棲區', '沙鹿區', '大雅區', '潭子區', '北屯區', '西屯區', '南屯區', '大肚區', '中區', '北區', '西區', '東區', '龍井區']
    for i,j in staname.iterrows():
        if j['region'] in region:
            color = 'green'
        else:
            color = 'black'
        folium.Marker( location = [j['lon'], j['lat']], 
                        icon = DivIcon(
                            icon_size = (150,36),
                            icon_anchor =(7,20),
                            html=f'<div style="font-size: 20pt; color : {color}">•</div>'),
                        popup = j['Address'], 
                        tooltip = j['name'] ).add_to(myMap)

    myMap.save('data/附件二.html')
