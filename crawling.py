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
import shutil   
import re
#from structure import structure_form

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

            if page == 2:
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
    for url in pdf_urls:
        if 'reader' in url:
            url = url.replace("reader", "pdf")
        try:    
            response = requests.get(url, timeout = 20)

            if (response.status_code == 200):
                check = False
                file_path = os.path.join(out_put, os.path.basename(url))
                with open(file_path, "wb") as f:
                    f.write(response.content)
        except requests.exceptions.RequestException as e:
            print("ERROR:", {e})

    if check == True:
        print("Downloading failed")
    else :
        print("Completed !!!")

def pdf_filter(pdf : str):
    try:
        with open(pdf, 'rb') as pdf:
            reader = pypdf.PdfReader(pdf, strict=False)
            pdf_text = []
            
            for page in reader.pages:
                content = page.extract_text()
                pdf_text.append(content)
            return pdf_text  
    except pypdf.errors.PdfReadError as e:
        print('------')
        print("ERROR:", {e})
        print('------')
        return []
    except Exception as e:
        print('------')
        print("UNDEFINED ERROR.")
        print('------')
        return []

if __name__ == "__main__":
    key_word = input("Entering your key word: ")

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
        for file in os.listdir(folder_path):
            path = os.path.join(folder_path, file)
            if os.path.isfile(path):
                extracted_text = pdf_filter(path)
                for text in extracted_text:
                    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
                    if len(emails) != 0:
                        for email in emails:
                            print(email)
        shutil.rmtree("pdf_save") # delete the folder and all its files

    else:
        print("❌No result.")