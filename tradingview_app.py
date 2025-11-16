# tradingview_app.py
# 🍎 Mac Trading Academy PRO – plate-forme entraînement TradingView
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Mac Trading Academy PRO", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0e0e0e 0%, #1a1a1a 100%);}
    h1,h2,h3{color:#fff}
</style>""", unsafe_allow_html=True)

st.title("🍎 Mac Trading Academy PRO – TradingView-like")

# ---------- sidebar ----------
ticker = st.sidebar.text_input("Symbole", "AAPL").upper()
tf     = st.sidebar.selectbox("Timeframe", ['1m','5m','15m','1h','1d','1W','1M'], index=4)
days   = st.sidebar.slider("Nb jours historique", 5, 365, 30)
capital = st.sidebar.number_input("Capital paper-trading", 1000, 100000, 10000)

# ---------- data ----------
@st.cache_data(show_spinner=False)
def fetch(ticker, period, interval):
    return yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)

data = fetch(ticker, f"{days}d", tf)
if data.empty:
    st.stop()

current = float(data.Close.iloc[-1])
change  = float(data.Close.pct_change().iloc[-1] * 100)
volume  = int(data.Volume.iloc[-1])
delta   = data.Close.diff()
gain    = delta.where(delta>0,0).rolling(14).mean()
loss    = (-delta.where(delta<0,0)).rolling(14).mean()
rsi     = float((100 - (100 / (1 + gain/loss))).iloc[-1])

# ---------- metrics ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Prix", f"${current:.2f}")
col2.metric("24 h", f"{change:.2f} %")
col3.metric("Volume", f"{volume:,}")
col4.metric("RSI", f"{rsi:.1f}")

# ---------- chart ----------
fig = make_subplots(rows=3,cols=1,shared_xaxes=True,row_heights=[0.6,0.2,0.2],
                    subplot_titles=('Prix & MA','Volume','RSI'))
fig.add_trace(go.Candlestick(x=data.index,open=data.Open,high=data.High,
                             low=data.Low,close=data.Close,name='Candles'),row=1,col=1)
ma20 = data.Close.rolling(20).mean()
ma50 = data.Close.rolling(50).mean()
fig.add_trace(go.Scatter(x=data.index,y=ma20,name='MA20'),row=1,col=1)
fig.add_trace(go.Scatter(x=data.index,y=ma50,name='MA50'),row=1,col=1)

close_v = data.Close.values
colors  = ['green' if close_v[i] > close_v[i-1] else 'red' for i in range(1,len(close_v))]
colors.insert(0,'green')
fig.add_trace(go.Bar(x=data.index,y=data.Volume,name='Volume',marker_color=colors),row=2,col=1)

fig.add_trace(go.Scatter(x=data.index,y=100-(100/(1+gain/loss)),name='RSI'),row=3,col=1)
fig.add_hline(y=70,line_dash='dash',line_color='red',row=3,col=1)
fig.add_hline(y=30,line_dash='dash',line_color='green',row=3,col=1)
fig.update_layout(height=700,template='plotly_dark',title=f'{ticker} – {tf}')
st.plotly_chart(fig, use_container_width=True)

# ---------- paper trading ----------
st.sidebar.subheader("🧪 Paper trading")
qty = st.sidebar.number_input("Quantité", 1, 100, 10)
if st.sidebar.button("Acheter"):
    st.sidebar.success(f"Achat {qty} × {ticker} @ ${current:.2f}")
if st.sidebar.button("Vendre"):
    st.sidebar.success(f"Vente {qty} × {ticker} @ ${current:.2f}")

# ---------- quick backtest ----------
st.sidebar.subheader("📈 Backtest MA cross")
fast = st.sidebar.slider("MA rapide", 5, 50, 20)
slow = st.sidebar.slider("MA lente", 10, 200, 50)
if st.sidebar.button("Lancer backtest"):
    if len(data) < slow:
        st.sidebar.warning("Pas assez de données")
    else:
        sma_f = data.Close.rolling(fast).mean()
        sma_s = data.Close.rolling(slow).mean()
        signal = np.where(sma_f > sma_s, 1, 0)
        ret = signal[1:] * data.Close.pct_change()[1:]
        cret = (1 + ret).cumprod()
        st.sidebar.write(f"Retour total MA-{fast}/MA-{slow} : **{float((cret.iloc[-1]-1)*100):.2f} %**")