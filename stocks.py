import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime as dt
import altair as alt
import pandas_datareader as pdr
import requests
from bs4 import BeautifulSoup
from get_all_tickers import get_tickers as gt



def get_stock_data(symbol, start_date, end_date):
    stock_data = yf.download(symbol, start=start_date, end=end_date)
    return stock_data


def create_stock_chart(symbol, days_to_show=50):
    print(symbol)
    st.title(f'Stock Price Analysis for {symbol}')
    start_date = pd.to_datetime("today") - pd.DateOffset(days=365*2)
    end_date = pd.to_datetime("today")
    stock_data = get_stock_data(symbol, start_date, end_date)
    stock_data['Close'] = stock_data['Close'].round(2)
    # Plot closing prices with tooltips
    chart = alt.Chart(stock_data.tail(days_to_show).reset_index(), title="Closing Price by Days").mark_line().encode(
        x=alt.X('Date:T', axis=alt.Axis(title="Days")),
        y=alt.Y('Close:Q', title='Price in Dollar'),
        tooltip=['Date:T', 'Close:Q'],
        strokeWidth=alt.value(6)
    ).properties(
        width=800,
        height=400
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    
    # Calculate 100-day and 200-day moving averages
    stock_data['100_MA'] = stock_data['Close'].rolling(window=100).mean().round(2)
    stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean().round(2)
    
    # Plot 100-day and 200-day moving averages with tooltips
    ma_chart = alt.Chart(stock_data.tail(days_to_show).reset_index(), title="100 & 200 Moving Average by Days").mark_line().encode(
        x=alt.X('Date:T', axis=alt.Axis(title="Days")),
        y=alt.Y('100_MA:Q', title='Price in Dollar'),
        color=alt.value('green'),
        tooltip=['Date:T', alt.Tooltip('100_MA:Q', title='100-day MA')],
        strokeWidth=alt.value(6)
    ).properties(
        width=800,
        height=400
    )

    ma_chart += alt.Chart(stock_data.tail(days_to_show).reset_index()).mark_line(strokeDash=[2, 2]).encode(
        x=alt.X('Date:T', axis=alt.Axis(title="Days")),
        y=alt.Y('200_MA:Q', title='Price in Dollar'),
        color=alt.value('red'),
        tooltip=['Date:T', alt.Tooltip('200_MA:Q', title='200-day MA')],
        strokeWidth=alt.value(6),
    )
    
    st.altair_chart(ma_chart, use_container_width=True)




if __name__ == "__main__":
    # Store the initial value of widgets in session state
    if "visibility" not in st.session_state:
        st.session_state.visibility = "visible"
        st.session_state.disabled = False
    text_input = st.text_input(
        "Enter Stock Ticker 👇",
        label_visibility=st.session_state.visibility,
        disabled=st.session_state.disabled,
        placeholder="Enter stock ticker here(Eg: NVDA)"
    )
    tickers =  ['AAPL', 'TSLA','MSFT','NFLX', 'NVDA']
    if text_input:
        st.write("You entered: ", text_input)
        create_stock_chart(symbol=text_input.upper(), days_to_show=50)
    create_stock_chart(symbol="AAPL", days_to_show=50)
    
