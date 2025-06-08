from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from crawl4ai import AsyncWebCrawler
import xlsxwriter
import requests
import os
import random
import pypdf
import pycountry
import shutil   
import re
#from structure import structure_form

header_list = ["Search date", "Conf", "Country", "Year", "name", "surname", "email", "country", "affiliation"]
country_list = [country.name for country in pycountry.countries]

def selenium_task(key_word):
    #crawl google page to collect all result links
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get("https://scholar.google.com/")
        search_bar = driver.find_element(By.NAME, 'q')
        search_bar.send_keys(key_word)
        search_bar.send_keys(Keys.RETURN)
        input("Solving Captcha, then push 'Enter'...")
        time.sleep(3)
        links = []
        page = 0
        while True:
            time.sleep(random.uniform(2, 5))
            page = page + 1
            url_links = driver.find_elements(By.XPATH, '//h3[@class="gs_rt"]/a')
            
            for link in url_links:
                href = link.get_attribute("href")
                if href:
                    links.append(href)
            #Find button
            try:
                button = driver.find_element(By.LINK_TEXT, "Next")
            except:
                try:
                    button = driver.find_element(By.LINK_TEXT, "Tiếp")
                except:
                    break
            button.click()

            if page == 10:
                break

        return links
    finally:
        driver.quit()
        
async def crawling_web(urls):
    #using crawl4ai to access each link result and find the paper of conf
    async with AsyncWebCrawler() as crawler:
        list1 = []
        for i in urls:
            if i.lower().endswith(".pdf"):
                list1.append(i)
                continue
            result = await crawler.arun(i)
            link = None
            soup = BeautifulSoup(result.html, "html.parser")
            for j in soup.find_all("a", href = True):
                href = j["href"]
                x = href.lower()
                if (x.find("/doi/reader") != -1) or (x.find("/pdf") != -1) or (x.find(".pdf") != -1):  
                    link = urljoin(i, href)
                    break
            if link != None:
                list1.append(link)
        return list1
    
def download_pdf(pdf_urls):
    out_put = './pdf_save'
    os.makedirs(out_put, exist_ok=True)
    print("Downloading...")
    check = True
    for i, url in enumerate(pdf_urls):
        if 'reader' in url:
            url = url.replace("reader", "pdf")
        try:    
            response = requests.get(url, timeout = 20)

            if (response.status_code == 200):
                if response.headers.get("Content-Type", "").lower() == "application/pdf" or response.content[:4] == b"%PDF":
                    check = False
                    file_path = os.path.join(out_put, f"file {i}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(response.content)
        except requests.exceptions.RequestException as e:
            print("ERROR:", {e})

    if check == True:
        print("Downloading failed")
    else :
        print("Completed !!!")

def structuring(email : str, author : str, affiliation : str, key_word : str, country : str, country2 : str) :
    parts = author.split()   
    surname = parts[len(parts) - 1]
    name = ' '.join(parts[0:(len(parts) - 1)])
    year = key_word.split()[-1]
    list1 = {
        'Search date': '2025-06-08',
        'Conf': key_word,
        'Country': country,
        'Year': year,
        'name': name,
        'surname': surname,
        'email': email,
        'country': country2,
        'affiliation': affiliation
    }
    return list1

def pdf_filter(pdf : str, key_word : str, country : str):
    try:
        with open(pdf, 'rb') as pdf:
            reader = pypdf.PdfReader(pdf, strict=False)
            text = reader.extract_text()

            lines = [line.strip() for line in text.split('\n') if line.strip()]
            emails = []
            authors = []
            affiliations = []
            country2 = ''
            for line in lines:
                # Bắt các email dạng {user1, user2}@domain.com
                match = re.findall(r"\{([^}]+)\}@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", line)
                if match:
                    for user_group, domain in match:
                        users = [u.strip() for u in user_group.split(',')]
                        for user in users:
                            emails.append(f"{user}@{domain}")
                    continue

                # Bắt các email thông thường
                found_email = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", line)
                if found_email:
                    emails.extend(found_email)
                    continue
                
                #Bắt affiliation
                if any(keyword in line.lower() for keyword in ["university", "institute", "school", "department", "faculty"]):
                    part = line.split(',')
                    clean_affiliation = [re.sub(r'^\d+\s*', '', p.strip()) for p in part if p.strip()]
                    for aff in clean_affiliation:
                        affiliations.append(aff)

                    for country_tmp in country_list:
                        pattern = r"\b" + re.escape(country_tmp) + r"\b"
                        if re.search(pattern, line):
                            country2 = country_tmp
                            break
                    continue

                #Bắt tên tác giả
                if ',' in line and ', and ' in line:
                    if '@' not in line and not any(k in line.lower() for k in ["university", "institute", "school", "department", "faculty"]):
                        parts = line.replace(', and ', ',').split(',')
                        clean_names = [re.sub(r'[\d†‡*#]+$', '', p.strip()) for p in parts if p.strip()]
                        for name in clean_names:
                            if len(name) != 0:
                                authors.append(name)
                        continue
                if 'abstract' in line.lower():
                    break
                
            max_len = max(len(emails), len(authors), len(affiliations))
            result = []
            for i in range(max_len):
                if i < len(emails) and i < len(authors) and i < len(affiliations):
                    if authors[i]:
                        result.append(structuring(emails[i], authors[i], affiliations[i], key_word, country, country2))
            return result
         
    except pypdf.errors.PdfReadError as e:
        print('------')
        print("ERROR:", {e})
        print('------')
        return []
    except Exception as e:
        print('------')
        print(f"ERROR: {e}")
        print('------')
        return []

def excel_files(header_list : list, data : list):
    result_file = xlsxwriter.Workbook("result.xlsx")
    worksheet = result_file.add_worksheet("Sheet 1")
    for index, header in enumerate(header_list):
        worksheet.write(0, index, str(header))

    for index, entry in enumerate(data):
        for index2, content in enumerate (header_list):
            worksheet.write(index + 1, index2, entry[content])

    result_file.close()

if __name__ == "__main__":
    key_word = input("Entering your key word: ")
    country = input("Entering the country of the conf: ")
    link_list = selenium_task(key_word)
    print(f"Found {len(link_list)} results.")
    if link_list:
        links = asyncio.run(crawling_web(link_list))
        print("✅These are links required.")
        for link in links:
            print(link)
        #asyncio.run(crawl_pdf(links[0]))
        #download files
        download_pdf(links)
        
        folder_path = "pdf_save"
        data = []
        for file in os.listdir(folder_path):
            path = os.path.join(folder_path, file)
            if os.path.isfile(path):
                data.extend(pdf_filter(path, key_word, country))
        
        excel_files(header_list, data)

        #shutil.rmtree("pdf_save") # delete the folder and all its files

    else:
        print("❌No result.")