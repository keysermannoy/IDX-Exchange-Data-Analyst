import pandas as pd
import geopandas as gpd

# ==================================================
# 1. LOAD DATASETS
# ==================================================

print("\n===== LOADING DATASETS =====")

sold = pd.read_csv(
    "sold_residential_engineered.csv",
    low_memory=False
)

districts = gpd.read_file(
    "data/DistrictAreas2425/DistrictAreas2425.shp"
)

print("Transactions:", len(sold))
print("School districts:", len(districts))


# ==================================================
# 2. PREPARE PROPERTY COORDINATES
# ==================================================

print("\n===== PREPARING PROPERTY COORDINATES =====")

# Keep only records with coordinates
valid_coordinates = (
    sold["Latitude"].between(-90, 90) &
    sold["Longitude"].between(-180, 180) &
    ~((sold["Latitude"] == 0) & (sold["Longitude"] == 0))
)

print("Records with usable coordinate values:",
      valid_coordinates.sum())

# Create a GeoDataFrame using longitude and latitude
properties = gpd.GeoDataFrame(
    sold.loc[valid_coordinates].copy(),
    geometry=gpd.points_from_xy(
        sold.loc[valid_coordinates, "Longitude"],
        sold.loc[valid_coordinates, "Latitude"]
    ),
    crs="EPSG:4326"
)

# Convert coordinates to match school district dataset
properties = properties.to_crs(districts.crs)


# ==================================================
# 3. PREPARE SCHOOL DISTRICT DATA
# ==================================================

print("\n===== PREPARING SCHOOL DISTRICTS =====")

districts = districts[
    [
        "DistrictNa",
        "CountyName",
        "DistrictTy",
        "GradeLow",
        "GradeHigh",
        "geometry"
    ]
].copy()

districts = districts.rename(
    columns={
        "DistrictNa": "SchoolDistrict",
        "CountyName": "SchoolDistrictCounty",
        "DistrictTy": "SchoolDistrictType"
    }
)

print("\n===== SCHOOL DISTRICT TYPES =====")
print(districts["SchoolDistrictType"].value_counts())

print("\n===== GRADE LEVELS =====")
print(
    districts[
        ["SchoolDistrictType", "GradeLow", "GradeHigh"]
    ].drop_duplicates().to_string(index=False)
)


# ==================================================
# 4. SPATIAL JOIN
# ==================================================

print("\n===== MATCHING PROPERTIES TO SCHOOL DISTRICTS =====")

matched = gpd.sjoin(
    properties,
    districts,
    how="left",
    predicate="within"
)

# Keep only records that matched a school district
valid_matches = matched[
    matched["SchoolDistrict"].notna()
].copy()

# Check multiple matches
match_counts = (
    valid_matches.groupby(level=0)["SchoolDistrict"].nunique()
)

print("\n===== MATCH VALIDATION =====")
print("Properties matched:", len(match_counts))
print("Properties with multiple district matches:",
      (match_counts > 1).sum())

# Check multiple matches within the same district type
valid_matches["_property_index"] = valid_matches.index

same_type_counts = (
    valid_matches.groupby(
        ["_property_index", "SchoolDistrictType"]
    )["SchoolDistrict"].nunique()
)

print("\n===== MULTIPLE MATCHES WITHIN DISTRICT TYPE =====")

for district_type in ["Elementary", "High", "Unified"]:
    type_matches = same_type_counts[
        same_type_counts.index.get_level_values(
            "SchoolDistrictType"
        ) == district_type
    ]

    print(
        district_type,
        "properties with multiple matches:",
        (type_matches > 1).sum()
    )


# ==================================================
# 5. CREATE SEPARATE DISTRICT COLUMNS
# ==================================================
# Preserve original MLS-reported school district information
sold.rename(
    columns={
        "ElementarySchoolDistrict": "MLSReportedElementarySchoolDistrict",
        "HighSchoolDistrict": "MLSReportedHighSchoolDistrict"
    },
    inplace=True
)

print("\n===== CREATING DISTRICT COLUMNS =====")

