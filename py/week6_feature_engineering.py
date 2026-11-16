import pandas as pd
import numpy as np

#----------------------------------------------------------------
# 1. LOAD CLEANED SOLD DATASET
print("Loading sold residential dataset...")

sold = pd.read_csv(
    "sold_residential_cleaned.csv",
    low_memory=False
)

print(f"Original dataset dimensions: {sold.shape}")


#----------------------------------------------------------------
# 2. CONVERT DATA TYPES 

# Convert numeric columns
numeric_columns = [
    "ClosePrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket"
]

for col in numeric_columns:
    sold[col] = pd.to_numeric(sold[col], errors="coerce")

# Convert date columns
date_columns = [
    "CloseDate",
    "ListingContractDate",
    "PurchaseContractDate"
]

for col in date_columns:
    sold[col] = pd.to_datetime(sold[col], errors="coerce")

print("\nData types converted successfully.")


#----------------------------------------------------------------
# 3. DATA QUALITY FLAGS

# Flag extremely high sale prices for review
sold["extreme_close_price_flag"] = (
    sold["ClosePrice"] > 100_000_000
)

# Flag implausibly small original list prices
sold["invalid_original_list_price_flag"] = (
    sold["OriginalListPrice"] < 1000
)

# Flag very small living areas
sold["small_living_area_flag"] = (
    sold["LivingArea"] < 100
)


#----------------------------------------------------------------
# 4. PRICE RATIO
# ClosePrice / OriginalListPrice

sold["PriceRatio"] = (
    sold["ClosePrice"] /
    sold["OriginalListPrice"].where(
        (sold["OriginalListPrice"] >= 10_000) &
        (~sold["extreme_close_price_flag"])
    )
)


#----------------------------------------------------------------
# 5. CLOSE-TO-ORIGINAL-LIST RATIO
# ClosePrice / OriginalListPrice

sold["CloseToOriginalListRatio"] = sold["PriceRatio"]


#----------------------------------------------------------------
# 6. PRICE PER SQUARE FOOT
# ClosePrice / LivingArea

sold["PricePerSqFt"] = (
    sold["ClosePrice"] /
    sold["LivingArea"].where(
        (sold["LivingArea"] > 100) &
        (~sold["extreme_close_price_flag"])
    )
)


#----------------------------------------------------------------
# 7. DAYS ON MARKET
# Existing DaysOnMarket field
# Preserve the original DaysOnMarket column.
# No additional calculation is necessary.


#----------------------------------------------------------------
# 8. YEAR / MONTH / YRMO
# Derived from CloseDate

sold["Year"] = sold["CloseDate"].dt.year

sold["Month"] = sold["CloseDate"].dt.month

sold["YrMo"] = (
    sold["CloseDate"]
    .dt.to_period("M")
    .astype("string")
)


#----------------------------------------------------------------
# 9. LISTING TO CONTRACT DAYS
# PurchaseContractDate - ListingContractDate

sold["ListingToContractDays"] = (
    sold["PurchaseContractDate"] -
    sold["ListingContractDate"]
).dt.days


#----------------------------------------------------------------
# 10. CONTRACT TO CLOSE DAYS
# CloseDate - PurchaseContractDate

sold["ContractToCloseDays"] = (
    sold["CloseDate"] -
    sold["PurchaseContractDate"]
).dt.days

# DATE QUALITY FLAGS

sold["extreme_price_ratio_flag"] = (
    sold["PriceRatio"] > 2
)

sold["extreme_price_per_sqft_flag"] = (
    sold["PricePerSqFt"] > 10_000
)

sold["invalid_original_list_price_flag"] = (
    sold["OriginalListPrice"] < 10_000
)

sold["negative_listing_to_contract_flag"] = (
    sold["ListingToContractDays"] < 0
)

sold["long_listing_to_contract_flag"] = (
    sold["ListingToContractDays"] > 365
)

sold["negative_contract_to_close_flag"] = (
    sold["ContractToCloseDays"] < 0
)

sold["long_contract_to_close_flag"] = (
    sold["ContractToCloseDays"] > 180
)

sold["missing_living_area_flag"] = sold["LivingArea"].isna()

#----------------------------------------------------------------
# 11. VALIDATE NEW COLUMNS

new_columns = [
    "PriceRatio",
    "CloseToOriginalListRatio",
    "PricePerSqFt",
    "DaysOnMarket",
    "Year",
    "Month",
    "YrMo",
    "ListingToContractDays",
    "ContractToCloseDays"
]

print("\nNEW ENGINEERED COLUMNS:")
print(sold[new_columns].describe().to_string())

flag_columns = [
    "extreme_close_price_flag",
    "invalid_original_list_price_flag",
    "small_living_area_flag",
    "extreme_price_per_sqft_flag",
    "negative_listing_to_contract_flag",
    "long_listing_to_contract_flag",
    "negative_contract_to_close_flag",
    "long_contract_to_close_flag",
    "missing_living_area_flag",
    "extreme_price_ratio_flag"
]

