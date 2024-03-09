import os
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

#todo make headless

options = Options()
options.headless = True
load_dotenv()
connection_string = os.getenv('DATABASE_URL')
conn = psycopg2.connect(connection_string)
cur = conn.cursor()


def parse_links():
    links = []
    browser = webdriver.Firefox(options=options)
    browser.get('https://zno.osvita.ua/ukrainian/tema.html')
    content = browser.page_source
    soup = BeautifulSoup(content, 'html.parser')
    lis2 = soup.find_all('li', {'class': 'tag-item'})[0]
    for li2 in lis2:
        r = (re.findall('href=\".*\" ', str(li2)))
        for i in r:
            links.append(i[6:-2])
    browser.close()
    links.pop()
    return links


def parse_data(links):
    browser = webdriver.Firefox(options=options)
    for i in links:
        browser.get(f"https://zno.osvita.ua{i}")
        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')
        try:
            spans = soup.find('div', {'class': 'tasks-numbers'}).find_all('span')
        except:
            continue
        browser.find_element(By.XPATH, f'//*[@id="tasks-numbers"]/span[{spans[-1].text}]').click()
        try:
            browser.find_element(By.XPATH, f'//*[@id="q_form_{spans[-1].text}"]/div[7]/div[2]/span').click()
        except:
            browser.find_element(By.XPATH, f'//*[@id="q_form_{spans[-1].text}"]/div[8]/div[2]/span').click()
        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')
        tasks = soup.findAll('div', {'class': 'task-card'})
        subject = soup.findAll('span', {'class': 'row'})[0].text
        chapter = soup.findAll('span', {'class': 'row'})[1].text
        theme = soup.findAll('span', {'class': 'row'})[2].text
        for j in range(1, len(tasks)):
            question = str(soup.find('div', {'id': f'q{j}'}).find('div', {'class': 'question'}))
            question = format_html(question)
            answers = soup.find('div', {'id': f'q{j}'}).findAll('div', {'class': 'answer'})
            answer_list = []
            for answer in answers:
                answer = format_html(str(answer))
                answer_list.append(answer)
            create_dict(subject, question, chapter, theme)
            #correct_answer = str((soup.find('div', {'id': f'q{j}'}).find('table', {'class': 'select-answers-variants'})))
            #print(correct_answer)
            #for ii in correct_answer:
            #p = re.findall("class=\"marker\"|class=\"marker ok\"", correct_answer)
            # #todo idk how to change link after pressing button
            # #todo add vidpovidnosti to answers
            # #todo explanation


def format_html(html_string):
    html_string = html_string.replace("<strong>", "**").replace("</strong>", "**")
    html_string = html_string.replace("<em>", "*").replace("</em>", "*")
    html_string = html_string.replace("<u>", "__").replace("</u>", "__")
    html_string = html_string.replace("<b>", "**").replace("</b>", "**")
    html_string = html_string.replace("<i>", "*").replace("</i>", "*")
    html_string = html_string.replace("<div class=\"question\">", "").replace("/div", "")
    html_string = html_string.replace("<p>", "").replace("</p>", "")
    html_string = html_string.replace("<br/>", "")
    html_string = html_string.replace("<>", "")
    q = re.findall("<style>\n.*\n</style>", html_string)
    for b in q:
        html_string = html_string.replace(b, "")
    y = re.findall("<style>.*</style>", html_string)
    for m in y:
        html_string = html_string.replace(m, "")
    x = re.findall("<.*>", html_string)
    for c in x:
        html_string = html_string.replace(c, "")
    return html_string



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
    cur.execute("CREATE TABLE ukrmova (subject VARCHAR(9000), question VARCHAR(9000), chapter VARCHAR(9000), theme VARCHAR(9000))")
    conn.commit()
    parse_data(parse_links())
    cur.close()
    conn.close()


main()
