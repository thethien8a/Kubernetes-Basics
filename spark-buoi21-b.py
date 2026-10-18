import os
from decimal import Decimal

from pyspark.sql import SparkSession, functions as F


input_uri = "s3a://de-lab/buoi20/input/orders.csv"

spark = (
    SparkSession.builder.appName("buoi21-s3-debug")
    .config("spark.driver.host", os.environ["POD_IP"])
    .config("spark.driver.bindAddress", "0.0.0.0")
    .getOrCreate()
)

try:
    sc = spark.sparkContext
    # Keep retries separate from earlier datasets without overwriting their evidence.
    output_uri = f"s3a://de-lab/buoi21/output/orders/{sc.applicationId}/"
    print(f"MASTER={sc.master}", flush=True)
    print(f"APP_ID={sc.applicationId}", flush=True)
    print(f"DRIVER_HOST={sc.getConf().get('spark.driver.host')}", flush=True)
    print(f"INPUT_URI={input_uri}", flush=True)
    print(f"OUTPUT_TARGET={output_uri}", flush=True)

    orders = (
        spark.read.schema("order_id INT, quantity INT, unit_price DECIMAL(10,2)")
        .option("header", "true")
        .option("enforceSchema", "false")
        .option("mode", "FAILFAST")
        .csv(input_uri)
    )
    result = orders.filter(F.col("quantity") > 0).withColumn(
        "amount", F.col("quantity") * F.col("unit_price")
    )
    result.write.mode("errorifexists").parquet(output_uri)

    # Read persisted output so a correct source DataFrame cannot hide a bad write.
    saved = spark.read.parquet(output_uri)
    # This fixture is tiny; collect is not a validation strategy for large datasets.
    rows = saved.orderBy("order_id").collect()
    actual = [
        (row["order_id"], row["quantity"], row["unit_price"], row["amount"])
        for row in rows
    ]
    expected = [
        (101, 2, Decimal("12.50"), Decimal("25.00")),
        (309, 3, Decimal("7.20"), Decimal("21.60")),
    ]
    if actual != expected:
        raise RuntimeError(f"Expected saved rows={expected}, got {actual}")

    total = sum((row["amount"] for row in rows), Decimal("0.00"))
    if total != Decimal("46.60"):
        raise RuntimeError(f"Expected total=46.60, got {total}")

    for row in rows:
        print(
            f"SAVED_ROW order_id={row['order_id']} quantity={row['quantity']} "
            f"unit_price={row['unit_price']} amount={row['amount']}",
            flush=True,
        )
    print(f"RESULT rows={len(rows)} total={total}", flush=True)
finally:
    spark.stop()
