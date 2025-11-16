# ÉTAPE 1 DEBUG CORRIGÉ - AVEC USER-AGENT
import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="DEBUG - Data Check", layout="wide")
st.title("🔍 ÉTAPE 1 : Vérification des données avec User-Agent")

# Dictionnaire des symboles
INDICES_VAL = {
    'APPLE TEST': 'AAPL',
    'NASDAQ Composite': '^IXIC',
    'S&P 500': '^GSPC',
    'FTSE 100': '^FTSE',
    'Nikkei 225': '^N225',
    'CAC 40': '^FCHI',
    'DAX': '^GDAXI',
    'Bitcoin': 'BTC-USD'
}

selected = st.selectbox("Sélectionnez un symbole", list(INDICES_VAL.keys()))
symbol = INDICES_VAL[selected]

# ★★★ LA FONCTION QUI RÉSOLUT LE BLOCAGE ★★★
@st.cache_data(show_spinner=False)
def download_data(ticker, period="5d", interval="1d"):
    """
    FORCER USER-AGENT pour passer le blocage Streamlit Cloud
    """
    try:
        # Crée une session avec User-Agent
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Méthode 1 : via Ticker avec session
        ticker_obj = yf.Ticker(ticker, session=session)
        df = ticker_obj.history(period=period, interval=interval, timeout=30)
        
        # Méthode 2 : fallback si vide
        if df.empty:
            st.warning("Méthode 1 vide, tentative fallback...")
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        
        return df
        
    except Exception as e:
        st.error(f"❌ ERREUR CRITIQUE: {e}")
        return pd.DataFrame()

# Téléchargement
st.subheader(f"Téléchargement de : **{selected}** (`{symbol}`)")
with st.spinner('Téléchargement...'):
    df = download_data(symbol)

# Affichage
if df.empty:
    st.warning("⚠️ DataFrame VIDE")
else:
    st.success(f"✅ Données reçues: {len(df)} lignes")
    st.dataframe(df.head())
    st.write("Colonnes:", df.columns.tolist())

# Bouton test global
if st.button("🧪 Tester TOUS les symboles"):
    results = {}
    for name, sym in INDICES_VAL.items():
        test_df = download_data(sym)
        results[name] = "✅ OK" if not test_df.empty else "❌ Vide"
    
    st.write("Résultats:")
    for k, v in results.items():
        st.write(f"{k}: {v}")
