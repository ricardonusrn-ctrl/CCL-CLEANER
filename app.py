import streamlit as st
import lasio
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="CCL Cleaner", layout="wide")

st.title("🛠️ Limpieza Inteligente de Curva CCL (.LAS)")
st.write("Corrige valores fuera de rango manteniendo la forma original de la curva.")

# 1. Cargar archivo LAS
archivo = st.file_uploader("Sube tu archivo LAS", type=["las"])

if archivo:
    las = lasio.read(archivo)
    df = las.df()

    # Identificar curva CCL
    ccl_column = None
    for col in df.columns:
        if "CCL" in col.upper():
            ccl_column = col
            break

    if not ccl_column:
        st.error("❌ No se encontró curva CCL en el archivo.")
        st.stop()

    st.success(f"Curva CCL detectada: **{ccl_column}**")

    # Valores mínimo y máximo actuales
    val_min = float(df[ccl_column].min())
    val_max = float(df[ccl_column].max())

    st.subheader("⚙️ Ajustar Cut-offs")
    cut_min = st.slider("Cut-off inferior", min_value=val_min, max_value=val_max, value=val_min)
    cut_max = st.slider("Cut-off superior", min_value=val_min, max_value=val_max, value=val_max)

    if cut_min > cut_max:
        st.error("El cut-off inferior no puede ser mayor al superior.")
        st.stop()

    # Copias para graficar
    original_curve = df[ccl_column].copy()

    # Corrección
    def corr(x):
        if x > cut_max:
            return cut_max
        elif x < cut_min:
            return cut_min
        return x

    df[ccl_column] = df[ccl_column].apply(corr)

    # Actualizar curvas en LAS
    for curve in las.curves:
        if curve.mnemonic in df.columns:
            curve.data = df[curve.mnemonic].values

    # Gráfica antes vs después
    st.subheader("📈 Gráfica Antes vs Después")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(original_curve, label="Original", alpha=0.6)
    ax.plot(df[ccl_column], label="Corregida", alpha=0.9)
    ax.set_xlabel("Índice (profundidad)")
    ax.set_ylabel("CCL")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Preparar archivo para descarga
    output = io.StringIO()
    las.write(output, version=2.0)
    output_bytes = output.getvalue().encode("utf-8")

    st.download_button(
        label="⬇️ Descargar LAS corregido (mismo nombre)",
        data=output_bytes,
        file_name=archivo.name,
        mime="application/octet-stream"
    )

