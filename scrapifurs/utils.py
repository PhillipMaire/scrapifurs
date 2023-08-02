
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


