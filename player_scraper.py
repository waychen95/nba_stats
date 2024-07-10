import pandas as pd
import numpy as np
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')

start_year = 2020
end_year = 2021

years = []

for year in range(start_year, end_year):
    year_end = year + 1
    year_end = str(year_end)[-2:]
    years.append(f'{year}-{year_end}')

type = 'Regular Season'

driver = webdriver.Chrome(options=options)

driver.get('https://www.nba.com/players')


dropdown = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div[2]/section/div/div[2]/div[1]/div[7]/div/div[3]/div/label/div/select')

# Print all options in the dropdown for debugging
select = Select(dropdown)
for option in select.options:
    print("Option text:", option.text)
select.select_by_visible_text("All")

time.sleep(20)

page_source = driver.page_source

soup = BeautifulSoup(page_source, 'html.parser')

player_list = soup.find('table', class_='players-list').find('tbody').find_all('tr')

print(len(player_list))


# player_list = soup.find('table', class_='players-list').find('tbody').find_all('tr')

# print(player_list[0])

driver.quit()


