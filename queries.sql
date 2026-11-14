-- Квест 1/5 — самый дешёвый товар
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
