import os
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait

load_dotenv()
connection_string = os.getenv('DATABASE_URL')
conn = psycopg2.connect(connection_string)
cur = conn.cursor()

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


def parse_data(links):
    browser = webdriver.Firefox()
    for i in links:
        browser.get(f"https://zno.osvita.ua{i}")
        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')
        try:
            spans = soup.find('div', {'class': 'tasks-numbers'}).find_all('span')
        except:
            continue
        wait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="tasks-numbers"]/span[{spans[-1].text}]'))).click()
        try:
            wait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="q_form_{spans[-1].text}"]/div[7]/div[2]/span'))).click()
        except:
            continue
        page_source = browser.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        tasks = soup.findAll('div', {'class': 'task-card'})
        subject = soup.findAll('span', {'class': 'row'})[0].text
        chapter = soup.findAll('span', {'class': 'row'})[1].text
        theme = soup.findAll('span', {'class': 'row'})[2].text
        for j in range(1, len(tasks)):
            question = soup.find('div', {'id': f'q{j}'}).find('div', {'class': 'question'}).text
            # todo bug cant understand which letter bald which not
            answers = soup.find('div', {'id': f'q{j}'}).findAll('div', {'class': 'answer'})
            answer_list = []
            for k in answers:
                answer = k.text[1:]
                answer_list.append(answer)
            create_dict(subject, question, chapter, theme)
            # correct_answer = (soup.find('div', {'id': f'q{j}'}).find('table', {'class': 'select-answers-variants'})).findAll('span')
            # #todo idk how to change link after pressing button
            # for ii in correct_answer:
            #     x = re.findall("class=\"marker\"|class=\"marker ok\"", ii)


def create_dict(subject, question, chapter, theme):
    data = {"subject": subject.replace("\'", "`"),
            "question": question.replace("\'", "`"),
            "chapter": chapter.replace("\'", "`"),
            "theme": theme.replace("\'", "`"),
    }
    connect_to_db(data)


def connect_to_db(data):
    cur.execute(f"INSERT INTO ukrmova (subject, question, chapter, theme) VALUES ('{data['subject']}', '{data['question']}', '{data['chapter']}', '{data['theme']}')")
    conn.commit()


def main():
    cur.execute("DROP TABLE IF EXISTS ukrmova")
    cur.execute("CREATE TABLE ukrmova (subject VARCHAR(1000), question VARCHAR(1000), chapter VARCHAR(1000), theme VARCHAR(1000))")
    conn.commit()
    parse_data(parse_links())
    cur.close()
    conn.close()

main()
