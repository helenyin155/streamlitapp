import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(page_title="Housing Explorer", page_icon="🏡", layout="wide")

# CSS Styling for UI
st.markdown("""
    <style>
        /* General Page Styling */
        body {
            background-color: #f7f9f8;
            font-family: 'Inter', sans-serif;
        }

        /* Card Styling */
        .card {
            background-color: #DCEBE4;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }

        /* Title Styling */
        .main-title {
            font-size: 40px;
            font-weight: bold;
            color: black;
            margin-bottom: 10px;
            text-align: center;
        }

        .sub-title {
            font-size: 18px;
            color: black;
            margin-bottom: 30px;
            text-align: center;
        }

        /* Chart Title */
        .chart-title {
            font-size: 20px;
            font-weight: bold;
            color: black;
            margin-bottom: 10px;
            text-align: center;
        }

        /* Sliders */
        .stSlider > div > div > div > div {
            color: #001f3f; /* Navy blue */
        }

        /* Horizontal Line */
        .line {
            margin: 10px 0;
            border-top: 1px solid #001f3f;
        }

        /* Center Content */
        .center-text {
            text-align: center;
            color: #333333;
        }
    </style>
""", unsafe_allow_html=True)

# MongoDB Connection Setup
MONGO_URI = "mongodb+srv://helenyin155:ZogdOfDehLLUPA8F@cluster0.qxthz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["NextDenV1"]
collection = db["Housing Data"]

@st.cache_data
def fetch_housing_data():
    """Fetch housing data from MongoDB."""
    data = list(collection.find({}, {"_id": 0}))
    return pd.DataFrame(data)

housing_df = fetch_housing_data()

# Extract relevant columns
housing_df['price'] = housing_df['Price']
housing_df['area'] = housing_df['Details'].apply(lambda x: x.get('Location', 'Unknown'))
housing_df['bedrooms'] = housing_df['Details'].apply(lambda x: int(x.get('Bedroom(s)', '0')) if x.get('Bedroom(s)', '').isdigit() else 0)
housing_df['distance'] = housing_df['Details'].apply(lambda x: float(x.get('Distance', '0').split()[0]) if x.get('Distance', '').split() else 0.0)

# Page Header
st.markdown("<div class='main-title'>Housing Explorer</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Find the perfect housing options with detailed visualizations and filters</div>", unsafe_allow_html=True)
st.markdown("<div class='line'></div>", unsafe_allow_html=True)  # Add horizontal line

# Filters Section
st.sidebar.header("Filters")
area_filter = st.sidebar.multiselect("Select Area", options=housing_df["area"].unique())
price_range = st.sidebar.slider("Price Range (per month)", 0, int(housing_df['price'].max()), (0, int(housing_df['price'].max())))
bedrooms_filter = st.sidebar.slider("Number of Bedrooms", 0, int(housing_df['bedrooms'].max()), (0, int(housing_df['bedrooms'].max())))
distance_filter = st.sidebar.slider("Distance to Campus (km)", 0.0, float(housing_df['distance'].max()), (0.0, float(housing_df['distance'].max())))

if area_filter == []:
    area_filter = housing_df["area"].unique()

# Apply Filters
filtered_df = housing_df[
    (housing_df["area"].isin(area_filter)) &
    (housing_df["price"] >= price_range[0]) & (housing_df["price"] <= price_range[1]) &
    (housing_df["bedrooms"] >= bedrooms_filter[0]) & (housing_df["bedrooms"] <= bedrooms_filter[1]) &
    (housing_df["distance"] >= distance_filter[0]) & (housing_df["distance"] <= distance_filter[1])
]


# Section 1: Average Housing Price by Area
st.markdown("<div class='card'><div class='chart-title'>Average Housing Price by Area</div>", unsafe_allow_html=True)
avg_price_area = filtered_df.groupby('area')['price'].mean().sort_values(ascending=False)
fig1, ax1 = plt.subplots(figsize=(6, 3))  # Smaller graph size
avg_price_area.plot(kind='bar', ax=ax1, color='#001f3f', alpha=0.8)  # Navy blue bars
ax1.set_xlabel("Area")
ax1.set_ylabel("Average Price ($)")
st.pyplot(fig1)
st.markdown("</div>", unsafe_allow_html=True)

# Section 2: Number of Listings by Area
st.markdown("<div class='card'><div class='chart-title'>Number of Listings by Area</div>", unsafe_allow_html=True)
listings_per_area = filtered_df['area'].value_counts()
fig2, ax2 = plt.subplots(figsize=(6, 3))  # Smaller graph size
listings_per_area.plot(kind='bar', ax=ax2, color='#001f3f', alpha=0.8)  # Navy blue bars
ax2.set_xlabel("Area")
ax2.set_ylabel("Number of Listings")
st.pyplot(fig2)
st.markdown("</div>", unsafe_allow_html=True)

# Section 3: Average Price Based on Number of Bedrooms
st.markdown("<div class='card'><div class='chart-title'>Average Price Based on Number of Bedrooms</div>", unsafe_allow_html=True)
avg_price_bedrooms = filtered_df.groupby('bedrooms')['price'].mean().sort_index()
fig3, ax3 = plt.subplots(figsize=(6, 3))  # Smaller graph size
avg_price_bedrooms.plot(kind='bar', ax=ax3, color='#001f3f', alpha=0.8)  # Navy blue bars
ax3.set_xlabel("Number of Bedrooms")
ax3.set_ylabel("Average Price ($)")
st.pyplot(fig3)
st.markdown("</div>", unsafe_allow_html=True)

# Section 4: Distance to Campus vs. Price
st.markdown("<div class='card'><div class='chart-title'>Distance to Campus vs. Price</div>", unsafe_allow_html=True)
fig4, ax4 = plt.subplots(figsize=(6, 3))  # Smaller graph size
ax4.scatter(filtered_df['distance'], filtered_df['price'], alpha=0.7, color='#001f3f')  # Navy blue points
ax4.set_xlabel("Distance to Campus (km)")
ax4.set_ylabel("Price ($)")
st.pyplot(fig4)
st.markdown("</div>", unsafe_allow_html=True)

# Summary Section
st.markdown("""
<div class="card">
    <div class="chart-title">Summary</div>
    <p><b>Total Listings:</b> {}</p>
    <p><b>Filtered Listings:</b> {}</p>
</div>
""".format(len(housing_df), len(filtered_df)), unsafe_allow_html=True)
