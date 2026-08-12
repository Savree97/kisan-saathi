import os
import sqlite3
import pandas as pd

def main():
    csv_path = os.path.join("data", "mandi_prices.csv")
    db_path = "mandi.db"
    table_name = "prices"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
        
    print(f"Loading data from {csv_path}...")
    # Load the CSV data using pandas
    df = pd.read_csv(csv_path)
    
    # Optional: ensure correct data types
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['min_price'] = pd.to_numeric(df['min_price'], errors='coerce')
    df['max_price'] = pd.to_numeric(df['max_price'], errors='coerce')
    df['modal_price'] = pd.to_numeric(df['modal_price'], errors='coerce')
    
    print(f"Connecting to SQLite database: {db_path}...")
    conn = sqlite3.connect(db_path)
    
    try:
        # Load dataframe to SQLite
        print(f"Writing to table '{table_name}'...")
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print("Data loaded successfully!")
        
        # Verify the table creation and row count
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"Verification: Found {row_count} rows in table '{table_name}'.")
        
        # Fetch schema information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("\nTable Schema:")
        for col in columns:
            print(f" - {col[1]} ({col[2]})")
            
        # Display sample rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        print("\nSample Data (First 5 rows):")
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"An error occurred during database operation: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
