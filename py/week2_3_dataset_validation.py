import pandas as pd
import os

# Find the CSV folder
csv_folder = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "CSV"
)

# Months from January 2024 through April 2026
months = pd.date_range(
    start="2024-01",
    end="2026-04",
    freq="MS"
).strftime("%Y%m").tolist()

# These sold files have "_filled" in their filename
filled_months = [
    "202401",
    "202403",
    "202404",
    "202405",
    "202406",
    "202407",
    "202501"
]

# Store each monthly sold dataset
sold_datasets = []

# Read each monthly sold file
for month in months:

    if month in filled_months:
        filename = f"CRMLSSold{month}_filled.csv"
    else:
        filename = f"CRMLSSold{month}.csv"

    filepath = os.path.join(csv_folder, filename)

    df = pd.read_csv(filepath)

    sold_datasets.append(df)

# Combine all monthly sold datasets
sold = pd.concat(sold_datasets, ignore_index=True)

print(f"Total sold rows: {len(sold)}")

# --------------------------------------------------
# DATASET STRUCTURE
# --------------------------------------------------

# Number of rows and columns
print("Dataset shape:", sold.shape)

# Column names
print("\nColumn names:")
print(sold.columns)

# First 5 rows
print("\nFirst 5 rows:")
print(sold.head())

# Data types
print("\nData types:")
print(sold.dtypes)

# --------------------------------------------------
# PROPERTY TYPE ANALYSIS
# --------------------------------------------------

# Show all unique property types
print("\nUnique Property Types:")
print(sold["PropertyType"].unique())

# Count properties in each category
print("\nProperty Type Counts:")
print(sold["PropertyType"].value_counts(dropna=False))

# Calculate percentage of each property type
print("\nProperty Type Percentages:")
print(sold["PropertyType"].value_counts(normalize=True, dropna=False) * 100)

# --------------------------------------------------
# FILTER TO RESIDENTIAL
# --------------------------------------------------

sold = sold[sold["PropertyType"] == "Residential"]

print("\nAfter Residential Filter:")
print("Rows:", len(sold))
print("Columns:", len(sold.columns))

# --------------------------------------------------
# MISSING VALUE ANALYSIS
# --------------------------------------------------

# Count missing values in each column
missing_count = sold.isnull().sum()

# Calculate percentage of missing values in each column
missing_percent = sold.isnull().mean() * 100

# Create a summary table
missing_report = pd.DataFrame({
    "MissingCount": missing_count,
    "MissingPercent": missing_percent
})

# Sort from most missing to least missing
missing_report = missing_report.sort_values(
    "MissingPercent",
    ascending=False
)

print("\nMissing Value Report:")
print(missing_report)

# Identify columns with more than 90% missing values
high_missing = missing_report[
    missing_report["MissingPercent"] > 90
]

print("\nColumns with more than 90% missing:")
print(high_missing)

# Drop columns with more than 90% missing values
columns_to_drop = high_missing.index

sold = sold.drop(columns=columns_to_drop)

print("\nAfter dropping columns with more than 90% missing:")
print("Rows:", len(sold))
print("Columns:", len(sold.columns))

# --------------------------------------------------
# NUMERIC DATA TYPE CHECK
# --------------------------------------------------

numeric_columns = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt"
]

print("\nNumeric Column Data Types:")
print(sold[numeric_columns].dtypes)

# --------------------------------------------------
# NUMERIC DISTRIBUTION SUMMARY
# --------------------------------------------------

summary_columns = [
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket"
]

numeric_summary = sold[summary_columns].describe(
    percentiles=[0.25, 0.50, 0.75]
)

print("\nNumeric Distribution Summary:")
print(numeric_summary)

# --------------------------------------------------
# HISTOGRAMS
# --------------------------------------------------

import matplotlib.pyplot as plt

# ClosePrice histogram
plt.figure()
sold[sold["ClosePrice"] <= 5000000]["ClosePrice"].dropna().hist(bins=50)
plt.title("Distribution of ClosePrice (Up to $5 Million)")
plt.xlabel("ClosePrice")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# LivingArea histogram
plt.figure()
sold[sold["LivingArea"] <= 10000]["LivingArea"].dropna().hist(bins=50)
plt.title("Distribution of LivingArea (Up to 10,000 sq ft)")
plt.xlabel("LivingArea")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# DaysOnMarket histogram
plt.figure()
sold[sold["DaysOnMarket"] <= 365]["DaysOnMarket"].hist(bins=50)
plt.title("Distribution of DaysOnMarket (Up to 365 Days)")
plt.xlabel("DaysOnMarket")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# Summary: ClosePrice is strongly right-skewed, with most sales concentrated 
# at lower prices and a long right tail caused by high-price properties
# and extreme outliers.

# LivingArea is right-skewed, with most properties having relatively
# smaller living areas and a long right tail caused by unusually large
# properties and extreme outliers.

# DaysOnMarket is right-skewed, with most properties concentrated at
# relatively low values and a long right tail. The dataset also contains
# negative DaysOnMarket values, which indicate potential data-quality issues.

# --------------------------------------------------
# BOXPLOTS
# --------------------------------------------------

for column in summary_columns:
    plt.figure()
    plt.boxplot(sold[column].dropna())
    plt.title(f"Boxplot of {column}")
    plt.ylabel(column)
    plt.tight_layout()
    plt.show()

# Summary: The ClosePrice boxplot shows many high-price outliers.
# The distribution is strongly right-skewed, causing the main box
# to appear compressed near the lower end of the price scale.

# The LivingArea boxplot shows substantial right-skewness and numerous
# high-end outliers. One extremely large observation is approximately
# 17 million square feet, far above the median of 1,642 square feet.