# Initialize new columns
for district_type in ["Elementary", "High", "Unified"]:
    sold[f"{district_type}SchoolDistrict"] = pd.NA
    sold[f"{district_type}SchoolDistrictCounty"] = pd.NA

# Assign district information separately by type
for district_type in ["Elementary", "High", "Unified"]:

    type_data = valid_matches[
        valid_matches["SchoolDistrictType"] == district_type
    ]

    # Preserve all unique district names for each property
    district_names = (
        type_data.groupby(level=0)["SchoolDistrict"]
        .agg(lambda x: " | ".join(sorted(set(x.dropna().astype(str)))))
    )

    district_counties = (
        type_data.groupby(level=0)["SchoolDistrictCounty"]
        .agg(lambda x: " | ".join(sorted(set(x.dropna().astype(str)))))
    )

    sold.loc[
        district_names.index,
        f"{district_type}SchoolDistrict"
    ] = district_names

    sold.loc[
        district_counties.index,
        f"{district_type}SchoolDistrictCounty"
    ] = district_counties

# Total number of distinct district matches per transaction
sold["SchoolDistrictMatchCount"] = 0

sold.loc[
    match_counts.index,
    "SchoolDistrictMatchCount"
] = match_counts


# ==================================================
# 6. COUNTY VALIDATION
# ==================================================

print("\n===== COUNTY MATCH VALIDATION =====")

county_check = valid_matches[
    valid_matches["CountyOrParish"].notna() &
    valid_matches["SchoolDistrictCounty"].notna()
].copy()

transaction_county = (
    county_check["CountyOrParish"]
    .str.replace(r"\s+county$", "", regex=True, case=False)
    .str.strip()
    .str.lower()
)

district_county = (
    county_check["SchoolDistrictCounty"]
    .str.strip()
    .str.lower()
)

county_mismatch = transaction_county != district_county

print("District matches compared:", len(county_check))
print("County mismatches:", county_mismatch.sum())

print("\n===== SAMPLE COUNTY MISMATCHES =====")

print(
    county_check.loc[
        county_mismatch,
        [
            "CountyOrParish",
            "SchoolDistrictCounty",
            "SchoolDistrict",
            "SchoolDistrictType"
        ]
    ].head(15).to_string(index=False)
)


# ==================================================
# 7. UNMATCHED TRANSACTIONS
# ==================================================

print("\n===== UNMATCHED PROPERTIES WITH COORDINATES =====")

unmatched_coordinates = sold.loc[
    valid_coordinates & ~sold.index.isin(match_counts.index),
    ["CountyOrParish", "Latitude", "Longitude"]
]

print("Count:", len(unmatched_coordinates))

print(
    unmatched_coordinates.head(20).to_string(index=False)
)


# ==================================================
# 8. ENRICHMENT RESULTS
# ==================================================

print("\n===== ENRICHMENT RESULTS =====")

print("Total original transactions:", len(sold))

print("Transactions with at least one district:",
      sold["SchoolDistrictMatchCount"].gt(0).sum())

print("Transactions without a district:",
      sold["SchoolDistrictMatchCount"].eq(0).sum())

print("\n===== DISTRICT TYPE COUNTS =====")

for district_type in ["Elementary", "High", "Unified"]:
    column = f"{district_type}SchoolDistrict"

    print(
        district_type,
        "matches:",
        sold[column].notna().sum()
    )

print("\n===== SAMPLE ENRICHED TRANSACTIONS =====")

print(
    sold[
        [
            "CountyOrParish",
            "Latitude",
            "Longitude",
            "ElementarySchoolDistrict",
            "HighSchoolDistrict",
            "UnifiedSchoolDistrict",
            "SchoolDistrictMatchCount"
        ]
    ].head(10).to_string(index=False)
)


# ==================================================
# 9. SAVE ENRICHED DATASET
# ==================================================

output_file = "sold_residential_with_school_districts.csv"

sold.to_csv(output_file, index=False)

print("\n===== SAVED DATASET =====")
print(output_file)
print("Final dimensions:", sold.shape)
