#!/usr/bin/env python3
"""
Create Comprehensive TRUSTA Spreadsheet from SKU Search Results
Converts the comprehensive SKU search results into formatted Excel spreadsheets
"""

import pandas as pd
import json
import os
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

class TrustaSpreadsheetGenerator:
    def __init__(self):
        self.results_data = None
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def load_search_results(self, results_file):
        """Load the comprehensive search results from JSON file"""
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                self.results_data = json.load(f)
            print(f"✅ Loaded search results from {results_file}")
            return True
        except FileNotFoundError:
            print(f"❌ Results file not found: {results_file}")
            return False
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return False
    
    def create_sku_summary_sheet(self):
        """Create SKU summary sheet with search results"""
        sku_data = []
        
        for sku, result in self.results_data.get('sku_results', {}).items():
            categories_found = ', '.join([cat['category'] for cat in result.get('found_in_categories', [])])
            
            row = {
                'Server SKU': sku,
                'Found on Website': 'Yes' if result.get('found_in_categories') else 'No',
                'Categories Found': categories_found,
                'QVL Accessible': 'Yes' if result.get('qvl_accessible') else 'No',
                'TRUSTA Found': 'Yes' if result.get('trusta_found') else 'No',
                'TRUSTA Products Count': len(result.get('trusta_data', {}).get('matches', [])) if result.get('trusta_data') else 0,
                'Search Timestamp': result.get('search_timestamp', ''),
                'Product URLs': ', '.join([cat['product_url'] for cat in result.get('found_in_categories', [])]) if result.get('found_in_categories') else ''
            }
            sku_data.append(row)
        
        return pd.DataFrame(sku_data)
    
    def create_trusta_findings_sheet(self):
        """Create detailed TRUSTA findings sheet"""
        trusta_data = []
        
        for finding in self.results_data.get('trusta_findings', []):
            base_info = {
                'Server SKU': finding.get('sku', ''),
                'QVL Page URL': finding.get('page_url', ''),
                'Discovery Timestamp': finding.get('timestamp', ''),
                'Total TRUSTA Products': len(finding.get('matches', []))
            }
            
            if finding.get('matches'):
                for i, match in enumerate(finding['matches'], 1):
                    row = base_info.copy()
                    row['Product #'] = i
                    row['Raw Table Data'] = match.get('raw_text', '')
                    
                    row_data = match.get('row_data', [])
                    for j, cell_data in enumerate(row_data[:10]):  # Limit to first 10 columns
                        row[f'Column {j+1}'] = cell_data
                    
                    trusta_data.append(row)
            else:
                trusta_data.append(base_info)
        
        return pd.DataFrame(trusta_data)
    
    def create_search_statistics_sheet(self):
        """Create search statistics and summary sheet"""
        metadata = self.results_data.get('search_metadata', {})
        summary = self.results_data.get('search_summary', {})
        
        stats_data = {
            'Metric': [
                'Total Server SKUs Processed',
                'SKUs Found on Website',
                'SKUs with Accessible QVL',
                'SKUs with TRUSTA Products',
                'Total TRUSTA Product Entries',
                'SKU Discovery Success Rate',
                'QVL Access Success Rate',
                'TRUSTA Discovery Rate',
                'Search Start Time',
                'Search End Time',
                'Categories Searched',
                'Search Method'
            ],
            'Value': [
                metadata.get('total_skus_searched', 0),
                metadata.get('skus_found', 0),
                metadata.get('skus_with_qvl', 0),
                metadata.get('skus_with_trusta', 0),
                len(self.results_data.get('trusta_findings', [])),
                summary.get('success_rate', {}).get('sku_discovery', '0%'),
                summary.get('success_rate', {}).get('qvl_access', '0%'),
                summary.get('success_rate', {}).get('trusta_discovery', '0%'),
                metadata.get('start_time', ''),
                metadata.get('end_time', ''),
                ', '.join(summary.get('categories_searched', [])),
                'Automated Web Crawler with QVL Navigation'
            ]
        }
        
        return pd.DataFrame(stats_data)
    
    def create_category_breakdown_sheet(self):
        """Create breakdown by server categories"""
        category_stats = {}
        
        for sku, result in self.results_data.get('sku_results', {}).items():
            for category_info in result.get('found_in_categories', []):
                category = category_info['category']
                if category not in category_stats:
                    category_stats[category] = {
                        'category': category,
                        'skus_found': 0,
                        'skus_with_qvl': 0,
                        'skus_with_trusta': 0,
                        'sku_list': []
                    }
                
                category_stats[category]['skus_found'] += 1
                category_stats[category]['sku_list'].append(sku)
                
                if result.get('qvl_accessible'):
                    category_stats[category]['skus_with_qvl'] += 1
                
                if result.get('trusta_found'):
                    category_stats[category]['skus_with_trusta'] += 1
        
        category_data = []
        for stats in category_stats.values():
            row = {
                'Enterprise Category': stats['category'],
                'SKUs Found': stats['skus_found'],
                'SKUs with QVL Access': stats['skus_with_qvl'],
                'SKUs with TRUSTA': stats['skus_with_trusta'],
                'TRUSTA Success Rate': f"{stats['skus_with_trusta']/stats['skus_found']*100:.1f}%" if stats['skus_found'] > 0 else "0%",
                'Server SKU List': ', '.join(stats['sku_list'])
            }
            category_data.append(row)
        
        return pd.DataFrame(category_data)
    
    def format_excel_file(self, filename):
        """Apply professional formatting to the Excel file"""
        try:
            wb = load_workbook(filename)
            
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                
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
                    adjusted_width = min(max_length + 2, 80)  # Cap at 80 characters
                    ws.column_dimensions[column_letter].width = adjusted_width
                
                for row in ws.iter_rows():
                    for cell in row:
                        cell.border = thin_border
                        if cell.row > 1:  # Data rows
                            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            
            wb.save(filename)
            print(f"✅ Excel formatting applied successfully")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not apply Excel formatting: {e}")
    
    def generate_comprehensive_spreadsheet(self, results_file):
        """Generate comprehensive Excel spreadsheet with all results"""
        if not self.load_search_results(results_file):
            return None
        
        filename = f"GIGABYTE_Comprehensive_TRUSTA_Search_Results_{self.timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                sku_summary_df = self.create_sku_summary_sheet()
                sku_summary_df.to_excel(writer, sheet_name='SKU Search Summary', index=False)
                
                trusta_findings_df = self.create_trusta_findings_sheet()
                if not trusta_findings_df.empty:
                    trusta_findings_df.to_excel(writer, sheet_name='TRUSTA Findings', index=False)
                else:
                    empty_df = pd.DataFrame(columns=['Server SKU', 'QVL Page URL', 'Discovery Timestamp', 'Total TRUSTA Products', 'Notes'])
                    empty_df.to_excel(writer, sheet_name='TRUSTA Findings', index=False)
                
                stats_df = self.create_search_statistics_sheet()
                stats_df.to_excel(writer, sheet_name='Search Statistics', index=False)
                
                category_df = self.create_category_breakdown_sheet()
                if not category_df.empty:
                    category_df.to_excel(writer, sheet_name='Category Breakdown', index=False)
                else:
                    empty_cat_df = pd.DataFrame(columns=['Enterprise Category', 'SKUs Found', 'SKUs with QVL Access', 'SKUs with TRUSTA'])
                    empty_cat_df.to_excel(writer, sheet_name='Category Breakdown', index=False)
            
            self.format_excel_file(filename)
            
            print(f"\n📊 COMPREHENSIVE SPREADSHEET CREATED")
            print("=" * 50)
            print(f"📁 Filename: {filename}")
            print(f"📋 Sheets Created:")
            print(f"   • SKU Search Summary - Overview of all 177 SKUs")
            print(f"   • TRUSTA Findings - Detailed TRUSTA product data")
            print(f"   • Search Statistics - Performance metrics and summary")
            print(f"   • Category Breakdown - Results by Enterprise category")
            
            metadata = self.results_data.get('search_metadata', {})
            print(f"\n📈 Key Results:")
            print(f"   • Total SKUs Processed: {metadata.get('total_skus_searched', 0)}")
            print(f"   • SKUs Found on Website: {metadata.get('skus_found', 0)}")
            print(f"   • SKUs with QVL Access: {metadata.get('skus_with_qvl', 0)}")
            print(f"   • SKUs with TRUSTA Products: {metadata.get('skus_with_trusta', 0)}")
            print(f"   • Total TRUSTA Findings: {len(self.results_data.get('trusta_findings', []))}")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error creating spreadsheet: {e}")
            return None

def find_latest_results_file():
    """Find the most recent comprehensive search results file"""
    try:
        files = [f for f in os.listdir('.') if f.startswith('gigabyte_comprehensive_sku_trusta_report_') and f.endswith('.json')]
        if files:
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return files[0]
        else:
            print("❌ No comprehensive search results file found")
            return None
    except Exception as e:
        print(f"❌ Error finding results file: {e}")
        return None

def main():
    """Main function"""
    print("GIGABYTE Comprehensive TRUSTA Search Results Spreadsheet Generator")
    print("=" * 70)
    
    results_file = find_latest_results_file()
    if not results_file:
        print("❌ No search results file found. Please run the comprehensive search first.")
        return 1
    
    print(f"📖 Using results file: {results_file}")
    
    generator = TrustaSpreadsheetGenerator()
    spreadsheet_file = generator.generate_comprehensive_spreadsheet(results_file)
    
    if spreadsheet_file:
        print(f"\n✅ Comprehensive spreadsheet generated successfully!")
        print(f"📋 File: {spreadsheet_file}")
        print(f"🎯 Ready for download and analysis!")
        return 0
    else:
        print(f"\n❌ Failed to generate spreadsheet")
        return 1

if __name__ == "__main__":
    exit(main())
