import psycopg2
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
import requests
import time
import sys

# parse options


conn = psycopg2.connect(host="localhost", database="studlife", user="root")

cur = conn.cursor()

cur.execute('SELECT version()')

print(cur.fetchone())




def get_section_url(section, page):
	return f"https://www.studlife.com/{section}/page/{page}/"

def process_page(n):
	url = get_section_url("forum", n)

	response = requests.get(url)

	if not response.status_code == 200:
		print(response.text)
		return False

	article_urls = get_article_urls(response.text)

	for article_url in article_urls:
		process_article(article_url)

	return True



def get_article_urls(page):
	html = BeautifulSoup(page, 'html.parser')
	urls = []

	for article in html.find_all("div", {"class": "article"}):
		link = article.find('a')
		url = link["href"]
		urls.append(url)

	return urls


def sanitize_article(html):
	return sanitize_article_helper(html, "")

def sanitize_article_helper(html, join_str):

	# print(html)

	if isinstance(html, NavigableString):
		return str(html)

	elif isinstance(html, Tag):
		sanitized_list = [sanitize_article_helper(element, "") for element in html.contents]
		return join_str.join(sanitized_list)
	else:
		return ""


def process_article(url):
	response = requests.get(url)

	if not response.status_code == 200:
		return False

	html = BeautifulSoup(response.text, "html.parser")

	# get author information

	author_id = ""
	author_name = ""


	author_span = html.find("span", {"class": "author-name"})
	if author_span is not None:
		author_link = author_span.find('a')
		if author_link is not None:
			author_url = author_link['href']
			author_id = author_url.split("/author/")[1][0:-1]
			author_name = str(author_link.contents[0])
		else:
			author_name = str(author_span.contents[0])
			author_id = author_name

	# get the date
	published_date = None

	article_div = html.find("div", {"class": "article"})
	if article_div is not None:
		time_element = article_div.find("time")
		if time_element is not None:
			date_string = None
			try:
				date_string = time_element["pubdate"]
			except KeyError:
				try:
					date_string = time_element["datetime"]
				except KeyError:
					pass
			if date_string is not None:
				# make the date string into a date
				published_date = date_string

	# get the section
	section = url.split("studlife.com/")[1].split("/")[0]

	# get the content
	content_div = html.find("div", {"class": "article-content"})

	# print(content_div)
	# print(sanitize_article(content_div))
	content = sanitize_article(content_div)

	sql = """
		INSERT INTO articles (author_id, author_name, url, published_date, section, content)
		VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
	"""

	cur.execute(sql, (author_id[0:64], author_name, url, published_date, section, content))
	conn.commit()










# go through the forum pages and get everything

success = True

page_start = int(sys.argv[1])
page_num = page_start


page_total = 291

start = time.time()
avg_time = 0
while success:
	success = process_page(page_num)
	page_num += 1
	

	count = page_num - page_start
	

	avg_time = (time.time() - start) / (count)

	print(f"{page_num - 1} page finished. {count} pages done at an average rate of {avg_time} seconds per page")
	print(f"Estimated time remaining: {avg_time * (page_total - page_num) / 60} minutes")

	


















