
from sodapy import Socrata
from pipeline.config import settings
import pandas as pd

client = Socrata(
    settings.socrata_domain,
    settings.socrata_app_token,
    timeout=60
)

try:
    records = client.get(
        settings.socrata_dataset_id,
        limit=10,
        order="last_updated DESC"
    )

    df = pd.DataFrame.from_records(records)

    print("\nLATEST 10 RECORDS FROM SOCRATA API")
    print("=" * 60)

    if df.empty:
        print("API returned no records.")
    else:
        print(df[["id", "date_time", "last_updated"]].to_string(index=False))

        print("\nLatest incident date:")
        print(df["date_time"].max())

        print("\nLatest update timestamp:")
        print(df["last_updated"].max())

finally:
    client.close()
