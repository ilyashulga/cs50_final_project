-- Keep a log of any SQL queries you execute as you solve the mystery.
.tables -- In order to see what are the tables in db provided
.schema crime_scene_reports -- to see what is the structure of the main table with event description
SELECT * FROM crime_scene_reports; -- to see how information is storred in crime_scene_reports
-- I need to filter out only events that took place on July 28, 2021 on Humphrey Street. And I'm interested only in description
SELECT crime_scene_reports.description FROM crime_scene_reports
WHERE year = '2021' AND month = '7' AND day = '28' AND street = 'Humphrey Street';
-- from the description I see that possible facts to hook on are the exact time, place and that there are 3 witnesses that were interviewed
-- I should start with finding their transctripts
-- there is "interviews" table that I can find there witnesses transcripts there
-- I know that all will mention "bakery"  in the transcript from crime_scene_reports.description
SELECT interviews.id, interviews.name, interviews.transcript FROM interviews
WHERE year = '2021' AND month = '7' AND day = '28';
-- from transcripts I found that:
-- 1. 10min after theft (10:25) - thief got into a car at the bakery parking lot (I can possibly find car license plate)
SELECT bakery_security_logs.activity, bakery_security_logs.license_plate, bakery_security_logs.hour, bakery_security_logs.minute FROM bakery_security_logs
WHERE year = '2021' AND month = '7' AND day = '28' AND hour = '10' and activity = 'exit';
-- Theif car's license plate options L93JTIZ or 322W7JE or 0NTHK55
--+----------+---------------+------+--------+
--| activity | license_plate | hour | minute |
--+----------+---------------+------+--------+
--| exit     | 5P2BI95       | 10   | 16     |
--| exit     | 94KL13X       | 10   | 18     |
--| exit     | 6P58WS2       | 10   | 18     |
--| exit     | 4328GD8       | 10   | 19     |
--| exit     | G412CB7       | 10   | 20     |
--| exit     | L93JTIZ       | 10   | 21     |
--| exit     | 322W7JE       | 10   | 23     |
--| exit     | 0NTHK55       | 10   | 23     |
--| exit     | 1106N58       | 10   | 35     |
--+----------+---------------+------+--------+
-- 2. Earlier than 10:15 thief used ATM on Legger Street
SELECT atm_transactions.id, atm_transactions.account_number, atm_transactions.amount, atm_transactions.atm_location FROM atm_transactions
WHERE year = '2021' AND month = '7' AND day = '28' AND transaction_type = 'withdraw' AND atm_location = 'Leggett Street'
ORDER BY atm_transactions.id;
-- now, let's get the names of the account holders

-- Thief possible IDs:
    --| 686048    |
    --| 514354    |
    --| 458378    |
    --| 395717    |
    --| 396669    |
    --| 467400    |
    --| 449774    |
    --| 438727    |
-- 3. When theif was leaving the bakery (10:25) he was talking via mobile phone (less than a minute) and the planned flight was for 29.07.2021 earliest flight
SELECT phone_calls.id, phone_calls.caller, phone_calls.receiver, phone_calls.duration FROM phone_calls
WHERE year = '2021' AND month = '7' AND day = '28' AND phone_calls.duration < 70
ORDER BY phone_calls.id;
-- Now we can look in people table to find phone, license plate, id matches
SELECT people.name from people
WHERE people.license_plate IN (SELECT bakery_security_logs.license_plate FROM bakery_security_logs
WHERE year = '2021' AND month = '7' AND day = '28' AND hour = '10' and activity = 'exit');
--+---------+
--|  name   |
--+---------+
--| Vanessa |
--| Barry   |
--| Iman    |
--| Sofia   |
--| Taylor  |
--| Luca    |
--| Diana   |
--| Kelsey  |
--| Bruce   |
--+---------+
-- Now we can look in people table to find phone matches for callers
SELECT people.name from people
WHERE people.phone_number IN (SELECT phone_calls.caller FROM phone_calls
WHERE year = '2021' AND month = '7' AND day = '28' AND phone_calls.duration < 70
ORDER BY phone_calls.id);
--+---------+
--|  name   |
--+---------+
--| Kenny   |
--| Sofia   |
--| Benista |
--| Taylor  |
--| Diana   |
--| Kelsey  |
--| Kathryn |
--| Peter   |
--| Bruce   |
--| Jason   |
--| Harold  |
--| Carina  |
--+---------+
-- on both lists: Sofia, Taylor, Diana, Kelsey, Bruce
-- Now we can look in people table to find phone matches for receivers
SELECT people.name from people
WHERE people.phone_number IN (SELECT phone_calls.receiver FROM phone_calls
WHERE year = '2021' AND month = '7' AND day = '28' AND phone_calls.duration < 70
ORDER BY phone_calls.id);
--+------------+
--| James      |
--| Larry      |
--| Luca       |
--| Anna       |
--| Jack       |
--| Melissa    |
--| Ethan      |
--| Jacqueline |
--| Daniel     |
--| Philip     |
--| Robin      |
--| Amy        |
--| Doris      |
--+------------+
--One of the above bought thief a ticket
--Now, let's check the ID matches:
SELECT people.name from people
WHERE people.passport_number IN (SELECT bank_accounts.person_id FROM bank_accounts
WHERE bank_accounts.account_number IN (SELECT atm_transactions.account_number FROM atm_transactions
WHERE year = '2021' AND month = '7' AND day = '28' AND transaction_type = 'withdraw' AND atm_location = 'Leggett Street'));
-- No matches since passport_number is not person_id...
-- Let's check suspects passport number
SELECT * from people
WHERE people.name IN ('Sofia', 'Taylor', 'Diana', 'Kelsey', 'Bruce');
--+--------+--------+----------------+-----------------+---------------+
--|   id   |  name  |  phone_number  | passport_number | license_plate |
--+--------+--------+----------------+-----------------+---------------+
--| 398010 | Sofia  | (130) 555-0289 | 1695452385      | G412CB7       |
--| 449774 | Taylor | (286) 555-6063 | 1988161715      | 1106N58       |
--| 514354 | Diana  | (770) 555-1861 | 3592750733      | 322W7JE       |
--| 560886 | Kelsey | (499) 555-9472 | 8294398571      | 0NTHK55       |
--| 686048 | Bruce  | (367) 555-5533 | 5773159633      | 94KL13X       |
+--------+--------+----------------+-----------------+---------------+
    --| 686048    |V
    --| 514354    |V
    --| 458378    |x
    --| 395717    |x
    --| 396669    |x
    --| 467400    |x
    --| 449774    |V
    --| 438727    |x
