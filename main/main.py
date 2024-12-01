import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import os
from urllib.parse import quote_plus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page Configuration
st.set_page_config(page_title="Housing Explorer", page_icon="🏡", layout="wide")

# CSS Styling for UI
st.markdown("""
    <style>
        body {
            background-color: #f7f9f8;
            font-family: 'Inter', sans-serif;
        }
        .card {
            background-color: #DCEBE4;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }
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
        .chart-title {
            font-size: 20px;
            font-weight: bold;
            color: black;
            margin-bottom: 10px;
            text-align: center;
        }
        .stSlider > div > div > div > div {
            color: #001f3f;
        }
        .line {
            margin: 10px 0;
            border-top: 1px solid #001f3f;
        }
        .center-text {
            text-align: center;
            color: #333333;
        }
        .error-message {
            color: red;
            padding: 10px;
            border: 1px solid red;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

def get_database_connection():
    """Establish connection to MongoDB with error handling."""
    try:
        # Get MongoDB URI from environment variable or use default for development
        MONGO_URI = os.environ.get(
            "MONGO_URI",
            "mongodb+srv://helenyin155:ZogdOfDehLLUPA8F@cluster0.qxthz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        )
        
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Test the connection
        client.server_info()
        logger.info("Successfully connected to MongoDB")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

@st.cache_data(ttl=600)  # Cache data for 10 minutes
def fetch_housing_data():
    """Fetch housing data from MongoDB with error handling."""
    client = get_database_connection()
    if client is None:
        st.error("Failed to connect to the database. Please check your connection settings.")
        return pd.DataFrame()
        
    try:
        db = client["NextDenV1"]
        collection = db["Housing Data"]
        data = list(collection.find({}, {"_id": 0}))
        
        if not data:
            logger.warning("No data retrieved from database")
            return pd.DataFrame()
            
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()
    finally:
        if client:
            client.close()

def safe_extract_value(details, key, default_value):
    """Safely extract values from the Details dictionary."""
    try:
        if key == 'Distance':
            value = details.get(key, '0')
            return float(value.split()[0]) if value and value.split() else 0.0
        elif key == 'Bedroom(s)':
            value = details.get(key, '0')
            return int(value) if value.isdigit() else 0
        else:
            return details.get(key, default_value)
    except Exception as e:
        logger.error(f"Error extracting {key}: {str(e)}")
        return default_value

# Fetch data
housing_df = fetch_housing_data()

if housing_df.empty:
    st.error("No data available. Please try again later.")
    st.stop()

try:
    # Extract relevant columns with error handling
    housing_df['price'] = housing_df['Price']
    housing_df['area'] = housing_df['Details'].apply(lambda x: safe_extract_value(x, 'Location', 'Unknown'))
    housing_df['bedrooms'] = housing_df['Details'].apply(lambda x: safe_extract_value(x, 'Bedroom(s)', 0))
    housing_df['distance'] = housing_df['Details'].apply(lambda x: safe_extract_value(x, 'Distance', 0.0))

    # Page Header
    st.markdown("<div class='main-title'>Housing Explorer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Find the perfect housing options with detailed visualizations and filters</div>", unsafe_allow_html=True)
    st.markdown("<div class='line'></div>", unsafe_allow_html=True)

    # Filters Section
    st.sidebar.header("Filters")
    
    # Get unique areas and sort them
    unique_areas = sorted(housing_df["area"].unique())
    area_filter = st.sidebar.multiselect("Select Area", options=unique_areas)
    
    # Safe price range calculation
    max_price = int(housing_df['price'].max()) if not housing_df['price'].empty else 10000
    price_range = st.sidebar.slider("Price Range (per month)", 0, max_price, (0, max_price))
    
    # Safe bedroom range calculation
    max_bedrooms = int(housing_df['bedrooms'].max()) if not housing_df['bedrooms'].empty else 5
    bedrooms_filter = st.sidebar.slider("Number of Bedrooms", 0, max_bedrooms, (0, max_bedrooms))
    
    # Safe distance range calculation
    max_distance = float(housing_df['distance'].max()) if not housing_df['distance'].empty else 10.0
    distance_filter = st.sidebar.slider("Distance to Campus (km)", 0.0, max_distance, (0.0, max_distance))

    # Apply Filters
    if not area_filter:  # If no area is selected, include all areas
        area_filter = unique_areas

    filtered_df = housing_df[
        (housing_df["area"].isin(area_filter)) &
        (housing_df["price"] >= price_range[0]) & (housing_df["price"] <= price_range[1]) &
        (housing_df["bedrooms"] >= bedrooms_filter[0]) & (housing_df["bedrooms"] <= bedrooms_filter[1]) &
        (housing_df["distance"] >= distance_filter[0]) & (housing_df["distance"] <= distance_filter[1])
    ]

    # Check if we have data after filtering
    if filtered_df.empty:
        st.warning("No properties match your selected filters. Please adjust your criteria.")
    else:
        # Section 1: Average Housing Price by Area
        st.markdown("<div class='card'><div class='chart-title'>Average Housing Price by Area</div>", unsafe_allow_html=True)
        avg_price_area = filtered_df.groupby('area')['price'].mean().sort_values(ascending=False)
        fig1, ax1 = plt.subplots(figsize=(6, 3))
        avg_price_area.plot(kind='bar', ax=ax1, color='#001f3f', alpha=0.8)
        ax1.set_xlabel("Area")
        ax1.set_ylabel("Average Price ($)")
        plt.xticks(rotation=45)
        st.pyplot(fig1)
        st.markdown("</div>", unsafe_allow_html=True)

        # Section 2: Number of Listings by Area
        st.markdown("<div class='card'><div class='chart-title'>Number of Listings by Area</div>", unsafe_allow_html=True)
        listings_per_area = filtered_df['area'].value_counts()
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        listings_per_area.plot(kind='bar', ax=ax2, color='#001f3f', alpha=0.8)
        ax2.set_xlabel("Area")
        ax2.set_ylabel("Number of Listings")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
        st.markdown("</div>", unsafe_allow_html=True)

        # Section 3: Average Price Based on Number of Bedrooms
        st.markdown("<div class='card'><div class='chart-title'>Average Price Based on Number of Bedrooms</div>", unsafe_allow_html=True)
        avg_price_bedrooms = filtered_df.groupby('bedrooms')['price'].mean().sort_index()
        fig3, ax3 = plt.subplots(figsize=(6, 3))
        avg_price_bedrooms.plot(kind='bar', ax=ax3, color='#001f3f', alpha=0.8)
        ax3.set_xlabel("Number of Bedrooms")
        ax3.set_ylabel("Average Price ($)")
        st.pyplot(fig3)
        st.markdown("</div>", unsafe_allow_html=True)

        # Section 4: Distance to Campus vs. Price
        st.markdown("<div class='card'><div class='chart-title'>Distance to Campus vs. Price</div>", unsafe_allow_html=True)
        fig4, ax4 = plt.subplots(figsize=(6, 3))
        ax4.scatter(filtered_df['distance'], filtered_df['price'], alpha=0.7, color='#001f3f')
        ax4.set_xlabel("Distance to Campus (km)")
        ax4.set_ylabel("Price ($)")
        st.pyplot(fig4)
        st.markdown("</div>", unsafe_allow_html=True)

        # Summary Section
        st.markdown(f"""
        <div class="card">
            <div class="chart-title">Summary</div>
            <p><b>Total Listings:</b> {len(housing_df)}</p>
            <p><b>Filtered Listings:</b> {len(filtered_df)}</p>
            <p><b>Average Price:</b> ${filtered_df['price'].mean():.2f}</p>
            <p><b>Price Range:</b> ${filtered_df['price'].min():.2f} - ${filtered_df['price'].max():.2f}</p>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    logger.error(f"An error occurred while processing the data: {str(e)}")
    st.error(f"An error occurred while processing the data. Please try again later.")
    st.exception(e)