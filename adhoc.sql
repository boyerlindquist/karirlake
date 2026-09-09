-- Cek persebaran kota & kecamatan yang belum standar
SELECT
    location_city,
    COUNT(*) AS total
FROM
    init_all_jobs
GROUP BY
    1
ORDER BY
    2 DESC;