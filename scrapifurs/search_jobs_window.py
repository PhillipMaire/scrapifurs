# Selenium related imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# BeautifulSoup for web scraping
from bs4 import BeautifulSoup

# Standard Python libraries
import os
import re
import time
import pickle
import glob
from datetime import datetime

# Data manipulation and analysis
import pandas as pd
import numpy as np

# Visualization libraries
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Machine Learning and data processing
from scipy.cluster.hierarchy import linkage, leaves_list

# Geolocation services
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Other specific libraries
from dotenv import load_dotenv
import openai
from tqdm import tqdm

# Custom module imports
from scrapifurs import utils
from scrapifurs.GPTinstructions import GPTinstructions


class JobListings:
    def __init__(self, driver):
        self.driver = driver
        self.job_titles = []
        self.current_job_index = -1  # Start before the first index
    def click_search_button(self):
        """Clicks the search button."""
        try:
            # Locate the button by its class name
            search_button_xpath = "//button[contains(@class, 'jobs-search-box__submit-button')]"
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, search_button_xpath))
            )
            search_button.click()
        except TimeoutException:
            print("Timed out waiting for the search button to be clickable.")
        except NoSuchWindowException:
            print("Browser window not found. Please check if the browser is still open.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    def load_job_titles(self):
        """Loads all job titles into the list."""
        try:
            # XPath to match all job title anchor tags
            job_title_elements_xpath = "//a[contains(@class,'job-card-list__title')]"
            # Wait for the job titles to be present to ensure the page has loaded
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, job_title_elements_xpath))
            )
            # Find all job title elements
            self.job_titles = self.driver.find_elements(By.XPATH, job_title_elements_xpath)
        except TimeoutException:
            print("Timed out waiting for job titles to appear.")
            self.job_titles = []
    
    def get_job_count(self):
        """Returns the number of jobs loaded."""
        return len(self.job_titles)
    
    def click_next_job(self):
        """Clicks the next job title in the list."""
        self.current_job_index += 1
        if self.current_job_index < len(self.job_titles):
            job_title_element = self.job_titles[self.current_job_index]
            self.driver.execute_script("arguments[0].scrollIntoView(true);", job_title_element)
            job_title_element.click()
            # You can add a wait here for the job details to load if necessary
        else:
            print("No more jobs to click.")
            return False
        return True
    
    def get_about_job_info(self):
        """Extracts the 'About the job' information from the job details page."""
        try:
            # Assuming the job details have been loaded at this point
            about_job_xpath = "//h2[text()='About the job']/following-sibling::span"
            about_job_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, about_job_xpath))
            )
            return about_job_element.text
        except TimeoutException:
            print("Timed out waiting for the 'About the job' section to appear.")
            return None
    def click_job_by_index(self, index):
        """Clicks a job title in the list based on its index."""
        if index < len(self.job_titles):
            job_title_element = self.job_titles[index]
            self.driver.execute_script("arguments[0].scrollIntoView(true);", job_title_element)
            job_title_element.click()
            return True
        else:
            print(f"Index {index} is out of range for the job titles list.")
            return False
            
