import streamlit as st
import finnhub, pandas as pd
from datetime import datetime

# ------------------ TU CLAVE FINNHUB ------------------
FINN_KEY = "d13asghr01qv1k0pjqa0d13asghr01qv1k0pjqag"
client = finnhub.Client(api_key=FINN_KEY)
# ------------------------------------------------------

# -------- helper caché --------
@st.cache_data(ttl=86400)  # 24 h por ticker
def get_data(tk: str):
    profile = client.company_profile2(symbol=tk)
    if not profile:
        raise ValueError("Ticker no encontrado.")

    funda   = client.company_basic_financials(symbol=tk, metric="all")["metric"]
    quote   = client.quote(tk)

    # histórico 1 año (candle diario)
    now, year = int(datetime.utcnow().timestamp()), 365 * 24 * 3600
    candles = client.stock_candles(tk, "D", now - year, now)
    hist = pd.Series(candles["c"],
                     index=pd.to_datetime(candles["t"], unit="s"))

    def _safe(key):
        v = funda.get(key)
        return None if v in (None, "None", "") else float(v)

    return dict(
        price=quote["c"],
        pe=_safe("peBasicExclExtraTTM"),
        pb=_safe("pbQuarterly"),
        ps=_safe("psTTM"),
        eps=_safe("epsExclExtraItemsTTM"),
        bv=_safe("bookValuePerShareQuarterly"),
        sps=_safe("revenuePerShareTTM"),
        hist=hist
    )

# ------------- UI -------------
st.set_page_config(page_title="Valorizador Finnhub", layout="centered")
st.title("📈 Valorizador Automatizado de Empresas (Finnhub)")

st.write(
    "Introduce el símbolo bursátil (ej.: **AAPL**, **MSFT**, **TSLA**) y pulsa "
    "**Valorar**. Se calculan múltiplos P/E, P/B y P/S con datos de Finnhub."
)

ticker = st.text_input("Ticker:", value="AAPL", max_chars=8).upper()

if st.button("Valorar"):
    try:
        m = get_data(ticker)

        # ------ valoración por múltiplos ------
        vals = []
        if m["pe"] and m["eps"]: vals.append(m["pe"] * m["eps"])
        if m["pb"] and m["bv"]:  vals.append(m["pb"] * m["bv"])
        if m["ps"] and m["sps"]: vals.append(m["ps"] * m["sps"])

        if not vals:
            st.warning("No hay suficientes métricas para este ticker."); st.stop()

        target = sum(vals) / len(vals)
        upside = (target / m["price"] - 1) * 100

        # --------- salida ---------
        st.metric("Precio actual (USD)", f"{m['price']:,.2f}")
        st.metric("Valor implícito (USD)", f"{target:,.2f}",
                  delta=f"{upside:+.1f}%")

        st.line_chart(m["hist"])

        st.table(pd.DataFrame({
            "Múltiplo": ["P/E", "P/B", "P/S"],
            "Valor (USD)": vals + [None] * (3 - len(vals))
        }))

    except Exception as e:
        st.error(f"Error al valorar {ticker}: {e}")
