
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from dotenv import load_dotenv
import os
import openai

from bs4 import BeautifulSoup
import re
import time
import pickle
import random
import glob

from scrapifurs.search_jobs_window import DataFile


def update_master_files(data_folder, fn_applied, fn_skipped):
    files = glob.glob(f'{data_folder}/*.xlsx')

    # Define initial columns (adjust as needed)
    initial_columns = ['job_id', 'job_title', 'company_name', 'job_location', 'salary_range', 'apply_link']
    # Load or initialize DataFrames for applied and skipped files
    try:
        df_applied = pd.read_excel(fn_applied)
    except FileNotFoundError:
        df_applied = pd.DataFrame(columns=initial_columns)

    try:
        df_skipped = pd.read_excel(fn_skipped)
    except FileNotFoundError:
        df_skipped = pd.DataFrame(columns=initial_columns)

    # Define a mapping for common keys
    key_mapping = {
        'job_ids': 'job_id',
        'job_title': 'job_title',
        'company_name': 'company_name',
        'Location': 'job_location',
        'pay': 'salary_range',
        'job_link': 'linked_in_link',
        'about_the_job' : 'description',
        # Add more mappings as needed
    }

    for fn in files:
        data_class = DataFile(fn, False)  # Assuming data_file is a class that loads the file
        for status, df_target in [(1, df_applied), (2, df_skipped)]:
            filtered_data = data_class.df_main[data_class.df_main["0_new__1_applied__2_skipped"] == status]
            
            # Map and combine data
            processed_data = filtered_data.rename(columns=key_mapping)
            additional_keys = set(filtered_data.columns) - set(key_mapping.keys())
            for key in additional_keys:
                processed_data[key] = filtered_data[key]

            # Append unique data
            unique_data = processed_data[~processed_data['job_id'].isin(df_target['job_id'])]
            df_target = pd.concat([df_target, unique_data], ignore_index=True)

            # Update the original DataFrames
            if status == 1:
                df_applied = df_target
            else:
                df_skipped = df_target

    # Save the results
    df_applied.to_excel(fn_applied, index=False)
    df_skipped.to_excel(fn_skipped, index=False)
    

def _check_pkl(name):
    if name[-4:] != '.pkl':
        return name + '.pkl'
    return name


def save_obj(obj, name, protocol=4):
    with open(_check_pkl(name), 'wb') as f:
        # pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        pickle.dump(obj, f, protocol=protocol)


def load_obj(name):
    with open(_check_pkl(name), 'rb') as f:
        return pickle.load(f)
    
def generate_numbers(n, total, min_val, max_val):
    print('asdfasfasfdasdfasdf')
    numbers = []
    while len(numbers) < n:
        remaining = total - sum(numbers)
        next_val = remaining if len(numbers) == n - 1 else random.randint(min_val, max_val)
        if sum(numbers) + next_val > total:
            continue
        numbers.append(next_val)
    return numbers



def click_next_button(driver):
    
    try:
        next_button = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Next']"))
        )
        next_button.click()

    except Exception as e2:
        raise Exception(f"Failed to find by aria-label, error: {str(e2)}")


def get_lxml_text(driver, remove_empty_lines=True):
#     time.sleep(5)  # Allow the page to load

    # Get the source HTML of the page
    source = driver.page_source

    # Parse the source HTML with BeautifulSoup
    soup = BeautifulSoup(source, 'lxml')

    # Get the text from the parsed HTML
    url_text = soup.get_text()
    if remove_empty_lines:
        # Split the text into lines and remove empty lines
        lines = url_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip() != ""]

        # Join the non-empty lines back into a single string
        url_text = "\n".join(non_empty_lines)

    return url_text



