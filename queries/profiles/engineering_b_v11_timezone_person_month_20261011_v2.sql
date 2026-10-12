/* Proxy geográfico estático del V11; modelo sólo en RAM.
   Oficinas públicas 2026; ubicación laboral de la propia foto, sin domicilios. */
WITH source AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
        manager_employee_id, TRIM(eng_or_noneng) AS engineering,
        MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(office_site)), '[^A-Z0-9]+', ''),'')) AS site_key, MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(country)), '[^A-Z0-9]+', ''),'')||'|'||NULLIF(REGEXP_REPLACE(UPPER(TRIM(city)), '[^A-Z0-9]+', ''),'')) AS city_key
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND employee_id IS NOT NULL
), workforce AS (
 SELECT snapshot_date,employee_id,MAX(manager_employee_id) AS manager_id,
        MAX(engineering) AS engineering, MAX(site_key) AS site_key, MAX(city_key) AS city_key,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR),'<NULL>')) AS manager_variants,
        COUNT(DISTINCT COALESCE(site_key,'<NULL>')) AS site_variants,
        COUNT(DISTINCT COALESCE(city_key,'<NULL>')) AS city_variants
 FROM source GROUP BY 1,2
), site_map AS (
SELECT '00c183e1db5981507b8fdc7cb16b59a3'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '011803575382f7c506ffcc86af0f4681'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '011a496d91fb974b5a2f7820b13171ca'::VARCHAR(32) AS map_key,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '06254b18606100b4f3ada82cfa56748e'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0635d7c5ff336ab2114350443ee8fc74'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '06bfcbacb2719a6ede7a129a90708ee0'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '06fa567b72d78b7e3ea746973fbbd1d5'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '07772429bb936c36488f3b7eba793955'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '08c1fe5f2a599040e6c328e800a309aa'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0a67d873ddfb70695f661f53ef0f5679'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0d1fb6ef95b3a9729d943c46d62e001c'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0d5ffb83f1932e1c2d95615f2158dd50'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0ec59c60136d5958e6f82be9056b705c'::VARCHAR(32) AS map_key,'Europe/Brussels'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0f20f2033dda31e8b4de17a68ac3fb1e'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0fd3f8dd5edc33b28db1162e15e8fcbc'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0ffa27c80b0f2b2a8ebb0ac3ab3b7657'::VARCHAR(32) AS map_key,'Europe/Helsinki'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1011a76dc1b928f0ca31213db8dc86c5'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '107c700fb12eea1632c0b2f73ea6f7a2'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '13ae5c8084fe8418fba7ccb1dbe40e56'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1488be530514097b7bda022efa0dc892'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1536f14df087e54581c19150d29e7ce0'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '15a2d8b50c931391d62799a701965b42'::VARCHAR(32) AS map_key,'Europe/Athens'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '15e5a91e187c33fd8f3f811b701b0b1a'::VARCHAR(32) AS map_key,'Europe/Amsterdam'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1720a3075ccb3b8debcae2a81fe92dd0'::VARCHAR(32) AS map_key,'Europe/Dublin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '17ab93b2f0334813a864959d44f75a1c'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1900513a99eb0180ec7fd09bc6903ca2'::VARCHAR(32) AS map_key,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '196dea15b33087437518b04e40e08444'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1d0039487c060a5d157ebb0dfb5a3ffe'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1d02de576e40490645865785f81cf4fc'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1e4ba88d1ac0a4d4249d72f1aa9c5a61'::VARCHAR(32) AS map_key,'America/Vancouver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1e8b5cf97b31f51cc9a0d8b657f367a4'::VARCHAR(32) AS map_key,'Australia/Sydney'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '21667751f2378c2b084bef71bf5f7efb'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '21d70f2ec762d1d8cb39e8cd7643ab9a'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '22f908f6b83866b82359247029131744'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '23545b8269fb560ebea5dcc393865867'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '248755b985256b51b80891d35fc63303'::VARCHAR(32) AS map_key,'America/Sao_Paulo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2495d9019f5d9c89d8f3546c944b3b9d'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '24992fbe6240e46f647c2b341f186152'::VARCHAR(32) AS map_key,'America/Sao_Paulo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2578f24a1e04951f0cb7974699564327'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '262c6b1d4dd6d3455b79564ed8ee8ea5'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '26748b021bdc8922f93d9bf054cbec5d'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2703ce5849f7590bac1d2d42ab496dd1'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '27e03c1c0caaea3c1bc7561d6f234a0e'::VARCHAR(32) AS map_key,'Europe/Bucharest'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2820bf76542869fc77b7b0ac90407d4b'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '29635cd46ec088bb4bbcc96e22f9b93e'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2aa227c406705d32e97554b1b3c54224'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2b20b84a8beff0831e0872353163caff'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2b3550882934e086d4aca9046e1e8ef9'::VARCHAR(32) AS map_key,'Europe/Zurich'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2b601545124d9af2666f29cd0b41e5c5'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2ba0dd593000926e7a1cd889bed0132e'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2c7ee6bb97b806a8ba2598af9274f960'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2d286a542a4a175a518a566cb1554be1'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '30d48d35feed5ce74cacb58ae1613c94'::VARCHAR(32) AS map_key,'Asia/Singapore'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '30eb075e362ee200397063de0b48710a'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '32004ad12ea11838b73c853e7d850234'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '32bc98cdec3bc4dd3c14fbd2bf08e4d7'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '32f116fb9aa693e81fb337413bdae2f3'::VARCHAR(32) AS map_key,'America/Sao_Paulo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '32f245efd2ff469e98d32a3dbd4b99b5'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '336254836e9a4f69d76b5ea29321e4fc'::VARCHAR(32) AS map_key,'America/Mexico_City'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3413b2f9af7f0974d95aeeecdc187551'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '347652647c59253af83bfa09451b933c'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3659fb528f055664ac9346c3b1833a03'::VARCHAR(32) AS map_key,'Europe/Athens'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '36ac54f89aca52df94ccd5c0246da1ac'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '36ad978e984950ba84ec0656e87c41f0'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '37cfca48ce53350e36b635af3307200a'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3912c3bee8037cc2290d30224e7ddf8f'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '393649ef107814c0f885ebef246266a1'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '39f2c38032b90036aa4cba7af5f9d1d4'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3a4d638474598ca62d977828733403eb'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3b2edf39e2ad9e1bd8acea8510452299'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3c09d32e6d7824ef2ef266dda2c5e1b8'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3f517d87d6c811dc742bf4edf2cdafd3'::VARCHAR(32) AS map_key,'Australia/Sydney'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3fdd857fdc4872f51f4c9a16b3088e86'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '406a827681ba573eb9029a9a41cae6d7'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4169faedf83f4c7583d80a2275d5fe4e'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4226432b0438416b28d30aadf33e27b8'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '426f7299dade4fde0e387e2df2d04318'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4306a04670067b5b27e766335d3d40fa'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '43688160f6cb4eb3afecca3312e6f415'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '436a2fdc5e87ce273212b818b338a0a9'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '44c29edb103a2872f519ad0c9a0fdaaa'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4539cf46b561ea74f70c14f84b68ccae'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '46a16059be2949aef0dad22b2d557122'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '46f817488eba852dcc70b66cde7b6655'::VARCHAR(32) AS map_key,'Europe/Bucharest'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4734e9f34139fd9490f87f8648083ac9'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '490f33efc8983ce4953c455d63d79756'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4948437c551efefbf5f3ef75f2c17fe5'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '49567424f15bbf4e7d47c4459f547f5a'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '49b025c3737338c80ccfbc88c543dd74'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '49e15f040e9a66ed7710dc79e871a438'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4aafa3a624043aa8c715626e2b58c877'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4cefb501c6f7e1d0faf1e067347d938e'::VARCHAR(32) AS map_key,'Europe/Amsterdam'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4d697eac6e2b98b88817279090e8acd4'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4daca4d7005fbb41307e800a6115bf2e'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4e3251cc2639fb7825ba9fcb5c0acfc2'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4e7f1406976e9abfa2771922379bfe47'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '50d89fb73859b37f890200a76d381216'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '517b448119bdb92077c268b3f7de29ef'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '51db7e0b581a83d2f3bf483dcf7893df'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '525231dddba24900b3ce54376a33863f'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '52b1b685cd1bdd76ccdadf166dbd68ab'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '546a9a80eb981c7f0aabcaeb34d9514e'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '554727c7d46ba724e886f62d01e85cee'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '55cab64c14fe28d843d46c532865d8eb'::VARCHAR(32) AS map_key,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '56d7db2c9e5ed29323f52982baa2fe72'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '575d5b76eeef045245442674b7bd1523'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5860837abe364d155d5ae6a3bd8add68'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '58e69a293e3d65294bd972b467c40996'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '59b229927ad75958be5fcd7cd7b5c4e4'::VARCHAR(32) AS map_key,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5a757cf41c6fcf90b69a32bc3d776d6f'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5b32709b4a0046cff3b9c06229b56e94'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5dbc98dcc983a70728bd082d1a47546e'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5fe1bd03c5ac51689c9295c2f2f7a347'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '602179f2cc46022af3bdf9dce545a79a'::VARCHAR(32) AS map_key,'America/Mexico_City'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '61e9c06ea9a85a5088a499df6458d276'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '62057118b6ffc36e9fe5fa341d471f73'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '62a955913eefb59a9c53026b98cfad4e'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '652409bfbbeb8c60ef63e9bf9de8eac9'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6574c87c4287011b16d91f3b9d927c5f'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6576320d62277b2ce43928611a1383d4'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6740958bfeb66e768e6b1397e84c4c8d'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '678971eaef91c4dabbe81ffb08b11821'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '678c54ae7d4a97a81a322bf3a18af666'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6892706f274f9b37d9a0cb23f57b28ee'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '68f2959032f58ef3e224cd73527c9d23'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '69691c7bdcc3ce6d5d8a1361f22d04ac'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6a40073d40d812bf60cdfac31b3b5449'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6aae4102830376b360d9dfc48fe3a1e0'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6b016b22458f037c9f62caa3c335d42c'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6b044f0a03d15de778c499e1904dafa5'::VARCHAR(32) AS map_key,'Asia/Jakarta'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6c28338a2761e07a65eb4eca67511f78'::VARCHAR(32) AS map_key,'Europe/Zurich'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6c9bd029abc9676d1dde7e47514a3dc0'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6e20bd405c36796b72978a875ac375c3'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6e2ad33f09e60227baed0de5a61ad5a1'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6e4137cdc0ea5b58b644d55141054505'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6f764f9d79f627dcc10d3d5e0a5e36bd'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '70081403c2b1983d1b650a8dc3f13a7b'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7015fedb41f0f7ef9c039ba8fdf2e426'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7123a13ddab3fed2977242dffd6d93b6'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '72337f3d95e6f132a59f96dafeb66fc5'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '72b835f5e1d4864fc31a85a30c8689d9'::VARCHAR(32) AS map_key,'Asia/Bangkok'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7446cf50d7c77ff08598c773e8ef726a'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '74af5ca6ec6d6e8e2ad8783710e12494'::VARCHAR(32) AS map_key,'Europe/Dublin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '74d8ed3e97a2d622db723beef601881c'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '754735ceedb726cc5f3ff4964e3c9c58'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '760727caa4976b45c29ffc1726ac4061'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '775bae8de451b881646c30ef92c1ef13'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '789e89d7fa94786b76c523501fbb37c9'::VARCHAR(32) AS map_key,'Europe/Amsterdam'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '78dd8f69c6062108db7eccabc08cb3e7'::VARCHAR(32) AS map_key,'Europe/Amsterdam'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7b8d2f92148f52cad46e331936922e80'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7ba46fc065c87599d38aa811e4ddef4d'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7d6a23d379bb7b11138d565ed4e85491'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7dcd159915b18a2450803ee1037b1fed'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7e9b9d67f7555889f730da86eaa7dcd6'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7f3c1ae38e1687965056c3834c48b343'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7f6144896e5287b136ff2934505bf905'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7fb0dc022c9bb8e404e1d02be1908921'::VARCHAR(32) AS map_key,'America/Detroit'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7fc56270e7a70fa81a5935b72eacbe29'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '800618943025315f869e4e1f09471012'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '802d4e6dba60647a207ebdc2c4256264'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '83ac4ccc9fbc83b0cca15236ab969927'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '86dcdeefd22d6d03a2ec7c0ce0213944'::VARCHAR(32) AS map_key,'Asia/Singapore'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '877bd0edaf1513c46266b3138e2d864f'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '87c73fb06b0aef4f616764824f0deba4'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '89928d0ca69d9bc62c79d72592455129'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8ae5faa230a5fd3197d1362c53d784a5'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8bbfcd335deac1cadf666d2af93ac93f'::VARCHAR(32) AS map_key,'America/Tijuana'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8bc1142b0b831c5cafcb9fbdd578a14f'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8c69bcdb2aef53b87ee64ae17f5aa9c0'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8d9c307cb7f3c4a32822a51922d1ceaa'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8e2747f9b555b3e326e89f0c9c06d71e'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9091aaba7f6c5ffa13145c1ff6301d2a'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '90b26a7d71dc43936c54d43ceaa9e828'::VARCHAR(32) AS map_key,'Europe/Madrid'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '93009a886cad217bfada654e0dcff67a'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9318d0c6393d27e3b20d0b41d90a5019'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '93a7f10fcc0a02e8ec7ecc1c60d27978'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '941f80982f9c1f5b8d5bd53014311cd4'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9475702f88d31ba4e90b89d5d3955d59'::VARCHAR(32) AS map_key,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '96d4cdff8ed57e93e3b3d843cffe3af7'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '98062dfe7ca7564a0563706ab45da69c'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9853ce6f93acb2d5a0af9d2e164f3d77'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '98ff10c631cdd246bd8921d9e7a1cff1'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9936ca8c8db4dbe7198ea13b17b26a84'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9c4678e7f6c761423fd032a9cfb6591b'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9c9ee64b6babc15e7f3f5f57aaba1e77'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9cd9c83ee9420edd9f51d4cc4b068b33'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9cda6daefa32e37706f81236a5a37e61'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9d30cd66e0a2a91fb4db2bec0fb9ec45'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9d3d9048db16a7eee539e93e3618cbe7'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9d4fcbac62869638c1068ed243696a1e'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9ddbb33cf099bb40ee826cb5502c7629'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9df2056925e5afd294e827b756d40bd2'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a23024f58979f0ffff69263c4b02e77f'::VARCHAR(32) AS map_key,'Europe/Helsinki'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a29c10857899496f2c2a7f3a67d0bf19'::VARCHAR(32) AS map_key,'Asia/Bangkok'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a3d4687af8bdf0ab698e3a4ef584e36d'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a47cb64b34d1a663f3cdea2611910126'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a4ae05988da76d71ae40e5f14a85c61f'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a4cb9cecd2f8016b22b9e65bc6a713bb'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a542e16b93dd5ddaa5de7e9886e1319a'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a580b411b7815ea0267b8aeb39829019'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a619aedd920a9c4783042e2d18575b53'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a6c1a060dbed11173bb468ba0b045524'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a80dea6cf9a288c5ca3d677314cfa2fd'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a82b09788d1fa47898fd8011f4d06615'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a8522b770693a6c14a26f3aeeec134a9'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a9016b78d5888e46b7ef14141c505782'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a9268b97d362b7553ced57806c580092'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a9751dc406ab09c7fa0249abe1474d95'::VARCHAR(32) AS map_key,'Asia/Singapore'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'aa3d2b10aeea0b39d427e26e43fd601d'::VARCHAR(32) AS map_key,'Europe/Brussels'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ab3b1c80ed945514d210e853a3a46ceb'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ab5cdebef46bab927308b2a228d5e34b'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ac242743f90ffbadd8334a20e245dce4'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ac29519f687e406414231f8c7658e798'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ac5afb2d6c00e93dfbcc6006b716ba0e'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'acd6526091ef4123e8934c44ec7e84dc'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ad29c491c4af49f43b25c1b1f4992de8'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ad320fbf36f85933f13f00cf94d9927a'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b2973b54dc12f4771bb094161f8bbe9f'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b5951e63289a09c605832e2c235b3510'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b5e790a351a3a66c0324d7b8e49df43f'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b611f1b43e91770719d6527659500d02'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b6dcdc59472a79434994d24117cc0e33'::VARCHAR(32) AS map_key,'Europe/Madrid'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b730dab701f2d5cf386202cd57384eec'::VARCHAR(32) AS map_key,'Europe/Dublin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b887436744e7e87d0dfecab024cd74fb'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b9527a6f9c515427d03fbcfae9d52c01'::VARCHAR(32) AS map_key,'America/Sao_Paulo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b9975c032149f6ce852cbca98e7745cc'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b9ece18c950afbfa6b0fdbfa4ff731d3'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'baad5ea844bc654a22d64977d6e6246c'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bb24649a14098b9d51a09fb0ad690128'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bc4a5e17c52eb7d1188ce491ebb54f85'::VARCHAR(32) AS map_key,'America/Tijuana'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bd04a10aceda3e0da2412874a27906cf'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bf2dadabb5f7568a7b0df699e8993a48'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c0008bd6aff65d969e6d9eb0d8256392'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c00fddd54f1e7dacbc43f9a40b7eced0'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c0e453e984e537d11d8ba85fdd94d73b'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c1f8c9ce634f99d4c1ec93264d95b33c'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c6ac46a32d7364688f4e3b001ae790cc'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c7f3c5cba8b73de2cf2c122a27c02e51'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ca155ef86e4efa590306464aa1451164'::VARCHAR(32) AS map_key,'America/Detroit'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cb66e85f3ca4e85b989b98848b336db2'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cd163ca40860f63de2acd0f0a84ec238'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd06e29fdfb33248936557fbd78359682'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd13b50a97e7f094c3fbf3e0eaa628c0f'::VARCHAR(32) AS map_key,'Europe/Bucharest'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd482c0d11c95c75672877f40d31cdec7'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd58d913bc6594db32f13c54709e01597'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd608302cad5d51b457a8aeb1fd161fa9'::VARCHAR(32) AS map_key,'Europe/Bucharest'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd60f1ab6e3550445ea4f3c3766cc88ec'::VARCHAR(32) AS map_key,'Asia/Jakarta'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd691e6bfb06e390e1f531d7cce4d36f6'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd711b954c64506541136ec7dcb6ca108'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd7320d92b9f12523acb1b3fbeb298634'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd97ac4f3e567821433dc1d20c9a1c131'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'da3c1cf6f2694db8244de18fe9847218'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'da418e201b046a2571cbbae4bab55c5f'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dcd90939dc8ad7a417313c5726cf732f'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dd0a544fa9fc9ad707614fb5f631b278'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dd751ace3598c44c564e6216c6b44697'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'deb8c5195afef4e127527d3563928230'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e06b91ca9417c238081c38211a6e1e67'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e10d7e0f6b887d5e11ef6972da2d4597'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e11a24d4117cb39e4e05d11ec393f09f'::VARCHAR(32) AS map_key,'America/Vancouver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e1e1d3d40573127e9ee0480caf1283d6'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e31c1e1d8d5e73e275a9e02f9f691551'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e3d4a839fdfcb260fb4ad664cd3e33ea'::VARCHAR(32) AS map_key,'Etc/GMT'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e495cca4853011f2f16931c06a0d7f34'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e497edf7529022873e52d971dee4a325'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e4dc0838052144aef38521478aad87da'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e79f4894380ed6d0be12dd8a4e383329'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e80af489928f146ce92ae2175757e014'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e90581d18a17cd9c4a6a12cf7eb102e7'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e979083c0caae4a24f0afa458d4633de'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e98fd1eda685e64b1d6dd1ee92ce637e'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'eb6020b8d2dab6a959e87c33f3b69e2d'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ed3c89b08189ee96cbdd12620f4f7a0b'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ee251a7ef0e97219e45833f5a5221f46'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ef0cd883eb5cf3b2cb7083be79b01d58'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f09564c9ca56850d4cd6b3319e541aee'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f0b6c901e32e747ce3dbfe0237ae6519'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f186217753c37b9b9f958d906208506e'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f313bbd3e94afd4801712265917250e9'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f472c73e1eb39a57256f271ae5887f10'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f531caa28b9ccc1824e28d92a6712798'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f5c5b428f7717ab504f64a696711669d'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f6045698f131464d316bf0f61d4a5283'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f752bdf4f710d540579699be7ce03989'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f7af3477fdd83f7d6e011fb445c8be5e'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f85b7b377112c272bc87f3e73f10508d'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f981f6b1ba0c13a03d42fbe2a5103672'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f993cd53be6c75d94a099a091be69719'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f9a89a6026f4196e605fe75e58f9a88c'::VARCHAR(32) AS map_key,'Europe/Oslo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fae817c1f8bd2c4842ac732cb7a8aa12'::VARCHAR(32) AS map_key,'America/Tijuana'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fcff81dcd4c3e01ae739517985b8d42d'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fe7a4d839a0c905cce553179b00aab2b'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fffd40a87ce17b9447d67b40ed75aa6a'::VARCHAR(32) AS map_key,'America/Vancouver'::VARCHAR(64) AS zone_name
), city_map AS (
SELECT '00698d2c0a26912df4a4670f1e04b328'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '00be1f0730fbd924b18bd00909c1596a'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '01093bcc1d00ee9daee685220e0b17dd'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '02140d679b8e8474e2d41735f047e7e4'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '02bd32b2034a1f201b3e2c25b24dda14'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '03c89a90dda510ad255bc9062b915d94'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '048d66ad63e096e443c9a50a10446cb8'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '087599d95c37d7f032e3509794000e16'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0885a3ad7a0d4fe684c21951ac789d9c'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '08d3e762131392c70f9117dd13cf8683'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '09c80073c080f1c8ab2508a31b513cef'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0b7ea8c168714dabb38a9c601b458cd6'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0beeb4979a0693df439fb57689b9f296'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0c194b86b9856881d4e209dbbff35c4d'::VARCHAR(32) AS map_key,'Europe/Dublin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0c6eb8cbf7c004ee0a996fd9d0df4edd'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0cb93755f1621e84d59f00b26a95a003'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0d6044ff46ac501d21d459f77060147f'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '0f1851f7cae4ce2a5329ec73ffbe7e6a'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '107225a1b0693d0b1553c4e1200a388a'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '12aea7bc5bf1f33cbdc5a4ce6b10daab'::VARCHAR(32) AS map_key,'Europe/Amsterdam'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '12f958e580708029929cd740ff2c0392'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '16413b9245179786fa0a2bcc584978a4'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '174cf947d8c6dc6607c01568330374af'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '17a7bcc5789c42e222d021ab8a56a1e8'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1853333cf77e77e2ffcaaacb57acbe76'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '18a3ce7436d9499aaa7431a2afc24bee'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1a85248b148fbf704686800ccdbbf59e'::VARCHAR(32) AS map_key,'Europe/Amsterdam'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1f9db421a7a31e672d33224be6e499d0'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '1fed499164c0f511d18007ee65c90988'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2085bb069f85afa01704ee6bcfbcfea6'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '254465d6fab18f6571a9c0b211d30056'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '257f8072078ce66cabd0d670f48a766b'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '264dbd446c111529b78f18f86dc71faa'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '26864048e7b68dc0d2311fb6f1c94bd3'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2697554b5e304f196cc1bbeaf2050f28'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '29b2da22a6aa2781f81e7134bccadf9c'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2cd4dfb5e6394bfdbf7306c6e4e1adb1'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2d8a6c5edea31534d071de716eb77ee2'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '2e99292f10ab793eeb1a30379a4750c4'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '331f5f89ff444ab563d8bc0114fe8c9e'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '33c5b51b45a8ce853dba359e479e8b18'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3605f56eab4602532b63c7076f8f1681'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '37256563aca3e717d36c9002018cbdc6'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '372b03c8f96548a4ce64957d1360db39'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '37959c0b6bfcd1bcf689fa6f30a2e12c'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '390b45fabd478d6aeb04775b7dd0debf'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3965cf0c785978006c79b4d27a3e7f36'::VARCHAR(32) AS map_key,'America/Mexico_City'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '39bc6048f0a1ddf92cec5955133d60db'::VARCHAR(32) AS map_key,'Asia/Jakarta'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3b088bf216b9935642c23ec5c647fbfe'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3e2a71b2749dbef74c0821a420c299d9'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3eb62aacb48e1025ee6fc7f0d9989353'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '3f8429601c184229c01e01ce33d94354'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '406f0a9436bd79b470ecaa22fecc71f3'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '408a85c32e167dc6341c8d60e9388b82'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4157fb25dcba437bb8798f106a425bed'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4189417f01df54afe98a43c16a838da9'::VARCHAR(32) AS map_key,'America/Sao_Paulo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '423d302d2578494bba84ef4d1ab991b2'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '43cd86ce9ed82b8a022710f535f937ce'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4440e2ff93f413186b56b00dc06a4d23'::VARCHAR(32) AS map_key,'Europe/Athens'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '449bd06f5ff45cab54cfd1a9ecf74cd0'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '44f7ebd662b7354474a66ad5d5e8179c'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '474581a9ab91c4d01d021d9ee542be2f'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '475d6fd17364d9f009e681361701a1c0'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '49b378ca63517a070f9f6c5874510bc8'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '49ccddd7b33751ba3f521ab305c129df'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4d18209cef5e81c3d173d81551c93e8a'::VARCHAR(32) AS map_key,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4e29c392759def7426bc0bf1e8d96524'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4e651671c11972256b383449cd9d18b7'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '4eac2cfd44cf51f081ab2ab0df72d014'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '50da1d636b8f6fda3f68e64e6dd030c7'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '53b0a4b859f0ca9d2c0184038ff5fddb'::VARCHAR(32) AS map_key,'Europe/Athens'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '544f468b7f4c24c56e7c231829ee968c'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5a0e73102523b0e66b3a2df9973816ce'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5aad71f087c5411ab12263f621e5c03c'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5b4ae4c8694f395fe96808f753eb55b4'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5b9081a633606bf914e062a0325bb491'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5e6ee4d4fc73cadd151dcaff6bc58ee7'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5f6a7ed88ab8990cfa14fe2e486318e9'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '5fa3912cc90aaddc10faeccd11d5e21b'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '604f18b0047feb6205f630f60e75f095'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '61d35735994ee79c690ade11f450af6a'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '62c6ea3fba14a16c32dfaed1b4027de4'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '63b8b4176a797bf167a11fc2479e9741'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6899dcbf7cf5b7d5172a32e85d6c226c'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6b67a19300452dd7bd9681d3ba458f1c'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6d3289af46080c6af53dde13a5f53e40'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6e22ea850e27ba2afef92e489ef9efc0'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '6ebcee1a0a1f07a15d3a2349244a5b96'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '70cb053be8259108ace4462de15b72e6'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '70cd5b9e5880ec91114631bafd265e5c'::VARCHAR(32) AS map_key,'Europe/Vienna'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '711740a30a6bcb8691dce162b7308c29'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '71d7be4492b04e6dd312e2e43f4d1a64'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '71ebfc204dcf3281a3b699521e41631c'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '73e2d1bb92abdf0aa214631080452480'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '74091a8e9eebe2ed5cf26a9ebda17079'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '747adbae73902dc07fe98da30c3233c2'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7605a9dc0521a43059593206796edc03'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '770a4ae8951b2040a503ea188f372430'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '79e549f94ba583b205b7a81d0c1c7c43'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7a22ab7650ed4f60fe71eeeae37c6c28'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7b76969b7840a0fea318c4cdef5b6415'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7b8b051895be5874a69a7c869fcc54fc'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7c1b0e220f83317b23de284d0c15dabe'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7d5a3cf1dc17f9303d7f3eb6e84a2337'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7f06da7760b403a5f3128c46183bff41'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '7fc6ea10a089d2849c29ba32e0c75a50'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '805b6df205d5603a62e31d7672ddf0f2'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8120abb46ab2f5c57b04760114c5b0ab'::VARCHAR(32) AS map_key,'Europe/Rome'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '820932500222ee1e4a8b4e53dd40c6d1'::VARCHAR(32) AS map_key,'America/Toronto'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '84df4a5a9b90ee15fa73b115526f2581'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8735eec7a464e286de4a95bb4ace0e5b'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '88b4685912df6aef8a0ba599159fb1a4'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '895c67524197fd08f87af82f4e68290e'::VARCHAR(32) AS map_key,'Europe/Helsinki'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8a25a3905353aca336cf20d0fc1a58b7'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8bb856c28da66f4b434e857f31d5f002'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8c439c24920ebb29532177d820f8b93b'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '8e2fbbeb38796329be953f14013cf1f6'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '926584c02f28ccbd37a68dec7ee6a279'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '935be595841dc0439b941a8aaba8597d'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '96555d0b100f40ec8b28f243ab4668cf'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9ae199d2ee3485ab61155256b8230308'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9c76938b59f838433f2d873b50271dc3'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9d12394913c47a9f2e1426e78eafd1a7'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT '9e69f660247b0374fe2624b87c5c18dd'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a088ac6c90913a4da3c9aefcd4b5e086'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a106f407e05fab3917c3a37249fc8227'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a206a915439020d2dd346d0cad59a842'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a24f7be89206b7cbf9d22614280b928e'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a27772edc11369116359ef37ef060322'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a4992853a5bebe3c7007b32b4b5f7431'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a5403d454205ba6410f4bedd78cf161c'::VARCHAR(32) AS map_key,'Asia/Seoul'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a6ec626c80927dde91448b5b90f6ba4f'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'a9a5e72f22d2f3d1cb8fbd9873a0ec1f'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'aa8e2b8814a816803319d759ee8333ff'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ad3979896d9fcb38b57afc96802e58d8'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'add0de222991308d7d718da776bd51d6'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'aef6173b052645a5fcabc2492af7f81c'::VARCHAR(32) AS map_key,'America/Sao_Paulo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'aef89fc909add0cc837bd3996f3694be'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'afe6018d1e0201e67a7c6dc4eea1331f'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b19b792f9527dcc6bc02c26e7ce6e4c1'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b1b9a10633d94b2a01a6ae281000c734'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b4c4d3b9dfc7ce43f9b0af303b5ffa81'::VARCHAR(32) AS map_key,'America/Detroit'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b71d841732ed9770b3f757c4142adb29'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b7425ec03e28fb65431220e44066611a'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'b98e06ecf1dfd799ae489c2b0ab59aec'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bc074b0cb8f96c76e37734521f0a458e'::VARCHAR(32) AS map_key,'Asia/Ho_Chi_Minh'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bc1663ffdb5e7ee6eda8651d92ac5b6a'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'bc774e6df2b6e1a27f92a4a76753474f'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'be41b65cbac520f7500bb39b25577a06'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'becaba227eb75e9ec2eb374b1915983f'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'becadb340d48c57697e53681db3e8dd8'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c2fde45d047482a3d7714f33f9c93247'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c30770013056d89ae27cfba006fcf7e8'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c372f3c89ed2c4ea7ee4f5169013916d'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c5934d84af27c777666b67606fef979e'::VARCHAR(32) AS map_key,'Asia/Bangkok'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'c678e0222a3bd0a52212265a2ddc1222'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cbe4da2d4c51183c60139f45ebd2c747'::VARCHAR(32) AS map_key,'Europe/Berlin'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cd65018cc4ce17ed1020347257bc8225'::VARCHAR(32) AS map_key,'Europe/Zurich'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cd7d3a67861e0958cf28981313e92bd4'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cdea80caa421c108215615f7b1bac23f'::VARCHAR(32) AS map_key,'Europe/Zurich'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ce5fac314c97bd5c57df260f7cb4b7b4'::VARCHAR(32) AS map_key,'America/Detroit'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cf7becfd6a89f733666a4de8682ee8ac'::VARCHAR(32) AS map_key,'Europe/Bucharest'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cf9be41bea20fc5f63972149245d4c0b'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'cffa1c7f3335c17c8ece3a4f11f3dd27'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd651eee36e5c35d418c3b8ac5137cfc1'::VARCHAR(32) AS map_key,'Europe/Stockholm'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd74195836fc5402dacc78b4ecb2511da'::VARCHAR(32) AS map_key,'Europe/Paris'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'd9493bc09017b0a0ab282c6bd78d473a'::VARCHAR(32) AS map_key,'America/Tijuana'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'da5d7c7f24add7aa890903b7bae7ae96'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'db32b27c46fd01af7070436dc82ea2d3'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dbb08a4f194ef56a4f6fbd50b45bb740'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dc9f5f628eb21a012f2d3178868ffd33'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dd9848b3ca82c0ffdb53084580cc9eec'::VARCHAR(32) AS map_key,'Europe/Brussels'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'de0636bc36935c9229c54aaa76754f6d'::VARCHAR(32) AS map_key,'Europe/Oslo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'dea09c75048acb1a3f9e8b0352974b1c'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ded8c85ee4e8a679018c94b080424652'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e09d619cd36da28b27b7f60e1616f556'::VARCHAR(32) AS map_key,'America/Chicago'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e55990dfe36fe959bec8f7e97c27aed8'::VARCHAR(32) AS map_key,'America/Phoenix'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e5be2fb5ecd5e8bf39152a7e5c34bf6d'::VARCHAR(32) AS map_key,'Australia/Sydney'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e7b6652853e86b1eb973b70eb522f311'::VARCHAR(32) AS map_key,'America/Denver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e81f20727eb4afbd88c7e358b8160d69'::VARCHAR(32) AS map_key,'America/Detroit'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'e8eaeb1add7e78235eb564fdb1320220'::VARCHAR(32) AS map_key,'Asia/Kolkata'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'eb69ec16ce6e25ed935809a5bf879215'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ec00d665f5243ff63abd8f676bab8dff'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ec2a96e6c393029b7d63e21d1f94153c'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ef5ab89522c874b6b033e60b2aac2438'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f0408a9fe21640203f2cd52f67cd2833'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f1571b960cb688b2ef32610222741220'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f1be5d6a4ca1f1ca0f504f430f8fc50e'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f4eb8cd346f9ee87f92ef644c51f7004'::VARCHAR(32) AS map_key,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f607dd435cc1e986c98cbae8eca821cf'::VARCHAR(32) AS map_key,'Asia/Tokyo'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f73b374e789618243d935e9fa2ae9caa'::VARCHAR(32) AS map_key,'America/Vancouver'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'f875dab87126c9a254a47253917199ce'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'faf0d137f0d089d816c5c28a72db304f'::VARCHAR(32) AS map_key,'Europe/Bucharest'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fbe5354b7bf11565bb48117fd1260a82'::VARCHAR(32) AS map_key,'Europe/London'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fc280ee572f0dd1213d9dc70f8ae45d8'::VARCHAR(32) AS map_key,'Europe/Madrid'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fe1d50ff4602a4adc2e47fc97e482025'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'fe42d53dfdf9ee3d48938ad6c6649bcd'::VARCHAR(32) AS map_key,'America/Los_Angeles'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ff2c3b1ac464b40a49bdd6af8b668b71'::VARCHAR(32) AS map_key,'Asia/Shanghai'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ff3b28d2c80ee7de7dbf30ed35320af4'::VARCHAR(32) AS map_key,'America/Kentucky/Louisville'::VARCHAR(64) AS zone_name
UNION ALL
SELECT 'ff7324e5f53836ade16241409b74030c'::VARCHAR(32) AS map_key,'America/New_York'::VARCHAR(64) AS zone_name
), zones AS (
 SELECT w.snapshot_date,w.employee_id,w.manager_id,w.engineering,w.site_key,w.city_key,w.source_rows,w.manager_variants,w.site_variants,w.city_variants,
        s.zone_name AS site_zone,c.zone_name AS city_zone
 FROM workforce w
 LEFT JOIN site_map s ON s.map_key=w.site_key
 LEFT JOIN city_map c ON c.map_key=w.city_key
), mapped AS (
 SELECT z.snapshot_date,z.employee_id,z.manager_id,z.engineering,z.site_key,z.city_key,z.source_rows,z.manager_variants,z.site_variants,z.city_variants,z.site_zone,z.city_zone, CASE WHEN site_zone IS NOT NULL AND city_zone IS NOT NULL
                       AND site_zone<>city_zone THEN NULL
                   ELSE COALESCE(site_zone,city_zone) END AS zone_name
 FROM zones z
), pairs AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,p.zone_name,
        m.snapshot_date AS manager_snapshot,m.employee_id AS matched_manager,
        m.site_key AS manager_site,m.city_key AS manager_city,m.zone_name AS manager_zone,
        p.source_rows,p.manager_variants,p.site_variants,p.city_variants,
        m.source_rows AS manager_rows,m.site_variants AS manager_site_variants,
        m.city_variants AS manager_city_variants,
        CASE WHEN p.site_zone IS NOT NULL AND p.city_zone IS NOT NULL
                       AND p.site_zone<>p.city_zone THEN 1 ELSE 0 END AS mapping_conflict,
        CASE WHEN p.source_rows=1 AND p.manager_variants=1 AND p.site_variants=1
                       AND p.city_variants=1 AND m.source_rows=1
                       AND m.site_variants=1 AND m.city_variants=1
                       AND p.manager_id<>p.employee_id THEN 1 ELSE 0 END AS usable_pair
 FROM mapped p LEFT JOIN mapped m
   ON m.snapshot_date=p.snapshot_date AND m.employee_id=p.manager_id
 WHERE p.engineering='Engineering'
), offsets AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,p.zone_name,p.manager_snapshot,p.matched_manager,p.manager_site,p.manager_city,p.manager_zone,p.source_rows,p.manager_variants,p.site_variants,p.city_variants,p.manager_rows,p.manager_site_variants,p.manager_city_variants,p.mapping_conflict,p.usable_pair,
   CONVERT_TIMEZONE('UTC',zone_name,DATEADD(hour,12,snapshot_date)) AS local_time,
   CONVERT_TIMEZONE('UTC',manager_zone,DATEADD(hour,12,snapshot_date)) AS manager_local_time
 FROM pairs p
), encoded AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,p.zone_name,p.manager_snapshot,p.matched_manager,p.manager_site,p.manager_city,p.manager_zone,p.source_rows,p.manager_variants,p.site_variants,p.city_variants,p.manager_rows,p.manager_site_variants,p.manager_city_variants,p.mapping_conflict,p.usable_pair,p.local_time,p.manager_local_time,
   CASE WHEN usable_pair<>1 OR site_key IS NULL OR manager_site IS NULL
                   OR city_key IS NULL OR manager_city IS NULL THEN '(unknown)'
        WHEN site_key=manager_site AND city_key=manager_city THEN 'same recorded site and city'
        ELSE 'different recorded site or city' END AS manager_colocation_v11,
   CASE WHEN usable_pair<>1 OR site_key IS NULL OR manager_site IS NULL THEN '(unknown)'
        WHEN site_key=manager_site THEN 'same recorded site'
        WHEN zone_name IS NULL OR manager_zone IS NULL THEN '(unmapped geography)'
        WHEN ABS(DATEDIFF(minute,local_time,manager_local_time))<=240 THEN 'different site up to 4 hours'
        ELSE 'different site more than 4 hours' END AS manager_timezone_relation
 FROM offsets p
)
-- MODEL_OUTPUT
SELECT snapshot_date,MD5(CAST(employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       manager_colocation_v11,manager_timezone_relation
FROM encoded
