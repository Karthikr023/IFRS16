import streamlit as st
import pandas as pd

import numpy as np
import openpyxl 
import datetime
from datetime import datetime, timedelta

def main():
    st.title('IFRS 16 Reporting')
    today = datetime.now()
    last_month = today - timedelta(days=30)
    default_date_str = last_month.strftime('%b-%y')  # Format it to "Sep-23"

    date= st.selectbox("Select Date", options=[default_date_str, 'Another Option'])
    opco = st.selectbox("Select OPCO", options=["IB", "VY"])

    uploaded_file = st.file_uploader("Upload the Datamart file", type=['xlsx'], key="file1")
    uploaded_file1 = st.file_uploader("Upload trades executed for the month", type=['xlsx'], key="file2")

    start_button = st.button("Start")

    if start_button:
        if uploaded_file is not None and uploaded_file1 is not None:
            data1 = pd.read_excel(uploaded_file, engine='openpyxl')
            data2 = pd.read_excel(uploaded_file1, engine='openpyxl')

            data2['TRN.STATUS'] = data2['TRN.STATUS'].astype(str)
            data2['CNT.NB'] = data2['CNT.NB'].astype(str)
            data2['B/S'] = data2['B/S'].astype(str)
            data2['Test1'] = data2['CNT.NB'].where(  (data2['TRN.STATUS'] == 'LIVE') & (data2['B/S'] == 'B'))
            data2['Test2'] = data2['TRN.NB'].where(  (data2['TRN.STATUS'] == 'DEAD') & (data2['CNT.TYPOLOGY'] == 'FX Swap'))
            data2['Test1'] = data2['Test1'].astype("string")
            data2['Test2'] = data2['Test2'].astype("string")
            data1['ContractID'] = data1['ContractID'].astype("string")
            data2['TRN.NB'] = data2['TRN.NB'].astype("string")
            data3 = data2[data2['Test1'].notna()]
            data4 = data2[data2['Test2'].notna()]
            data4 = data4.rename(columns={'CNT.NB': 'ContractID'})
            list1 = data3['Test1']
            list2 = data4['Test2']
            list3 = data4['ContractID']
            output1 = data1[data1['ContractID'].isin(list1)]
            output2 = data1[data1['ContractID'].isin(list3)]
            merged_df = pd.merge(output2, data4[['ContractID','EXPIRY', 'NOMINAL']], on='ContractID', how='left', suffixes=('', '_data4'))
            merged_df['EXPIRY'] = pd.to_datetime(merged_df['EXPIRY']).dt.strftime('%d/%m/%Y')
            merged_df['ValueDate'] = merged_df['EXPIRY']
            merged_df['ExpireDate'] = merged_df['EXPIRY']
            merged_df['NominalEqv'] = merged_df['NOMINAL']
            merged_df.loc[:, 'BuySell'] = 'S'
            merged_df = merged_df.drop(['EXPIRY', 'NOMINAL'], axis=1)
            result = pd.concat([output1, merged_df], ignore_index=True)      
            result = result.sort_values(by='ContractID', ascending=True)
            result['TradeDate'] = pd.to_datetime(result['TradeDate'])
            result['TradeDate'] = result['TradeDate'].dt.strftime('%d/%m/%Y')

            result['ValueDate'] = pd.to_datetime(result['ValueDate'])

# Format the date column to UK style
            result['ValueDate'] = result['ValueDate'].dt.strftime('%d/%m/%Y')

            result['ExpireDate'] = pd.to_datetime(result['ExpireDate'])

# Format the date column to UK style
            result['ExpireDate'] = result['ExpireDate'].dt.strftime('%d/%m/%Y')
            result = result.drop(['Mut.Break S.Date', 'FX_TP_SPOT'], axis=1)
            result.to_excel(r'Z:\FRM FX and Liquidity\FX\KR- Python output test\IFRS 16\_'+opco+'_'+date+'.xlsx', index = False)
# Show DataFrame
            st.write("Data Preview:")
            st.write(result.head())

        # Perform your data analysis and optimization here

if __name__ == "__main__":
    main()
