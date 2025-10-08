import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- FUNCIONS ---
@st.cache_data
def load_data():
    files = [
        "Barems_Fluencies_Verbal_Global_18-94.xlsx",
        "Barems_BNT_Global_18-94.xlsx",
        "Barems_WMSIII_Subtests_Completo_16-89.xlsx",
        "Barems_WMSIII_Indices_Completo_16-89.xlsx",
        "Barems_RAVLT_16-95.xlsx",
        "Barems_WAISIII_Subtests_16-89.xlsx",
        "Barems_WAISIII_Indexs_16-89.xlsx",
        "Barems_TMT_A_B_18-94.xlsx",
        "Barems_SDMT_18-94.xlsx",
        "Barems_ROCF_18-49.xlsx",
        "Barems_FCSRT_18-49.xlsx"
    ]

    dataframes = []
    for file in files:
        try:
            df = pd.read_excel(file)
            dataframes.append(df)
        except Exception as e:
            st.warning(f"No s'ha pogut carregar {file}: {e}")
    return pd.concat(dataframes, ignore_index=True)

def match_interval(value, rule):
    try:
        rule = str(rule)
        if "-" in rule:
            low, high = map(float, rule.replace("–", "-").split("-"))
            return low <= value <= high
        elif ">=" in rule:
            val = float(rule.replace(">=", ""))
            return value >= val
        elif "<=" in rule:
            val = float(rule.replace("<=", ""))
            return value <= val
        elif "<" in rule:
            val = float(rule.replace("<", ""))
            return value < val
        elif ">" in rule:
            val = float(rule.replace(">", ""))
            return value > val
        else:
            return float(rule) == value
    except:
        return False

def interpretar_percentil(percentil_str):
    try:
        if "-" in str(percentil_str):
            low, high = map(int, percentil_str.split("-"))
            percentil = (low + high) / 2
        elif "<" in str(percentil_str):
            percentil = int(percentil_str.replace("<", "")) - 1
        elif ">" in str(percentil_str):
            percentil = int(percentil_str.replace(">", "")) + 1
        else:
            percentil = int(percentil_str)
    except:
        return "No interpretable"

    if percentil < 5:
        return "Patològic"
    elif percentil < 16:
        return "Límit / Baix"
    elif percentil < 85:
        return "Normal"
    elif percentil < 95:
        return "Normal-alt"
    else:
        return "Alt / Superior"

def generar_informe_pdf(dades):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 80, "Informe de Resultats Neuropsicològics")

    c.setFont("Helvetica", 11)
    y = height - 130
    for key, value in dades.items():
        c.drawString(80, y, f"{key}: {value}")
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFÍCIE STREAMLIT ---
df = load_data()

st.title("🧠 Calculadora Normativa")

# --- SELECCIÓ DE CATEGORIA ---
grans_categories = [
    "Fluències Verbals",
    "Boston Naming Test",
    "WMS-III",
    "RAVLT",
    "WAIS-III",
    "Trail Making Test (TMT)",
    "Symbol Digit Modalities Test (SDMT)",
    "Rey-Osterrieth Complex Figure (ROCF)",
    "Free and Cued Selective Reminding Test (FCSRT)"
]
categoria = st.sidebar.selectbox("Selecciona la categoria", grans_categories)

if categoria == "Fluències Verbals":
    df_cat = df[df["Prova"].str.contains("Fluència", na=False)]
    col_ref = "Versió"
elif categoria == "Boston Naming Test":
    df_cat = df[df["Prova"].str.contains("Boston Naming", na=False)]
    col_ref = "Versió"
elif categoria == "WMS-III":
    df_cat = df[df["Prova"].str.contains("WMS-III", na=False)]
    col_ref = "Subtest" if "Subtest" in df_cat.columns else "Índex"
elif categoria == "RAVLT":
    df_cat = df[df["Prova"].str.contains("RAVLT", na=False)]
    col_ref = "Variable"
