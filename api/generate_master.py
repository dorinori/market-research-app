import os
import pandas as pd

def concatenate_state_files():
    # Set up directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(current_dir, 'data', 'scraped_data')
    OUTPUT_DIR = os.path.join(current_dir, 'data')
    OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'master_real_estate_data.xlsx')
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"Data directory not found at: {DATA_DIR}")
    
    # Find all state files
    state_files = [
        f for f in os.listdir(DATA_DIR) 
        if f.startswith('scraped_population_and_job_data') and f.endswith('.xlsx')
    ]
    
    if not state_files:
        raise FileNotFoundError("No state files found in the data directory")
    
    # Initialize an empty list to store DataFrames
    dfs = []
    
    # Define expected output columns in order
    output_columns = [
        'City', 'Metro Area', 'Population', '1. Pop Growth',
        '2. Median Household Income (45-48k, <85/90k)', '2. Rent to Income',
        '3. Job Growth (last 12 months)', '4. Median Household Income/Condo Value',
        'MHI', '5. MCV Growth', 'Median Condo Value', 'MCV',
        '6. Crime Index', '6. Unemployment', '7. Price Rent Ratio',
        'Median Contract Rent', '8. Poverty', '9. Largest Ethnicity Percentage',
        '10. Largest Ethnicity Slice', 'MHI Growth', 'City Trailing 12 - Cap Rate'
    ]
    
    # Process each state file
    for state_file in state_files:
        try:
            # Read the Excel file
            file_path = os.path.join(DATA_DIR, state_file)
            df = pd.read_excel(file_path)
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Map input columns to our standardized names
            column_mapping = {
                'city': 'City',
                'closest metro area': 'Metro Area',
                'population in 2022': 'Population',
                'population change since 2000 (%)': '1. Pop Growth',
                'median household income in 2022': '2. Median Household Income (45-48k, <85/90k)',
                'median household income in 2000': 'MHI',
                'median condo value in 2022': 'Median Condo Value',
                'median condo value in 2000': 'MCV',
                'median contract rent': 'Median Contract Rent',
                'poverty percentage': '8. Poverty',
                'largest ethnicity percentage': '9. Largest Ethnicity Percentage',
                'largest ethnicity slice': '10. Largest Ethnicity Slice',
                'most recent crime index': '6. Crime Index',
                'unemployment rate': '6. Unemployment',
                'job growth (%)': '3. Job Growth (last 12 months)'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Calculate derived columns (empty for now)
            df['2. Rent to Income'] = ''
            df['4. Median Household Income/Condo Value'] = ''
            df['5. MCV Growth'] = '' 
            df['7. Price Rent Ratio'] = '' 
            df['MHI Growth'] = ''
            df['City Trailing 12 - Cap Rate'] = ''
            
            # Reorder columns
            df = df.reindex(columns=output_columns)
            
            dfs.append(df)
            print(f"Processed {state_file} successfully")
            
        except Exception as e:
            print(f"Error processing file {state_file}: {str(e)}")
            continue
    
    if not dfs:
        raise ValueError("No valid data found in any state files")
    
    for df in dfs:
        df.replace(['NA', 'N/A', 'na', 'n/a', 'nan'], '', inplace=True)
        df.fillna('', inplace=True)

    # Concatenate all DataFrames
    master_df = pd.concat(dfs, ignore_index=True)
    
    # Save to Excel with custom formatting
    with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
        # First write the DataFrame without formatting
        master_df.to_excel(writer, index=False, sheet_name='Real Estate Data')
        
        workbook = writer.book
        worksheet = writer.sheets['Real Estate Data']

        # Define formats
        dollar_format = workbook.add_format({'num_format': '$#,##0'})
        percent_format = workbook.add_format({'num_format': '0.00%'})
        percent_whole_format = workbook.add_format({'num_format': '0%'})
        text_format = workbook.add_format()
        number_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # Write all data with appropriate formatting
        for row_num in range(1, len(master_df)+1):
            # Column 0: City (text)
            worksheet.write(row_num, 0, str(master_df.at[row_num-1, 'City']), text_format)
            
            # Column 1: Metro Area (text)
            worksheet.write(row_num, 1, str(master_df.at[row_num-1, 'Metro Area']), text_format)
            
            # Column 2: Population (number)
            pop = master_df.at[row_num-1, 'Population']
            if pd.notna(pop) and str(pop).replace('.','',1).isdigit():
                worksheet.write_number(row_num, 2, float(pop), text_format)
            else:
                worksheet.write(row_num, 2, str(pop), text_format)
            
            # Column 3: 1. Pop Growth (percentage)
            pop_growth = master_df.at[row_num-1, '1. Pop Growth']
            try:
                worksheet.write_number(row_num, 3, float(pop_growth), percent_format)
            except:
                worksheet.write(row_num, 3, str(pop_growth), text_format)
            
            # Column 4: 2. Median Household Income (dollar)
            mhi = master_df.at[row_num-1, '2. Median Household Income (45-48k, <85/90k)']
            try:
                worksheet.write_number(row_num, 4, float(mhi), dollar_format)
            except:
                worksheet.write(row_num, 4, str(mhi), text_format)
            
            # Column 5: 2. Rent to Income (formula)
            worksheet.write_formula(
                f'F{row_num+1}',
                f'=P{row_num+1}/(E{row_num+1}/12)',
                percent_format
            )
            
            # Column 6: 3. Job Growth (percentage)
            job_growth = master_df.at[row_num-1, '3. Job Growth (last 12 months)']
            try:
                worksheet.write_number(row_num, 6, float(job_growth), percent_format)
            except:
                worksheet.write(row_num, 6, str(job_growth), text_format)
            
            # Column 7: 4. Median Household Income/Condo Value (formula)
            worksheet.write_formula(
                f'H{row_num+1}',
                f'=E{row_num+1}/K{row_num+1}',
                percent_format
            )
            
            # Column 8: MHI (dollar)
            mhi_2000 = master_df.at[row_num-1, 'MHI']
            try:
                worksheet.write_number(row_num, 8, float(mhi_2000), dollar_format)
            except:
                worksheet.write(row_num, 8, str(mhi_2000), text_format)
            
            # Column 9: 5. MCV Growth (formula)
            worksheet.write_formula(
                f'J{row_num+1}',
                f'=(K{row_num+1}-L{row_num+1})/L{row_num+1}',
                percent_format
            )
            
            # Column 10: Median Condo Value (special handling for "over")
            mcv = master_df.at[row_num-1, 'Median Condo Value']
            if str(mcv).lower() == 'over':
                worksheet.write(row_num, 10, 'over', text_format)
            else:
                try:
                    worksheet.write_number(row_num, 10, float(mcv), dollar_format)
                except:
                    worksheet.write(row_num, 10, str(mcv), text_format)
            
            # Column 11: MCV (dollar)
            mcv_2000 = master_df.at[row_num-1, 'MCV']
            try:
                worksheet.write_number(row_num, 11, float(mcv_2000), dollar_format)
            except:
                worksheet.write(row_num, 11, str(mcv_2000), text_format)
            
            # Column 12: 6. Crime Index (number)
            crime = master_df.at[row_num-1, '6. Crime Index']
            try:
                worksheet.write_number(row_num, 12, float(crime), number_format)
            except:
                worksheet.write(row_num, 12, str(crime), text_format)
            
            # Column 13: 6. Unemployment (percentage)
            unemployment = master_df.at[row_num-1, '6. Unemployment']
            try:
                worksheet.write_number(row_num, 13, float(unemployment), percent_whole_format)
            except:
                worksheet.write(row_num, 13, str(unemployment), text_format)
            
            # Column 14: 7. Price Rent Ratio (formula)
            worksheet.write_formula(
                f'O{row_num+1}',
                f'=K{row_num+1}/(P{row_num+1}*12)',
                number_format
            )
            
            # Column 15: Median Contract Rent (dollar)
            rent = master_df.at[row_num-1, 'Median Contract Rent']
            try:
                worksheet.write_number(row_num, 15, float(rent), dollar_format)
            except:
                worksheet.write(row_num, 15, str(rent), text_format)
            
            # Column 16: 8. Poverty (percentage)
            poverty = master_df.at[row_num-1, '8. Poverty']
            try:
                worksheet.write_number(row_num, 16, float(poverty), percent_whole_format)
            except:
                worksheet.write(row_num, 16, str(poverty), text_format)
            
            # Column 19: MHI Growth (formula)
            worksheet.write_formula(
                f'T{row_num+1}',
                f'=(E{row_num+1}-I{row_num+1})/I{row_num+1}',
                percent_format
            )
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'align': 'center',
            'border': 1,
        })
        
        # Write the headers with wrapping
        for col_num, value in enumerate(master_df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Set ALL columns to width 10
        for col_num in range(len(master_df.columns)):
            worksheet.set_column(col_num, col_num, 12)

        criteria_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'align': 'center',
            'border': 1,
            'bg_color': '#FFFFF0',  # Light yellow background
            'font_size': 9,         # Smaller font
            'italic': True
        })

        criteria_values = [
            "Thumbs-up Criteria",  # City
            "",  # Metro Area
            "Yr 2022",  # Population
            "small 15%+, med 20%+, large 30%+",  # 1. Pop Growth
            "Yr 2022", # 2. Meidn aHousehold Income
            "Below 30-35%, lower = renter can afford rent",  # 2. Rent to Income Ratio
            ">2% / yr",  # 3. Job Growth
            "ideally 13-25%, harder for people to buy house, and there's room to raise rent",  # 4. Median Household Income / Condo Value
            "Yr 2000", # MHI
            "40%+ (20 years)",  # 5. MCV Growth
            "Yr 2022",  # Median Condo Value
            "Yr 2000", # MCV
            "<500 good, <100 best, trending less (<250)",  # 6. Crime Level
            "<2.5%",  # 6. Unemployment
            ">13 (15-25)",  # 7. Price Rent Ratio
            "700-1000", # Median Contract Rent
            "<20%",  # 8. Poverty
            "<75%",  # 9. Ethnicity
            "", 
            "30-35%+ (20 yrs)", # MHI Growth
            ""
        ]
        
        for col_num, value in enumerate(criteria_values):
            worksheet.write(1, col_num, value, criteria_format)

        green_format = workbook.add_format({
            'bg_color': '#ABDDC5',  # Light green fill
        })

        # Apply conditional formatting to Column D (index 3)
        worksheet.conditional_format(
            'D3:D' + str(len(master_df)+2), 
            {
                'type': 'cell',
                'criteria': 'greater than',
                'value': 0.3,  # 30%
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'F3:F' + str(len(master_df)+2), 
            {
                'type': 'cell',
                'criteria': 'less than',
                'value': 0.3,  # 30%
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'G3:G' + str(len(master_df)+2), 
            {
                'type': 'cell',
                'criteria': 'greater than',
                'value': 0.02,  # 30%
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'H3:H' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'between',
                'minimum': 0.13, 
                'maximum': 0.25, 
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'J3:J' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'greater than',
                'value': 0.4,
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'M3:M' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'less than',
                'value': 500,
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'N3:N' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'less than',
                'value': 0.025,
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'O3:O' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'between',
                'minimum': 15, 
                'maximum': 25, 
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'P3:P' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'between',
                'minimum': 700, 
                'maximum': 1000, 
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'Q3:Q' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'less than',
                'value': 0.2, 
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'R3:R' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'less than',
                'value': 0.75, 
                'format': green_format
            }
        )

        worksheet.conditional_format(
            'T3:T' + str(len(master_df)+2),
            {
                'type': 'cell',
                'criteria': 'between',
                'minimum': 0.3,
                'maximum': 0.35, 
                'format': green_format
            }
        )

        # Freeze header row
        worksheet.freeze_panes(1, 0)
        
        # Add autofilter
        worksheet.autofilter(0, 0, 0, len(output_columns)-1)
    
    print(f"Master file created successfully at: {OUTPUT_FILE}")
    print(f"Total records processed: {len(master_df)}")

if __name__ == "__main__":
    concatenate_state_files()