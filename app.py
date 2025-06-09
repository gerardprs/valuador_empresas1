import streamlit as st
import yfinance as yf
import pandas as pd
from math import isnan

st.set_page_config(page_title="Valorizador de Empresas", layout="centered")

st.title("📈 Valorizador Automatizado de Empresas")
st.write(
    """Ingresa el **ticker** (símbolo bursátil) de la empresa que quieras valorar
    —p. ej. AAPL, MSFT, GOOG— y pulsa *Valorar*.
    La app descarga datos financieros públicos con **yfinance** y calcula rápidamente
    un valor implícito usando múltiplos básicos (P/E, P/B, P/S)."""
)

ticker = st.text_input("Ticker:", value="AAPL", max_chars=10).upper()

if st.button("Valorar"):
    try:
        data = yf.Ticker(ticker)
        info = data.info

        # -------- múltiplos --------
        pe, pb, ps = info.get("trailingPE"), info.get("priceToBook"), info.get("priceToSalesTrailing12Months")
        price = info.get("currentPrice")

        eps   = info.get("trailingEps")
        bvps  = info.get("bookValue")
        sales = info.get("totalRevenue")
        sh_out= info.get("sharesOutstanding", 1)
        spu   = sales / sh_out            # sales-per-share

        valores = []
        if pe and eps and not isnan(pe)  and not isnan(eps):  valores.append(pe * eps)
        if pb and bvps and not isnan(pb) and not isnan(bvps): valores.append(pb * bvps)
        if ps and spu and not isnan(ps)  and not isnan(spu):  valores.append(ps * spu)

        if valores and price:
            objetivo = sum(valores) / len(valores)
            upside   = (objetivo / price - 1) * 100

            st.subheader("📝 Resultado")
            st.metric("Precio actual (USD)", f"{price:,.2f}")
            st.metric("Valor implícito (USD)", f"{objetivo:,.2f}",
                      delta=f"{upside:+.1f}%")

            hist = data.history(period="5y")["Close"]
            st.line_chart(hist)

            detalle = pd.DataFrame({
                "Múltiplo": ["P/E", "P/B", "P/S"],
                "Valor (USD)": valores + [None]*(3-len(valores))
            })
            st.table(detalle)

        else:
            st.warning("No existen datos suficientes para ese ticker.")
    except Exception as e:
        st.error(f"Ocurrió un error con {ticker}: {e}")
