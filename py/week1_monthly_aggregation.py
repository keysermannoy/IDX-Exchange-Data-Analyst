import pandas as pd
import os

# Folder containing the monthly listing CSV files
csv_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "CSV")

# List of months from January 2024 through April 2026
months = pd.date_range(start="2024-01", end="2026-04", freq="MS").strftime("%Y%m").tolist()

# Store each monthly listing dataset
listing_datasets = []

# Read each monthly listing file
for month in months:
    filename = f"CRMLSListing{month}.csv"
    filepath = os.path.join(csv_folder, filename)

    df = pd.read_csv(filepath)

    # Comment: row count for each monthly file
    print(f"{filename}: {len(df)} rows")

    listing_datasets.append(df)

# Combine all monthly listing datasets
listings = pd.concat(listing_datasets, ignore_index=True)

# Row count after concatenation
print(f"Total listing rows before Residential filter: {len(listings)}")
# Listing rows before Residential filter: 860898

# Keep only Residential properties
listings = listings[listings["PropertyType"] == "Residential"]

# Row count after Residential filter
print(f"Total listing rows after Residential filter: {len(listings)}")
# Listing rows after Residential filter: 547162

# Save the combined Residential listing dataset
output_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "listings_residential_combined.csv"
)

listings.to_csv(output_file, index=False)

print(f"Saved combined listings dataset to: {output_file}")

# --------------------------------------------------
# SOLD DATASETS
# --------------------------------------------------

# Store each monthly sold dataset
sold_datasets = []

# Months from January 2024 through April 2026
for month in months:

    # Some sold files have "_filled" in their filename
    filled_months = [
        "202401",
        "202403",
        "202404",
        "202405",
        "202406",
        "202407",
        "202501"
    ]

    if month in filled_months:
        filename = f"CRMLSSold{month}_filled.csv"
    else:
        filename = f"CRMLSSold{month}.csv"

    filepath = os.path.join(csv_folder, filename)

    df = pd.read_csv(filepath)

    # Comment: row count for each monthly file
    print(f"{filename}: {len(df)} rows")

    sold_datasets.append(df)

# Combine all monthly sold datasets
sold = pd.concat(sold_datasets, ignore_index=True)

# Row count after concatenation
print(f"Total sold rows before Residential filter: {len(sold)}")
# Sold rows before Residential filter: 615707

# Keep only Residential properties
sold = sold[sold["PropertyType"] == "Residential"]

# Row count after Residential filter
print(f"Total sold rows after Residential filter: {len(sold)}")
# Sold rows after Residential filter: 414054

# Save the combined Residential sold dataset
sold_output_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sold_residential_combined.csv"
)

sold.to_csv(sold_output_file, index=False)

print(f"Saved combined sold dataset to: {sold_output_file}")

