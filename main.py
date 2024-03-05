from selenium import webdriver
from bs4 import BeautifulSoup
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait


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


def go_to_links(links):
    browser = webdriver.Firefox()
    for i in links:
        print(f"https://zno.osvita.ua{i}")
        browser.get(f"https://zno.osvita.ua{i}")
        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')
        spans = soup.find('div', {'class': 'tasks-numbers'}).find_all('span')

        wait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="tasks-numbers"]/span[{spans[-1].text}]'))).click()
        wait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="q_form_39"]/div[7]/div[2]/span'))).click()
        for i in range (1, len(spans) + 1):
            wait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="tasks-numbers"]/span[{i}]'))).click()


go_to_links(parse_links())