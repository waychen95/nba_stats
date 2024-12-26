import datetime
import pandas as pd
import numpy as np
import requests
import time
import os
import psycopg2
import random
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from fake_useragent import UserAgent

def get_player_info(player_list, value):
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

        print(f"Getting player info for {player_first_name} {player_last_name}")

        player_team_a_tag = player_info_list[1].find('a')
        if player_team_a_tag:
            player_team = player_team_a_tag.text.strip()
            player_team_url = f"{domain}{player_team_a_tag.get('href')}"
        else:
            player_team = player_info_list[1].text.strip()
            player_team_url = ''
            print(f"Player {player_first_name} {player_last_name} is not currently on a team, using {player_team} as the team name")

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
    player_df.to_csv(f"players/player_data_{value}.csv", index=False)

    return player_df

def get_players_stats(player_df, driver, value):

    # Base URL for player stats
    player_stats_url = 'https://www.nba.com/stats/player/'

    # List to store all player stats dictionaries
    all_player_stats = []

    # List to store missing player IDs
    missing_data = []

    required_columns = [
        'year', 'team', 'gp', 'min', 'pts', 'fgm', 'fga', 'fg%', '3pm', '3pa', '3p%', 
        'ftm', 'fta', 'ft%', 'oreb', 'dreb', 'reb', 'ast', 'tov', 'stl', 'blk', 'pf', 
        'fp', 'dd2', 'td3', '+/-', 'player_id'
    ]

    for index, row in player_df.iterrows():
        print(f"Getting player stats for {row['first_name']} {row['last_name']} (Row {index})")

        player_id = row['id']
        player_url = f"{player_stats_url}{player_id}?SeasonType=Regular%20Season"

        driver.get(player_url)

        # Check if "No data available" appears
        try:
            no_message_xpath = '/html/body/div[1]/div[2]/div[2]/section/div[4]/section[3]/div/div[2]'
            no_message = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, no_message_xpath))
            )
            if no_message.text.strip().lower() == 'no data available':
                print(f"No data available for {row['first_name']} {row['last_name']}")
                continue
        except:
            pass  # Proceed if "No data available" does not show up

        # Attempt to locate stats table
        retries = 3
        while retries > 0:
            try:
                table_xpath = "//div[@class='Crom_container__C45Ti crom-container']/table"
                table = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.XPATH, table_xpath))
                )
                print(f"Stats table found for {row['first_name']} {row['last_name']}")
                break
            except:
                print(f"Retrying for table... ({3 - retries} attempts left)")
                retries -= 1
                time.sleep(random.randint(1, 3))

        if retries == 0:
            print(f"Stats table not found for {row['first_name']} {row['last_name']}")
            missing_data.append(player_id)
            continue

        # Get updated page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract table headers dynamically
        column_headers = [
            th.text.strip().lower()
            .replace('by year', 'year')
            .replace('season', 'year')
            for th in soup.find('tr', class_='Crom_headers__mzI_m').find_all('th')
        ]


        # Extract stats rows
        player_stats_list = soup.find('tbody', class_='Crom_body__UYOcU').find_all('tr')

        for player_stats in player_stats_list:
            stats = player_stats.find_all('td')

            # Map stats to their respective headers
            stats_dict = {
                column_headers[i]: (stat.text.strip() if stat.text.strip() != '-' else '')
                for i, stat in enumerate(stats)
            }


            # Add player_id to the stats
            stats_dict['player_id'] = player_id

            # Append to overall stats list
            all_player_stats.append(stats_dict)

    # Convert the list of stats dictionaries into a DataFrame
    all_stats_df = pd.DataFrame(all_player_stats)

    all_stats_df.to_csv(f'player_stats_all_{value}.csv', index=False)

    # Keep only the required columns
    final_stats_df = all_stats_df[required_columns]

    # Export final data to CSV
    final_stats_df.to_csv(f'player_stats/player_stats_{value}.csv', index=False)
    print(f"Player stats saved to 'player_stats_{value}.csv'")

    # Save missing player IDs to a separate CSV
    missing_data_df = pd.DataFrame(missing_data, columns=['player_id'])
    missing_data_df.to_csv(f'missing_stats_data_{value}.csv', index=False)
    print(f"Missing data saved to 'missing_data_{value}.csv'")


def get_player_stats(row, driver):
    player_stats_url = 'https://www.nba.com/stats/player/'

    player_stats_all_df = pd.DataFrame()

    column_headers = []

    print(f"Getting player stats for {row['first_name']} {row['last_name']}")

    player_id = row['id']
    player_url = f"{player_stats_url}{player_id}?SeasonType=Regular%20Season"

    print(player_url)
    page_source = driver.get(player_url)

    retries = 3

    # Wait until the table is present and visible
    while retries > 0:
        try:
            table_xpath = "//div[@class='Crom_container__C45Ti crom-container']/table"
            table = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, table_xpath))
            )
            break
        except:
            print('Table not found, retrying...')
            retries -= 1
            time.sleep(random.randint(1, 3))
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

    player_stats_all_df.to_csv(f"player_stats_{player_id}.csv", index=False)

