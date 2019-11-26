import psycopg2

conn = psycopg2.connect(host="localhost", database="studlife", user="root")

cur = conn.cursor()

cur.execute("""
  CREATE TABLE articles(
    arcticle_id SERIAL PRIMARY KEY,
    author_id VARCHAR(1024),
    author_name VARCHAR(1024),
    url VARCHAR(1024) UNIQUE,
    published_date TIMESTAMP WITH TIME ZONE,
    section VARCHAR(1024),
    content VARCHAR(65536)
  );
  """)

conn.commit()

cur.close()
conn.close()