print("\nDATA QUALITY SUMMARY:")

for col in flag_columns:
    print(f"{col}: {sold[col].sum():,}")


#----------------------------------------------------------------
# 12. DISPLAY SAMPLE OUTPUT

sample_columns = [
    "ClosePrice",
    "OriginalListPrice",
    "PriceRatio",
    "CloseToOriginalListRatio",
    "LivingArea",
    "PricePerSqFt",
    "DaysOnMarket",
    "CloseDate",
    "Year",
    "Month",
    "YrMo",
    "ListingToContractDays",
    "ContractToCloseDays"
]

print("\nSAMPLE OF ENGINEERED DATA:")
print(
    sold[sample_columns]
    .head(10)
    .to_string(index=False)
)


#----------------------------------------------------------------
# 13. SAVE ENGINEERED DATASET

sold.to_csv(
    "sold_residential_engineered.csv",
    index=False
)

print("\nEngineered dataset saved successfully!")
print(f"Final dataset dimensions: {sold.shape}")

print("\nWEEK 6 FEATURE ENGINEERING COMPLETED!")


df = pd.read_csv(
    "sold_residential_engineered.csv",
    low_memory=False
)

print("\n===== PRICE RATIO ABOVE 2 =====")

print(
    df[df["PriceRatio"] > 2][
        ["ListingKey", "ClosePrice", "OriginalListPrice",
         "PriceRatio", "PropertySubType", "CountyOrParish"]
    ].sort_values("PriceRatio", ascending=False)
    .head(15)
    .to_string(index=False)
)

print("\n===== PRICE PER SQ FT ABOVE $10,000 =====")

print(
    df[df["PricePerSqFt"] > 10000][
        ["ListingKey", "ClosePrice", "LivingArea",
         "PricePerSqFt", "PropertySubType", "CountyOrParish"]
    ].sort_values("PricePerSqFt", ascending=False)
    .head(15)
    .to_string(index=False)
)


#----------------------------------------------------------------
# COUNTY-LEVEL MARKET SUMMARY
county_summary = sold.groupby("CountyOrParish").agg(
    TransactionCount=("ClosePrice", "count"),
    MedianSalePrice=("ClosePrice", "median"),
    AverageSalePrice=("ClosePrice", "mean"),
    MedianPricePerSqFt=("PricePerSqFt", "median"),
    MedianDaysOnMarket=("DaysOnMarket", "median"),
    MedianPriceRatio=("PriceRatio", "median")
).reset_index()

county_summary = county_summary.sort_values(
    by="TransactionCount",
    ascending=False
)

print("\n===== COUNTY-LEVEL MARKET SUMMARY =====")
print(county_summary.head(15).to_string(index=False))


#----------------------------------------------------------------
# PROPERTY TYPE MARKET SUMMARY

property_summary = sold.groupby("PropertyType").agg(
    TransactionCount=("ClosePrice", "count"),
    MedianSalePrice=("ClosePrice", "median"),
    AverageSalePrice=("ClosePrice", "mean"),
    MedianPricePerSqFt=("PricePerSqFt", "median"),
    MedianDaysOnMarket=("DaysOnMarket", "median"),
    MedianPriceRatio=("PriceRatio", "median")
).reset_index()

property_summary = property_summary.sort_values(
    by="TransactionCount",
    ascending=False
)

print("\n===== PROPERTY TYPE MARKET SUMMARY =====")
print(property_summary.to_string(index=False))


#----------------------------------------------------------------
# PROPERTY SUBTYPE MARKET SUMMARY

subtype_summary = sold.groupby("PropertySubType").agg(
    TransactionCount=("ClosePrice", "count"),
    MedianSalePrice=("ClosePrice", "median"),
    AverageSalePrice=("ClosePrice", "mean"),
    MedianPricePerSqFt=("PricePerSqFt", "median"),
    MedianDaysOnMarket=("DaysOnMarket", "median"),
    MedianPriceRatio=("PriceRatio", "median")
).reset_index()

subtype_summary = subtype_summary.sort_values(
    by="TransactionCount",
    ascending=False
)

print("\n===== PROPERTY SUBTYPE MARKET SUMMARY =====")
print(subtype_summary.to_string(index=False))


#----------------------------------------------------------------
# MLS MARKET AREA SUMMARY

area_summary = sold.groupby("MLSAreaMajor").agg(
    TransactionCount=("ClosePrice", "count"),
    MedianSalePrice=("ClosePrice", "median"),
    AverageSalePrice=("ClosePrice", "mean"),
    MedianPricePerSqFt=("PricePerSqFt", "median"),
    MedianDaysOnMarket=("DaysOnMarket", "median"),
    MedianPriceRatio=("PriceRatio", "median")
).reset_index()

area_summary = area_summary.sort_values(
    by="TransactionCount",
    ascending=False
)

print("\n===== MLS MARKET AREA SUMMARY =====")
print(area_summary.head(20).to_string(index=False))