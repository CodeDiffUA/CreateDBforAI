from selenium import webdriver
from bs4 import BeautifulSoup
import re


def parse_links():
    links = []
    browser = webdriver.Firefox()
    browser.get('https://zno.osvita.ua/ukrainian/tema.html')
    content = browser.page_source
    soup = BeautifulSoup(content, 'html.parser')
    lis2 = soup.find_all('li', {'class': 'tag-item'})[0]
    for li2 in lis2:
        r = (re.findall('href=\".*\" ', str(li2)))
        for i in r:
            links.append(i[6:-2])
    browser.close()
    return links


parse_links()