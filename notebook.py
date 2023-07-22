# %%
import os
import time
import statistics
import datetime
from rich import print
from plotly.subplots import make_subplots
from glob import glob
from pypdf import PdfMerger

import plotly.graph_objects as go
import yfinance as yf


# import pandas as pd
import pandas_ta as ta

currentDateTime = datetime.datetime.now()
currentdate = currentDateTime.date()
currentyear = int(currentdate.strftime("%Y"))


def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return ((current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return float("inf")


# read in tickers
try:
    with open("tickers.txt") as file:
        tickers = [line.rstrip() for line in file]
except Exception as ex:
    print("No tickers found in tickers.txt file :( ", ex)
# tickers = ["AAPL"]


sma_multiply = 1

for ticker in tickers:
    # download dataframe using pandas_datareader
    ticker_df = yf.download(ticker, period="100y", interval="1wk")
    ticker_df = ticker_df.reset_index()

    # STATS
    stochrsi = ta.stochrsi(ticker_df["Close"], length=14)
    ticker_df["stochrsi_k"] = stochrsi["STOCHRSIk_14_14_3_3"]
    ticker_df["stochrsi_d"] = stochrsi["STOCHRSId_14_14_3_3"]
    ticker_df["rsi"] = ta.rsi(ticker_df["Close"], length=14 * sma_multiply)
    ticker_df["sma_14"] = ta.sma(ticker_df["Low"], length=14 * sma_multiply)
    ticker_df["sma_50"] = ta.sma(ticker_df["Low"], length=50 * sma_multiply)
    ticker_df["sma_200"] = ta.sma(ticker_df["Low"], length=200 * sma_multiply)

    ticker_df["year"] = (
        ticker_df[ticker_df.columns[0]]
        .apply(lambda x: str(x).split("-")[0])
        .astype("int")
    )

    ticker_df_by_year = ticker_df.groupby("year")
    yearly_increase = {}
    for year, year_df in ticker_df_by_year:
        yearly_increase[year] = get_change(
            year_df.iloc[-1]["High"], year_df.iloc[0]["Low"]
        )

    years = len(yearly_increase.keys())

    start = ticker_df[str(ticker_df.columns[0])].min()
    end = ticker_df[str(ticker_df.columns[0])].max()
    yearly_median_increase = round(
        statistics.median(list(yearly_increase.values())), 2
    )
    total_growth = round(
        get_change(ticker_df.iloc[-1]["High"], ticker_df.iloc[0]["Low"]), 2
    )

    yearly_avg_increase = round((total_growth / years), 2)

    # VISUALS
    if True:
        # reduce visuals to last 5 years
        ticker_df = ticker_df[ticker_df["year"] >= (currentyear - 5)].copy()
        yearly_increase = {
            k: yearly_increase[k]
            for k in yearly_increase.keys()
            if k >= (currentyear - 5)
        }

        # build figure
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True)

        fig.add_trace(
            go.Candlestick(
                x=ticker_df[ticker_df.columns[0]],
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
                    x=ticker_df[ticker_df.columns[0]],
                    y=ticker_df[f"sma_{sma[0]}"],
                    mode="lines",
                    line=go.scatter.Line(color=sma[1]),
                    showlegend=True,
                    name=f"sma_{sma[0]}",
                ),
                row=1,
                col=1,
            )

        fig.add_trace(
            go.Scatter(
                x=ticker_df[ticker_df.columns[0]],
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
                x=ticker_df[ticker_df.columns[0]],
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
                x=ticker_df[ticker_df.columns[0]],
                y=ticker_df["rsi"],
                mode="lines",
                line=go.scatter.Line(color="yellow"),
                showlegend=True,
                name="rsi",
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=list(yearly_increase.keys()),
                y=list(yearly_increase.values()),
                mode="lines",
                line=go.scatter.Line(color="yellow"),
                showlegend=True,
                name="rsi",
            ),
            row=3,
            col=1,
        )

        stock_title = f"{ticker} ({start} - {end}) - median/year: {yearly_median_increase}% / avg/year: {yearly_avg_increase}% / total {total_growth}% / in {years} years"

        fig.update_layout(
            title_text=stock_title,
            xaxis_rangeslider_visible=False,
            autosize=True,
            width=1800,
            height=900,
            template="plotly_dark",
        )
        # fig.show()
        # fig.write_html(f"plots/{ticker}.html")
        fig.write_image(f"plots/{ticker}.pdf")

        # reduce calls to Yahoo api
        time.sleep(1)

pdfs = glob(os.path.join("plots", "*.pdf"))

merger = PdfMerger()

for pdf in pdfs:
    merger.append(pdf)

merger.write("result.pdf")
merger.close()
# %%
