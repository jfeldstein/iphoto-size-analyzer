# Photos Library Growth Analyzer

This script analyzes how your Photos Library has grown in size over time by month.

![Sample Output](examples/sample_output.png)

## Features

- Measures the size of media added to your Photos Library each month
- Calculates cumulative growth over time
- Generates visualizations of monthly and cumulative growth
- Provides summary statistics about your library growth
- Exports data to CSV for further analysis

## Example Output

The script generates two main visualizations:
1. **Monthly Growth**: Shows how much data (in GB) was added to your Photos Library each month
2. **Cumulative Growth**: Shows the total size of your Photos Library over time

It also provides summary statistics such as:
- Total library size
- Average monthly growth
- Maximum monthly growth
- Recent growth trends (3, 6, and 12 months)
- Top months with highest growth

## Requirements

- Python 3.6+
- pandas
- matplotlib
- numpy

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Make sure your Photos Library is accessible
2. Run the script:

```bash
python analyze_photos_library.py
```

By default, the script looks for your Photos Library at:
`/Users/jordan/Pictures/Photos Library.photoslibrary`

If your library is in a different location, you can modify the `PHOTOS_DB_PATH` variable in the script.

## Output

The script will:
1. Print summary statistics to the console
2. Save a CSV file with monthly growth data (`photos_library_growth.csv`)
3. Generate and save a visualization (`photos_library_growth.png`)
4. Display the visualization

## Notes

- This script accesses the SQLite database in your Photos Library to gather information about when media was added and its size
- The script is read-only and does not modify your Photos Library in any way
- The script may take some time to run if you have a large library 