
from pathlib import Path
import pandas as pd

# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Input datasets are in the main project folder
sold_path = BASE_DIR / "sold_residential_with_mortgage_rates.csv"
listings_path = BASE_DIR / "listings_residential_with_mortgage_rates.csv"

# Check that both files exist
print("Sold dataset exists:", sold_path.exists())
print("Listings dataset exists:", listings_path.exists())

print("Sold file:", sold_path)
print("Listings file:", listings_path)


# Load the datasets
sold = pd.read_csv(sold_path, low_memory=False)
listings = pd.read_csv(listings_path, low_memory=False)

# Record original dimensions before cleaning
print("\n--- ORIGINAL DATASET SUMMARY ---")

print(f"Sold rows: {len(sold):,}")
print(f"Sold columns: {len(sold.columns):,}")

print(f"Listings rows: {len(listings):,}")
print(f"Listings columns: {len(listings.columns):,}")

# Check the required columns
required_columns = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate",
    "ContractStatusChangeDate",
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "Latitude",
    "Longitude",
]

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    print(f"\n{dataset_name} missing required columns: {missing_columns}")


# Inspect columns related to bedrooms, bathrooms, dates,
# numeric property details, and geographic coordinates

print("\n--- RELEVANT COLUMN NAMES ---")

keywords = [
    "bed", "bath", "room",
    "date", "price", "area",
    "market", "latitude", "longitude",
    "propertytype", "year_month", "mortgage"
]

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    print(f"\n{dataset_name} dataset:")

    for column in df.columns:
        if any(word in column.lower() for word in keywords):
            print(f"{column}: {df[column].dtype}")

#-----------
# DATE CONSISTENCY CHECK (WEEK 4)
#-------------

date_columns = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate",
    "ContractStatusChangeDate",
]

print("\n--- DATE CONVERSION ---")

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    print(f"\n{dataset_name} dataset:")

    # Convert date columns to datetime
    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )
            print(f"{column}: {df[column].dtype}")

    # Check date consistency.
    # Missing dates are not automatically considered violations.
    listing = df["ListingContractDate"]
    purchase = df["PurchaseContractDate"]
    close = df["CloseDate"]

    df["listing_after_close_flag"] = (
        listing.notna()
        & close.notna()
        & (listing > close)
    )

    df["purchase_after_close_flag"] = (
        purchase.notna()
        & close.notna()
        & (purchase > close)
    )
    # A purchase contract dated before the listing date
    # violates the expected listing -> purchase -> closing order.
    df["negative_timeline_flag"] = (
        listing.notna()
        & purchase.notna()
        & (purchase < listing)
    )

    # Report the number of violations
    print("\nDate consistency flag counts:")

    for flag in [
        "listing_after_close_flag",
        "purchase_after_close_flag",
        "negative_timeline_flag",
    ]:
        print(f"{flag}: {df[flag].sum():,}")

# NUMERIC DATA QUALITY CHECKS
numeric_columns = [
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
]

print("\n--- NUMERIC DATA QUALITY CHECKS ---")

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    print(f"\n{dataset_name} dataset:")

    for column in numeric_columns:
        if column not in df.columns:
            print(f"{column}: COLUMN NOT FOUND")
            continue

        # Ensure values are numeric
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        print(
            f"{column}: dtype={df[column].dtype}, "
            f"missing={df[column].isna().sum():,}"
        )

    # Count invalid numeric values
    invalid_checks = {
        "ClosePrice <= 0": df["ClosePrice"] <= 0,
        "LivingArea <= 0": df["LivingArea"] <= 0,
        "DaysOnMarket < 0": df["DaysOnMarket"] < 0,
        "BedroomsTotal < 0": df["BedroomsTotal"] < 0,
        "BathroomsTotalInteger < 0": (
            df["BathroomsTotalInteger"] < 0
        ),
    }

    print("\nInvalid numeric value counts:")

    for check_name, condition in invalid_checks.items():
        # Missing values are excluded from these counts
        count = condition.fillna(False).sum()
        print(f"{check_name}: {count:,}")

