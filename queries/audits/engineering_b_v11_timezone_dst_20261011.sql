WITH cases AS (
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2020-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2021-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2022-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2023-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2024-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2025-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-01-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-03-08 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-240 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,600 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-07-15 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Chicago'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Denver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Detroit'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Los_Angeles'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Mexico_City'::VARCHAR(64) AS zone_name,-360 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/New_York'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Phoenix'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Sao_Paulo'::VARCHAR(64) AS zone_name,-180 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Tijuana'::VARCHAR(64) AS zone_name,-480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Toronto'::VARCHAR(64) AS zone_name,-300 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'America/Vancouver'::VARCHAR(64) AS zone_name,-420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Bangkok'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Jakarta'::VARCHAR(64) AS zone_name,420 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Kolkata'::VARCHAR(64) AS zone_name,330 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Seoul'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Shanghai'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Singapore'::VARCHAR(64) AS zone_name,480 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Asia/Tokyo'::VARCHAR(64) AS zone_name,540 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Australia/Sydney'::VARCHAR(64) AS zone_name,660 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Etc/GMT'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Amsterdam'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Athens'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Berlin'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Brussels'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Bucharest'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Dublin'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Helsinki'::VARCHAR(64) AS zone_name,120 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/London'::VARCHAR(64) AS zone_name,0 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Madrid'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Oslo'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Paris'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Rome'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Stockholm'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Vienna'::VARCHAR(64) AS zone_name,60 AS expected_minutes
UNION ALL
SELECT TIMESTAMP '2026-11-01 12:00:00' AS instant,'Europe/Zurich'::VARCHAR(64) AS zone_name,60 AS expected_minutes
)
SELECT COUNT(*) AS cases_checked, SUM(CASE WHEN DATEDIFF(minute,instant,CONVERT_TIMEZONE('UTC',zone_name,instant))<>expected_minutes THEN 1 ELSE 0 END) AS offset_mismatches FROM cases
