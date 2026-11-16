
import pandas as pd

# ==================================================
# 1. LOAD ENRICHED DATASET
# ==================================================

print("\n===== LOADING ENRICHED DATASET =====")

sold = pd.read_csv(
    "sold_residential_with_school_districts.csv",
    low_memory=False
)

print("Transactions:", len(sold))
print("Columns:", len(sold.columns))


# ==================================================
# 2. PREPARE NUMERIC COLUMNS
# ==================================================

print("\n===== PREPARING NUMERIC COLUMNS =====")

numeric_columns = [
    "ClosePrice",
    "PricePerSqFt",
    "PriceRatio",
    "DaysOnMarket"
]

for column in numeric_columns:
    sold[column] = pd.to_numeric(
        sold[column],
        errors="coerce"
    )


# ==================================================
# 3. CREATE SCHOOL DISTRICT SUMMARY FUNCTION
# ==================================================

def create_district_summary(
    data,
    district_column,
    county_column,
    district_type
):

    print(f"\n===== {district_type.upper()} DISTRICT ANALYSIS =====")

    # Keep transactions with an assigned district
    district_data = data.dropna(
        subset=[district_column]
    ).copy()

    # Group transactions by district and county
    summary = (
        district_data.groupby(
            [district_column, county_column],
            dropna=False
        )
        .agg(
            Transactions=("ClosePrice", "size"),
            MedianSalePrice=("ClosePrice", "median"),
            MedianPricePerSqFt=("PricePerSqFt", "median"),
            MedianPriceRatio=("PriceRatio", "median"),
            MedianDaysOnMarket=("DaysOnMarket", "median")
        )
        .reset_index()
    )

    # Rename columns for clearer output
    summary = summary.rename(
        columns={
            district_column: "SchoolDistrict",
            county_column: "DistrictCounty"
        }
    )

    # Sort districts by transaction volume
    summary = summary.sort_values(
        "Transactions",
        ascending=False
    )

    # Round financial metrics
    summary["MedianSalePrice"] = (
        summary["MedianSalePrice"].round(2)
    )

    summary["MedianPricePerSqFt"] = (
        summary["MedianPricePerSqFt"].round(2)
    )

    summary["MedianPriceRatio"] = (
        summary["MedianPriceRatio"].round(4)
    )

    summary["MedianDaysOnMarket"] = (
        summary["MedianDaysOnMarket"].round(1)
    )

    # Display results
    print("Number of district groups:", len(summary))

    print("\nTOP 15 DISTRICTS BY TRANSACTION COUNT:")

    print(
        summary.head(15).to_string(index=False)
    )

    return summary


# ==================================================
# 4. ELEMENTARY SCHOOL DISTRICT ANALYSIS
# ==================================================

elementary_summary = create_district_summary(
    sold,
    "ElementarySchoolDistrict",
    "ElementarySchoolDistrictCounty",
    "Elementary"
)


# ==================================================
# 5. HIGH SCHOOL DISTRICT ANALYSIS
# ==================================================

high_summary = create_district_summary(
    sold,
    "HighSchoolDistrict",
    "HighSchoolDistrictCounty",
    "High School"
)


# ==================================================
# 6. UNIFIED SCHOOL DISTRICT ANALYSIS
# ==================================================

unified_summary = create_district_summary(
    sold,
    "UnifiedSchoolDistrict",
    "UnifiedSchoolDistrictCounty",
    "Unified"
)


# ==================================================
# 7. SAVE SUMMARY TABLES
# ==================================================

print("\n===== SAVING SCHOOL DISTRICT SUMMARIES =====")

elementary_summary.to_csv(
    "school_district_elementary_summary.csv",
    index=False
)

high_summary.to_csv(
    "school_district_high_summary.csv",
    index=False
)

unified_summary.to_csv(
    "school_district_unified_summary.csv",
    index=False
)

print("Saved: school_district_elementary_summary.csv")
print("Saved: school_district_high_summary.csv")
print("Saved: school_district_unified_summary.csv")

print("\n===== SCHOOL DISTRICT ANALYSIS COMPLETE =====")
