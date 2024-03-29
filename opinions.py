import psycopg2
import math
from scipy import stats
import random

# set the seed, so the "random" results are the same everytime
# this presents accidental bias from re-running the statistics
# if you do not like the results

random.seed(7804925)

lvl3_words = ["must", "need", "needs", "deserves", "deserve", "commend"]
lvl2_words = ["should", "shouldn't", "recommend", "urge", "expect"]
lvl1_words = ["believe", "think", "seems", "understand", "doubt", "suggest", "feel", "blame",
    "object", "see", "consider", "share", "sure", "like", "say", "wish", "support", "agree",
    "disagree", "opposed", "shocked", "disappointed", "proud", "happy", "glad", "angry", "hate"]

opinion_words = lvl3_words + lvl2_words + lvl1_words

fpp_multis = [["I"], ["we"], ["Student", "Life", "Editorial", "Board"]]

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

def process_word(word):     
    newWord = ""

    for char in word:
        if 'a' <= char <= 'z' or 'A' <= char <= 'Z':
            newWord += char

    return newWord

def process_article_basic(article, matcher):

    words = split_article(article)

    count = 0
    context = []

    for index, word in enumerate(words):

        if process_word(word.lower()) in matcher:
            context.append(get_context(words, index))
            count += 1

    return count, context;
    
def process_article_structure(article, match_word):
    words = split_article(article)

    count = 0
    context = []

    for index, word in enumerate(words):

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

def match_multi_word(words, start_index, multi_word):
    for i in range(len(multi_word)):
        if start_index+i >= len(words):
            return False

        if process_word(words[start_index + i].lower()) != process_word(multi_word[i].lower()):
            return False

    return True

def match_multi_word_array(words, start_index, multi_word_array):
    for mulit_word in multi_word_array:
        if match_multi_word(words, start_index, mulit_word):
            return True

    return False

def word_in_next_6(words, start_index, word):
    for index in range(6):
        if start_index + index >= len(words):
            return False
        if process_word(word.lower()) == process_word(words[start_index + index].lower()):
            return True

    return False

def opinion_word_in_next_6(words, index, opinion_words):
    for opinion_word in opinion_words:
        if word_in_next_6(words, index, opinion_word):
            return True

    return False

def process_first_person(article):
    
    words = split_article(article)

    count = 0
    context = []

    for index, word in enumerate(words):
        if match_multi_word_array(words, index, fpp_multis) \
        and opinion_word_in_next_6(words, index, opinion_words):
            count += 1

            context.append(get_context(words, index))

    return count, context;

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
collection_names = ["Staff Editorials", "Columns", "Op-Eds"]

# a processor for each category
processors = [process_lvl3, process_lvl2, process_lvl1, process_while, process_if, process_first_person]
processor_names = ["lvl3", "lvl2", "lvl1", "while", "if", "fpp"]

process_file_names = ["out/" + f + ".txt" for f in ["lvl3", "lvl2", "lvl1", "while", "if", "fpp"]]

def process_articles(articles, processor):

    total = 0
    squared_sum = 0
    counts = 0

    article_count = 0

    contexts = []

    for article in articles:
        content = article[3]
        url = article[1]

        article_len = len(split_article(content))

        article_count += 1

        count, context = processor(content)
        
        context = [line + " " + url for line in context]

        val = count/article_len

        total += val
        squared_sum += val * val

        contexts += context

    # calculate average and standard deviation
    avg = total/article_count

    std = math.sqrt(squared_sum / (article_count - 1) - avg * avg * article_count / (article_count -1))

    return avg, std, article_count, contexts

def calc_t(m1, m2, std1, std2, l1, l2):
    total_std = math.sqrt(std1 * std1 / l1 + std2 * std2 / l2)
    mean = m1 - m2
    
    if total_std == 0:
        return 0
    else:
        return mean / total_std

# prints out all distinct pairs of two integers (x, y) 0 <= x < y < n
def range_pairs(n):
    for i in range(n):
        for j in range(i+1, n):
            yield i, j


all_contexts = [[] for _ in processors]

for proc_index, processor in enumerate(processors):
    avgs = []
    stds = []
    article_lens = []

    proc_name = processor_names[proc_index]

    for col_index, collection in enumerate(collections):

        

        avg, std, article_len, contexts = process_articles(collection, processor)
        avgs.append(avg)
        stds.append(std)
        article_lens.append(article_len)

        all_contexts[proc_index] += contexts

        col_name = collection_names[col_index]

        print(f"{proc_name} for {col_name}: average: {avg}, standard deviation: {std}, sample size: {article_len}")

    # TODO: Make more readable
    for i, j in range_pairs(len(avgs)):
        col1_name = collection_names[i]
        col2_name = collection_names[j]

        t = calc_t(avgs[i], avgs[j], stds[i], stds[j], article_lens[i], article_lens[j])
        
        df = article_lens[i] + article_lens[j] - 2

        abs_t = t if t > 0 else -t

        p = 2*(1 - stats.t.cdf(abs_t, df=df))

        significant = "SIGNIFICANT " if p < 0.01 else "            "

        print(f"{significant}{proc_name}: comparing {col1_name}, {col2_name}: p: {p}. t: {t}, df: {df}")


    if len(all_contexts[proc_index]) <= 30:
        random_contexts = all_contexts[proc_index]
    else:
        random_contexts = random.sample(population=all_contexts[proc_index], k=30)

    format_contexts = "\n".join(random_contexts)

    with open(process_file_names[proc_index], "w") as out_file:
        out_file.write(format_contexts)
    

    # print("\n".join(random_contexts))

# print(process_articles(articles))

collection_file_names = ["out/staff.txt", "out/column.txt", "out/oped.txt"]

for index, collection in enumerate(collections):
  urls = [article[1] for article in random.sample(collection, k=30)]
  
  formatted = "\n".join(urls)
  
  with open(collection_file_names[index], "w") as file:
    file.write(formatted)











