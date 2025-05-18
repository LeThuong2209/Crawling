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

def selenium_task(key_word, pages):
    #crawl google page to collect all result links
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get("https://scholar.google.com/")
        search_bar = driver.find_element(By.NAME, 'q')
        search_bar.send_keys(key_word)
        search_bar.send_keys(Keys.RETURN)

        time.sleep(3)

        links = []
        #links_element = driver.find_elements(By.XPATH, '//h3[@class="gs_rt"]/a')
        
        for i in range(pages + 1):
            links_element = driver.find_elements(By.XPATH, '//h3[@class="gs_rt"]/a')
            for j in links_element:
                links.append(j.get_attribute("href"))
            try:
                next_button = driver.find_element(By.LINK_TEXT, "Next")
                next_button.click()
                time.sleep(2)
            except:
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
                if "/doi/reader" in href.lower():
                    link = urljoin(i, href)
                    break
            list1.append(link)
        return list1
    
if __name__ == "__main__":
    key_word = input("Entering your key word: ")
    pages = int(input("Enterring number of pages you want to crawl: "))
    link_list = selenium_task(key_word, pages)
    print(f"Found {len(link_list)} results.")
    if link_list:
        links = asyncio.run(crawling_web(link_list))
        for link in links:
            print(link)
    else:
        print("No result.")
