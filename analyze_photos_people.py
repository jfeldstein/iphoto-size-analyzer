#!/usr/bin/env python3
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import numpy as np
import hashlib
import random

# Path to the Photos Library database
PHOTOS_DB_PATH = "/Users/jordan/Pictures/Photos Library.photoslibrary/database/Photos.sqlite"

# Flag to enable name anonymization
ANONYMIZE_NAMES = True

# List of fictional first names for anonymization
FICTIONAL_FIRST_NAMES = [
    "Zephyr", "Luna", "Atlas", "Nova", "Orion", "Sage", "Phoenix", "Echo", "Caspian", "Aurora",
    "Ember", "Indigo", "Jasper", "Lyra", "Cosmo", "Juniper", "Cypress", "Solstice", "Zenith", "Nebula",
    "Fable", "Quasar", "Tempest", "Vesper", "Wren", "Zion", "Astro", "Borealis", "Celestial", "Dune",
    "Everest", "Frost", "Galaxy", "Horizon", "Infinity", "Jupiter", "Krypton", "Legacy", "Meridian", "Neon",
    "Olympus", "Pixel", "Quantum", "Rogue", "Stellar", "Tundra", "Utopia", "Vortex", "Whisper", "Xenon"
]

# List of fictional last names for anonymization
FICTIONAL_LAST_NAMES = [
    "Starlight", "Moonbeam", "Thunderbolt", "Winterfall", "Summercrest", "Nightshade", "Daybreak", "Skydancer", "Fireforge", "Stormchaser",
    "Dreamweaver", "Shadowheart", "Lightbringer", "Cloudwalker", "Riverdance", "Mountaincrest", "Oceantide", "Windwhisper", "Sunseeker", "Moonshadow",
    "Stardust", "Frostfire", "Wildflower", "Silverbrook", "Goldenhawk", "Ironwood", "Crystalclear", "Emeraldsky", "Sapphirewave", "Rubyheart",
    "Diamondpeak", "Amberlight", "Pearlriver", "Jadeforest", "Obsidiannight", "Marblegleam", "Coralreef", "Azuresky", "Crimsonflame", "Violetdusk",
    "Indigomist", "Tealbreeze", "Magentabloom", "Vermilionrise", "Ceruleanfall", "Sienna", "Hazel", "Cobalt", "Amber", "Slate"
]

def connect_to_db(db_path):
    """Connect to the SQLite database."""
    return sqlite3.connect(db_path)