def player_scraper(value):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    # start_year = 2020
    # end_year = 2021

    # years = []

    # for year in range(start_year, end_year):
    #     year_end = year + 1
    #     year_end = str(year_end)[-2:]
    #     years.append(f'{year}-{year_end}')

    type = 'Regular Season'

    driver = webdriver.Chrome(options=options)

    driver.get('https://www.nba.com/players')

    toggle = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div[2]/section/div/div[2]/div[1]/div[6]/label/div/span')
    if not toggle.is_selected():
        toggle.click()

    # change the dropdown value to the desired value
    dropdown_name = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div[2]/section/div/div[2]/div[1]/div[1]/label/div/select')

    # Use the Select class to interact with the dropdown
    select_dropdown = Select(dropdown_name)

    # Select the option with the value "A"

    select_dropdown.select_by_value(value)

    print(f"Dropdown value: {select_dropdown.first_selected_option.text}")

    # Set dropdown to "All"
    dropdown_row = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div[2]/section/div/div[2]/div[1]/div[7]/div/div[3]/div/label/div/select')
    select_row = Select(dropdown_row)
    select_row.select_by_visible_text("1")
    time.sleep(1)
    select_row.select_by_visible_text("All")

    # Wait for rows to load
    time.sleep(5)

    print(f"Selected option: {select_row.first_selected_option.text}")

    page_source = driver.page_source

    soup = BeautifulSoup(page_source, 'html.parser')

    # with open('output.html', 'w', encoding='utf-8') as file:
    #     file.write(soup.prettify())

    player_list = soup.find('table', class_='players-list').find('tbody').find_all('tr')

    print(f"Total players: {len(player_list)}")

    player_df = get_player_info(player_list, value)

    get_players_stats(player_df, driver, value)

    driver.quit()

def player_number_age_scraper(player_df, value):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    driver = webdriver.Chrome(options=options)

    player_number_age_df = pd.DataFrame()

    for index, row in player_df.iterrows():
        print(f"Getting player number and age for {row['first_name']} {row['last_name']} in row {index} for {row['url']}")

        player_url = row['url']

        driver.get(player_url)

        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        player_number = ''
        player_age = ''

        player_number_div = soup.find('div', class_='PlayerSummary_mainInnerPlayer__YGffe')

        if player_number_div:
            player_number_p = player_number_div.find('p', class_='PlayerSummary_mainInnerInfo__jv3LO')
            if player_number_p:
                player_number_p_text = player_number_p.text.strip()
                player_number_split = player_number_p_text.split(' | ')
                if len(player_number_split) > 1:
                    player_number = player_number_split[1].strip().replace('#', '').strip()
                else:
                    print(f"No player number found for {row['first_name']} {row['last_name']}")

        print(f"Player number: {player_number}")

        player_age_div = soup.find_all('div', class_='PlayerSummary_playerInfo__om2G4')

        player_age_container = None
        player_birthdate_container = None

        for div in player_age_div:
            label_div = div.find('p', class_='PlayerSummary_playerInfoLabel__hb5fs')
            if label_div:
                if label_div.text.strip() == 'AGE':
                    player_age_container = div
                elif label_div.text.strip() == 'BIRTHDATE':
                    player_birthdate_container = div

        if player_age_container:
            player_age_p = player_age_container.find('p', class_='PlayerSummary_playerInfoValue__JS8_v')
            if player_age_p:
                player_age = player_age_p.text.strip().split(' ')[0]
        else:
            player_age = 0

        if player_birthdate_container:
            player_birthdate_p = player_birthdate_container.find('p', class_='PlayerSummary_playerInfoValue__JS8_v')
            if player_birthdate_p:
                player_birthdate = player_birthdate_p.text.strip()
                player_age = datetime.datetime.now().year - int(player_birthdate.split(', ')[-1])
                print(f"Player birthdate: {player_birthdate}")
        else:
            player_birthdate = 'No birthdate available'
            print(f"No player birthdate found for {row['first_name']} {row['last_name']}")

        
        if player_age == 0:
            player_age = 'No age available'
        else:
            print(f"Player age: {player_age}")

        player_number_age_dict = {
            'id': row['id'],
            'number': player_number,
            'age': player_age,
            'birthdate': player_birthdate
        }

        player_number_age_df = pd.concat([player_number_age_df, pd.DataFrame([player_number_age_dict])], ignore_index=True)

    # Remove rows with no player number
    # player_number_age_df = player_number_age_df[~player_number_age_df['number'].isnull()]

    player_number_age_df.to_csv(f'player_ages/player_number_age_{value}.csv', index=False)

    driver.quit()

