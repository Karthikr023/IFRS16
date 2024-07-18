import streamlit as st
import paramiko
import pandas as pd
import os
from datetime import datetime

host = '18.132.169.253'
username = 'karthik'
private_key_path = r'Z:\FRM FX and Liquidity\FX\KR-Python code test\weekly summary\karthik.pem'
remote_directory = '/interfaces/reporting/FX_Hedging/'
local_directory = r'Z:\FRM FX and Liquidity\FX\KR- Python output test\SFTP output\\'

# Set up SSH client
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Connect using the private key
    ssh_client.connect(host, username=username, key_filename=private_key_path)

    # Open an SFTP session
    sftp = ssh_client.open_sftp()

    # Get list of files in the remote directory
    files = sftp.listdir_attr(remote_directory)

    # Extract filenames and dates
    filenames = [f.filename for f in files if f.filename.startswith('FX_Hedging_') and f.filename.endswith('.csv')]
    
    # Function to extract date from filename
    def extract_date(filename):
        date_str = filename.replace('FX_Hedging_', '').replace('.csv', '')
        return datetime.strptime(date_str, '%Y%m%d').date()  # Convert to date object

    # Create a dictionary to map dates to filenames
    date_to_filename = {extract_date(f): f for f in filenames}

    # Sort dates in descending order
    sorted_dates = sorted(date_to_filename.keys(), reverse=True)

    # Close SFTP client
    sftp.close()
    ssh_client.close()

    # Streamlit UI elements
    st.title('Sensitivity Analysis')

    # Date input for date selection
    selected_date = st.date_input('Select a date', sorted_dates[0])

    if selected_date in date_to_filename:
        st.write(f'You selected: {selected_date.strftime("%Y-%m-%d")}')

        selected_filename = date_to_filename[selected_date]

        # Set up SSH client again to download the selected file
        ssh_client.connect(host, username=username, key_filename=private_key_path)
        sftp = ssh_client.open_sftp()

        # Generate remote and local file paths
        remote_file_path = os.path.join(remote_directory, selected_filename)
        local_file_path = os.path.join(local_directory, selected_filename)

        # Download the selected file
        sftp.get(remote_file_path, local_file_path)
        st.success(f"File {selected_filename} downloaded to {local_file_path}")

        # Read the file using pandas with semicolon delimiter
        df = pd.read_csv(local_file_path, sep=';')

        # Close SFTP client and SSH client
        sftp.close()
        ssh_client.close()

        # Streamlit UI elements for sensitivity analysis
        st.title('Sensitivity Analysis Tool')
        GBPUSD_value = st.number_input('Cable ref rate', value=1.2750, step=0.01)
        steps_value = st.number_input('Steps', value=0.05, step=0.01)
        EURUSD_value = st.number_input('EURUSD ref rate', value=1.0850, step=0.01)
        EURGBP_value = st.number_input('EURGBP ref rate', value=0.85, step=0.01)
        group_level = st.checkbox('Group Level')        
        # Manually specified portfolio options
        portfolio_options = ['BA Fuel', 'BA Revenue', 'BA Capex', 'IB1 Fuel','IB2 Fuel', 'IB Revenue', 'IB2 Revenue', 'IB1 Maint','IB2 Maint', 'IB Capex', 'VY Fuel', 'VY Maint','VY Capex', 'EI Fuel', 'EI Revenue', 'EI Capex' ]  # Add other portfolios as needed
        selected_portfolios = st.multiselect('Select Portfolio', options=portfolio_options)

        # Reverse mapping for filtering if needed
         # Portfolio mapping
        portfolio_mapping = {
            'BA Fuel': 'BA01_FUEL_FX',
            'BA Revenue': 'BA01_FX_REVENUE',
            'BA Capex': 'BA01_CAPEX',
            'IB1 Fuel': 'IB01_FUEL_FX',
            'IB2 Fuel': 'IB02_FUEL_FX',
            'IB Revenue': 'IB01_FX_REVENUE',
            'IB2 Revenue': 'IB02_FX_REVENUE',
            'IB1 Maint': 'IB01_FX_MAINTEN',
            'IB2 Maint': 'IB02_FX_MAINTEN',
            'IB Capex': 'IB01_CAPEX',
            'VY Fuel': 'VY01_FUEL_FX',
            'VY Maint': 'VY01_FX_MAINTEN',
            'VY Capex': 'VY01_CAPEX',
            'EI Fuel': 'EI01_FUEL_FX',
            'EI Revenue': 'EI01_FX_REVENUE',
            'EI Capex': 'EI01_FX_CAPEX'
        }

        reverse_portfolio_mapping = {v: k for k, v in portfolio_mapping.items()}
        # Rename a column
        df.rename(columns={'NOMINAL_0': 'NOMINAL 0'}, inplace=True)
        if st.button('Update'):
            # Create new columns for the calculation
            df['Step +1'] = 0
            df['Step +2'] = 0
            df['Step +3'] = 0
            df['Central point'] = 0 
            df['Step -1'] = 0
            df['Step -2'] = 0
            df['Step -3'] = 0

            for index, row in df.iterrows():
                if row['RATE'] == 0:
                    continue  # Skip the row if RATE is zero to avoid division by zero

                if (row['PL INSTRUMENT'] == "GBP/USD") and (row['GROUP'] == "FXD") and (row['B/S'] == "B"):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / GBPUSD_value)
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "GBP/USD") and (row['C/P'] == "C") and (row['B/S'] == "B") and (row['STRIKE'] >= GBPUSD_value):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / GBPUSD_value)
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "GBP/USD") and (row['C/P'] == "C") and (row['B/S'] == "B") and (row['STRIKE'] < GBPUSD_value):
                    df.loc[index, 'Central point'] = 0
                    df.loc[index, 'Step +1'] = 0
                    df.loc[index, 'Step +2'] = 0
                    df.loc[index, 'Step +3'] = 0
                    df.loc[index, 'Step -1'] = 0
                    df.loc[index, 'Step -2'] = 0
                    df.loc[index, 'Step -3'] = 0
                elif (row['PL INSTRUMENT'] == "GBP/USD") and (row['C/P'] == "P") and (row['B/S'] == "S") and (row['STRIKE'] < GBPUSD_value):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / GBPUSD_value)
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "GBP/USD") and (row['GROUP'] == "FXD") and (row['B/S'] == "S"):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / GBPUSD_value - row['NOMINAL 0'] / row['RATE'])
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (GBPUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "EUR/USD") and (row['GROUP'] == "FXD") and (row['B/S'] == "B"):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / EURUSD_value)
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "EUR/USD") and (row['C/P'] == "C") and (row['B/S'] == "B") and (row['STRIKE'] >= EURUSD_value):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / EURUSD_value)
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "EUR/USD") and (row['C/P'] == "C") and (row['B/S'] == "B") and (row['STRIKE'] < EURUSD_value):
                    df.loc[index, 'Central point'] = 0
                    df.loc[index, 'Step +1'] = 0
                    df.loc[index, 'Step +2'] = 0
                    df.loc[index, 'Step +3'] = 0
                    df.loc[index, 'Step -1'] = 0
                    df.loc[index, 'Step -2'] = 0
                    df.loc[index, 'Step -3'] = 0
                elif (row['PL INSTRUMENT'] == "EUR/USD") and (row['C/P'] == "P") and (row['B/S'] == "S") and (row['STRIKE'] < EURUSD_value):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / EURUSD_value)
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['STRIKE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 3)))
                elif (row['PL INSTRUMENT'] == "EUR/USD") and (row['GROUP'] == "FXD") and (row['B/S'] == "S"):
                    df.loc[index, 'Central point'] = -1 * (row['NOMINAL 0'] / EURUSD_value - row['NOMINAL 0'] / row['RATE'])
                    df.loc[index, 'Step +1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 1)))
                    df.loc[index, 'Step +2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 2)))
                    df.loc[index, 'Step +3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value + (steps_value * 3)))
                    df.loc[index, 'Step -1'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 1)))
                    df.loc[index, 'Step -2'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 2)))
                    df.loc[index, 'Step -3'] = -1 * (row['NOMINAL 0'] / row['RATE'] - row['NOMINAL 0'] / (EURUSD_value - (steps_value * 3)))
                else:
                    df.loc[index, 'Central point'] = 0
            df['TRN.DATE'] = pd.to_datetime(df['TRN.DATE'], format='%d/%m/%y')
            df['EXPIRY'] = pd.to_datetime(df['EXPIRY'], format='%d/%m/%y')
            df_filtered = df
            #df_filtered = df[df['EXPIRY'] >= pd.to_datetime(selected_date)]
            df_filtered['Quarter'] = df_filtered['EXPIRY'].dt.to_period('Q').dt.strftime('Q%q %y')
            if selected_portfolios:
                selected_portfolio_codes = [portfolio_mapping[portfolio] for portfolio in selected_portfolios]
                df_filtered = df_filtered[df_filtered['PORTFOLIO'].isin(selected_portfolio_codes)]
            if group_level:
                conversion_rate = EURGBP_value
    # Apply conversion only to GBP/USD rows
                gbp_usd_mask = df_filtered['PL INSTRUMENT'] == "GBP/USD"
                df_filtered.loc[gbp_usd_mask, ['Step -3', 'Step -2', 'Step -1', 'Central point', 'Step +1', 'Step +2', 'Step +3']] *= conversion_rate


                
            df_pivot = df_filtered.pivot_table(index='Quarter', values=['Step -3', 'Step -2', 'Step -1', 'Central point', 'Step +1', 'Step +2', 'Step +3'], aggfunc='sum', fill_value=0)
            df_pivot = df_pivot / 1000000
            df_pivot = df_pivot.round(4)
            # Sort the pivot table by quarter
            def quarter_sort_key(quarter):
                year = int(quarter.split()[1])
                quarter_num = int(quarter.split()[0][1])
                return year * 10 + quarter_num

            df_pivot = df_pivot.sort_index(key=lambda x: x.map(quarter_sort_key))
             # Add a row for the rates used in the calculation
            rates_row = pd.DataFrame([[''] * len(df_pivot.columns)], columns=df_pivot.columns, index=['Scenario Rate'])
            rates_row.loc['Scenario Rate', 'Central point'] = GBPUSD_value if not group_level else EURUSD_value
            for i in range(1, 4):
                rates_row.loc['Scenario Rate', f'Step +{i}'] = EURUSD_value + (steps_value * i)
                rates_row.loc['Scenario Rate', f'Step -{i}'] = EURUSD_value - (steps_value * i)

            df_pivot = pd.concat([rates_row, df_pivot])
# Define a function to highlight positive and negative values differently
            def highlight_values(val):
                if val > 0:
                    color = 'green'
                elif val < 0:
                    color = 'red'
                else:
                    color = 'black'
                return f'color: {color}'

# Style the DataFrame
# Style the DataFrame
            styled_df = df_pivot.style.applymap(highlight_values).format("{:.2f}")

            
            
            st.write("Pivot Table:")
            st.write(styled_df)

            if st.button('Download'):
                folder_path = r'Z:\FRM FX and Liquidity\FX\KR- Python output test\Sensitivity'
                file_path = os.path.join(folder_path, 'pivot_table.csv')
                os.makedirs(folder_path, exist_ok=True)
                df_pivot.insert(0, 'Quarters', df_pivot.index)
                df_pivot.to_csv(file_path, index=False)
                st.success(f'Pivot table downloaded as "{file_path}".')

    else:
        st.error(f"No file available for the selected date: {selected_date}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")