def anonymize_name(name, person_id=None):
    """Anonymize a person's name with a fictional but consistent name."""
    if not ANONYMIZE_NAMES:
        return name
    
    # Use the hash of the original name to ensure consistent anonymization
    hash_object = hashlib.md5(name.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    
    # Use the hash to deterministically select first and last names
    first_name_index = hash_int % len(FICTIONAL_FIRST_NAMES)
    last_name_index = (hash_int // len(FICTIONAL_FIRST_NAMES)) % len(FICTIONAL_LAST_NAMES)
    
    first_name = FICTIONAL_FIRST_NAMES[first_name_index]
    last_name = FICTIONAL_LAST_NAMES[last_name_index]
    
    return f"{first_name} {last_name}"

def get_people_data(conn):
    """Query the database to get data about people in the Photos Library."""
    query = """
    SELECT 
        ZPERSON.Z_PK as person_id,
        ZPERSON.ZDISPLAYNAME as person_name,
        ZPERSON.ZFACECOUNT as face_count,
        COUNT(DISTINCT ZDETECTEDFACE.ZASSETFORFACE) as asset_count
    FROM 
        ZPERSON
    LEFT JOIN 
        ZDETECTEDFACE ON ZPERSON.Z_PK = ZDETECTEDFACE.ZPERSONFORFACE
    WHERE 
        ZPERSON.ZDISPLAYNAME IS NOT NULL
        AND ZPERSON.ZDISPLAYNAME != ''
    GROUP BY 
        ZPERSON.Z_PK
    ORDER BY 
        asset_count DESC
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Anonymize names if enabled
    if ANONYMIZE_NAMES:
        # Store original names for internal reference
        df['original_name'] = df['person_name']
        # Apply anonymization
        df['person_name'] = df.apply(lambda row: anonymize_name(row['person_name'], row['person_id']), axis=1)
    
    return df

def get_people_timeline(conn):
    """Query the database to get data about when people appear in photos over time."""
    query = """
    SELECT 
        ZPERSON.Z_PK as person_id,
        ZPERSON.ZDISPLAYNAME as person_name,
        ZASSET.ZADDEDDATE as added_date
    FROM 
        ZPERSON
    JOIN 
        ZDETECTEDFACE ON ZPERSON.Z_PK = ZDETECTEDFACE.ZPERSONFORFACE
    JOIN 
        ZASSET ON ZDETECTEDFACE.ZASSETFORFACE = ZASSET.Z_PK
    WHERE 
        ZPERSON.ZDISPLAYNAME IS NOT NULL
        AND ZPERSON.ZDISPLAYNAME != ''
        AND ZASSET.ZADDEDDATE IS NOT NULL
    ORDER BY 
        ZASSET.ZADDEDDATE
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Anonymize names if enabled
    if ANONYMIZE_NAMES:
        # Apply anonymization
        df['person_name'] = df.apply(lambda row: anonymize_name(row['person_name'], row['person_id']), axis=1)
    
    # Convert timestamps from Mac Core Data format (seconds since 2001-01-01) to Python datetime
    # Mac Core Data epoch is 2001-01-01
    mac_epoch = datetime(2001, 1, 1)
    
    # Function to convert timestamp safely
    def convert_timestamp(ts):
        try:
            # The timestamp is seconds since 2001-01-01
            if pd.isna(ts) or ts == 0:
                return pd.NaT
            
            # Convert to float and handle potential errors
            ts_float = float(ts)
            
            # Check if the timestamp is reasonable (between 2000 and 2050)
            if ts_float < 0 or ts_float > 1577836800:  # ~50 years in seconds
                return pd.NaT
                
            return mac_epoch + pd.Timedelta(seconds=ts_float)
        except (ValueError, OverflowError, TypeError):
            return pd.NaT
    
    # Apply the conversion function
    df['added_date'] = df['added_date'].apply(convert_timestamp)
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['added_date'])
    
    return df

def plot_top_people(people_df, top_n=20):
    """Plot the top N people with the most photos/videos."""
    # Get the top N people
    top_people = people_df.head(top_n).copy()
    
    # Create a horizontal bar chart
    plt.figure(figsize=(12, 10))
    sns.set_style("whitegrid")
    
    # Plot the data
    ax = sns.barplot(x='asset_count', y='person_name', data=top_people, palette='viridis')
    
    # Add labels and title
    plt.title(f'Top {top_n} People in Your Photos Library', fontsize=16)
    plt.xlabel('Number of Photos/Videos', fontsize=12)
    plt.ylabel('Person', fontsize=12)
    
    # Add count labels to the bars
    for i, v in enumerate(top_people['asset_count']):
        ax.text(v + 0.5, i, str(v), va='center')
    
    plt.tight_layout()
    plt.savefig('photos_people_count.png')
    print(f"Plot saved as photos_people_count.png")
    
    # Show the plot
    plt.show()

def plot_people_timeline(timeline_df, top_n=5):
    """Plot how the top N people appear in photos over time."""
    # Get the top N people by count
    top_people_counts = timeline_df['person_name'].value_counts().head(top_n)
    top_people = top_people_counts.index.tolist()
    
    # Filter the timeline data to only include the top N people
    filtered_df = timeline_df[timeline_df['person_name'].isin(top_people)]
    
    # Group by person and month, count occurrences
    filtered_df['year_month'] = filtered_df['added_date'].dt.to_period('M')
    monthly_counts = filtered_df.groupby(['person_name', 'year_month']).size().reset_index(name='count')
    
    # Pivot the data for plotting
    pivot_df = monthly_counts.pivot(index='year_month', columns='person_name', values='count')
    pivot_df = pivot_df.fillna(0)
    
    # Plot the data
    plt.figure(figsize=(15, 8))
    pivot_df.plot(kind='line', marker='o', ax=plt.gca())
    
    # Add labels and title
    plt.title(f'Appearances of Top {top_n} People Over Time', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Number of Photos/Videos', fontsize=12)
    plt.xticks(rotation=90)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Person')
    
    plt.tight_layout()
    plt.savefig('photos_people_timeline.png')
    print(f"Plot saved as photos_people_timeline.png")
    
    # Show the plot
    plt.show()

def print_people_statistics(people_df):
    """Print statistics about people in the Photos Library."""
    total_people = len(people_df)
    total_faces = people_df['face_count'].sum()
    total_assets_with_people = people_df['asset_count'].sum()
    
    print("\n===== Photos Library People Statistics =====")
    print(f"Total number of people: {total_people}")
    print(f"Total number of faces detected: {total_faces}")
    print(f"Total number of photos/videos with people: {total_assets_with_people}")
    
    # Print the top 20 people
    print("\nTop 20 people with the most photos/videos:")
    for i, (_, row) in enumerate(people_df.head(20).iterrows(), 1):
        print(f"{i}. {row['person_name']}: {row['asset_count']} photos/videos, {row['face_count']} faces")

def export_to_csv(people_df):
    """Export the people data to a CSV file."""
    # Create a copy to avoid modifying the original dataframe
    export_df = people_df.copy()
    
    # Remove the original_name column if it exists (for privacy)
    if 'original_name' in export_df.columns:
        export_df = export_df.drop(columns=['original_name'])
        
    csv_path = 'photos_people_data.csv'
    export_df.to_csv(csv_path, index=False)
    print(f"Data exported to {csv_path}")

def main():
    try:
        # Connect to the database
        conn = connect_to_db(PHOTOS_DB_PATH)
        
        # Get people data
        print("Fetching people data from Photos Library database...")
        people_df = get_people_data(conn)
        
        if people_df.empty:
            print("No people data found. Please check if the database path is correct.")
            return
        
        print(f"Found {len(people_df)} people in the library.")
        
        # Print statistics
        print_people_statistics(people_df)
        
        # Export to CSV
        export_to_csv(people_df)
        
        # Plot top people
        plot_top_people(people_df)
        
        # Get and plot timeline data
        print("\nFetching timeline data for people...")
        timeline_df = get_people_timeline(conn)
        
        if not timeline_df.empty:
            plot_people_timeline(timeline_df)
        else:
            print("No timeline data found.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 