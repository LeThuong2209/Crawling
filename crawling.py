from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin
import time

from crawl4ai import AsyncWebCrawler

def selenium_task(key_word):
    
    driver = webdriver.Chrome()
    try:
        driver.get("https://scholar.google.com/")
        search_bar = driver.find_element(By.NAME, 'q')
        search_bar.send_keys(key_word)
        search_bar.send_keys(Keys.RETURN)

        time.sleep(3)

        links = []
        links_element = driver.find_elements(By.XPATH, '//h3[@class="gs_rt"]/a')

        for elements in links_element:
            href = elements.get_attribute("href")
            if href:
                links.append(href)

        if len(links) != 0:
            print(f"Tìm thấy {len(links)} link: ")
            for i, link in enumerate(links):
                print(f"{i}.", link)
            return links
        else:
            print("Can't find anything")
    finally:
        driver.quit()
        
async def crawling_web(url):
    async with AsyncWebCrawler() as crawler:
        list1 = []
        for i in url:
            result = await crawler.arun(i)
            link = None
            soup = BeautifulSoup(result.html, "html.parser")
            for j in soup.find_all("a", href = True):
                href = j["href"]
                if "/doi/reader" in href.lower():
                    link = urljoin(url, href)
                    break
            list1.append(link)
        return list1
    
if __name__ == "__main__":
    key_word = input("Entering your key word: ")
    link_list = selenium_task(key_word)
    if link_list:
        links = asyncio.run(crawling_web(link_list))
        for link in links:
            print(link)
    else:
        print("No result.")
