# 🍎 Mac Trading Academy PRO – Plateforme TradingView Complète
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Configuration
st.set_page_config(page_title="Mac Trading Academy PRO", page_icon="🎯", layout="wide")
st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0e0e0e 0%, #1a1a1a 100%);}
    .trading-header {background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
                     padding: 20px; border-radius: 15px; margin-bottom: 30px;
                     box-shadow: 0 8px 32px rgba(0,0,0,.3);}
</style>""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
st.sidebar.header("⚙️ Configuration Trading")

# Dictionnaire des indices (symboles valides)
INDICES = {
    'NASDAQ Composite': '^IXIC',
    'S&P 500': '^GSPC',
    'FTSE 100 (Londres)': '^FTSE',
    'Nikkei 225 (Tokyo)': '^N225',
    'CAC 40 (Paris)': '^FCHI',
    'DAX (Francfort)': '^GDAXI',
    'Bitcoin': 'BTC-USD',
    'Euro/USD': 'EURUSD=X'
}

# Sélection de l'indice
market_name = st.sidebar.selectbox("📈 Choisir l'indice", list(INDICES.keys()))
symbol = INDICES[market_name]

# PÉRIODE & TIMEFRAME (défini AVANT l'utilisation)
days = st.sidebar.slider("📅 Période historique (jours)", 5, 730, 90)
tf = st.sidebar.selectbox("⏰ Timeframe", ['1d', '1h', '15m', '5m', '1m'], index=0)

# ==================== FETCH DATA ====================
@st.cache_data(show_spinner=False)
def download_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            # Fallback si le symbole avec ^ ne marche pas
            df = yf.download(ticker.replace('^', ''), period=period, interval=interval, progress=False)
        return df
    except Exception as e:
        st.error(f"❌ Erreur téléchargement {ticker}: {e}")
        return pd.DataFrame()

# TÉLÉCHARGEMENT DES DONNÉES
data = download_data(symbol, f"{days}d", tf)

# ==================== VÉRIFICATION DONNÉES ====================
if data.empty or len(data) < 10:
    st.error(f"❌ Aucune donnée valide pour {symbol}. Essayez un autre indice.")
    st.info("💡 Symboles valides: ^IXIC, ^GSPC, ^FTSE, ^N225, ^FCHI, ^GDAXI, BTC-USD, EURUSD=X")
    st.stop()

# ==================== DASHBOARD PRINCIPAL ====================
st.markdown(f"<div class='trading-header'><h1 style='text-align:center;'>{market_name}</h1></div>", 
            unsafe_allow_html=True)

# Métriques
current = float(data.Close.iloc[-1])
change = float(data.Close.pct_change().iloc[-1] * 100)
volume = int(data.Volume.iloc[-1])

col1, col2, col3 = st.columns(3)
col1.metric("💰 Prix actuel", f"${current:,.2f}")
col2.metric("📊 Change 24h", f"{change:+.2f}%", delta=f"{change:+.2f}%")
col3.metric("📈 Volume", f"{volume:,}")

# ==================== GRAPHIQUE PRINCIPAL ====================
st.subheader("📊 Graphique Principal")

# Indicateurs
delta = data.Close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rsi = 100 - (100 / (1 + gain / loss))
ma20 = data.Close.rolling(20).mean()
ma50 = data.Close.rolling(50).mean()

fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
    row_heights=[0.6, 0.2, 0.2],
    subplot_titles=('Prix & Moyennes Mobiles', 'Volume', 'RSI (14)')
)

# Chandeliers
fig.add_trace(go.Candlestick(
    x=data.index, open=data.Open, high=data.High, low=data.Low, close=data.Close,
    name='Candlesticks', increasing_line_color='#00d084', decreasing_line_color='#ff4757'
), row=1, col=1)

# MA
fig.add_trace(go.Scatter(x=data.index, y=ma20, name='MA 20', line=dict(color='#ff6b6b', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=ma50, name='MA 50', line=dict(color='#4ecdc4', width=2)), row=1, col=1)

# Volume
close_vals = data.Close.values
colors = ['#00d084' if close_vals[i] > close_vals[i-1] else '#ff4757' for i in range(1, len(close_vals))]
colors.insert(0, '#00d084')
fig.add_trace(go.Bar(x=data.index, y=data.Volume, name='Volume', marker_color=colors, opacity=0.7), row=2, col=1)

# RSI
fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='#9b59b6')), row=3, col=1)
fig.add_hline(y=70, line_dash='dash', line_color='#ff4757', row=3, col=1)
fig.add_hline(y=30, line_dash='dash', line_color='#00d084', row=3, col=1)