class StringSectionExtractor():
    '''
    
To request an appropriate pattern or string match for this class, you could ask:

"Please provide a string or a regular expression pattern that we should use for the start 
rule or end rule. If you provide a regular expression pattern, please specify that it is 
a regex. Also, note that for regular expressions, we're using Python's 're' module, so the 
pattern should be compatible with it. If you want to extract from the start or end of the 
text when no matching rule is found, please indicate that as well."
    '''

    def __init__(self):
        self.start_rules = []
        self.end_rules = []

    def add_start_rule(self, rule, is_regex=False):
        self.start_rules.append((rule, is_regex))

    def add_end_rule(self, rule, is_regex=False):
        self.end_rules.append((rule, is_regex))

    def extract(self, text, extract_if_no_start=False, extract_if_no_end=False):
        if len(self.start_rules) > 0 and not extract_if_no_start:
            start_index = None
        else:
            start_index = 0

        if len(self.end_rules) > 0 and not extract_if_no_end:
            end_index = None
        else:
            end_index = len(text)



        for rule, is_regex in self.start_rules:
            if is_regex:
                match = re.search(rule, text)
                if match is not None:
                    start_index = match.end()  # We want the index after the start rule
                    break  # If we've found a match, we can break
            else:
                idx = text.find(rule)
                if idx != -1:
                    start_index = idx + len(rule)  # We want the index after the start rule
                    break  # If we've found a match, we can break

        for rule, is_regex in self.end_rules:
            if is_regex:
                match = re.search(rule, text[start_index if start_index is not None else 0:])
                if match is not None:
                    end_index = (start_index if start_index is not None else 0) + match.start()  # We want the index before the end rule
                    break  # If we've found a match, we can break
            else:
                idx = text.find(rule, start_index if start_index is not None else 0)  # We search after the start index
                if idx != -1:
                    end_index = idx
                    break  # If we've found a match, we can break

        if start_index is None or end_index is None:
            return ''
        
        return text[start_index:end_index]




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
    # def click_search_button(self):
    #     """Clicks the search button."""
    #     try:
    #         # Locate the button by its class name
    #         search_button_xpath = "//button[contains(@class, 'jobs-search-box__submit-button')]"
    #         search_button = WebDriverWait(self.driver, 10).until(
    #             EC.element_to_be_clickable((By.XPATH, search_button_xpath))
    #         )
    #         search_button.click()
    #     except TimeoutException:
    #         print("Timed out waiting for the search button to be clickable.")

    
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
    if len(all_ids) == 0:
        return np.asarray([])
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

        
            
        

        if job_title != "" and company_name != "":
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
        # sort by newest jobs first!
        self.df_main = self.df_main.sort_values(by='job_ids', ascending=False).reset_index(drop=True)
        
        try:
            self.df_main.to_excel(self.filename, index=False)
        except Exception as e:
            print(f"Error saving {self.filename}: {e}")





# def scrape_job_data(info_dict, data_class, n_pages_to_scrape=5, wait_sec_each_page=5, update_every_n_secs=360, existing_job_ids=[]):
#     """
#     Scrapes job data for a specified number of pages and intervals.

#     Args:
#     - info_dict: A dictionary containing start_url and other necessary information.
#     - data_class: An instance of a DataClass containing df_main and a save_it method.
#     - n_pages_to_scrape: Number of pages to scrape.
#     - wait_sec_each_page: Time to wait on each page before scraping.
#     - update_every_n_secs: How often to update the data in seconds.
#     """

#     driver = open_browser(info_dict)
#     driver.get(info_dict['start_url'])

#     try:
#         while True:
#             for n_page in range(n_pages_to_scrape):
#                 if n_page == 0:
#                     # Go back to the first page
#                     driver.get(info_dict['start_url'])
#                 else:
#                     go_to_next_page(driver)
#                 time.sleep(wait_sec_each_page)
#                 # Update data
#                 job_data = get_job_details(driver, existing_job_ids)
#                 job_data = pd.DataFrame(job_data)
#                 job_data['job_ids'] = job_data['job_ids'].astype('int')
#                 data_class.df_main = update_dataframe(data_class.df_main, job_data, ['job_ids'])
            
#                 data_class.save_it()
            
#             print('_____________________________________________\n\n____________________')
#             time.sleep(update_every_n_secs)
#     finally:
#         driver.quit()



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
