#!/usr/bin/env python3
import sqlite3
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, linregress, shapiro, f_oneway

DB_NAME = "hiu_web.db"

st.set_page_config(
    page_title="Monitoring Hiu",
    layout="wide"
)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pengamatan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            jam TEXT,
            fase_makan TEXT,
            waktu_input TEXT,
            pengamat TEXT,
            lokasi TEXT,
            kolam TEXT,
            id_hiu TEXT,
            spesies TEXT,

            salinitas REAL,
            do REAL,
            orp REAL,
            ph REAL,
            suhu REAL,
            amonia REAL,
            nitrit REAL,
            nitrat REAL,

            feed INTEGER,
            act INTEGER,
            resp INTEGER,
            phys INTEGER,
            soc INTEGER,
            rest INTEGER,
            srbh INTEGER,
            interpretasi TEXT,
            catatan TEXT
        )
    """)
    conn.commit()
    conn.close()

def interpretasi_srbh(skor):
    if skor >= 16:
        return "Baik/Stabil"
    elif skor >= 12:
        return "Sedang/Perlu Perhatian"
    else:
        return "Buruk/Indikasi Stres"

def load_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM pengamatan ORDER BY id DESC", conn)
    conn.close()
    return df

def save_data(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pengamatan (
            tanggal, jam, fase_makan, waktu_input, pengamat, lokasi, kolam,
            id_hiu, spesies, salinitas, do, orp, ph, suhu,
            amonia, nitrit, nitrat, feed, act, resp, phys, soc, rest,
            srbh, interpretasi, catatan
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def filter_df(df, spesies, kolam, id_hiu, fase):
    hasil = df.copy()

    if spesies != "Semua":
        hasil = hasil[hasil["spesies"].astype(str).str.contains(spesies, case=False, na=False)]

    if kolam != "Semua":
        hasil = hasil[hasil["kolam"].astype(str).str.contains(kolam, case=False, na=False)]

    if id_hiu != "Semua":
        hasil = hasil[hasil["id_hiu"].astype(str).str.contains(id_hiu, case=False, na=False)]

    if fase != "Semua":
        hasil = hasil[hasil["fase_makan"] == fase]

    return hasil

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data Monitoring")
    return output.getvalue()

def analisis_text(df):
    if df.empty:
        return "Belum ada data."

    teks = []
    teks.append("RINGKASAN ANALISIS PENELITIAN")
    teks.append(f"Jumlah data: {len(df)}")
    teks.append("")

    parameter_air = ["salinitas", "do", "orp", "ph", "suhu", "amonia", "nitrit", "nitrat"]
    perilaku = ["feed", "act", "resp", "phys", "soc", "rest", "srbh"]

    teks.append("Rata-rata Parameter Air:")
    for p in parameter_air:
        teks.append(f"- {p}: {df[p].mean():.2f}")

    teks.append("")
    teks.append("Rata-rata Skor Perilaku:")
    for p in perilaku:
        teks.append(f"- {p}: {df[p].mean():.2f}")

    teks.append("")
    teks.append("Distribusi SRBH:")
    teks.append(f"- Baik/Stabil: {(df['srbh'] >= 16).sum()} data")
    teks.append(f"- Sedang: {((df['srbh'] >= 12) & (df['srbh'] <= 15)).sum()} data")
    teks.append(f"- Buruk: {(df['srbh'] <= 11).sum()} data")

    teks.append("")
    teks.append("Analisis Sebelum vs Sesudah Makan:")
    for fase in ["Sebelum Makan", "Sesudah Makan"]:
        sub = df[df["fase_makan"] == fase]
        if not sub.empty:
            teks.append(f"- {fase}: n={len(sub)}, rata-rata SRBH={sub['srbh'].mean():.2f}")
        else:
            teks.append(f"- {fase}: belum ada data")

    sebelum = df[df["fase_makan"] == "Sebelum Makan"]["srbh"]
    sesudah = df[df["fase_makan"] == "Sesudah Makan"]["srbh"]

    if len(sebelum) > 0 and len(sesudah) > 0:
        selisih = sesudah.mean() - sebelum.mean()
        teks.append(f"- Selisih sesudah - sebelum makan: {selisih:.2f}")
        if selisih > 0:
            teks.append("- Interpretasi: SRBH cenderung membaik setelah makan.")
        elif selisih < 0:
            teks.append("- Interpretasi: SRBH cenderung menurun setelah makan.")
        else:
            teks.append("- Interpretasi: tidak ada perubahan rata-rata SRBH.")

    teks.append("")
    teks.append("Uji Normalitas Shapiro-Wilk SRBH:")
    if len(df) >= 3:
        w, p = shapiro(df["srbh"])
        teks.append(f"- W={w:.3f}, p={p:.4f}")
    else:
        teks.append("- Minimal 3 data diperlukan.")

    teks.append("")
    teks.append("Korelasi Pearson terhadap SRBH:")
    for p in parameter_air + ["rest"]:
        if len(df) >= 3 and df[p].nunique() > 1 and df["srbh"].nunique() > 1:
            r, pv = pearsonr(df[p], df["srbh"])
            teks.append(f"- {p}: r={r:.3f}, p={pv:.4f}")
        else:
            teks.append(f"- {p}: data belum cukup")

    teks.append("")
    teks.append("Regresi Linear terhadap SRBH:")
    for p in ["do", "ph", "suhu", "amonia", "nitrit", "nitrat", "rest"]:
        if len(df) >= 3 and df[p].nunique() > 1 and df["srbh"].nunique() > 1:
            reg = linregress(df[p], df["srbh"])
            teks.append(
                f"- {p}: SRBH = {reg.intercept:.2f} + {reg.slope:.2f}*{p}; "
                f"R²={reg.rvalue**2:.3f}; p={reg.pvalue:.4f}"
            )
        else:
            teks.append(f"- {p}: data belum cukup")

    teks.append("")
    teks.append("ANOVA per Spesies:")
    groups = [g["srbh"].values for _, g in df.groupby("spesies") if len(g) >= 2]
    if len(groups) >= 2:
        f, p = f_oneway(*groups)
        teks.append(f"- F={f:.3f}, p={p:.4f}")
    else:
        teks.append("- Butuh minimal 2 spesies, masing-masing minimal 2 data.")

    teks.append("")
    teks.append("ANOVA per Kolam:")
    groups = [g["srbh"].values for _, g in df.groupby("kolam") if len(g) >= 2]
    if len(groups) >= 2:
        f, p = f_oneway(*groups)
        teks.append(f"- F={f:.3f}, p={p:.4f}")
    else:
        teks.append("- Butuh minimal 2 kolam, masing-masing minimal 2 data.")

    return "\n".join(teks)

def plot_trend(df, y_col):
    fig, ax = plt.subplots(figsize=(10, 4))
    x = df["tanggal"].astype(str) + " " + df["jam"].astype(str)
    ax.plot(x, df[y_col], marker="o")
    ax.set_title(f"Tren {y_col.upper()}")
    ax.set_xlabel("Waktu")
    ax.set_ylabel(y_col.upper())
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def plot_before_after(df):
    fig, ax = plt.subplots(figsize=(6, 4))
    data = df.groupby("fase_makan")["srbh"].mean()
    ax.bar(data.index, data.values)
    ax.set_title("Rata-rata SRBH Sebelum vs Sesudah Makan")
    ax.set_ylabel("SRBH")
    plt.tight_layout()
    return fig

def plot_scatter_regression(df, x_col):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(df[x_col], df["srbh"])

    if len(df) >= 3 and df[x_col].nunique() > 1:
        reg = linregress(df[x_col], df["srbh"])
        y_pred = reg.intercept + reg.slope * df[x_col]
        ax.plot(df[x_col], y_pred)
        ax.set_title(f"{x_col.upper()} vs SRBH | R²={reg.rvalue**2:.3f}, p={reg.pvalue:.4f}")
    else:
        ax.set_title(f"{x_col.upper()} vs SRBH")

    ax.set_xlabel(x_col.upper())
    ax.set_ylabel("SRBH")
    plt.tight_layout()
    return fig

def plot_boxplot(df, group_col):
    fig, ax = plt.subplots(figsize=(7, 4))
    groups = []
    labels = []

    for label, group in df.groupby(group_col):
        groups.append(group["srbh"])
        labels.append(label)

    ax.boxplot(groups, labels=labels)
    ax.set_title(f"Boxplot SRBH per {group_col}")
    ax.set_ylabel("SRBH")
    plt.xticks(rotation=30)
    plt.tight_layout()
    return fig

def plot_heatmap(df):
    cols = ["salinitas", "do", "orp", "ph", "suhu", "amonia", "nitrit", "nitrat", "rest", "srbh"]
    corr = df[cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr, vmin=-1, vmax=1)
    fig.colorbar(im, ax=ax)

    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45)
    ax.set_yticklabels(cols)

    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

    ax.set_title("Heatmap Korelasi")
    plt.tight_layout()
    return fig

init_db()

st.title("🦈 Monitoring Parameter Air dan Perilaku Hiu")
st.caption("Versi web untuk HP: sebelum/sesudah makan, istirahat, statistik, grafik, dan Excel.")

tab1, tab2, tab3 = st.tabs(["Input Data", "Data & Filter", "Analisis & Grafik"])

with tab1:
    st.subheader("Input Pengamatan")

    with st.form("form_input"):
        c1, c2, c3 = st.columns(3)

        with c1:
            tanggal = st.date_input("Tanggal", datetime.now())
            jam = st.time_input("Jam", datetime.now().time())
            fase_makan = st.selectbox("Fase Makan", ["Sebelum Makan", "Sesudah Makan"])
            pengamat = st.text_input("Nama Pengamat")

        with c2:
            lokasi = st.text_input("Lokasi")
            kolam = st.text_input("Kode Kolam/Tank")
            id_hiu = st.text_input("ID Hiu", value="1")
            spesies = st.text_input("Spesies")

        with c3:
            salinitas = st.number_input("Salinitas", value=0.0)
            do = st.number_input("DO", value=0.0)
            orp = st.number_input("ORP", value=0.0)
            ph = st.number_input("pH", value=0.0)
            suhu = st.number_input("Suhu", value=0.0)
            amonia = st.number_input("Amonia", value=0.0)
            nitrit = st.number_input("Nitrit", value=0.0)
            nitrat = st.number_input("Nitrat", value=0.0)

        st.markdown("### Skor Perilaku")
        st.info("Skor: 1 = buruk, 2 = sedang, 3 = baik/normal. REST: 1=diam di dasar, 2=berenang santai, 3=berenang tanpa berhenti.")

        p1, p2, p3, p4, p5, p6 = st.columns(6)
        feed = p1.selectbox("FEED", [1, 2, 3], index=2)
        act = p2.selectbox("ACT", [1, 2, 3], index=2)
        resp = p3.selectbox("RESP", [1, 2, 3], index=2)
        phys = p4.selectbox("PHYS", [1, 2, 3], index=2)
        soc = p5.selectbox("SOC", [1, 2, 3], index=2)
        rest = p6.selectbox("REST", [1, 2, 3], index=1)

        catatan = st.text_area("Catatan Harian / Kejadian Khusus")

        submitted = st.form_submit_button("Simpan Data")

        if submitted:
            srbh = feed + act + resp + phys + soc + rest
            interpretasi = interpretasi_srbh(srbh)

            data = (
                str(tanggal),
                jam.strftime("%H:%M"),
                fase_makan,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                pengamat,
                lokasi,
                kolam,
                id_hiu,
                spesies,
                salinitas,
                do,
                orp,
                ph,
                suhu,
                amonia,
                nitrit,
                nitrat,
                feed,
                act,
                resp,
                phys,
                soc,
                rest,
                srbh,
                interpretasi,
                catatan
            )

            save_data(data)
            st.success(f"Data berhasil disimpan. SRBH = {srbh} ({interpretasi})")

df = load_data()

with tab2:
    st.subheader("Data Pengamatan")

    if df.empty:
        st.warning("Belum ada data.")
    else:
        st.dataframe(df, use_container_width=True)

        excel_data = to_excel(df)
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name="data_monitoring_hiu_web.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with tab3:
    st.subheader("Analisis dan Grafik")

    if df.empty:
        st.warning("Belum ada data untuk dianalisis.")
    else:
        c1, c2, c3, c4 = st.columns(4)

        spesies_filter = c1.text_input("Filter Spesies", value="Semua")
        kolam_filter = c2.text_input("Filter Kolam", value="Semua")
        hiu_filter = c3.text_input("Filter ID Hiu", value="Semua")
        fase_filter = c4.selectbox("Filter Fase Makan", ["Semua", "Sebelum Makan", "Sesudah Makan"])

        dff = filter_df(df, spesies_filter, kolam_filter, hiu_filter, fase_filter)

        st.markdown("### Data Setelah Filter")
        st.dataframe(dff, use_container_width=True)

        st.markdown("### Analisis Statistik")
        st.text(analisis_text(dff))

        st.markdown("### Grafik Penelitian")

        g1, g2 = st.columns(2)

        with g1:
            param_tren = st.selectbox(
                "Grafik Tren",
                ["srbh", "salinitas", "do", "orp", "ph", "suhu", "amonia", "nitrit", "nitrat", "rest"]
            )
            st.pyplot(plot_trend(dff, param_tren))

            if dff["fase_makan"].nunique() > 1:
                st.pyplot(plot_before_after(dff))

        with g2:
            param_scatter = st.selectbox(
                "Scatter Regresi SRBH vs",
                ["do", "ph", "suhu", "amonia", "nitrit", "nitrat", "rest"]
            )
            st.pyplot(plot_scatter_regression(dff, param_scatter))

            if len(dff) >= 3:
                st.pyplot(plot_heatmap(dff))

        st.markdown("### Boxplot")
        b1, b2, b3 = st.columns(3)

        if dff["spesies"].nunique() >= 2:
            b1.pyplot(plot_boxplot(dff, "spesies"))
        else:
            b1.info("Boxplot spesies butuh minimal 2 spesies.")

        if dff["kolam"].nunique() >= 2:
            b2.pyplot(plot_boxplot(dff, "kolam"))
        else:
            b2.info("Boxplot kolam butuh minimal 2 kolam.")

        if dff["id_hiu"].nunique() >= 2:
            b3.pyplot(plot_boxplot(dff, "id_hiu"))
        else:
            b3.info("Boxplot hiu butuh minimal 2 individu.")
