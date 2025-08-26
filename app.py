import streamlit as st
import pandas as pd
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gastos de Comida", page_icon="🍎")

# --------- Conexión a Google Sheets ----------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
gc = gspread.authorize(creds)

SHEET_ID = st.secrets["default"]["SPREADSHEET_ID"]
WS_NAME = st.secrets.get("WORKSHEET_NAME", "Gastos")

sh = gc.open_by_key(SHEET_ID)
try:
    ws = sh.worksheet(WS_NAME)
except gspread.exceptions.WorksheetNotFound:
    ws = sh.add_worksheet(title=WS_NAME, rows=1000, cols=10)
    ws.update("A1:D1", [["Fecha", "Monto", "Lugar", "Metodo"]])

# --------- Funciones de datos ----------
def load_df():
    rows = ws.get_all_records()  # requiere encabezados en la fila 1
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Fecha", "Monto", "Lugar", "Metodo"])
    # Tipos
    if "Monto" in df.columns:
        df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0).round(2)
    if "Fecha" in df.columns:
        # Intentar convertir a datetime
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df

def append_row(fecha, monto, lugar, metodo):
    ws.append_row(
        [fecha, float(monto) if monto else 0.0, lugar, metodo],
        value_input_option="RAW",  # RAW mantiene el número como tal
    )

# --------- UI ----------
st.title("📊 Registro de Gastos de Comida (Google Sheets)")
st.caption("Multiusuario y persistente en la nube")

with st.form("nuevo_gasto"):
    monto = st.number_input("Monto (€)", min_value=0.0, step=0.5, format="%.2f")
    lugar = st.text_input("Lugar de compra (opcional)")
    metodo = st.selectbox("Método de pago", ["Tarjeta", "Efectivo"])
    submitted = st.form_submit_button("Agregar gasto")

    if submitted:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_row(fecha, monto, lugar, metodo)
        st.success("✅ Gasto agregado correctamente")

# Recargar datos después de posibles inserciones
HEADERS = ["Fecha", "Monto", "Lugar", "Metodo"]

def load_df():
    try:
        # Verificar si hay encabezados válidos
        headers = ws.row_values(1)
        if headers != HEADERS:
            ws.update("A1:D1", [HEADERS])

        rows = ws.get_all_records(expected_headers=HEADERS)
        df = pd.DataFrame(rows)

        if df.empty:
            df = pd.DataFrame(columns=HEADERS)

    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        df = pd.DataFrame(columns=HEADERS)

    # Convertir tipos
    if "Monto" in df.columns:
        df["Monto"] = (
            df["Monto"]
            .astype(str)
            .str.replace(",", ".", regex=False)  # 👈 arregla 0,15 → 0.15
        )
        df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0).round(2)
    
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")


    return df


df = load_df()
# st.write("DEBUG → tipo df:", type(df))  # 👈 esta línea es opcional, solo para ver
rows = ws.get_all_values()
st.write(rows[:5])  # ver qué trae exactamente


st.subheader("📅 Últimos gastos")

if isinstance(df, pd.DataFrame) and not df.empty:
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.info("Aún no hay gastos registrados.")


# Métrica mensual
if not df.empty and "Fecha" in df.columns:
    ahora = pd.Timestamp.now()
    mask_mes = (df["Fecha"].dt.year == ahora.year) & (df["Fecha"].dt.month == ahora.month)
    total_mes = df.loc[mask_mes, "Monto"].sum()
else:
    total_mes = 0.0

st.metric("💰 Total gastado este mes", f"{total_mes:.2f} €")

# Gráfico por método de pago
if not df.empty:
    st.subheader("📊 Gastos por método de pago")
    agrup = df.groupby("Metodo", dropna=False)["Monto"].sum()
    st.bar_chart(agrup)
