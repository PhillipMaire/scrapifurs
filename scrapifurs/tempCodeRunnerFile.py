
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
import numpy as np 


from scrapifurs import utils
from scrapifurs.GPTinstructions import GPTinstructions

# setup basic variable as dict 
info_dict = {'init_url':'https://www.linkedin.com/',
             'save_password_dir':'/Users/phil/Dropbox/GITHUB/DATA/saved_cookies',
             'start_url':'https://www.linkedin.com/search/results/people/?keywords=data%20scientist&origin=CLUSTER_EXPANSION&sid=fRq'}
info_dict['full_cookies_save_path'] = info_dict['save_password_dir']+os.sep+"linkedin_cookies.pkl"


# setup API key for chatGPT 
load_dotenv()  # take environment variables from .env.
os.environ["OPENAI_API_KEY"]  = os.getenv("OPENAI_API_KEY")
openai.api_key = os.environ["OPENAI_API_KEY"]


#init chrome 
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)

driver.get(info_dict['init_url'])
time.sleep(5)


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
    

input('''set zoom to 25% for winow to see all website data that it needs, press enter to continue''')