def open_browser(info_dict):
    #init chrome 
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    
    driver.get(info_dict['init_url'])
    time.sleep(1)
    driver.get(info_dict['init_url'])
    time.sleep(2)
    
    
    # Load cookies if they exist
    try:
        cookies = pickle.load(open(info_dict['full_cookies_save_path'], "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        assert(not not cookies)# if empty try a different method
    except:
        print("No cookies found. Manual login required.")
        # If not logged in
        input('Please login and press Enter to continue...')
        pickle.dump(driver.get_cookies(), open(info_dict['full_cookies_save_path'], "wb")) # save cookies after login
    time.sleep(4)
    return driver
        
    

def go_to_next_page(driver):
    try:
        # Step 1: Find the pagination element
        pagination = driver.find_element(By.CSS_SELECTOR, 'ul.artdeco-pagination__pages')
    except NoSuchElementException:
        print("Pagination not found")
        return

    try:
        # Step 2: Find the current active page
        current_page_elem = pagination.find_element(By.CSS_SELECTOR, 'li.active')
        current_page = int(current_page_elem.text)
    except NoSuchElementException:
        print("Current page not found")
        return

    # Step 3: Find the next page
    next_page = current_page + 1
    next_page_selector = f'li[data-test-pagination-page-btn="{next_page}"]'

    try:
        next_page_elem = pagination.find_element(By.CSS_SELECTOR, next_page_selector)
    except NoSuchElementException:
        print("Next page not found")
        return

    # Step 4: Click the next page
    next_page_elem.click()




def update_dataframe(df_main, df_new, keys=None):
    # Updated keys to include all from the job_dict
    if keys is None:
        keys = ['job_ids', 'is_promoted', 'job_title', 'company_name', 'Location', 'pay', 
                'job_link', 'time_added', 'about_the_job', '0_new__1_applied__2_skipped']

    # Initialize df_main if it is None
    if df_main is None:
        df_main = pd.DataFrame(columns=keys)

    # Check if types are the same for each key and correct them if needed
    for key in keys:
        if key in df_new and key in df_main:
            # Ensure the data type of df_new is the same as that of df_main
            df_new[key] = df_new[key].astype(df_main[key].dtype)
        else:
            # If the key does not exist in df_main, add it
            df_main[key] = pd.Series(dtype=df_new[key].dtype)

    # Merge new rows into the main dataframe
    for _, new_row in df_new.iterrows():
        mask = (df_main[keys].to_numpy() == new_row[keys].to_numpy()).all(axis=1)
        if not any(mask):
            df_main = pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True)
            os.system('say "JOB"')  # macOS specific command
            print('\nNEW JOB')
            print(new_row['job_link'])
            print(new_row)

    return df_main

def grab_all_job_ids_in_folder(bd):
    if isinstance(bd, list):
        files = []
        for d in bd:
            files+=glob.glob(f'{d}/*.xlsx')
    else:
        files = glob.glob(f'{bd}/*.xlsx')
    files = [file for file in files if not os.path.basename(file).startswith('~')]
    all_ids = []
    for fn in files:
        data = DataFile(fn, False)
        try:
            all_ids.append(data.df_main['job_ids'])
        except:
            all_ids.append(data.df_main['job_id'])
    return np.unique(np.concatenate(all_ids))


def get_job_details(driver, existing_job_ids=[]):
    job_dict = {
        "job_ids": [],
        "is_promoted": [],
        "job_title": [],
        "company_name": [],
        "Location": [],
        "pay": [],
        "job_link": [],
        "time_added": [],
        "about_the_job": [],
        "0_new__1_applied__2_skipped": [],
    }


    # setup the "about section" grabbing class
    job_listings = JobListings(driver)
    job_listings.load_job_titles()

    # get all the job data for processing
    jobs = driver.find_elements(By.CSS_SELECTOR, '[data-occludable-job-id]')
    about_the_job_list = []  # Assuming this is populated earlier in your code

    for job_ind, job in enumerate(jobs):
        try:
            job_id = job.get_attribute("data-occludable-job-id")
            job_id = int(job_id)
        except NoSuchElementException:
            job_id = -1

        # Skip the job if its ID is -1 or already exists in the existing_job_ids list or variable passed in of previous job IDs
        if job_id == -1 or job_id in existing_job_ids or job_id in job_dict["job_ids"]:
            print(f'Job with ID {job_id} exists, ... skipping')
            continue
        
        try:
            promoted_elements = job.find_elements(By.CSS_SELECTOR, '.job-card-container__footer-item')
            is_promoted = "Promoted" in [e.text for e in promoted_elements]
        except NoSuchElementException:
            is_promoted = False

        try:
            job_title = job.find_element(By.CSS_SELECTOR, '.job-card-list__title').text
        except NoSuchElementException:
            job_title = ""

        try:
            company_name = job.find_element(By.CSS_SELECTOR, '.job-card-container__primary-description').text
        except NoSuchElementException:
            company_name = ""

        try:
            Location = job.find_element(By.CSS_SELECTOR, '.job-card-container__metadata-wrapper li').text
        except NoSuchElementException:
            Location = ""

        try:
            pay = job.find_element(By.CSS_SELECTOR, '.mt1 .job-card-container__metadata-wrapper li').text
        except NoSuchElementException:
            pay = ""
            
        try:
            job_link = job.find_element(By.CSS_SELECTOR, "a.job-card-container__link").get_attribute("href")
        except NoSuchElementException:
            job_link = ""

        
            
        

        if job_title != "" and company_name != "":#$%^ check if the continue is working here since if continue hten it should avoid this 
            # but i think it is running all of them 
            job_dict["job_ids"].append(job_id)
            job_dict["is_promoted"].append(is_promoted)
            job_dict["job_title"].append(job_title)
            job_dict["company_name"].append(company_name)
            job_dict["Location"].append(Location)
            job_dict["pay"].append(pay)
            job_dict["job_link"].append(job_link)
            
            current_time = datetime.now()
            formatted_time = current_time.strftime('%Y%m%d%H%M%S')
            formatted_time_as_int = int(formatted_time)
            job_dict["time_added"].append(formatted_time_as_int)

            
            if job_listings.click_job_by_index(job_ind): #$%^ validate clicks only new ones
                job_dict["about_the_job"].append(job_listings.get_about_job_info())
                time.sleep(np.random.uniform(1.5, 3)) # if its too fast i think linked in will flag 
            else:
                job_dict["about_the_job"].append('NA')

            
            # job_dict["about_the_job"].append(about_the_job)
            job_dict["0_new__1_applied__2_skipped"].append(-1)
    
        
    return job_dict



class DataFile:

    def __init__(self, filename, include_date=False):
        date_str = datetime.now().strftime('_%Y_%m_%d_%H-%M') if include_date else ''
        self.filename = f"{filename.split('.')[0]}{date_str}.xlsx"
        self.exists = self.check_if_exists()
        self.df_main = None
        self.load_it()

    def check_if_exists(self):
        return os.path.exists(self.filename)

    def load_it(self):
        if self.exists:
            try:
                self.df_main = pd.read_excel(self.filename)
            except Exception as e:
                print(f"Error loading {self.filename}: {e}")
        else:
            print(f"File {self.filename} does not exist")

    def save_it(self):
        # Assuming 'job_ids' is a column in the DataFrame. Uncomment and adjust if needed.
        # self.df_main = self.df_main.sort_values(by='job_ids', ascending=False).reset_index(drop=True)
        
        try:
            self.df_main.to_excel(self.filename, index=False)
        except Exception as e:
            print(f"Error saving {self.filename}: {e}")



def scrape_job_data(info_dict, scraper_settings_list, data_class, auto_update_link=True):
    """
    Scrapes job data based on specified settings.

    Args:
    - info_dict: A dictionary containing general information for the browser setup.
    - scraper_settings: A dictionary containing specific settings for scraping, including start_url.
    - data_class: An instance of a DataClass containing df_main and a save_it method.
    """
    for scraper_settings in scraper_settings_list:
        start_url = scraper_settings.get('start_url')
        n_pages_to_scrape = scraper_settings.get('n_pages_to_scrape', 5)
        wait_sec_each_page = scraper_settings.get('wait_sec_each_page', 5)
        update_every_n_secs = scraper_settings.get('update_every_n_secs', 60*5)
        existing_job_ids = scraper_settings.get('existing_job_ids', [])
    
        driver = open_browser(info_dict)
        driver.get(start_url)
        
        if auto_update_link:
            # we click the search button to update the link then print it
            job_listings = JobListings(driver)
            time.sleep(2)
            job_listings.click_search_button()
            current_url = driver.current_url
            print("Current URL:", current_url)
            start_url = current_url
            driver.get(start_url)
    
    
        try:
            while True:
                for n_page in range(n_pages_to_scrape):
                    if n_page == 0:
                        # Go back to the first page
                        driver.get(start_url)
                    else:
                        go_to_next_page(driver)
                    time.sleep(wait_sec_each_page)
                    # Update data
                    job_data = get_job_details(driver, existing_job_ids)
                    job_data = pd.DataFrame(job_data)
                    job_data['job_ids'] = job_data['job_ids'].astype('int')
                    data_class.df_main = update_dataframe(data_class.df_main, job_data, ['job_ids'])
                
                    data_class.save_it()
                
                print('_____________________________________________\n\n_____________________________________________')
                time.sleep(update_every_n_secs)
        finally:
            driver.quit()