--Now I see that id matches transaction from the ATM withdrawals list
-- So we left with Bruce, Diana and Taylor
--Just before we continue let's check who suspects called to
SELECT people.name from people
WHERE people.phone_number IN (SELECT phone_calls.receiver FROM phone_calls
WHERE year = '2021' AND month = '7' AND day = '28' AND phone_calls.caller IN (SELECT people.phone_number from people
WHERE people.name IN ('Taylor', 'Diana', 'Bruce')));
--+---------+
--|  name   |
--+---------+
--| James   |
--| Gregory |
--| Carl    |
--| Philip  |
--| Robin   |
--| Deborah |
--| Angela  |
--+---------+
-- Let's find out the FiftyVille airport abbreviation and id
SELECT * from airports
WHERE airports.city LIKE '%FiftyVille%';
--+----+--------------+-----------------------------+------------+
--| id | abbreviation |          full_name          |    city    |
--+----+--------------+-----------------------------+------------+
--| 8  | CSF          | Fiftyville Regional Airport | Fiftyville |
--+----+--------------+-----------------------------+------------+
SELECT * from passengers
WHERE passengers.passport_number IN (SELECT people.passport_number from people
WHERE people.name IN ('Taylor', 'Diana', 'Bruce'));
--+-----------+-----------------+------+
--| flight_id | passport_number | seat |
--+-----------+-----------------+------+
--| 18        | 3592750733      | 4C   |
--| 24        | 3592750733      | 2C   |
--| 36        | 5773159633      | 4A   |
--| 36        | 1988161715      | 6D   |
--| 54        | 3592750733      | 6C   |
--+-----------+-----------------+------+
-- Let's check all flights details
SELECT * from flights
WHERE flights.id IN (SELECT passengers.flight_id from passengers
WHERE passengers.passport_number IN (SELECT people.passport_number from people
WHERE people.name IN ('Taylor', 'Diana', 'Bruce')));
--+----+-------------------+------------------------+------+-------+-----+------+--------+
--| id | origin_airport_id | destination_airport_id | year | month | day | hour | minute |
--+----+-------------------+------------------------+------+-------+-----+------+--------+
--| 18 | 8                 | 6                      | 2021 | 7     | 29  | 16   | 0      |
--| 24 | 7                 | 8                      | 2021 | 7     | 30  | 16   | 27     |
--| 36 | 8                 | 4                      | 2021 | 7     | 29  | 8    | 20     |
--| 54 | 8                 | 5                      | 2021 | 7     | 30  | 10   | 19     |
--+----+-------------------+------------------------+------+-------+-----+------+--------+
-- Two flights took place on 29.07 and one is earlier - Flight id 36 (we know from transcript that the flight should be on 29 and earliest)
-- 2 people were on that flight - Bruce and Taylor
-- Taylor left parking lot on 10:35 (20 minutes after a theft), looks like Bruce in our theif since he left 2-3 minutes after
-- Let's check who Bruce called to:
SELECT people.name from people
WHERE people.phone_number IN (SELECT phone_calls.receiver FROM phone_calls
WHERE year = '2021' AND month = '7' AND day = '28' AND phone_calls.caller = '(367) 555-5533' AND phone_calls.duration < '60');
--+-------+
--| name  |
--+-------+
--| Robin |
--+-------+
-- Robin helped Bruce to ecape
SELECT * from airports
WHERE airports.id  IN (SELECT flights.origin_airport_id from flights
WHERE flights.id IN (SELECT passengers.flight_id from passengers
WHERE passengers.passport_number = '5773159633'));
--+----+--------------+-----------------------------+------------+
--| id | abbreviation |          full_name          |    city    |
--+----+--------------+-----------------------------+------------+
--| 8  | CSF          | Fiftyville Regional Airport | Fiftyville |
--+----+--------------+-----------------------------+------------+
-- Now let's see destinations
SELECT * from airports
WHERE airports.id  IN (SELECT flights.destination_airport_id from flights
WHERE flights.id IN (SELECT passengers.flight_id from passengers
WHERE passengers.passport_number = '5773159633'));
--+----+--------------+-------------------+---------------+
--| id | abbreviation |     full_name     |     city      |
--+----+--------------+-------------------+---------------+
--| 4  | LGA          | LaGuardia Airport | New York City |
--+----+--------------+-------------------+---------------+
-- On 29.07.21 Bruce escaped from Fiftyville to New York City with the help of Robin