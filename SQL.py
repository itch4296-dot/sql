import shutil
import sqlite3
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
DB_NAME = "deals.db"
BACKUP_NAME = "deals_backup.db"
SQL_FILE = "queries.sql"

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

QUEST_SQL_TEXT = """-- Квест 1/5 — самый дешёвый товар
SELECT * FROM products
ORDER BY price ASC
LIMIT 1;

-- Квест 2/5 — топ-5 товаров по рейтингу
SELECT * FROM products
ORDER BY rating DESC
LIMIT 5;

-- Квест 3/5 — поиск по слову
-- Роль символов %: знак процента заменяет любое количество любых символов (включая ноль символов) до и после искомого слова.
SELECT * FROM products
WHERE name LIKE '%The%';

-- Квест 4/5 — товары дешевле N (например, дешевле 20)
SELECT * FROM products
WHERE price < 20;

-- Квест 5/5 — поиск повторов (дубликатов) по названию
SELECT name, COUNT(*)
FROM products
GROUP BY name
HAVING COUNT(*) > 1;
"""


def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            rating INTEGER NOT NULL,
            url TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()


def scrape_books(url, limit=20):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article.product_pod")

    books = []
    for article in articles[:limit]:
        title_tag = article.select_one("h3 a")
        price_tag = article.select_one("p.price_color")
        rating_tag = article.select_one("p.star-rating")

        if not (title_tag and price_tag and rating_tag):
            continue

        name = title_tag["title"].strip()
        book_url = urljoin(url, title_tag["href"])
        price = float(price_tag.text.strip().replace("£", "").replace("Â", ""))

        rating = 0
        for cls in rating_tag.get("class", []):
            if cls in RATING_MAP:
                rating = RATING_MAP[cls]
                break

        books.append((name, price, rating, book_url))

    return books


def save_to_db(conn, books):
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO products (name, price, rating, url)
        VALUES (?, ?, ?, ?)
    """, books)
    conn.commit()


def create_sql_file(filename):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(QUEST_SQL_TEXT)
    print(f"Файл с запросами {filename} успешно создан.")


def run_quest_queries(conn):
    cursor = conn.cursor()

    print("\n--- Квест 1/5: Самый дешёвый товар ---")
    cursor.execute("SELECT * FROM products ORDER BY price ASC LIMIT 1;")
    print(cursor.fetchone())

    print("\n--- Квест 2/5: Топ-5 по рейтингу ---")
    cursor.execute("SELECT * FROM products ORDER BY rating DESC LIMIT 5;")
    for row in cursor.fetchall():
        print(row)

    print("\n--- Квест 3/5: Поиск по слову (параметр '?') ---")
    search_word = "%The%"
    cursor.execute("SELECT * FROM products WHERE name LIKE ?;", (search_word,))
    for row in cursor.fetchall():
        print(row)

    print("\n--- Квест 4/5: Товары дешевле N (параметр '?') ---")
    max_price = 20.0
    cursor.execute("SELECT * FROM products WHERE price < ?;", (max_price,))
    for row in cursor.fetchall():
        print(row)

    print("\n--- Квест 5/5: Проверка на повторы названий ---")
    cursor.execute("""
        SELECT name, COUNT(*)
        FROM products
        GROUP BY name
        HAVING COUNT(*) > 1;
    """)
    duplicates = cursor.fetchall()
    print("Найдено дубликатов:", len(duplicates))


def main():
    books = scrape_books(BASE_URL, limit=20)
    print(f"Собрано товаров с сайта: {len(books)}")

    with sqlite3.connect(DB_NAME) as conn:
        init_db(conn)
        save_to_db(conn, books)

        shutil.copyfile(DB_NAME, BACKUP_NAME)
        print(f"База {DB_NAME} заполнена, резервная копия {BACKUP_NAME} создана.")

        create_sql_file(SQL_FILE)

        run_quest_queries(conn)


if __name__ == "__main__":
    main()
