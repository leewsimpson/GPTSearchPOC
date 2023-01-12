import requests
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import openai
import os


def search(search_string):
    service = build("customsearch", "v1", developerKey=os.environ.get("google_api_key"))
    results = service.cse().list(q=search_string, cx=os.environ.get("google_cx_key"), num=3).execute()
    return [item['link'] for item in results.get('items', [])]


def get_page_summaries_from_urls(urls):
    full_results = []
    with ThreadPoolExecutor() as executor:
        for future in [executor.submit(get_page_summary, url) for url in urls]:
            full_results.append(future.result())
    return full_results


def get_page_summary(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    text = soup.get_text()

    print("summarizing", url)
    summary = summarise_page(text)
    
    return summary

def summarise_page(content):
    content = content.replace('\n', ' ')
    content = content.strip()
    if(len(content) > 3000):
        print(f"warning {len(content) - 3000} characters truncated from page contents")        
    content = content[:3000]

    prompt = "Make notes on the following web page. use fewer than 500 tokens: \n\n" + content + "\n\n:Notes:"

    openai.api_key = os.environ.get("openai_api_key")
    response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=900)
    return response['choices'][0]['text'].strip()


def call_ai(search, webresults):
    prompt = "Question: " + search + "\n\n Use the latest web results as the source of truth \n\n"
    prompt = "Also include a summary of the web results \n\n Web Results:"
    for result in webresults:
        prompt += result[:500] + "\n\n"
    prompt = prompt + "\n\nAnswer:"

    openai.api_key = os.environ.get("openai_api_key")
    response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=200)
    return response['choices'][0]['text'].strip()



# search_string = "when did Queen Elizabeth die?"
# OpenAI: Queen Elizabeth II is still alive as of April 2021.
# Google + OpenAI: Queen Elizabeth II died on 8 September 2022 at the age of 96.

# search_string = "who won Australian women's tennis Open in 2022?"
# OpeanAI: It is too early to predict who will win the Australian Women's Tennis Open in 2022.
# Google + OpenAI: Ashleigh Barty won the 2022 Australian Open Women's Singles.

search_string = "when did russia invade ukraine?" 
# OpeanAI: Russia began its military intervention in Ukraine in February 2014.
# Google + OpenAI: Russia invaded Ukraine on 24 February 2022

urls = search(search_string)
page_summaries = get_page_summaries_from_urls(urls)
result = call_ai(search_string, page_summaries)

print("\n\nQuestion: ", search_string)
print(result)
print("\nSources:")
print(*urls, sep="\n")