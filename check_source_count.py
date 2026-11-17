
from sodapy import Socrata
from pipeline.config import settings
from pipeline.extract import extract_data

client = Socrata(
    settings.socrata_domain,
    settings.socrata_app_token,
    timeout=60
)

try:
    # Independent count directly from Socrata
    count_result = client.get(
        settings.socrata_dataset_id,
        select="count(*) as total"
    )

    latest_result = client.get(
        settings.socrata_dataset_id,
        select="max(date_time) as latest_incident, "
            "max(last_updated) as latest_update"
    )

    print("LIVE SOCRATA API")
    print("Total records:", count_result[0]["total"])
    print("Latest timestamps:", latest_result[0])

finally:
    client.close()

# Now test your actual pipeline extractor
df = extract_data()

print("\nPIPELINE EXTRACTOR")
print("Extracted rows:", len(df))
print("Unique IDs:", df["id"].nunique())
print("Latest incident:", df["date_time"].max())
print("Latest source update:", df["last_updated"].max())
