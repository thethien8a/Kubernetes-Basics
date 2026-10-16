import os
import time

from pyspark.sql import SparkSession, functions as F


driver_ip = os.environ["POD_IP"]
spark = (
    SparkSession.builder.appName("buoi18-client")
    .config("spark.driver.host", driver_ip)
    .config("spark.driver.bindAddress", "0.0.0.0")
    .getOrCreate()
)

try:
    sc = spark.sparkContext
    print(f"MASTER={sc.master}", flush=True)
    print(f"APP_ID={sc.applicationId}", flush=True)
    print(f"DRIVER_HOST={sc.getConf().get('spark.driver.host')}", flush=True)

    total = (
        spark.range(1, 11, numPartitions=2)
        .filter("id % 2 = 0")
        .selectExpr("id * 10 AS amount")
        .agg(F.sum("amount").alias("total"))
        .first()["total"]
    )
    if total != 300:
        raise RuntimeError(f"Expected total=300, got {total}")
    print(f"RESULT total={total}", flush=True)

    # Keep the Executors visible long enough to inspect the Master UI.
    print("OBSERVE_UI: keeping the application alive for 30 seconds", flush=True)
    time.sleep(30)
finally:
    spark.stop()
