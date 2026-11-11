-- TerraPulse (run_sql), table anp_fuel_prices_weekly. Dev: period_start < '2023-07-02'.
-- Holdout: period_start BETWEEN '2023-07-02' AND '2023-07-23' (fetched after the plan commit).
WITH x AS (SELECT period_start, location, value,
  row_number() OVER (PARTITION BY observation_id ORDER BY publication_date DESC, retrieved_at DESC) AS rn
  FROM anp_fuel_prices_weekly
  WHERE product='hydrated_ethanol' AND field='retail_price' AND location IN ('SP','MG')
    AND period_start < '2023-07-02')
SELECT period_start AS w, max(CASE WHEN location='SP' THEN value END) AS sp,
       max(CASE WHEN location='MG' THEN value END) AS mg
FROM x WHERE rn=1 GROUP BY period_start ORDER BY period_start;
