import pandas as pd
import numpy as np
import concurrent.futures
import gc


def process_csv_files(uploaded_files, max_position, branded_terms):
    """Process SEMrush CSV files with branded keyword identification"""
    
    def process_single_file(file):
        """Process a single file with memory optimization"""
        try:
            file.seek(0)
            df = pd.read_csv(file)
            
            # Optimize data types to save memory
            for col in df.columns:
                if df[col].dtype == 'object':
                    if df[col].nunique() / len(df) < 0.5:
                        df[col] = df[col].astype('category')
                elif df[col].dtype == 'int64':
                    df[col] = pd.to_numeric(df[col], downcast='integer')
                elif df[col].dtype == 'float64':
                    df[col] = pd.to_numeric(df[col], downcast='float')
            return df
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return None
    
    # Process files
    print("Reading CSV files...")
    
    dfs = []
    if len(uploaded_files) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_file = {executor.submit(process_single_file, file): file 
                             for file in uploaded_files}
            
            for future in concurrent.futures.as_completed(future_to_file):
                df = future.result()
                if df is not None:
                    dfs.append(df)
    else:
        df = process_single_file(uploaded_files[0])
        if df is not None:
            dfs.append(df)
    
    if not dfs:
        print("No files could be processed successfully")
        return None
    
    print("Combining and deduplicating data...")
    
    # Combine dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    del dfs
    gc.collect()
    
    # Validate required columns
    required_columns = ['Keyword', 'Position', 'Search Volume', 'URL', 'Traffic', 'Timestamp']
    missing_columns = [col for col in required_columns if col not in combined_df.columns]
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return None
    
    # Remove duplicates
    initial_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(
        subset=['Keyword', 'URL', 'Position', 'Timestamp'], 
        keep='first'
    )
    dedup_count = initial_count - len(combined_df)
    if dedup_count > 0:
        print(f"Removed {dedup_count:,} duplicate rows")
    
    combined_df.reset_index(drop=True, inplace=True)
    
    # Convert Position to numeric and filter
    print("Filtering by position...")
    combined_df['Position'] = pd.to_numeric(combined_df['Position'], errors='coerce')
    filtered_df = combined_df[combined_df["Position"] <= max_position]
    print(f"Filtered from {len(combined_df):,} to {len(filtered_df):,} rows (position <= {max_position})")
    
    # Select and rename columns
    column_mapping = {
        "Keyword": "keyword",
        "Position": "position",
        "Search Volume": "search_volume",
        "Keyword Intents": "keyword_intents",
        "URL": "url",
        "Traffic": "traffic",
        "Timestamp": "timestamp"
    }
    
    available_columns = {k: v for k, v in column_mapping.items() if k in filtered_df.columns}
    output_df = filtered_df[list(available_columns.keys())].rename(columns=available_columns)
    
    # Clean and process Traffic column
    print("Processing traffic data...")
    if 'traffic' in output_df.columns:
        traffic_cleaned = output_df['traffic'].astype(str).str.replace(',', '').str.replace('$', '')
        traffic_numeric = pd.to_numeric(traffic_cleaned, errors='coerce').fillna(0).astype(int)
        output_df = output_df.assign(traffic=traffic_numeric)
        output_df = output_df.sort_values(by='traffic', ascending=False)
    
    # Normalize timestamps to YYYY-MM-11 format
    print("Normalizing timestamps...")
    if 'timestamp' in output_df.columns:
        timestamp_dt = pd.to_datetime(output_df['timestamp'], errors='coerce')
        normalized_timestamps = timestamp_dt.dt.strftime('%Y-%m') + '-11'
        normalized_timestamps = normalized_timestamps.replace('NaT-11', pd.NaT)
        output_df = output_df.assign(timestamp=normalized_timestamps)
    
    # Process branded keywords if provided
    if branded_terms and any(term.strip() for term in branded_terms):
        print("Identifying branded keywords...")
        pattern = '|'.join(r'\b{}\b'.format(term.strip()) for term in branded_terms if term.strip())
        output_df["branded"] = output_df["keyword"].str.lower().str.contains(pattern, na=False, regex=True)
    
    print("Processing complete!")
    
    return output_df


def convert_df_to_csv(df):
    """Convert dataframe to CSV string"""
    return df.to_csv(index=False)