elif categoria == "WAIS-III":
    df_cat = df[df["Prova"].str.contains("WAIS-III", na=False)]
    col_ref = "Subtest" if "Subtest" in df_cat.columns else "Índex"
elif categoria == "Trail Making Test (TMT)":
    df_cat = df[df["Prova"].str.contains("TMT", na=False)]
    col_ref = "Versió"
elif categoria == "Symbol Digit Modalities Test (SDMT)":
    df_cat = df[df["Prova"].str.contains("SDMT", na=False)]
    col_ref = "Versió"
elif categoria == "Rey-Osterrieth Complex Figure (ROCF)":
    df_cat = df[df["Prova"].str.contains("ROCF", na=False)]
    col_ref = "Variable"
else:  # FCSRT
    df_cat = df[df["Prova"].str.contains("FCSRT", na=False)]
    col_ref = "Variable"

# --- SELECCIÓ DETALLADA ---
proves = sorted(df_cat["Prova"].unique())
prova = st.selectbox("Selecciona la prova", proves)

versions = sorted(df_cat[df_cat["Prova"] == prova][col_ref].dropna().unique())
versio = st.selectbox(f"Selecciona {col_ref.lower()}", versions)

# --- ENTRADA DE DADES ---
edat = st.number_input("Edat del pacient", min_value=16, max_value=95, value=45)
puntuacio = st.text_input("Puntuació bruta / composta", value="25")

# --- CERCA DE RESULTATS ---
subdf = df_cat[
    (df_cat[col_ref] == versio) &
    (df_cat["Edat_min"] <= edat) &
    (df_cat["Edat_max"] >= edat)
]

resultat = None
for _, row in subdf.iterrows():
    col_punt = "Puntuacio_bruta" if "Puntuacio_bruta" in row else "Puntuacio_composta"
    if match_interval(float(puntuacio), row[col_punt]):
        resultat = row
        break

# --- RESULTATS ---
if resultat is not None:
    st.subheader("📊 Resultats")
    if "Escalar" in resultat:
        st.success(f"Puntuació Escalar: **{resultat['Escalar']}**")
    st.info(f"Percentil: **{resultat['Percentil']}**")
    interpretacio = interpretar_percentil(resultat["Percentil"])
    st.write(f"🧾 Interpretació qualitativa: **{interpretacio}**")

    dades = {
        "Categoria": categoria,
        "Prova": prova,
        col_ref: versio,
        "Edat": edat,
        "Puntuació bruta / composta": puntuacio,
        "Resultat escalar": resultat.get("Escalar", "-"),
        "Percentil": resultat["Percentil"],
        "Interpretació": interpretacio
    }

    st.download_button(
        label="📥 Descarregar informe PDF",
        data=generar_informe_pdf(dades),
        file_name=f"Informe_{prova.replace(' ', '_')}_{edat}anys.pdf",
        mime="application/pdf"
    )

# --- Registrar dades del pacient ---
if resultat is not None:
    registre_id = st.text_input("Número de registre del pacient (ex. NB2025-001)", "")
    if st.button("💾 Guardar registre"):
        dades_pacient = {
            "Registre": registre_id,
            "Categoria": categoria,
            "Prova": prova,
            col_ref: versio,
            "Edat": edat,
            "Puntuació": puntuacio,
            "Escalar": resultat.get("Escalar", "-"),
            "Percentil": resultat["Percentil"],
            "Interpretació": interpretacio
        }
        # Fitxer on es guardaran els registres
        file_path = "registres_pacients.xlsx"

        if os.path.exists(file_path):
            df_reg = pd.read_excel(file_path)
            df_reg = pd.concat([df_reg, pd.DataFrame([dades_pacient])], ignore_index=True)
        else:
            df_reg = pd.DataFrame([dades_pacient])

        df_reg.to_excel(file_path, index=False)
        st.success(f"✅ Registre {registre_id} guardat correctament!")
else:
    st.warning("⚠️ No s'ha trobat un barem exacte per aquesta puntuació o edat.")
    import os
