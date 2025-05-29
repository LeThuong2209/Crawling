import os
import requests
import pypdf
import re

def pdf_fil(pdf : str):
    with open(pdf, 'rb') as pdf:
        reader = pypdf.PdfReader(pdf, strict=False)
        pdf_text = []
        
        for page in reader.pages:
            content = page.extract_text()
            pdf_text.append(content)
        return pdf_text

url = "https://proceedings.mlr.press/v26/nicol12a/nicol12a.pdf"
response = requests.get(url)
if response.status_code == 200:
    with open("this.pdf", 'wb') as f:
        f.write(response.content)   

if __name__ == '__main__':
    extracted_text = pdf_fil("this.pdf")
    for text in extracted_text:
        split_message = re.split(r'\s+|[,i?!.-]\s*', text.lower())
        if 'gmail' in split_message:
            print(split_message)