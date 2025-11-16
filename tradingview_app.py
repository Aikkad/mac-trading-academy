# ÉTAPE 1 DEBUG - VÉRIFICATION DES DONNÉES UNIQUEMENT
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="DEBUG - Data Check", layout="wide")
st.title("🔍 ÉTAPE 1 : Vérification des données brutes")

# Dictionnaire des symboles testés et VALIDÉS
INDICES_VAL = {
    'NASDAQ Composite': '^IXIC',
    'S&P 500': '^GSPC',
    'FTSE 100': '^FTSE',
    'Nikkei 225': '^N225',
    'CAC 40': '^FCHI',
    'DAX': '^GDAXI',
    'Bitcoin': 'BTC-USD',
    'Euro/USD': 'EURUSD=X'
}

# Menu simple
selected = st.selectbox("Sélectionnez un indice à tester", list(INDICES_VAL.keys()))
symbol = INDICES_VAL[selected]

# Téléchargement
st.subheader(f"Téléchargement de : **{selected}**")
st.code(f"Symbole envoyé à yfinance : {symbol}")

with st.spinner('Téléchargement en cours...'):
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
        st.success("✅ Téléchargement réussi !")
    except Exception as e:
        st.error(f"❌ ERREUR : {e}")
        df = pd.DataFrame()

# Affichage des résultats
if df.empty:
    st.warning("⚠️ DataFrame VIDE - Aucune donnée reçue")
else:
    st.info(f"📊 Données reçues : **{len(df)} lignes** × **{len(df.columns)} colonnes**")
    
    # Vérifie les colonnes
    st.subheader("Colonnes disponibles")
    st.write(df.columns.tolist())
    
    # Affiche les premières lignes
    st.subheader("5 premières lignes")
    st.dataframe(df.head())
    
    # Stats basiques
    st.subheader("Statistiques")
    st.write(df.describe())

# Bouton de diagnostic
if st.button("🧪 Tester TOUS les symboles"):
    results = {}
    for name, sym in INDICES_VAL.items():
        try:
            test_df = yf.download(sym, period="5d", interval="1d", progress=False)
            results[name] = "✅ OK" if not test_df.empty else "❌ Vide"
        except:
            results[name] = "❌ Erreur"
    
    st.write("Résultats du test :")
    for k, v in results.items():
        st.write(f"{k}: {v}")
