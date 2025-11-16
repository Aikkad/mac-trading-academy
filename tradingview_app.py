# tradingview_app.py – version corrigée et debuggée
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Config
st.set_page_config(page_title="Mac Trading Academy PRO", page_icon="🎯", layout="wide")

# Titre
st.title("🍎 Mac Trading Academy PRO – TradingView-like")

# Sidebar
st.sidebar.header("⚙️ Paramètres")
ticker = st.sidebar.text_input("Symbole", "AAPL").upper()
tf = st.sidebar.selectbox("Timeframe", ['1d', '1h', '15m', '5m', '1m'], index=0)
days = st.sidebar.slider("Nb jours historique", 5, 365, 30)

# Données
@st.cache_data(show_spinner=False)
def fetch(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        return df
    except Exception as e:
        st.error(f"Erreur téléchargement : {e}")
        return pd.DataFrame()

data = fetch(ticker, f"{days}d", tf)

# Debug : afficher si les données sont vides
if data.empty:
    st.warning("⚠️ Aucune donnée reçue. Vérifie le symbole (ex: AAPL, BTC-USD, EURUSD=X)")
    st.stop()

# Métriques
current = float(data.Close.iloc[-1])
change = float(data.Close.pct_change().iloc[-1] * 100)
volume = int(data.Volume.iloc[-1])
delta = data.Close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rsi = float((100 - (100 / (1 + gain / loss))).iloc[-1])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Prix", f"${current:.2f}")
col2.metric("24h", f"{change:.2f}%")
col3.metric("Volume", f"{volume:,}")
col4.metric("RSI", f"{rsi:.1f}")

# Graphique
st.subheader(f"📊 Graphique {ticker} – {tf}")

try:
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Prix & MA', 'Volume', 'RSI')
    )
    
    fig.add_trace(go.Candlestick(
        x=data.index, open=data.Open, high=data.High, low=data.Low, close=data.Close,
        name='Candles', increasing_line_color='#00d084', decreasing_line_color='#ff4757'
    ), row=1, col=1)
    
    ma20 = data.Close.rolling(20).mean()
    ma50 = data.Close.rolling(50).mean()
    fig.add_trace(go.Scatter(x=data.index, y=ma20, name='MA20', line=dict(color='#ff6b6b')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=ma50, name='MA50', line=dict(color='#4ecdc4')), row=1, col=1)
    
    close_vals = data.Close.values
    colors = ['#00d084' if close_vals[i] > close_vals[i-1] else '#ff4757' for i in range(1, len(close_vals))]
    colors.insert(0, '#00d084')
    fig.add_trace(go.Bar(x=data.index, y=data.Volume, name='Volume', marker_color=colors), row=2, col=1)
    
    fig.add_trace(go.Scatter(x=data.index, y=100-(100/(1+gain/loss)), name='RSI', line=dict(color='#9b59b6')), row=3, col=1)
    fig.add_hline(y=70, line_dash='dash', line_color='#ff4757', row=3, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='#00d084', row=3, col=1)
    
    fig.update_layout(height=700, template='plotly_dark', xaxis_rangeslider_visible=False)
    
    # Affichage avec fallback
    st.plotly_chart(fig, use_container_width=True, key="chart")
    st.success("✅ Graphique rendu avec succès")
    
except Exception as e:
    st.error(f"❌ Erreur lors du rendu du graphique : {e}")
    st.write("Données :", data.head())  # Debug

# Paper trading
st.sidebar.subheader("🧪 Paper Trading")
qty = st.sidebar.number_input("Quantité", 1, 100, 10)
if st.sidebar.button("Acheter"):
    st.sidebar.success(f"Achat {qty} × {ticker} @ ${current:.2f}")
if st.sidebar.button("Vendre"):
    st.sidebar.success(f"Vente {qty} × {ticker} @ ${current:.2f}")

# Backtest
st.sidebar.subheader("📈 Backtest MA Cross")
fast = st.sidebar.slider("MA rapide", 5, 50, 20)
slow = st.sidebar.slider("MA lente", 10, 200, 50)
if st.sidebar.button("Lancer Backtest"):
    if len(data) < slow:
        st.sidebar.warning("Pas assez de données")
    else:
        sma_f = data.Close.rolling(fast).mean()
        sma_s = data.Close.rolling(slow).mean()
        signal = np.where(sma_f > sma_s, 1, 0)
        ret = signal[1:] * data.Close.pct_change()[1:]
        cret = (1 + ret).cumprod()
        st.sidebar.write(f"Retour MA-{fast}/MA-{slow} : **{float((cret.iloc[-1]-1)*100):.2f}%**")
