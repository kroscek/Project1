from selenium import webdriver
from bs4 import BeautifulSoup as soup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import re

browser = webdriver.Firefox()
browser.get('https://karagarga.in')
web = WebDriverWait(browser, 10).until(
    EC.visibility_of_element_located((By.XPATH, "/html/body/table[2]/tbody/tr/td/a[1]")))
web.click()
web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.NAME, "username")))
web.send_keys('username')
web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.NAME, "password")))
web.send_keys('password')

web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located(
    (By.XPATH, "/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr/td[2]/form/table/tbody/tr[2]/td[2]/span[1]/a/b")))
first_movie = web.text
web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located(
    (By.XPATH, "/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr/td[2]/form/table/tbody/tr[2]/td[8]/a")))
upper = web.text
htmls = []
page = 4228
for i in range(11008, 13184 + 1):
    print(i)
    browser.get('https://karagarga.in/browse.php?page={}&sort=added&d=DESC&search_type=torrent'.format(i))
    web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="browse"]')))
    html = web.get_attribute('outerHTML')
    page_soup = soup(html, "html.parser")
    #    containers = page_soup.findAll("tr",{"class":"oddrow"})
    containers = page_soup.findAll("tr")
    for row in containers:
        try:
            title = str(row.findAll("b")[0])
        except:  # skip the specific iteration if title is none
            continue
        title = title.replace("<b>", '')
        title = title.replace("</b>", '')
        upper = str(row.findAll("a"))
        upper = re.findall('userdetails\.php\?id=\d+">(.*?)<\/a>', upper)
        if title == 'G.B.H.' and upper[0] == 'ausmanx':
            break
        htmls.append(row)
    htmls = htmls[0:len(htmls) - 1]
    last_inspected_page = 'https://karagarga.in/browse.php?page={}&search_type=torrent'.format(i)
# %%
i = 0
d = []
no_imdb = []
for i in range(len(htmls)):
    if i % 1000 == 0:
        print(i)
    if re.findall("snatchedrow", str(htmls[i])):  # skip already downloaded torrent
        continue
    is_movie = re.findall('genreimages\/(.*?).(.*?)" title="(.*?):', str(htmls[i]))
    status = False
    for x in is_movie:
        for y in x:
            if y == 'Movie':
                status = True
                break
    if status:
        Snatches = str(htmls[i].findAll("a"))
        Snatches = re.findall('snatchers"\>(\d+)', Snatches)
        try:
            Snatches = Snatches[0]
        except:
            Snatches = None
            continue
        if int(Snatches) < 26:
            continue
        try:
            genre = re.findall('incldead=">(.*?)<', str(htmls[i].findAll("a")))
            genre = list(filter(None, genre))
            if len(genre) > 1:
                genre = str('/'.join(genre))
            else:
                genre = genre[0]
        except:
            genre = None
        if genre.find('Short') > -1 or genre.find('Silent') > -1 or genre.find('Animation') > -1 or genre.find(
                'War') > -1 or genre.find('Giallo') > -1 or genre.find('Musical') > -1:
            continue
        try:
            title = str(htmls[i].findAll("b")[0])
        except:  # skip the specific iteration if title is none
            continue
        title = title.replace("<b>", '')
        title = title.replace("</b>", '')
        imdb = str(htmls[i].findAll("a"))
        imdb = re.findall('imdb.com\/title\/(.*?)"', imdb)
        try:
            imdb = re.findall('((tt)(\d+))', imdb[0])[0][0]
        except:
            imdb = None
        if imdb is not None:
            if imdb.find('/') > -1:
                imdb = imdb.replace('/', '')
        try:
            link = str(htmls[i].findAll("a"))
            link = re.findall('down.php\/(.*?)"', link)
            link = link[0]
            link = link.replace('&amp;', '&')
            link = "https://karagarga.in/down.php/" + link
        except:
            link = None
        try:
            year = str(htmls[i].findAll("a"))
            year = re.findall('year">(.*?)<', year)
            year = year[0]
        except:
            year = None
        try:
            country = str(htmls[i].findAll("a"))
            country = re.findall('flag\/(.*?).gif', country)
            country = country[0]
        except:
            country = None
        try:
            director = str(htmls[i].findAll("a"))
            director = re.findall('dirsearch=(.*?)">(.*?)<', director)
            director = director[0][1]
        except:
            director = None
        if imdb is None:
            no_imdb.append((title, country, genre, imdb, link, Snatches, year, director))
        else:
            d.append((title, country, genre, imdb, link, Snatches, year, director))

