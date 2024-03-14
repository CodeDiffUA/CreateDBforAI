import os
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep

# todo make headless

options = Options()
# options.add_argument(r"load-extension=./adblock.crx")
# options.headless = True
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
        sleep(1)
        try:
            browser.find_element(By.XPATH, f'//*[@id="q_form_{spans[-1].text}"]/div[7]/div[2]/span').click()
            sleep(1)
        except:
            browser.find_element(By.XPATH, f'//*[@id="q_form_{spans[-1].text}"]/div[8]/div[2]/span').click()
            sleep(1)
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
            # print(answers)
            # print()
            for answer in answers:
                answer = format_html(str(answer))[1:]
                answer_list.append(answer)
            correct_answers = str(
                (soup.find('div', {'id': f'q{j}'}).find('table', {'class': 'select-answers-variants'})))

            p = re.findall("class=\"marker\"|class=\"marker ok\"", correct_answers)
            correct_answer_iterator = 0
            for ii in p:
                if ii == 'class=\"marker ok\"':
                    break
                correct_answer_iterator += 1

            create_dict(subject, question, chapter, theme, answer_list, answer_list[correct_answer_iterator])

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
    # x = re.findall("<.*>", html_string)
    # for c in x:
    #     html_string = html_string.replace(c, "")
    while html_string.find("<") != -1:
        left = html_string.find("<")
        right = html_string.find(">")
        html_string = html_string.replace(html_string[left: right + 1], "")
    return html_string
    return html_string


def create_dict(subject, question, chapter, theme, answer_list, correct_answer):
    data = {"subject": subject.replace("\'", "`"),
            "question": question.replace("\'", "`"),
            "chapter": chapter.replace("\'", "`"),
            "theme": theme.replace("\'", "`"),
            "answer1": answer_list[0].replace("\'", "`"),
            "answer2": answer_list[1].replace("\'", "`"),
            "answer3": answer_list[2].replace("\'", "`"),
            "answer4": answer_list[3].replace("\'", "`"),
            "correct_answer": correct_answer.replace("\'", "`"),
            }
    connect_to_db(data)


def connect_to_db(data):
    cur.execute(
        f"INSERT INTO ukrmova (subject, question, chapter, theme, answer1, answer2, answer3, answer4, correct_answer) "
        f"VALUES ('{data['subject']}', '{data['question']}', '{data['chapter']}', '{data['theme']}', '{data['answer1']}', '{data['answer2']}', '{data['answer3']}', '{data['answer4']}', '{data['correct_answer']}')")
    conn.commit()


def main():
    cur.execute("DROP TABLE IF EXISTS ukrmova")

    cur.execute("CREATE TABLE ukrmova ("
                "subject VARCHAR(9000),"
                "question VARCHAR(9000),"
                "chapter VARCHAR(9000),"
                "theme VARCHAR(9000),"
                "answer1 VARCHAR(9000),"
                "answer2 VARCHAR(9000),"
                "answer3 VARCHAR(9000),"
                "answer4 VARCHAR(9000),"
                "correct_answer VARCHAR(9000))"
                )
    conn.commit()
    parse_data(parse_links())
    cur.close()
    conn.close()


main()