def player_bio_scraper(player_df, value):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    driver = webdriver.Chrome(options=options)

    player_bio_df = pd.DataFrame()

    for index, row in player_df.iterrows():

        player_url = row['url']

        player_name = f"{row['first_name']}-{row['last_name']}"

        url = f"https://www.nba.com/player/{row['id']}/{player_name}/bio"

        print(f"Getting player bio for {row['first_name']} {row['last_name']} in row {index} for {url}")

        driver.get(url)

        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        # for title in player_bio_title:
        #     if title.text.strip().lower() == 'player bio':
        #         print(f"Player bio found for {row['first_name']} {row['last_name']}")
        #         player_bio_exist = True
        #         break

        player_bio_div = soup.find('div', class_='PlayerBio_player_bio__kIsc_')

        player_bios = {}

        if player_bio_div:
            print(f"Player bio found for {row['first_name']} {row['last_name']}")
            player_bio_container = player_bio_div.find_all('div', class_='cplayer-bio__container')
            for container in player_bio_container:
                title = container.find('h2', class_='cplayer-bio__title').text.strip()
                bio = container.find('div', class_='cplayer-bio__content').text.strip()
                # clean ambiguous unicode characters
                bio = bio.replace('\u2019', "'").replace('\u2014', '-').replace('\u2013', '-').replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
                player_bios[title] = bio
        else:
            print(f"No player bio found for {row['first_name']} {row['last_name']}")


        player_bio_dict = {
            'id': row['id'],
            'professional_bio': player_bios.get('PROFESSIONAL CAREER', 'No professional bio available'),
            'personal_bio': player_bios.get('PERSONAL LIFE', 'No personal bio available'),
            'before_nba_bio': player_bios.get('BEFORE NBA', 'No before NBA bio available'),
            'url': url
        }

        player_bio_df = pd.concat([player_bio_df, pd.DataFrame([player_bio_dict])], ignore_index=True)

    player_bio_df.to_csv(f'player_bios/player_bio_{value}.csv', index=False)

    driver.quit()

def get_team_url(player_csv):
    player_df = pd.read_csv(player_csv)

    team_urls = player_df['team_url'].unique()

    return team_urls

def load_existing_team_data():
    try:
        existing_team_df = pd.read_csv('team_data.csv')
    except pd.errors.EmptyDataError:
        existing_team_df = pd.DataFrame()
    except FileNotFoundError:
        existing_team_df = pd.DataFrame()
    except Exception as e:
        print(f"Error: {e}")

    return existing_team_df

def team_scraper():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless')
    options.add_argument(f'user-agent={UserAgent().random}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')

    driver = webdriver.Chrome(options=options)

    team_urls = get_team_url('player_data.csv')

    existing_team_df = load_existing_team_data()

    error_urls = []

    for team_url in team_urls:
        print(f"Getting team info for {team_url}")

        id = ''
        team_name = ''
        team_city = ''
        team_full_name = ''
        team_logo_url = ''

        try:
            driver.get(team_url)

            page_source = driver.page_source

            soup = BeautifulSoup(page_source, 'html.parser')

            team_logo_div = soup.find('div', class_='TeamLogo_block__rSWmO')

            if team_logo_div:
                team_logo_url = team_logo_div.find('img').get('src')

            id = team_url.split('/')[-3]

            if not existing_team_df.empty and id in existing_team_df['id'].values:
                print(f"Team {id} already exists")
                continue

            team_name_divs = soup.find('div', class_='TeamHeader_name__MmHlP')

            if team_name_divs:
                team_name_divs = team_name_divs.find_all('div')
                team_city = team_name_divs[0].text.strip()
                team_name = team_name_divs[1].text.strip()
                team_full_name = f"{team_city} {team_name}"

            coaching_staff_divs = soup.find('div', class_='TeamProfile_sectionCoaches__e66bL').find('div', class_='Block_titleContainerBetween__0GYet').find_next_sibling().find_all('div')

            head_coach = ''
            associate_head_coach_list = []
            assistant_coach_list = []

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

            # Append the new data to the existing DataFrame
            if existing_team_df.empty:
                existing_team_df = pd.DataFrame([team_dict])
            else:
                existing_team_df = pd.concat([existing_team_df, pd.DataFrame([team_dict])], ignore_index=True)

            # Save the updated DataFrame to the CSV
            existing_team_df.to_csv('team_data.csv', index=False)

            print(f"Saved team {team_full_name} to CSV")

        except Exception as e:
            print(f"Error: {e} while processing {team_url}")
            error_urls.append(team_url)
            continue

        time.sleep(random.randint(3, 5))

    print(f"Error URLs: {error_urls}")

    driver.quit()

def team_bio_text_checker(bio_text, first_name, last_name):
    bio_text_lower = bio_text.lower()

    first_name_lower = first_name.lower()
    last_name_lower = last_name.lower()

    if first_name_lower not in bio_text_lower and last_name_lower not in bio_text_lower:
        return "No bio text found"
    
    return bio_text


def main():

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')


    # player_scraper('Š')

    # Š

    active_player_df = pd.read_csv('active_players.csv')

    player_df = pd.read_csv('players/player_data_G.csv')

    # player_number_age_scraper(player_df, 'G')

    player_bio_scraper(player_df, 'G')


if __name__ == '__main__':
    main()


