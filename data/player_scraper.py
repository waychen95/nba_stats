import pandas as pd
import numpy as np
import requests
import time
import os
import psycopg2
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

def get_player_info(player_list):
    player_data = []

    domain = 'https://www.nba.com'

    for player in player_list:
        player_info_list = player.find_all('td', class_='text')

        player_primary_tag = player_info_list[0]
        player_url = f"{domain}{player_primary_tag.find('a').get('href')}"
        player_id = player_url.split('/')[-3]
        player_image_url = player_primary_tag.find('img').get('src')

        player_first_name_p = player_primary_tag.find('p', class_='RosterRow_playerFirstName__NYm50')

        player_first_name = player_first_name_p.text.strip()
        player_last_name = player_first_name_p.next_sibling.text.strip()

        player_team = player_info_list[1].find('a').text.strip()
        player_team_url = f"{domain}{player_info_list[1].find('a').get('href')}"

        player_number = player_info_list[1].next_sibling.text.strip()

        player_position = player_info_list[2].text.strip()

        player_height = player_info_list[2].next_sibling.text.strip()

        player_weight = player_info_list[3].text.strip().split(' ')[0]

        player_last_attended = player_info_list[4].text.strip()

        player_country = player_info_list[5].text.strip()

        player_dict = {
            'id': player_id,
            'first_name': player_first_name,
            'last_name': player_last_name,
            'url': player_url,
            'image_url': player_image_url,
            'team': player_team,
            'team_url': player_team_url,
            'number': player_number,
            'position': player_position,
            'height': player_height,
            'weight': player_weight,
            'last_attended': player_last_attended,
            'country': player_country
        }

        player_data.append(player_dict)

        time.sleep(1)

    player_df = pd.DataFrame(player_data)
    print(player_df.head())
    player_df.to_csv('player_data.csv', index=False)

    return player_df

def get_player_stats(player_df, driver):
    player_stats_url = 'https://www.nba.com/stats/player/'

    player_stats_all_df = pd.DataFrame()

    column_headers = []

    for index, row in player_df.iterrows():

        print(f"Getting player stats for {row['first_name']} {row['last_name']} in row {index}")

        player_id = row['id']
        player_url = f"{player_stats_url}{player_id}?SeasonType=Regular%20Season"

        print(player_url)
        page_source = driver.get(player_url)

        # Wait until the table is present and visible
        try:
            table_xpath = "//div[@class='Crom_container__C45Ti crom-container']/table"
            table = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, table_xpath))
            )
        except:
            print('Table not found')
            continue

        # Scroll the table into view
        driver.execute_script("arguments[0].scrollIntoView(true);", table)

        # Get the updated page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        column_list = soup.find('tr', class_='Crom_headers__mzI_m').find_all('th')

        if not column_headers:
            for column in column_list:
                text = column.text.replace('"', '').strip().lower()
                column_headers.append(text)

            print(column_headers)

        player_stats_list = soup.find('tbody', class_='Crom_body__UYOcU').find_all('tr')

        player_stats_data = []

        for player_stats in player_stats_list:
            stats = player_stats.find_all('td')

            stats_dict = {}

            for i, stat in enumerate(stats):
                stat = stat.text.replace('"', '').strip()
                stats_dict[column_headers[i]] = stat

            player_stats_data.append(stats_dict)

        player_stats_df = pd.DataFrame(player_stats_data)
        player_stats_df['player_id'] = player_id
        player_stats_df.rename(columns={'by year': 'year'}, inplace=True)

        player_stats_all_df = pd.concat([player_stats_all_df, player_stats_df], axis=0, ignore_index=True)

    print(player_stats_all_df.head())

    player_stats_all_df.to_csv('player_stats_all.csv', index=False)



def player_scraper():
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
    select.select_by_visible_text("All")

    # toggle = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div[2]/section/div/div[2]/div[1]/div[6]/label/div/span')
    # if not toggle.is_selected():
    #     toggle.click()

    page_source = driver.page_source

    soup = BeautifulSoup(page_source, 'html.parser')

    player_list = soup.find('table', class_='players-list').find('tbody').find_all('tr')

    print(len(player_list))

    player_df = get_player_info(player_list)

    get_player_stats(player_df, driver)

    driver.quit()

def get_team_url(player_csv):
    player_df = pd.read_csv(player_csv)

    team_urls = player_df['team_url'].unique()

    print(team_urls)

    return team_urls

def team_scraper():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    driver = webdriver.Chrome(options=options)

    team_urls = get_team_url('player_data.csv')

    teams = []

    for team_url in team_urls:
        print(f"Getting team info for {team_url}")

        driver.get(team_url)

        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        team_logo_div = soup.find('div', class_='TeamLogo_block__rSWmO')

        if team_logo_div:
            team_logo_url = team_logo_div.find('img').get('src')

        id = team_url.split('/')[-2]
        
        team_name_divs = soup.find('div', class_='TeamHeader_name__MmHlP')

        team_city = ''
        team_name = ''
        team_full_name = ''

        if team_name_divs:
            team_name_divs = team_name_divs.find_all('div')

            team_city = team_name_divs[0].text.strip()

            team_name = team_name_divs[1].text.strip()

            team_full_name = f"{team_city} {team_name}"

        coaching_staff_divs = soup.find('div', class_='TeamProfile_sectionCoaches__e66bL').find('div', class_='Block_titleContainerBetween__0GYet').find_next_sibling().find_all('div')

        head_coach = ''
        associate_head_coach = []
        assistant_coach = []

        if len(coaching_staff_divs) >= 3:

            head_coach_div = coaching_staff_divs[0]
            head_coach = head_coach_div.find('ul', class_='TeamCoaches_list__xqA2i').find('li').text.strip()

            associate_head_coach_list = coaching_staff_divs[1].find('ul', class_='TeamCoaches_list__xqA2i').find_all('li')

            assistant_coach_list = coaching_staff_divs[2].find('ul', class_='TeamCoaches_list__xqA2i').find_all('li')
        elif len(coaching_staff_divs) == 2:
            head_coach_div = coaching_staff_divs[0]
            head_coach = head_coach_div.find('ul', class_='TeamCoaches_list__xqA2i').find('li').text.strip()

            assistant_coach_list = coaching_staff_divs[1].find('ul', class_='TeamCoaches_list__xqA2i').find_all('li')
        elif len(coaching_staff_divs) == 1:
            head_coach_div = coaching_staff_divs[0]
            head_coach = head_coach_div.find('ul', class_='TeamCoaches_list__xqA2i').find('li').text.strip()

        associate_head_coach = [coach.text.strip() for coach in associate_head_coach_list]

        assistant_coach = [coach.text.strip() for coach in assistant_coach_list]

        team_dict = {
            'id': id,
            'name': team_name,
            "city": team_city,
            'full_name': team_full_name,
            'url': team_url,
            'logo_url': team_logo_url,
            'head_coach': head_coach,
            'associate_head_coach': associate_head_coach,
            'assistant_coach': assistant_coach
        }

        teams.append(team_dict)

    team_df = pd.DataFrame(teams)

    print(team_df.head())

    team_df.to_csv('team_data.csv', index=False)

    driver.quit()

def main():
    team_scraper()
    # player_scraper()


if __name__ == '__main__':
    main()