#----------------------
# GEOGRAPHIC DATA QUALITY CHECKS (WEEK 5)
#----------------------
print("\n--- GEOGRAPHIC DATA QUALITY CHECKS ---")

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    print(f"\n{dataset_name} dataset:")

    # Ensure coordinates are numeric
    for column in ["Latitude", "Longitude"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    lat = df["Latitude"]
    lon = df["Longitude"]

    # Create boolean quality flags
    df["missing_coordinates_flag"] = (
        lat.isna() | lon.isna()
    )

    df["zero_coordinates_flag"] = (
        lat.eq(0) | lon.eq(0)
    )

    df["positive_longitude_flag"] = lon > 0

    # Broad California coordinate bounds.
    # These are screening bounds, not exact state boundaries.
    df["implausible_coordinates_flag"] = (
        lat.notna()
        & lon.notna()
        & (
            ~lat.between(32.5, 42.1)
            | ~lon.between(-124.5, -114.0)
        )
    )

    # Summarize the results
    flags = [
        "missing_coordinates_flag",
        "zero_coordinates_flag",
        "positive_longitude_flag",
        "implausible_coordinates_flag",
    ]

    for flag in flags:
        print(f"{flag}: {df[flag].sum():,}")

    # Count records with at least one geographic issue
    any_geo_issue = df[flags].any(axis=1)

    print(
        "Records with at least one geographic issue:",
        f"{any_geo_issue.sum():,}"
    )

# INVESTIGATE DUPLICATE-LOOKING COLUMNS
print("\n--- DUPLICATE COLUMN INVESTIGATION ---")

column_pairs = [
    ("PropertyType", "PropertyType.1"),
    ("DaysOnMarket", "DaysOnMarket.1"),
    ("LivingArea", "LivingArea.1"),
    ("Longitude", "Longitude.1"),
    ("Latitude", "Latitude.1"),
    ("ListPrice", "ListPrice.1"),
    ("CloseDate", "CloseDate.1"),
]

for col1, col2 in column_pairs:
    print(f"\nComparing {col1} vs {col2}")

    if col1 not in listings.columns or col2 not in listings.columns:
        print("One or both columns are missing.")
        continue

    first = listings[col1]
    second = listings[col2]

    both_present = first.notna() & second.notna()
    either_present = first.notna() | second.notna()

    # Compare values only where both columns have data
    matches = first.eq(second) & both_present
    mismatches = both_present & ~first.eq(second)

    print("First column missing:", f"{first.isna().sum():,}")
    print("Second column missing:", f"{second.isna().sum():,}")
    print("Rows where both have values:", f"{both_present.sum():,}")
    print("Matching values:", f"{matches.sum():,}")
    print("Different values:", f"{mismatches.sum():,}")
    print(
        "Rows with a value in either column:",
        f"{either_present.sum():,}"
    )

    if mismatches.any():
        print("Example mismatches:")
        print(
            listings.loc[mismatches, [col1, col2]]
            .head(5)
            .to_string(index=False)
        )

# FIND ALL DUPLICATE-LOOKING .1 COLUMNS (listing)
print("\n--- ALL COLUMNS ENDING IN .1 ---")

duplicate_style_columns = [
    col for col in listings.columns
    if col.endswith(".1")
]

print("Number of columns ending in .1:", len(duplicate_style_columns))

for col in duplicate_style_columns:
    original_col = col[:-2]

    if original_col in listings.columns:
        print(f"{original_col}  <->  {col}")
    else:
        print(f"No matching original column found for: {col}")

# CHECK REMAINING DUPLICATE-LOOKING COLUMNS
print("\n--- REMAINING DUPLICATE COLUMN CHECKS ---")

remaining_pairs = [
    ("ListAgentFirstName", "ListAgentFirstName.1"),
    ("ListAgentLastName", "ListAgentLastName.1"),
    ("BuyerOfficeName", "BuyerOfficeName.1"),
    ("UnparsedAddress", "UnparsedAddress.1"),
]

for col1, col2 in remaining_pairs:
    first = listings[col1]
    second = listings[col2]

    both_present = first.notna() & second.notna()
    mismatches = both_present & first.ne(second)

    first_only = first.notna() & second.isna()
    second_only = first.isna() & second.notna()

    print(f"\n{col1} vs {col2}")
    print("Matching values where both are present:",
          f"{(both_present & first.eq(second)).sum():,}")
    print("Different values where both are present:",
          f"{mismatches.sum():,}")
    print("Only original column has a value:",
          f"{first_only.sum():,}")
    print("Only .1 column has a value:",
          f"{second_only.sum():,}")

    if mismatches.any():
        print("Examples of different values:")
        print(
            listings.loc[mismatches, [col1, col2]]
            .head(5)
            .to_string(index=False)
        )

    if second_only.any():
        print("Examples where only .1 has a value:")
        print(
            listings.loc[second_only, [col1, col2]]
            .head(5)
            .to_string(index=False)
        )

# INVESTIGATE BUYER OFFICE NAME MISMATCH
print("\n--- BUYER OFFICE NAME MISMATCH ---")

mismatch = (
    listings["BuyerOfficeName"].notna()
    & listings["BuyerOfficeName.1"].notna()
    & listings["BuyerOfficeName"].ne(listings["BuyerOfficeName.1"])
)

columns_to_show = [
    col for col in [
        "BuyerOfficeName",
        "BuyerOfficeName.1",
        "ListAgentFirstName",
        "ListAgentLastName",
        "UnparsedAddress",
        "ListingContractDate",
        "CloseDate",
        "PropertyType",
    ]
    if col in listings.columns
]

print("Number of mismatches:", f"{mismatch.sum():,}")

print(
    listings.loc[mismatch, columns_to_show].to_string(index=False)
)

# FIND ALL DUPLICATE-LOOKING .1 COLUMNS (sold)
print("\n--- SOLD DATASET: COLUMNS ENDING IN .1 ---")

sold_duplicate_style_columns = [
    col for col in sold.columns
    if col.endswith(".1")
]

print(
    "Number of columns ending in .1:",
    len(sold_duplicate_style_columns)
)

for col in sold_duplicate_style_columns:
    original_col = col[:-2]

    if original_col in sold.columns:
        print(f"{original_col}  <->  {col}")
    else:
        print(f"No matching original column found for: {col}")


# ACTUAL CLEANING - STEP 1
# Remove redundant .1 columns from listings
# The .1 columns are duplicates of their original columns,
# except for one BuyerOfficeName mismatch.
# We preserve the original columns and remove the .1 versions.

print("\n--- CLEANING STEP 1: REDUNDANT COLUMNS ---")

redundant_columns = [
    "PropertyType.1",
    "ListAgentFirstName.1",
    "DaysOnMarket.1",
    "LivingArea.1",
    "Longitude.1",
    "Latitude.1",
    "ListPrice.1",
    "ListAgentLastName.1",
    "CloseDate.1",
    "BuyerOfficeName.1",
    "UnparsedAddress.1",
]

# Only drop columns that actually exist
columns_to_drop = [
    col for col in redundant_columns
    if col in listings.columns
]

listings.drop(columns=columns_to_drop, inplace=True)

print("Redundant columns removed:", len(columns_to_drop))
print("Removed columns:", columns_to_drop)
print("Listings rows after cleaning:", f"{len(listings):,}")
print("Listings columns after cleaning:", f"{len(listings.columns):,}")

# STEP 2: FLAG AND CLEAN INVALID NUMERIC VALUES
# Keep property records, but replace invalid numeric entries with missing values.
# This prevents invalid values from distorting later analysis.

numeric_checks = {
    "invalid_close_price_flag": ("ClosePrice", lambda s: s <= 0),
    "invalid_living_area_flag": ("LivingArea", lambda s: s <= 0),
    "negative_days_on_market_flag": ("DaysOnMarket", lambda s: s < 0),
    "negative_bedrooms_flag": ("BedroomsTotal", lambda s: s < 0),
    "negative_bathrooms_flag": ("BathroomsTotalInteger", lambda s: s < 0),
}

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    print(f"\n{dataset_name}: NUMERIC CLEANING")

    for flag_name, (column, condition) in numeric_checks.items():
        # Identify invalid values before changing them.
        invalid = condition(df[column]).fillna(False)

        # Save a flag so we can identify affected records later.
        df[flag_name] = invalid

        print(f"{flag_name}: {int(invalid.sum())}")

        # Replace invalid values with missing values, not entire rows.
        df.loc[invalid, column] = float("nan")

    print(f"Rows preserved: {len(df):,}")

# STEP 3: EXPORT CLEANED DATASETS
# Save new files so the original source datasets remain unchanged.

sold_output = BASE_DIR / "sold_residential_cleaned.csv"
listings_output = BASE_DIR / "listings_residential_cleaned.csv"

sold.to_csv(sold_output, index=False)
listings.to_csv(listings_output, index=False)

print("\n" + "=" * 50)
print("FINAL CLEANED DATASETS")
print("=" * 50)

for dataset_name, df, output_path in [
    ("Sold", sold, sold_output),
    ("Listings", listings, listings_output),
]:
    print(f"\n{dataset_name}")
    print(f"Output file: {output_path.name}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")
    print("Date column types:")

    for column in [
        "CloseDate",
        "PurchaseContractDate",
        "ListingContractDate",
        "ContractStatusChangeDate",
    ]:
        if column in df.columns:
            print(f"  {column}: {df[column].dtype}")

    print("Numeric column types:")

    for column in [
        "ClosePrice",
        "LivingArea",
        "DaysOnMarket",
        "BedroomsTotal",
        "BathroomsTotalInteger",
        "Latitude",
        "Longitude",
    ]:
        if column in df.columns:
            print(f"  {column}: {df[column].dtype}")

print("\nCleaned CSV files exported successfully.")


# STEP 4: FINAL DATE AND GEOGRAPHIC QUALITY SUMMARY
# Summarize the flags required for the internship report.

date_flags = [
    "listing_after_close_flag",
    "purchase_after_close_flag",
    "negative_timeline_flag",
]

geo_flags = [
    "missing_coordinates_flag",
    "zero_coordinates_flag",
    "positive_longitude_flag",
    "implausible_coordinates_flag",
]

for dataset_name, df in [
    ("Sold", sold),
    ("Listings", listings),
]:
    print(f"\n{'=' * 50}")
    print(f"{dataset_name.upper()}: QUALITY SUMMARY")
    print("=" * 50)

    print("\nDate consistency flags:")
    for flag in date_flags:
        if flag in df.columns:
            print(f"  {flag}: {int(df[flag].sum()):,}")

    print("\nGeographic data quality:")
    for flag in geo_flags:
        if flag in df.columns:
            print(f"  {flag}: {int(df[flag].sum()):,}")

    # Count unique records with at least one geographic issue.
    existing_geo_flags = [f for f in geo_flags if f in df.columns]
    if existing_geo_flags:
        geographic_issue = df[existing_geo_flags].any(axis=1)
        print(
            "  Records with at least one geographic issue: "
            f"{int(geographic_issue.sum()):,}"
        )

print("\nQuality summary complete.")
