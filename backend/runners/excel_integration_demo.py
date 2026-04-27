#!/usr/bin/env python3
"""
Excel Integration Demo - Shows how Excel file controls cross-testing
"""

import pandas as pd
import os

def demonstrate_excel_integration():
    """Show how Excel controls the testing framework"""
    
    print("=" * 60)
    print("EXCEL INTEGRATION DEMONSTRATION")
    print("=" * 60)
    
    # Step 1: Read Excel file (saved as CSV)
    excel_file = "Excel_Test_Cases.csv"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return
    
    print(f"Reading Excel file: {excel_file}")
    df = pd.read_csv(excel_file)
    
    print(f"Loaded {len(df)} test cases from Excel")
    print("\nExcel Test Cases:")
    print(df.to_string(index=False))
    
    # Step 2: Show cross-testing capabilities
    print(f"\nCross-Testing Analysis:")
    
    # Group by functionality
    by_functionality = df.groupby('functionality').size()
    print(f"\nTests by Area:")
    for area, count in by_functionality.items():
        print(f"  {area}: {count} tests")
    
    # Show enabled vs disabled
    enabled_tests = df[df['enabled'] == True]
    disabled_tests = df[df['enabled'] == False]
    
    print(f"\nTest Control:")
    print(f"  Enabled: {len(enabled_tests)} tests")
    print(f"  Disabled: {len(disabled_tests)} tests")
    
    # Show cross-testing scenarios
    print(f"\nCross-Testing Scenarios Available:")
    areas = df['functionality'].unique()
    
    for i, area1 in enumerate(areas):
        for area2 in areas[i+1:]:
            print(f"  {area1.upper()} <-> {area2.upper()} validation")
    
    # Step 3: Show how to run from Excel
    print(f"\nHow to Execute from Excel:")
    print(f"  1. Edit Excel_Test_Cases.csv in Excel")
    print(f"  2. Save as CSV format")
    print(f"  3. Run: python etl_runner.py")
    print(f"  4. Framework reads Excel data automatically")
    
    # Step 4: Demonstrate business user control
    print(f"\nBusiness User Control Examples:")
    
    # Show priority-based execution
    if 'priority' in df.columns:
        priorities = df['priority'].value_counts()
        print(f"\nTest Priorities from Excel:")
        for priority, count in priorities.items():
            print(f"  {priority}: {count} tests")
    
    # Show owner-based organization
    if 'owner' in df.columns:
        owners = df['owner'].value_counts()
        print(f"\nTest Ownership from Excel:")
        for owner, count in owners.items():
            print(f"  {owner}: {count} tests")
    
    print(f"\n" + "=" * 60)
    print("EXCEL SUCCESSFULLY CONTROLS CROSS-TESTING!")
    print("Business users can manage all testing areas from Excel!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_excel_integration()