# %%
df = pd.DataFrame(d, columns=["Title", "Country", "Genre", "IMDB", "Link", "Snatches", "Year", "Director"])
a = df.groupby(['IMDB'], sort=False)['Snatches'].max()  # group to find the max snatches for the same IMDB title
a = a.reset_index()
a = [tuple(x) for x in a.values]
dd = []
for i in df.index:
    title = df.loc[i, 'IMDB']
    snatches = df.loc[i, 'Snatches']
    yes = ((title, snatches))
    if yes in a:
        yes = tuple(df.iloc[i, :])
        dd.append(yes)
df = pd.DataFrame(dd, columns=["Title", "Country", "Genre", "IMDB", "Link", "Snatches", "Year", "Director"])
df = df.drop_duplicates('IMDB').reset_index(drop=True)
df = df[df.Country != 'indonesia']
df = df[df.Country != 'ussr']
df = df[df.Country != 'yugoslavia']
df = df[df.Country != 'russia']
df = df[df.Country != 'austria']
df = df[df.Country != 'australia']
df.to_csv('kg_imdb.csv', index=False)
df = pd.DataFrame(no_imdb, columns=["Title", "Country", "Genre", "IMDB", "Link", "Snatches", "Year", "Director"])
df = df[df.Country != 'indonesia']
df = df[df.Country != 'ussr']
df = df[df.Country != 'yugoslavia']
df = df[df.Country != 'russia']
df = df[df.Country != 'austria']
df = df[df.Country != 'australia']
df.to_csv('kg_noimdb.csv', index=False)
# %%
import re

a = "animal=cat,dog,cat,tiger,dog"
A = re.findall('(?:animal)(?:=)([A-Za-z]+),([A-Za-z]+),([A-Za-z]+)', a)
a = "I want (seafood) in AUstralia"
A = re.findall('(\(.*?\))', a)
a = "http://stackoverflow.com/"
A = re.findall('(?:https?|ftp)://([^/\r\n]+)?', a)
a = '<a href="browse.php?cat=6"><img alt="Hidden Gems" border="0" height="50" src="img/cat-gems.gif" title="Hidden Gems" width="67"/></a>'
A = re.findall("[^=]*", a)
a = 'Allan-Tanaka Tanonaka-Dalton'
a = a.split()
A = re.findall("[^\-]+", a[0])
A.extend(re.findall("[^\-]+", a[1]))
a = 'a href="/title/tt0054806/releaseinfo?ref_=tt_ov_inf" title="See more release dates">September 1962 (UK)\n</a>'
A = re.findall('>(.*?)\d+', a)
A = re.findall('\[.*?\]', a)
re.findall('[12][0-9]{3}', A[1])
# %%DOWNLOAD KARAGARGA
import glob
import time
import re

idx = 0
browser = webdriver.Chrome('/usr/bin/chromedriver')
browser.get('https://karagarga.in')
web = WebDriverWait(browser, 10).until(
    EC.visibility_of_element_located((By.XPATH, "/html/body/table[2]/tbody/tr/td/a[1]")))
web.click()
web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.NAME, "username")))
web.send_keys('username')
web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.NAME, "password")))
web.send_keys('password')
web = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="browse"]')))
html = web.get_attribute('outerHTML')
page_soup = soup(html, "html.parser")
containers = page_soup.findAll("tr")
count = 0
ja = pd.read_csv('/home/lemma/kg.csv')
ja = ja.Link.values.tolist()
while True:
    count += 1
    if idx > len(ja) - 1:
        break
    while len(glob.glob('/home/lemma/Downloads/*.torrent')) != count:
        browser.get(ja[idx])
        time.sleep(2)
    idx += 1