fig.update_layout(
    height=800, template='plotly_dark', title=f'{market_name} - {tf}',
    xaxis_rangeslider_visible=False, hovermode='x unified'
)

# RENDU FIXÉ
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True})

# ==================== ANALYSE GLOBALE 24H ====================
st.subheader("🌍 Analyse 24H – Corrélation Marchés")

# Récupération des 3 indices clés
asia = download_data('^N225', '5d', '1d')
europe = download_data('^FTSE', '5d', '1d')
usa = download_data('^IXIC', '5d', '1d')

col_a, col_e, col_u = st.columns(3)

with col_a:
    st.markdown("### 🌏 Asie (Nikkei)")
    if not asia.empty:
        ret_asia = float((asia.Close.iloc[-1] / asia.Close.iloc[0] - 1) * 100)
        st.metric("Performance 5j", f"{ret_asia:+.2f}%", delta=f"{ret_asia:+.2f}%")

with col_e:
    st.markdown("### 🇪🇺 Europe (FTSE)")
    if not europe.empty:
        ret_eur = float((europe.Close.iloc[-1] / europe.Close.iloc[0] - 1) * 100)
        st.metric("Performance 5j", f"{ret_eur:+.2f}%", delta=f"{ret_eur:+.2f}%")

with col_u:
    st.markdown("### 🇺🇸 Amérique (NASDAQ)")
    if not usa.empty:
        ret_usa = float((usa.Close.iloc[-1] / usa.Close.iloc[0] - 1) * 100)
        st.metric("Performance 5j", f"{ret_usa:+.2f}%", delta=f"{ret_usa:+.2f}%")

# ==================== HORAIRES MARCHÉS ====================
st.subheader("🕐 Heures d'Ouverture des Marchés (Temps Réel)")
now = datetime.now(pytz.UTC)

markets_info = {
    'Tokyo (Nikkei)': {'tz': 'Asia/Tokyo', 'open': '09:00', 'close': '15:00'},
    'Londres (FTSE)': {'tz': 'Europe/London', 'open': '08:00', 'close': '16:30'},
    'New York (NASDAQ)': {'tz': 'US/Eastern', 'open': '09:30', 'close': '16:00'}
}

for market_name, info in markets_info.items():
    tz = pytz.timezone(info['tz'])
    local_time = now.astimezone(tz).time()
    open_t = pd.to_datetime(info['open']).time()
    close_t = pd.to_datetime(info['close']).time()
    is_open = open_t <= local_time <= close_t
    st.metric(market_name, "🟢 OUVERT" if is_open else "🔴 FERMÉ", 
             f"{info['open']} - {info['close']}")

# ==================== PAPER TRADING ====================
st.sidebar.subheader("🧪 Paper Trading")
qty = st.sidebar.number_input("Quantité (actions)", 1, 1000, 100)
if st.sidebar.button("Acheter"):
    st.sidebar.success(f"➕ Achat {qty} × {symbol} @ ${current:,.2f}")
if st.sidebar.button("Vendre"):
    st.sidebar.success(f"➖ Vente {qty} × {symbol} @ ${current:,.2f}")

# ==================== BACKTEST ====================
st.sidebar.subheader("📈 Backtest Simple")
fast = st.sidebar.slider("MA Rapide", 5, 50, 20)
slow = st.sidebar.slider("MA Lente", 20, 200, 50)
if st.sidebar.button("Lancer Backtest"):
    if len(data) < slow:
        st.sidebar.error("❌ Pas assez de données pour cette période")
    else:
        sma_f = data.Close.rolling(fast).mean()
        sma_s = data.Close.rolling(slow).mean()
        signal = np.where(sma_f > sma_s, 1, 0)
        ret = signal[1:] * data.Close.pct_change()[1:]
        cret = (1 + ret).cumprod()
        final_ret = float((cret.iloc[-1] - 1) * 100)
        st.sidebar.success(f"📊 Retour total MA-{fast}/MA-{slow}: **{final_ret:+.2f}%**")
