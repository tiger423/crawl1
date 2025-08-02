#!/usr/bin/env python3
"""
Process Gigacomputing QVL spreadsheet to create server SKU list
Uses Example 1 concept: column-by-column concatenation of row 3 and row 4
"""

import pandas as pd
import os

def process_spreadsheet():
    """Process the spreadsheet to create server SKU list"""
    
    file_path = "/home/ubuntu/attachments/24278908-0c57-47a4-b239-a61e669e79e9/Gigacomputing-QVL.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return False
    
    try:
        print(f"📖 Reading Excel file: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        
        print(f"✅ Successfully loaded spreadsheet")
        print(f"📊 Spreadsheet dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        
        print(f"\n📋 First 5 rows of the spreadsheet:")
        print(df.head().to_string())
        
        if df.shape[0] < 4:
            print(f"❌ Error: Spreadsheet has only {df.shape[0]} rows, need at least 4 rows")
            return False
        
        row_3 = df.iloc[2]  # Row 3 (0-indexed)
        row_4 = df.iloc[3]  # Row 4 (0-indexed)
        
        print(f"\n🔍 Row 3 data:")
        print(row_3.to_string())
        print(f"\n🔍 Row 4 data:")
        print(row_4.to_string())
        
        server_skus = []
        
        print(f"\n🔧 Processing columns to create server SKUs (Example 1 method)...")
        
        for col_idx in range(df.shape[1]):
            row_3_value = str(row_3.iloc[col_idx]) if pd.notna(row_3.iloc[col_idx]) else ""
            row_4_value = str(row_4.iloc[col_idx]) if pd.notna(row_4.iloc[col_idx]) else ""
            
            if (not row_3_value or row_3_value.lower() == 'nan') and \
               (not row_4_value or row_4_value.lower() == 'nan'):
                continue
            
            if row_3_value.lower() == 'nan':
                row_3_value = ""
            if row_4_value.lower() == 'nan':
                row_4_value = ""
            
            if row_3_value and row_4_value:
                server_sku = f"{row_3_value}-{row_4_value}"
            elif row_3_value:
                server_sku = row_3_value
            elif row_4_value:
                server_sku = row_4_value
            else:
                continue
            
            server_skus.append(server_sku)
            print(f"   Column {col_idx}: '{row_3_value}' + '{row_4_value}' = '{server_sku}'")
        
        print(f"\n✅ Generated {len(server_skus)} server SKUs")
        
        output_file = "server-sku.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for sku in server_skus:
                f.write(f"{sku}\n")
        
        print(f"💾 Saved server SKU list to: {output_file}")
        
        print(f"\n📋 Generated Server SKU List:")
        print("-" * 50)
        for i, sku in enumerate(server_skus, 1):
            print(f"{i:2d}. {sku}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing spreadsheet: {e}")
        return False

def main():
    """Main function"""
    print("Gigacomputing QVL Server SKU Processor")
    print("Creating server SKU list using Example 1 method (column-by-column)")
    print("=" * 60)
    
    success = process_spreadsheet()
    
    if success:
        print(f"\n🎉 SUCCESS: Server SKU list created successfully!")
        print(f"📁 Output file: server-sku.txt")
        return 0
    else:
        print(f"\n❌ FAILED: Could not process spreadsheet")
        return 1

if __name__ == "__main__":
    exit(main())
