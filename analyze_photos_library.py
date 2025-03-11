#!/usr/bin/env python3
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import numpy as np

# Path to the Photos Library database
PHOTOS_DB_PATH = "/Users/jordan/Pictures/Photos Library.photoslibrary/database/Photos.sqlite"

def connect_to_db(db_path):
    """Connect to the SQLite database."""
    return sqlite3.connect(db_path)

def get_library_growth_data(conn):
    """Query the database to get data about when media was added and its size."""
    query = """
    SELECT 
        ZASSET.Z_PK as asset_id,
        ZASSET.ZADDEDDATE as added_date,
        ZINTERNALRESOURCE.ZDATALENGTH as file_size
    FROM 
        ZASSET
    JOIN 
        ZINTERNALRESOURCE ON ZASSET.Z_PK = ZINTERNALRESOURCE.ZASSET
    WHERE 
        ZASSET.ZADDEDDATE IS NOT NULL
        AND ZINTERNALRESOURCE.ZDATALENGTH IS NOT NULL
    ORDER BY 
        ZASSET.ZADDEDDATE
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Debug the timestamp values
    print(f"Sample added_date values: {df['added_date'].head().tolist()}")
    
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

def analyze_monthly_growth(df):
    """Analyze the growth of the library by month."""
    # Group by month and calculate total size
    df['year_month'] = df['added_date'].dt.to_period('M')
    
    # Calculate cumulative size in GB
    monthly_data = df.groupby('year_month').agg({'file_size': 'sum'}).reset_index()
    monthly_data['file_size_gb'] = monthly_data['file_size'] / (1024**3)  # Convert bytes to GB
    monthly_data['cumulative_size_gb'] = monthly_data['file_size_gb'].cumsum()
    
    # Calculate growth rate
    monthly_data['growth_gb'] = monthly_data['file_size_gb']
    
    return monthly_data

def plot_library_growth(monthly_data):
    """Plot the growth of the library over time."""
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Monthly Growth
    plt.subplot(2, 1, 1)
    plt.bar(monthly_data['year_month'].astype(str), monthly_data['growth_gb'], color='skyblue')
    plt.title('Monthly Growth of Photos Library (GB)')
    plt.xlabel('Month')
    plt.ylabel('Size Added (GB)')
    plt.xticks(rotation=90)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot 2: Cumulative Growth
    plt.subplot(2, 1, 2)
    plt.plot(monthly_data['year_month'].astype(str), monthly_data['cumulative_size_gb'], marker='o', color='darkblue')
    plt.title('Cumulative Size of Photos Library Over Time')
    plt.xlabel('Month')
    plt.ylabel('Total Size (GB)')
    plt.xticks(rotation=90)
    plt.grid(linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('photos_library_growth.png')
    print(f"Plot saved as photos_library_growth.png")
    
    # Show the plot
    plt.show()

def print_summary_statistics(monthly_data):
    """Print summary statistics about the library growth."""
    total_size_gb = monthly_data['cumulative_size_gb'].iloc[-1]
    total_months = len(monthly_data)
    avg_monthly_growth = monthly_data['growth_gb'].mean()
    max_monthly_growth = monthly_data['growth_gb'].max()
    max_growth_month = monthly_data.loc[monthly_data['growth_gb'].idxmax(), 'year_month']
    
    print("\n===== Photos Library Growth Summary =====")
    print(f"Total library size: {total_size_gb:.2f} GB")
    print(f"Data spans {total_months} months")
    print(f"Average monthly growth: {avg_monthly_growth:.2f} GB")
    print(f"Maximum monthly growth: {max_monthly_growth:.2f} GB (in {max_growth_month})")
    
    # Calculate growth rate for the last 3, 6, and 12 months
    if len(monthly_data) >= 3:
        last_3_months_avg = monthly_data['growth_gb'].tail(3).mean()
        print(f"Average monthly growth (last 3 months): {last_3_months_avg:.2f} GB")
    
    if len(monthly_data) >= 6:
        last_6_months_avg = monthly_data['growth_gb'].tail(6).mean()
        print(f"Average monthly growth (last 6 months): {last_6_months_avg:.2f} GB")
    
    if len(monthly_data) >= 12:
        last_12_months_avg = monthly_data['growth_gb'].tail(12).mean()
        print(f"Average monthly growth (last 12 months): {last_12_months_avg:.2f} GB")
    
    # Print the top 5 months with highest growth
    print("\nTop 5 months with highest growth:")
    top_months = monthly_data.sort_values('growth_gb', ascending=False).head(5)
    for _, row in top_months.iterrows():
        print(f"{row['year_month']}: {row['growth_gb']:.2f} GB")

def export_to_csv(monthly_data):
    """Export the monthly growth data to a CSV file."""
    # Convert period to string for better CSV compatibility
    monthly_data['year_month'] = monthly_data['year_month'].astype(str)
    
    # Save to CSV
    csv_path = 'photos_library_growth.csv'
    monthly_data.to_csv(csv_path, index=False)
    print(f"Data exported to {csv_path}")

def main():
    try:
        # Connect to the database
        conn = connect_to_db(PHOTOS_DB_PATH)
        
        # Get the data
        print("Fetching data from Photos Library database...")
        df = get_library_growth_data(conn)
        
        if df.empty:
            print("No data found. Please check if the database path is correct.")
            return
        
        print(f"Found {len(df)} media items in the library.")
        
        # Analyze monthly growth
        monthly_data = analyze_monthly_growth(df)
        
        # Print summary statistics
        print_summary_statistics(monthly_data)
        
        # Export to CSV
        export_to_csv(monthly_data)
        
        # Plot the growth
        plot_library_growth(monthly_data)
        
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