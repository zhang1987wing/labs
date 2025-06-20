SELECT * FROM stock.stockquote
#WHERE stock_code = 0000001
WHERE cur_date = '2025-02-26';

DELETE FROM stock.stockquote
WHERE cur_date < '2025-02-01';

UPDATE stock.stockquote
SET cur_date = '2024-04-30'
WHERE cur_date = '2024-05-01';

DELETE FROM stock.stockquote
WHERE cur_date = '2025-02-26';

SELECT * FROM ma5_more_than_ma10
#WHERE stock_code = '000026'
WHERE end_date IS NULL
AND macd_analyze = 1 AND dmi_analyze = 1
AND last_day = 1
ORDER BY last_day DESC;

SELECT last_day, COUNT(stock_code), begin_date, '2025-02-14 00:00:00'
            FROM ma5_more_than_ma10
            WHERE end_date IS NULL
            GROUP BY last_day
            ORDER BY last_day;

SELECT * FROM stockcode_lastday_daily
ORDER BY lastday, cur_date ASC;

DELETE FROM stockcode_lastday_daily
WHERE cur_date = '2025-02-17 00:00:00';

SELECT * FROM world.city;

SELECT * FROM world.countrylanguage;

SELECT * FROM world.countrylanguage language
LEFT JOIN world.Country Country ON language.CountryCode = Country.Code
WHERE language.IsOfficial = 'T';

SELECT city.*, Country.* FROM world.city city INNER JOIN world.Country Country ON city.CountryCode = Country.Code;

SELECT city.*, Country.* FROM world.city city LEFT JOIN world.Country Country ON city.CountryCode = Country.Code;

SELECT a.cityName, a.name, language.Language FROM world.countrylanguage language
LEFT JOIN
(SELECT city.Name as cityName, Country.Name, Country.Code FROM world.city city LEFT JOIN world.Country Country ON city.CountryCode = Country.Code) a
ON language.CountryCode = a.Code
WHERE language.IsOfficial = 'T'
ORDER BY a.Name;

SELECT city.*, Country.* FROM world.city city RIGHT JOIN world.Country Country ON city.CountryCode = Country.Code;

SELECT city.*, Country.* FROM world.city city LEFT JOIN world.Country Country ON city.CountryCode = Country.Code
UNION
SELECT city.*, Country.* FROM world.city city RIGHT JOIN world.Country Country ON city.CountryCode = Country.Code;

SELECT * FROM world.country;

SELECT Continent, AVG(Population) FROM world.country GROUP BY Continent HAVING AVG(Population) > 3;

SELECT * FROM world.countrylanguage;