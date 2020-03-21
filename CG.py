from selenium import webdriver
from bs4 import BeautifulSoup as soup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.webdriver.firefox.options import Options
import re
from multiprocessing import Pool
import numpy as np
cores=8
def parallelize_dataframe(df, func):
    df_split = np.array_split(df, cores)
    pool = Pool(cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df
PAGE=5130
options = Options()
options.headless = True
browser=webdriver.Firefox(options=options)
browser.get('http://cinemageddon.net')
web=WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/table[2]/tbody/tr/td/p/a[1]")))
web.click()
web=WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.NAME, "username")))
web.send_keys('username')
web=WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.NAME, "password")))
web.send_keys('password')
web=WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/table[2]/tbody/tr/td/form/table/tbody/tr[3]/td/input")))
web.click()
htmls=[]
for i in range(5936):
    print (i)
    browser.get('http://cinemageddon.net/browse.php?page={}'.format(PAGE+i))
    web=WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/table[2]/tbody/tr/td[2]/form/table[3]")))
    html = web.get_attribute('outerHTML')
    page_soup = soup(html, "html.parser")
    containers = page_soup.findAll("tbody")
    for row in containers:
        for x in row.findAll("tr"):
            htmls.append(x)
    last_inspected_page='http://cinemageddon.net/browse.php?page={}'.format(PAGE+i)
#%%
i=0
d=[]
for i in range(len(htmls)):
    try:
        genre=re.findall('img alt="(.*?)"',str(htmls[i].findAll("a")[0]))
        genre=genre[0]
    except:
        continue
    if genre=='OST' or genre=='Ebooks' or genre=='Tinfoil Hat' or genre=='Trailers':
        continue
    try:
        title=str(htmls[i].findAll("b")[0])
    except:#skip the specific iteration if title is none
        continue
    title=title.replace("<b>",'')
    title=title.replace("</b>",'')
    val=re.findall('(?i)(bdrip)',title)
    if val:
        continue
    imdb=str(htmls[i].findAll("a"))
    imdb=re.findall('imdb.com\/title\/(.*?)\/',imdb)
    try:
        imdb=imdb[0]
    except:
        imdb=None
    link=str(htmls[i].findAll("a"))
    link=re.findall('"download.php(.*?)"',link)
    try:
        link=link[0]
        link=link.replace('amp;','')
        link="download.php"+link
        link="cinemageddon.net/"+link
    except:
        link=None
    Snatches=str(htmls[i].findAll("a"))
    Snatches=re.findall('completed">(.*?)<',Snatches)
    try:
        status='snatches_none'
        Snatches=Snatches[0]
    except:
        Snatches=None
        continue
    if int(Snatches)<26:
        continue
    d.append((title,genre,imdb,link,Snatches))
df = pd.DataFrame(d,columns=["Title", "Genre", "IMDB", "Link", "Snatches"])
a=df.groupby(['IMDB'], sort=False)['Snatches'].max()#group to find the max snatches for the same IMDB title
a = a.reset_index()
a = [tuple(x) for x in a.values]
dd=[]
for i in df.index:
    title=df.loc[i,'IMDB']
    snatches=df.loc[i,'Snatches']
    yes=((title,snatches))  
    if yes in a:
        yes=tuple(df.iloc[i,:])
        dd.append(yes)
df = pd.DataFrame(dd,columns=["Title", "Genre", "IMDB", "Link", "Snatches"])
def no_imdb(x):
    status=False
    if x is None:
        status=True
    return status
def clean_str_df(df):
    return df.apply( lambda s : no_imdb(s))
df['status'] = parallelize_dataframe(df['IMDB'], clean_str_df) 
No_imdb=df[df['status']==True]
No_imdb.to_csv('no_imdb.csv',index=False)
df= df[df['status']==False] 
##################IMDB ISSUE##################
years=pd.DataFrame(columns=['year'])
for i in df.index:
    title=df.loc[i,'Title']
    year=re.findall('[12][0-9]{3}',str(title))
    try:
        years.loc[i]=year[0]
    except:
        years.loc[i]=None
        continue
df['years']=years
for i in df.index:
    if df.loc[i,'years'] is np.nan:
        link='https://www.imdb.com/title/'+df.loc[i,'IMDB']+'/releaseinfo?ref_=tt_ov_inf'
        browser.get(link)
        try:
            web=WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/div/div[2]/div[3]/div[1]/div[1]/div[1]/div/div/h3/span")))
        except:
            continue
        html = web.get_attribute('outerHTML')
        page_soup = soup(html, "html.parser")
        year=re.findall('[12][0-9]{3}',str(page_soup))
        try:
            df.loc[i,'years']=year[0]
            print (i, 'yes')
        except:
            df.loc[i,'years']=None
            print ('no')
for i in df.index:
    years=df.loc[i,'years']
    if years<'2001' and years>'1945':
        yes=tuple(df.iloc[i,:])
        d.append(yes)
df = pd.DataFrame(d,columns=["Title", "Genre", "IMDB", "Link", "Snatches", "years"])