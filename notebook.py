# %%
import time
from rich import print
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import yfinance as yf

# import pandas as pd
import pandas_ta as ta

days = 365

# read in tickers
tickers = ["MSFT"]
try:
    with open("tickers.txt") as file:
        tickers = [line.rstrip() for line in file]
except Exception as ex:
    print("No tickers found in tickers.txt file :( ", ex)


for ticker in tickers:
    # download dataframe using pandas_datareader
    ticker = yf.Ticker(ticker)
    ticker_df = ticker.history(period="max")
    ticker_df = ticker_df.reset_index()

    # STATS
    stochrsi = ta.stochrsi(ticker_df["Close"], length=14)
    ticker_df["stochrsi_k"] = stochrsi["STOCHRSIk_14_14_3_3"]
    ticker_df["stochrsi_d"] = stochrsi["STOCHRSId_14_14_3_3"]
    ticker_df["rsi"] = ta.rsi(ticker_df["Close"], length=14)
    ticker_df["sma_14"] = ta.sma(ticker_df["Low"], length=14)
    ticker_df["sma_50"] = ta.sma(ticker_df["Low"], length=50)
    ticker_df["sma_200"] = ta.sma(ticker_df["Low"], length=200)

    # limit data to x days
    ticker_df = ticker_df.tail(days).copy()

    # VISUALS
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

    fig.add_trace(
        go.Candlestick(
            x=ticker_df["Date"],
            open=ticker_df["Open"],
            high=ticker_df["High"],
            low=ticker_df["Low"],
            close=ticker_df["Close"],
        ),
        row=1,
        col=1,
    )

    for sma in [(14, "yellow"), (50, "orange"), (200, "green")]:
        fig.add_trace(
            go.Scatter(
                x=ticker_df["Date"],
                y=ticker_df[f"sma_{sma[0]}"],
                mode="lines",
                line=go.scatter.Line(color=sma[1]),
                showlegend=True,
                name="sma_14",
            ),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=ticker_df["Date"],
            y=ticker_df["stochrsi_k"],
            mode="lines",
            line=go.scatter.Line(color="royalblue"),
            showlegend=True,
            name="stoch_rsi_k",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=ticker_df["Date"],
            y=ticker_df["stochrsi_d"],
            mode="lines",
            line=go.scatter.Line(color="red"),
            showlegend=True,
            name="stoch_rsi_d",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=ticker_df["Date"],
            y=ticker_df["rsi"],
            mode="lines",
            line=go.scatter.Line(color="purple"),
            showlegend=True,
            name="rsi",
        ),
        row=2,
        col=1,
    )

    fig.update_xaxes(rangeslider_thickness=0.1)

    stock_title = (
        f"{ticker.info['exchange'].upper()} - {ticker.info['longName']}"
    )
    try:
        mc = "{:,.2f}".format(ticker.info["marketCap"])
        stock_title = (
            f"{stock_title} - marketcap: {mc} {ticker.info['currency']}"
        )
    except Exception:
        pass

    fig.update_layout(
        title_text=stock_title,
        xaxis_rangeslider_visible=True,
        autosize=False,
        width=1600,
        height=1000,
    )
    fig.show()

    # reduce calls to Yahoo api
    time.sleep(1)

# %%
