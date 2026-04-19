import pandas as pd
import sys

def merge_csvs(csv_filenames, output_filename='merged_output.csv'):
    """
    Merge multiple CSV files with matching column headers.
    
    Args:
        csv_filenames: List of CSV file paths to merge
        output_filename: Name of the output merged CSV file
    
    Returns:
        True if successful, False otherwise
    """
    if not csv_filenames:
        print("Error: No CSV files provided")
        return False
    
    try:
        # Read the first CSV to get reference headers
        first_df = pd.read_csv(csv_filenames[0])
        reference_headers = set(first_df.columns)
        
        print(f"Reference headers from '{csv_filenames[0]}':")
        print(f"  {list(first_df.columns)}\n")
        
        # List to store all dataframes
        dfs = [first_df]
        
        # Read and validate remaining CSVs
        for filename in csv_filenames[1:]:
            df = pd.read_csv(filename)
            current_headers = set(df.columns)
            
            # Check if headers match
            if current_headers != reference_headers:
                print(f"Error: Not matching column headers!")
                print(f"  File: '{filename}'")
                print(f"  Expected: {sorted(reference_headers)}")
                print(f"  Got: {sorted(current_headers)}")
                return False
            
            dfs.append(df)
            print(f"✓ '{filename}' - headers match")
        
        # Concatenate all dataframes
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Save to output file
        merged_df.to_csv(output_filename, index=False)
        
        print(f"\n✓ Successfully merged {len(csv_filenames)} files")
        print(f"  Total rows: {len(merged_df)}")
        print(f"  Output saved to: '{output_filename}'")
        
        return True
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    # Input CSV files to merge
    csv_files = [
    ]

    csv_files.extend([
        '/Users/jay/Downloads/suggested_profiles_2026-02-26_01-14-41.csv',
        '/Users/jay/Downloads/suggested_profiles_2026-02-26_01-15-44.csv',
        '/Users/jay/Downloads/suggested_profiles_2026-02-26_01-21-22.csv'
    ])

    # Output file path
    output_file = 'instagram-profiles/jay-to-be-reached-5.csv'
    
    # You can also pass files via command line arguments
    if len(sys.argv) > 1:
        csv_files = sys.argv[1:]
    
    merge_csvs(csv_files, output_filename=output_file)