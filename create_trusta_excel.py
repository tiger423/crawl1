#!/usr/bin/env python3
"""
Create Excel Spreadsheet for TRUSTA T7P5 QVL Data
Converts the comprehensive QVL report into a formatted Excel table
"""

import pandas as pd
import json
from datetime import datetime
import os

def load_trusta_data():
    """Load TRUSTA T7P5 data from the comprehensive report"""
    try:
        with open('gigabyte_qvl_trusta_comprehensive_report.json', 'r', encoding='utf-8') as f:
            report = json.load(f)
        return report
    except FileNotFoundError:
        print("Error: gigabyte_qvl_trusta_comprehensive_report.json not found")
        return None
    except Exception as e:
        print(f"Error loading report: {e}")
        return None

def create_excel_table(report):
    """Create Excel spreadsheet with TRUSTA T7P5 QVL data"""
    
    trusta_products = report.get('trusta_t7p5_products', [])
    
    if not trusta_products:
        print("No TRUSTA products found in report")
        return False
    
    excel_data = []
    
    for product in trusta_products:
        analysis = product.get('analysis', {})
        
        row = {
            'Server Sku': 'G293-S40-AAP1',
            'Product Name': product.get('product_name', ''),
            'Vendor': product.get('vendor', ''),
            'Series': product.get('series', ''),
            'Capacity': product.get('capacity', ''),
            'Capacity (TB)': analysis.get('capacity_tb', ''),
            'Form Factor': product.get('form_factor', ''),
            'Type': product.get('type', ''),
            'Interface': product.get('interface', ''),
            'Interface Speed': product.get('interface_speed', ''),
            'PCIe Generation': 'Gen 5' if analysis.get('is_gen5') else 'Other',
            'NVMe Support': 'Yes' if analysis.get('is_nvme') else 'No',
            'VROC Support': product.get('other', ''),
            'Hot-Swap Compatible': 'Yes' if analysis.get('form_factor_type') == 'U.2 2.5" 15mm' else 'Unknown',
            'QVL Status': 'Officially Qualified',
            'Remark': product.get('remark', '')
        }
        excel_data.append(row)
    
    df = pd.DataFrame(excel_data)
    
    filename = f"GIGABYTE_G293-S40-AAP1_TRUSTA_T7P5_QVL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='TRUSTA T7P5 QVL Data', index=False)
        
        summary_data = {
            'Metric': [
                'Total TRUSTA T7P5 Products',
                'Server Model',
                'QVL Section',
                'All PCIe Gen 5',
                'All NVMe Compatible',
                'All VROC Supported',
                'Capacity Range',
                'Form Factor',
                'Interface Type',
                'QVL URL',
                'Report Generated'
            ],
            'Value': [
                len(trusta_products),
                'G293-S40-AAP1 GPU Server',
                'Storage - NVMe SSD',
                'Yes',
                'Yes', 
                'Yes',
                f"{min(p['analysis']['capacity_tb'] for p in trusta_products)}TB - {max(p['analysis']['capacity_tb'] for p in trusta_products)}TB",
                'U.2 2.5" 15mm',
                'SFF8639(NVMe) - PCIe Gen5 x4',
                report.get('qvl_url', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        capacity_data = []
        for product in trusta_products:
            capacity_data.append({
                'Product Name': product.get('product_name', ''),
                'Capacity': product.get('capacity', ''),
                'Capacity (TB)': product.get('analysis', {}).get('capacity_tb', ''),
                'Use Case Recommendation': get_use_case_recommendation(product.get('analysis', {}).get('capacity_tb', 0))
            })
        
        capacity_df = pd.DataFrame(capacity_data)
        capacity_df.to_excel(writer, sheet_name='Capacity Options', index=False)
    
    format_excel_file(filename)
    
    print(f"✅ Excel file created successfully: {filename}")
    return filename

def get_use_case_recommendation(capacity_tb):
    """Get use case recommendation based on capacity"""
    if capacity_tb >= 6:
        return "Large AI training datasets, Enterprise databases"
    elif capacity_tb >= 3:
        return "Medium AI workloads, Virtualization, Content creation"
    else:
        return "Boot drives, Small datasets, Development environments"

def format_excel_file(filename):
    """Apply formatting to the Excel file"""
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    
    wb = load_workbook(filename)
    
    ws = wb['TRUSTA T7P5 QVL Data']
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
        ws.column_dimensions[column_letter].width = adjusted_width
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for row in ws.iter_rows():
        for cell in row:
            cell.border = thin_border
            if cell.row > 1:  # Data rows
                cell.alignment = Alignment(horizontal="left", vertical="center")
    
    ws_summary = wb['Summary']
    
    for cell in ws_summary[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    for column in ws_summary.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 60)
        ws_summary.column_dimensions[column_letter].width = adjusted_width
    
    for row in ws_summary.iter_rows():
        for cell in row:
            cell.border = thin_border
            if cell.row > 1:
                cell.alignment = Alignment(horizontal="left", vertical="center")
    
    ws_capacity = wb['Capacity Options']
    
    for cell in ws_capacity[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    for column in ws_capacity.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws_capacity.column_dimensions[column_letter].width = adjusted_width
    
    for row in ws_capacity.iter_rows():
        for cell in row:
            cell.border = thin_border
            if cell.row > 1:
                cell.alignment = Alignment(horizontal="left", vertical="center")
    
    wb.save(filename)

def display_excel_info(filename):
    """Display information about the created Excel file"""
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        print(f"\n📊 EXCEL FILE CREATED SUCCESSFULLY")
        print("=" * 50)
        print(f"📁 Filename: {filename}")
        print(f"📏 File Size: {file_size:,} bytes")
        print(f"📋 Sheets Created:")
        print(f"   • TRUSTA T7P5 QVL Data - Main product table")
        print(f"   • Summary - Key metrics and overview")
        print(f"   • Capacity Options - Capacity breakdown with use cases")
        print(f"\n✅ Ready for download and use!")
        return True
    else:
        print(f"❌ Error: Excel file {filename} was not created")
        return False

def main():
    """Main function"""
    print("GIGABYTE G293-S40-AAP1 TRUSTA T7P5 Excel Generator")
    print("Creating Excel spreadsheet from QVL data...")
    print("-" * 60)
    
    report = load_trusta_data()
    if not report:
        return 1
    
    print(f"✅ Loaded report with {len(report.get('trusta_t7p5_products', []))} TRUSTA products")
    
    filename = create_excel_table(report)
    if not filename:
        return 1
    
    if display_excel_info(filename):
        print(f"\n🎯 MISSION ACCOMPLISHED!")
        print(f"Excel file '{filename}' is ready for the user.")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
