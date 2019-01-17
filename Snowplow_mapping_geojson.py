
# coding: utf-8

# In[361]:


import requests 
from time import gmtime, strftime
import pandas as pd
from shapely.geometry import shape, Point
from pyproj import Proj, transform
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
import shapely
import folium
from datetime import *
import numpy as np


# In[362]:

f=open("/home/pi/map_test_syracuse/account.txt","r")
lines=f.readlines()
username=lines[0].rstrip()
password=lines[1].rstrip()
f.close()


# In[363]:

# In[364]:



payload = "grant_type=password&username=" +username*"&password="+password
headers = {
    'Content-Type': "application/x-www-form-urlencoded",
    'Cache-Control': "no-cache",
    
    }


# In[365]:


response = requests.request("POST", 'https://auth.networkfleet.com/token', data=payload, headers=headers)


# In[366]:



response = response.json()


# In[367]:


response


# In[368]:


snowice = ['975118',
             '975119',
             '940427',
             '938761',
             '951625',
             '977159',
             '955397',
             '977157',
             '951170',
             '954050',
             '955394',
             '952387',
             '966234',
             '952216',
             '977624',
             '955417',
             '952150',
             '952406',
             '977106',
             '955411',
             '970771',
             '973267',
             '952080',
             '973265',
             '950063',
             '954287',
             '954281',
             '954279',
             '953696',
             '952315',
             '952883',
             '977331',
             '966223',
             '957144',
             '955921',
             '970767',
             '970755']


# In[369]:


dataSrc = gpd.read_file('/home/pi/map_test_syracuse/dataSrc.geojson')


# In[370]:


mergeddata_all = gpd.read_file('/home/pi/mergeddata.geojson')


# In[371]:


dataSrc = dataSrc[(dataSrc['CART_TYPE'] != 'INTERSTATES') & (dataSrc['CART_TYPE']!='RAMPS') & (dataSrc['CART_TYPE']!='PEDESTRIAN') &
        (dataSrc['CART_OWN']!="PRIVATE") &
        (~dataSrc['STREET'].isin(['FARMERS MARKET WAY' , 'NBT BANK PKWY' , 'DESTINY USA SERVICE RD', 'DESTINY USA TO SB I 81 RAMP', 'DESTINY USA FROM SB I 81 RAMP', 'DESTINY USA DR'])) &
        (~dataSrc['STREET_ID'].isin([13020737,12572689,13013383,13013382,13013377,13013381,13013380,12572623,12572620,13013389,13021028,13013390,12572506,12572503,13013391,12572501,12572508,12572525,12572526,12572664,12572659,13028975,13001278,13001275,13001277,13008682,13001274,12574889,12574981,13028975]))
       ]


# In[372]:


timezone = timedelta(hours = 5)
systime = datetime.now() + timezone - timedelta(hours = 1)
hour = (systime - timezone).hour
date = (systime - timezone).strftime('%Y-%m-%d')
start_date = systime.strftime("%Y-%m-%dT%H") + ':00:00Z'
end_date = systime.strftime("%Y-%m-%dT%H") + ':59:59Z'


# In[373]:


appended_data = pd.DataFrame(columns=['STREET_ID', 'date', 'hour'])


# In[374]:


for i in snowice:
    try:
        r=requests.get("https://api.networkfleet.com/locations/vehicle/"+i+"/track?limit=5000", 
                       headers={'Authorization': "Bearer " + response['access_token'],
                                            'Accept': "application/vnd.networkfleet.api-v1+json",
                                            'Content-Type': "application/json",
                                            'Cache-Control': "no-cache",
                                            'Postman-Token': response['refresh_token']},
                       params={"with-start-date":start_date,
                         "with-end-date":end_date}
                      )
        rjson = r.json()
        x = pd.DataFrame(rjson)
        Name = pd.io.json.json_normalize(x['gpsMessage'])
        Nameedit = Name[['latitude', 'longitude', 'messageTime']]
        Nameedit['truck_name'] = 970767
        Nameedit['timeedit'] = pd.to_datetime(Nameedit['messageTime'])
        Nameedit['hour'] = (Nameedit["timeedit"]-timezone).dt.hour
        Nameedit['date'] = (Nameedit['timeedit']-timezone).dt.strftime("%Y-%m-%d")
        geometry = [Point(xy) for xy in zip(Nameedit.longitude, Nameedit.latitude)]
        Nameedit1 = GeoDataFrame(Nameedit, geometry=geometry)
        Nameedit1 = Nameedit1.groupby(['truck_name', 'hour','date'])['geometry'].apply(lambda x: LineString(x.tolist()))
        Nameedit1 = GeoDataFrame(Nameedit1, geometry='geometry')
        Nameedit1 = pd.DataFrame(Nameedit1.to_records())
        Nameedit1 = GeoDataFrame(Nameedit1, geometry='geometry')
        Nameedit1.crs = {'init' :'epsg:4326'}
        x1 = gpd.sjoin(Nameedit1, dataSrc, op='intersects')
        x1 = x1[['STREET_ID', 'hour', 'date']]
        appended_data = appended_data.append(x1)
    except:
        pass



# In[375]:


res = appended_data.groupby('STREET_ID')['hour', 'date'].max().reset_index()


# In[376]:


mergeddata = dataSrc[['STREET', 'geometry', 'STREET_ID']].merge(res, left_on='STREET_ID', right_on='STREET_ID', how='right')


# In[377]:


mergeddata_all = mergeddata_all.append(mergeddata)


# In[378]:


mergeddata_all = mergeddata_all.groupby(['STREET_ID'])['hour', 'date'].max().reset_index()


# In[379]:


mergeddata_all = dataSrc[['STREET', 'geometry', 'STREET_ID']].merge(mergeddata_all, left_on='STREET_ID', right_on='STREET_ID', how='right')


# In[380]:


with open('/home/pi/map_test_syracuse/mergeddata.geojson', 'w') as f:
    f.write(mergeddata_all.to_json())



# In[381]:


notplowed = dataSrc[(~dataSrc['STREET_ID'].isin(mergeddata_all['STREET_ID'].astype(object)))]


# In[382]:


notplowed = notplowed[['STREET', 'geometry', 'STREET_ID']]


# In[383]:


with open('/home/pi/map_test_syracuse/notplowed.geojson', 'w') as f:
    f.write(notplowed.to_json())

