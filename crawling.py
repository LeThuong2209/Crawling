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
        page = 1
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
        if (url.find("reader") != -1):
            url = url.replace("reader", "pdf")

        response = requests.get(url)

        if (response.status_code == 200):
            check = False
            file_path = os.path.join(out_put, os.path.basename(url))
            with open(file_path, "wb") as f:
                f.write(response.content)
    if check == True:
        print("Downloading failed")
    else :
        print("Completed !!!")
        
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
    else:
        print("❌No result.")