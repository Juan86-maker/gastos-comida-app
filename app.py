import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Archivo donde se guardarán los gastos
FILE_PATH = "gastos.csv"

# Crear el archivo si no existe
if not os.path.exists(FILE_PATH):
    df = pd.DataFrame(columns=["Fecha", "Monto", "Lugar", "Metodo"])
    df.to_csv(FILE_PATH, index=False)

# Cargar datos existentes
df = pd.read_csv(FILE_PATH)

st.title("📊 Registro de Gastos de Comida")

# --- Formulario para ingresar un gasto ---
with st.form("nuevo_gasto"):
    monto = st.number_input("Monto (€)", min_value=0.0, step=0.5, format="%.2f")
    lugar = st.text_input("Lugar de compra (opcional)")
    metodo = st.selectbox("Método de pago", ["Tarjeta", "Efectivo"])
    submitted = st.form_submit_button("Agregar gasto")

    if submitted:
        nueva_fila = {
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Monto": monto,
            "Lugar": lugar,
            "Metodo": metodo
        }
        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        df.to_csv(FILE_PATH, index=False)
        st.success("✅ Gasto agregado correctamente")

# --- Mostrar resumen ---
st.subheader("📅 Últimos gastos")
st.dataframe(df.tail(10))

total_mes = df[df["Fecha"].str.startswith(datetime.now().strftime("%Y-%m"))]["Monto"].sum()
st.metric("💰 Total gastado este mes", f"{total_mes:.2f} €")

# --- Gráfico por método de pago ---
if not df.empty:
    st.subheader("📊 Gastos por método de pago")
    st.bar_chart(df.groupby("Metodo")["Monto"].sum())
