import psycopg2
import math

lvl3_words = ["must", "need", "needs", "deserves", "deserve", "commend"]
lvl2_words = ["should", "shouldn't", "recommend", "urge", "expect"]
lvl1_words = ["believe", "think", "seems", "understand", "doubt", "suggest", "feel", "blame",
	"object", "see", "consider", "share", "sure", "like", "say", "wish", "support", "agree",
	"disagree", "opposed", "shocked", "disappointed", "proud", "happy", "glad", "angry", "hate"]

opinion_words = lvl3_words + lvl2_words + lvl1_words

def get_context(words, index):
	first_index = index
	last_index = index

	while first_index >= 0 and not is_sentence_end(words[first_index]):
		first_index -= 1

	while last_index < len(words) - 1 and not is_sentence_end(words[last_index]):
		last_index += 1


	return " ".join(words[first_index + 1: last_index + 1])

def is_integer(x):
	try:
		int(x)
		return True
	except:
		return False

# says if a word represents the end of a sentence
# returns true if it has a ! or ? or has a . and is lower case
def is_sentence_end(word):
	if len(word) == 0:
		return False


	# three cases
	# Case 1 is ending in ! or ?
	# Case 2 is ending in . and being lower case and not an integer
	# Case 3 is being a quote that ends a sentence
	# If 1 is satisfied, it is the end of a sentence
	is_end = len(word) > 0 and word[-1] in ["!", "?"] \
		or (word[-1] == "." and word.lower() == word and not is_integer(word[0:-1])) \
		or (word[-1] in ["\"", "'"] and is_sentence_end(word[0:-1]))

	return is_end


def split_article(article):
	# replace newlines in the article with spaces
	article = article.replace("\n", " ")

	words = article.split(" ")

	return words

def process_article_basic(article, matcher):

	words = split_article(article)

	count = 0
	context = []

	for index, word in enumerate(words):
		def process_word(word):
			word = word.lower()
			
			newWord = ""

			for char in word:
				if 'a' <= char <= 'z':
					newWord += char

			return newWord

		if process_word(word) in matcher:
			context.append(get_context(words, index))
			count += 1

	return count, context;
	
def process_article_structure(article, match_word):
	words = split_article(article)

	count = 0
	context = []

	for index, word in enumerate(words):
		def process_word(word):
			newWord = ""

			for char in word:
				if 'a' <= char <= 'z' or 'A' <= char <= 'Z':
					newWord += char

			return newWord

		if process_word(word) == match_word:
			context.append(get_context(words, index))
			count += 1

	return count, context;

# processors for different statistics

def process_lvl3(article):
	return process_article_basic(article, lvl3_words)

def process_lvl2(article):
	return process_article_basic(article, lvl2_words)

def process_lvl1(article):
	return process_article_basic(article, lvl1_words)

def process_while(article):
	return process_article_structure(article, "While")

def process_if(article):
	return process_article_structure(article, "If")

def process_first_person(article):

# connect to the database

conn = psycopg2.connect(host="localhost", database="studlife", user="root")

cur = conn.cursor()

cur.execute("""SELECT author_id, url, published_date, content FROM articles
	WHERE author_id = 'StaffEditorial';""")

staff_ed_articles = cur.fetchall()


cur.execute("""SELECT author_id, url, published_date, content FROM articles
	WHERE author_id != author_name AND LENGTH(author_name) < 60
	AND author_id != 'StaffEditorial'
	AND url NOT LIKE('%op-ed%') AND url NOT LIKE('%letter-to-the-editor%');""")

column_articles = cur.fetchall()


cur.execute("""SELECT author_id, url, published_date, content FROM articles
	WHERE url LIKE('%op-ed%') OR url LIKE('%letter-to-the-editor%');""")

op_ed_articles = cur.fetchall()

collections = [staff_ed_articles, column_articles, op_ed_articles]

# a processor for each category
processors = [process_lvl3, process_lvl2, process_lvl1, process_while, process_if]

# global variable to store the contexts of each processor (category)
contexts = [[] for _ in processors]

def process_articles(articles):

	totals = [0 for _ in processors]
	squared_sums = [0 for _ in processors]
	counts = [0 for _ in processors]

	article_count = 0

	for article in articles[0:50]:
		content = article[3]
		url = article[1]

		article_len = len(split_article(content))

		article_count += 1


		# run every processor
		for index, processor in enumerate(processors):
			count, context = processor(content)

			val = count/article_len

			totals[index] += val
			squared_sums[index] += val * val

			contexts[index] += context

	# calculate average and standard deviation
	for index, _ in enumerate(totals):
		totals[index] = totals[index]/article_count

		squared_sums[index] = math.sqrt((squared_sums[index] - totals[index] * totals[index]) / (article_count -1))

	return totals, squared_sums

for collection in collections:
	avg, std = process_articles(collection)

	print(avg)
	print(std)


# print(contexts[0])

# print(process_articles(articles))












