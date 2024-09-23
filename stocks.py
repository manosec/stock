import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime as dt
import altair as alt
import pandas_datareader as pdr
import requests
from get_all_tickers import get_tickers as gt
from dateutil.relativedelta import relativedelta
from tensorflow.keras.models import load_model
import joblib
import numpy as np

@st.cache_resource()
def get_stock_data(symbol, start_date, end_date):
    try:
        stock_data = yf.download(symbol, start=start_date, end=end_date)
        return stock_data
    except Exception as  e:
        return e

@st.cache_resource()
def load_lstm_model(model_path='model.joblib'):
    return joblib.load(model_path)

@st.cache_resource()
def load_scaler(scaler_path='scaler.joblib'):
    return joblib.load(scaler_path)

def plot_existing_and_forecast_trend(stock_data, days_to_show, ticker, lstm_model=load_lstm_model(), scaler=load_scaler(), forecast_days=15):
    st.subheader(f'Existing Trend and {forecast_days}-Day Price Forecast for {ticker}')

    # Scale the closing price data
    scaled_data = scaler.transform(stock_data['Close'].values.reshape(-1, 1))
    
    # Prepare the data for LSTM model input
    last_sequence = scaled_data[-60:]  # Take the last 60 data points
    predictions = []
    
    for _ in range(forecast_days):
        # Ensure the sequence is in the correct shape: (1, 60, 1)
        last_sequence_reshaped = last_sequence.reshape(1, 60, 1)
        
        # Predict the next value
        prediction = lstm_model.predict(last_sequence_reshaped)
        predictions.append(prediction[0, 0])
        
        # Append the prediction to the sequence and remove the first element to maintain the sequence length
        last_sequence = np.append(last_sequence, prediction)[-60:]

    # Inverse scale the predictions
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
    
    # Create a date range for the forecast
    last_date = stock_data.index[-1]
    forecast_dates = pd.date_range(last_date, periods=forecast_days + 1)[1:]  # Exclude the last date
    
    # Prepare data for plotting
    forecast_data = pd.DataFrame({
        'Date': forecast_dates,
        'Forecasted Close': predictions
    })
    
    # Plot the existing data
    existing_chart = alt.Chart(stock_data.tail(days_to_show).reset_index(), title="Existing Trend and Forecast").mark_line().encode(
        x=alt.X('Date:T', axis=alt.Axis(title="Date")),
        y=alt.Y('Close:Q', title='Price in Dollar'),
        tooltip=['Date:T', alt.Tooltip('Close:Q', title="Existing Closing Price")],
        color=alt.value('blue'),
        strokeWidth=alt.value(8)
    ).properties(
        width=800,
        height=400
    )
    
    # Plot the forecast data
    forecast_chart = alt.Chart(forecast_data, title="Forecasted Trend").mark_line(strokeDash=[5, 5]).encode(
        x=alt.X('Date:T', axis=alt.Axis(title="Date")),
        y=alt.Y('Forecasted Close:Q', title='Price in Dollar'),
        tooltip=['Date:T', alt.Tooltip('Forecasted Close:Q', title="Forecasted Closing Price")],
        color=alt.value('orange'),
        strokeWidth=alt.value(8)
    )
    
    # Combine both charts
    combined_chart = existing_chart + forecast_chart
    
    st.altair_chart(combined_chart, use_container_width=True)

def create_daily_return_scatter(symbol, stock_data, days_to_show):
    st.subheader(f'Daily Return Scatter Plot for {symbol}')

    scatter_chart = alt.Chart(stock_data['Daily Return'].tail(days_to_show).reset_index()).mark_circle(size=60).encode(
        x=alt.X('Date:T', axis=alt.Axis(title="Date")),
        y=alt.Y('Daily Return:Q', title='Daily Return (%)'),
        tooltip=['Date:T', alt.Tooltip('Daily Return:Q', title="Daily Return (%)")]
    ).properties(
        width=800,
        height=400
    )
    
    st.altair_chart(scatter_chart, use_container_width=True)


def create_stock_chart(symbol, days_to_show):
    try:
        st.title(f'Stock Price Analysis for {symbol}')
        start_date = pd.to_datetime("today") - pd.DateOffset(days=365*3)
        end_date = pd.to_datetime("today")
        stock_data = get_stock_data(symbol, start_date, end_date)
        stock_data['Close'] = stock_data['Close'].round(2)
        stock_data['Daily Return'] = stock_data['Adj Close'].pct_change()
        stock_data['Daily Return'] = (stock_data['Daily Return'] * 100).round(2)
        
        # Calculate 100-day and 200-day moving averages
        stock_data['100_MA'] = stock_data['Close'].rolling(window=100).mean().round(2)
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean().round(2)
            
        ma_chart = alt.Chart(stock_data.tail(days_to_show).reset_index(), title="Closing Price by Days").mark_line().encode(
            x=alt.X('Date:T', axis=alt.Axis(title="Days")),
            y=alt.Y('Close:Q', title='Price in Dollar'),
            tooltip=['Date:T', alt.Tooltip('Close:Q', title="Closing Price")],
            strokeWidth=alt.value(8)
        ).properties(
            width=800,
            height=400
        )
        
        # Plot 100-day and 200-day moving averages with tooltips
        ma_chart += alt.Chart(stock_data.tail(days_to_show).reset_index()).mark_line().encode(
            x=alt.X('Date:T', axis=alt.Axis(title="Days")),
            y=alt.Y('100_MA:Q', title='Price in Dollar'),
            color=alt.value('green'),
            tooltip=['Date:T', alt.Tooltip('100_MA:Q', title='100-day MA')],
            strokeWidth=alt.value(8)
        )

        ma_chart += alt.Chart(stock_data.tail(days_to_show).reset_index()).mark_line(strokeDash=[2, 2]).encode(
            x=alt.X('Date:T', axis=alt.Axis(title="Days")),
            y=alt.Y('200_MA:Q', title='Price in Dollar'),
            color=alt.value('red'),
            tooltip=['Date:T', alt.Tooltip('200_MA:Q', title='200-day MA')],
            strokeWidth=alt.value(8),
        )
        
        st.altair_chart(ma_chart, use_container_width=True)
        create_daily_return_scatter(symbol, stock_data, days_to_show)
        plot_existing_and_forecast_trend(stock_data=stock_data, days_to_show=days_to_show, ticker=symbol)

    except Exception as e:
        print(e)
        st.write("Something Went wrong, Please Refresh")



if __name__ == "__main__":
    # Store the initial value of widgets in session state
    text_input = st.text_input(
        "Enter Stock Ticker 👇",
        placeholder="Enter stock ticker here(Eg: NVDA)"
    )
    days = st.number_input(
        "No of Days",
        step=50,
        max_value=500,
        min_value=50,
        value=50,
        placeholder="Enter the number of months to show the data"
    )

    if text_input and days:
        create_stock_chart(symbol=text_input.upper(), days_to_show=days)
    elif days and not text_input:
        create_stock_chart(symbol="AAPL", days_to_show=days)
    else:
        create_stock_chart(symbol="AAPL", days_to_show=50)
    