# The DaysOnMarket boxplot shows a strong right-skewed distribution.
# Most observations are concentrated at relatively low values, while
# several high-value observations appear as outliers. The maximum is
# approximately 12,430 days. The dataset also contains negative
# DaysOnMarket values, which may indicate data-quality issues.

# --------------------------------------------------
# SAVE CLEANED RESIDENTIAL DATASET
# --------------------------------------------------

output_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sold_residential_cleaned.csv"
)

sold.to_csv(output_file, index=False)

print("\nCleaned dataset saved to:")
print(output_file)

# --------------------------------------------------
# SAVE MISSING VALUE REPORT
# --------------------------------------------------

missing_report_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "missing_value_report.csv"
)

missing_report.to_csv(missing_report_file)

print("\nMissing value report saved to:")
print(missing_report_file)

# --------------------------------------------------
# SAVE NUMERIC DISTRIBUTION SUMMARY
# --------------------------------------------------

summary_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "numeric_distribution_summary.csv"
)

numeric_summary.to_csv(summary_file)

print("\nNumeric distribution summary saved to:")
print(summary_file)

# Week 3: MORTGAGE RATE ENRICHMENT

# Load the combined Residential datasets from Week 1
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sold_combined = pd.read_csv(
    os.path.join(project_folder, "sold_residential_combined.csv")
)

listings_combined = pd.read_csv(
    os.path.join(project_folder, "listings_residential_combined.csv")
)

print("\nWEEK 3: MORTGAGE RATE ENRICHMENT")
print("Sold rows:", len(sold_combined))
print("Listings rows:", len(listings_combined))


# STEP 1: Fetch mortgage rates from FRED
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

mortgage = pd.read_csv(url, parse_dates=["observation_date"])
mortgage.columns = ["date", "rate_30yr_fixed"]

mortgage["rate_30yr_fixed"] = pd.to_numeric(
    mortgage["rate_30yr_fixed"], errors="coerce"
)

print("\nMortgage data preview:")
print(mortgage.head())

print("\nMortgage data date range:")
print(mortgage["date"].min(), "to", mortgage["date"].max())


# --------------------------------------------------
# STEP 2: RESAMPLE WEEKLY RATES TO MONTHLY AVERAGES
# --------------------------------------------------

mortgage["year_month"] = mortgage["date"].dt.to_period("M")

mortgage_monthly = (
    mortgage.groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .reset_index()
)

print("\nMonthly mortgage rate preview:")
print(mortgage_monthly.head())

print("\nMonthly mortgage rate date range:")
print(mortgage_monthly["year_month"].min(), "to",
      mortgage_monthly["year_month"].max())

print("\nNumber of monthly observations:", len(mortgage_monthly))

# --------------------------------------------------
# STEP 3: CREATE YEAR-MONTH KEYS FOR MLS DATASETS
# --------------------------------------------------

# Sold properties: use the closing date
sold_combined["year_month"] = pd.to_datetime(
    sold_combined["CloseDate"], errors="coerce"
).dt.to_period("M")

# Listings: use the listing contract date
listings_combined["year_month"] = pd.to_datetime(
    listings_combined["ListingContractDate"], errors="coerce"
).dt.to_period("M")

print("\nSold year-month preview:")
print(sold_combined[["CloseDate", "year_month"]].head())

print("\nListings year-month preview:")
print(listings_combined[["ListingContractDate", "year_month"]].head())

print("\nMissing sold year-month keys:",
      sold_combined["year_month"].isna().sum())

print("Missing listings year-month keys:",
      listings_combined["year_month"].isna().sum())


# --------------------------------------------------
# STEP 4: MERGE MORTGAGE RATES INTO MLS DATASETS
# --------------------------------------------------

# Merge monthly mortgage rates into sold properties
sold_with_rates = sold_combined.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)

# Merge monthly mortgage rates into listings
listings_with_rates = listings_combined.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)

print("\nSold dataset after mortgage merge:")
print("Rows:", len(sold_with_rates))
print("Columns:", len(sold_with_rates.columns))

print("\nListings dataset after mortgage merge:")
print("Rows:", len(listings_with_rates))
print("Columns:", len(listings_with_rates.columns))

# Preview the merged results
print("\nSold mortgage rate preview:")
print(
    sold_with_rates[
        ["CloseDate", "year_month", "ClosePrice", "rate_30yr_fixed"]
    ].head()
)

print("\nListings mortgage rate preview:")
print(
    listings_with_rates[
        ["ListingContractDate", "year_month", "ListPrice", "rate_30yr_fixed"]
    ].head()
)


# --------------------------------------------------
# STEP 5: VALIDATE THE MERGE
# --------------------------------------------------

sold_missing_rates = sold_with_rates["rate_30yr_fixed"].isnull().sum()
listings_missing_rates = listings_with_rates["rate_30yr_fixed"].isnull().sum()

print("\nMortgage rate validation:")
print("Sold rows with missing rates:", sold_missing_rates)
print("Listings rows with missing rates:", listings_missing_rates)

# Confirm whether the merge is complete
if sold_missing_rates == 0 and listings_missing_rates == 0:
    print("SUCCESS: All MLS rows have mortgage rates.")
else:
    print("WARNING: Some MLS rows are missing mortgage rates.")


# --------------------------------------------------
# STEP 6: SAVE ENRICHED DATASETS
# --------------------------------------------------

sold_output = os.path.join(
    project_folder,
    "sold_residential_with_mortgage_rates.csv"
)

listings_output = os.path.join(
    project_folder,
    "listings_residential_with_mortgage_rates.csv"
)

sold_with_rates.to_csv(sold_output, index=False)
listings_with_rates.to_csv(listings_output, index=False)

print("\nEnriched datasets saved successfully:")
print(sold_output)
print(listings_output)