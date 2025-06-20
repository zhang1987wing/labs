SELECT * FROM stock.stock_quote
WHERE stock_code = 600000;
#WHERE stock_name NOT LIKE '%ST%'
#WHERE cur_date = '20250529';

UPDATE stock.stock_quote
SET cur_date = '2024-04-30'
WHERE cur_date = '2024-05-01';

SELECT * FROM stock.open_position_stock
#WHERE stock_code = '603918'
WHERE buy_date = 20250620# AND profit > 9
ORDER BY profit DESC;

SELECT * FROM stock.stock_fund_flow
#WHERE stock_code = 002258;
WHERE fund_date = 20250620# and stock_code = 301229;
ORDER BY stock_code;

SELECT * FROM stock.stock_basic_info
WHERE stock_code = '002181'
#WHERE industry LIKE '%风电设备%'
ORDER BY market_cap DESC;

SELECT * FROM stock.concept_fund_flow_daily
WHERE net_fund > 0;

SELECT * FROM stock.industry_fund_flow_daily
#WHERE create_date = '20250612'
#WHERE industry LIKE '%文化传媒%';
ORDER BY create_date DESC;

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