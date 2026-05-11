import os
from io import BytesIO
from datetime import datetime

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, linregress, shapiro, f_oneway

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_OK = True
except Exception:
    GSHEETS_OK = False


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Monitoring Parameter Air dan Perilaku Hiu",
    layout="wide",
    page_icon="🦈"
)

LOCAL_CSV = "data_monitoring_hiu_local.csv"

HEADERS = [
    "id", "tanggal", "jam", "fase_makan", "waktu_input",
    "pengamat", "lokasi", "kolam", "id_hiu", "spesies",
    "salinitas", "do", "orp", "ph", "suhu",
    "amonia", "nitrit", "nitrat",
    "feed", "act", "resp", "phys", "soc", "rest",
    "interaksi_khusus", "event_khusus",
    "srbh", "interpretasi", "catatan"
]

UNITS = {
    "salinitas": "ppt",
    "do": "mg/L",
    "orp": "mV",
    "ph": "",
    "suhu": "°C",
    "amonia": "ppm",
    "nitrit": "ppm",
    "nitrat": "ppm",
}

INDIKATOR = {
    "FEED — Respons Makan": [
        [3, "Baik/normal", "Hiu merespons pakan dengan cepat, mendekati area feeding, dan mengambil pakan secara normal."],
        [2, "Sedang", "Respons lambat, hanya mendekat tetapi tidak langsung makan, atau makan lebih sedikit dari biasanya."],
        [1, "Buruk", "Tidak merespons pakan, menjauh dari area feeding, atau menolak pakan."],
    ],
    "ACT — Aktivitas/Berenang": [
        [3, "Normal/aktif stabil", "Berenang stabil, arah renang normal, tidak tampak panik atau lesu."],
        [2, "Sedang", "Aktivitas menurun, berenang lambat, lebih pasif, tetapi masih menunjukkan pergerakan normal."],
        [1, "Buruk/tidak normal", "Sangat lesu, berenang menyentak, tidak terarah, disorientasi, atau menunjukkan gerakan abnormal."],
    ],
    "REST — Istirahat": [
        [3, "Istirahat normal", "Hiu diam di dasar/substrat dengan posisi tubuh normal, stabil, dan masih responsif terhadap rangsangan sekitar."],
        [2, "Istirahat sedang/perlu perhatian", "Hiu terlalu lama diam di satu titik, respons lambat, atau posisi tubuh kurang aktif dibanding biasanya."],
        [1, "Istirahat tidak normal", "Diam terlalu lama dengan posisi tidak wajar, tidak responsif, tampak lemah, atau disertai tanda stres/pernapasan tidak normal."],
    ],
    "RESP — Respirasi/Stres Tampak": [
        [3, "Normal", "Tidak terlihat megap-megap, tidak sering ke permukaan, ritme napas tampak normal."],
        [2, "Sedang", "Sesekali tampak napas cepat, membuka mulut lebih sering, atau naik ke permukaan sesekali."],
        [1, "Buruk", "Sering gasping/megap-megap, napas sangat cepat, sering ke permukaan, atau tanda stres napas jelas dan berulang."],
    ],
    "PHYS — Kondisi Fisik Tampak": [
        [3, "Normal", "Tidak terlihat luka baru, lesi, perubahan warna mencolok, atau kerusakan sirip."],
        [2, "Sedang", "Ada temuan ringan, seperti lecet kecil, sirip sedikit rusak, atau perubahan warna ringan."],
        [1, "Buruk", "Luka/lesi jelas, luka bertambah, flashing berulang, perubahan warna ekstrem, atau kondisi luar tampak memburuk."],
    ],
    "SOC — Respons Organisme Lain": [
        [3, "Baik/normal", "Hidup bersama organisme lain secara normal, tidak agresif, dan tidak menghindar berlebihan."],
        [2, "Sedang", "Cenderung sendiri atau menghindar, tetapi tidak menunjukkan agresi berat."],
        [1, "Buruk", "Agresif terhadap organisme lain atau menunjukkan interaksi sosial tidak normal."],
    ],
}


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 85% 5%, rgba(32, 122, 180, 0.35), transparent 28%),
        linear-gradient(135deg, #03101d 0%, #06213a 45%, #020b14 100%);
    color: #eaf7ff;
}

.block-container {
    padding-top: 0.7rem;
    padding-left: 1.2rem;
    padding-right: 1.2rem;
    max-width: 100%;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #061b31, #03101d);
    border-right: 1px solid rgba(72, 167, 234, 0.25);
}

h1, h2, h3, h4, h5 {
    color: #f2fbff !important;
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #09253f, #06182a);
    border: 1px solid rgba(92, 184, 255, 0.28);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 0 18px rgba(0, 145, 255, 0.08);
}

.card {
    background: linear-gradient(145deg, rgba(9, 38, 67, 0.95), rgba(3, 16, 29, 0.95));
    border: 1px solid rgba(86, 177, 255, 0.28);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 0 20px rgba(0, 130, 255, 0.08);
}

.hero {
    background:
        linear-gradient(90deg, rgba(3, 16, 29, 0.9), rgba(4, 44, 75, 0.85)),
        radial-gradient(circle at 75% 50%, rgba(53, 167, 255, 0.25), transparent 25%);
    border: 1px solid rgba(86, 177, 255, 0.32);
    border-radius: 22px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

.hero-title {
    font-size: 38px;
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: 0.5px;
    color: #ffffff;
}

.hero-sub {
    color: #8fe8ff;
    font-size: 15px;
    margin-top: 7px;
}

.shark-big {
    font-size: 82px;
    text-align: right;
    filter: drop-shadow(0 0 12px rgba(93, 203, 255, .55));
}

.section-title {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 8px;
}

.small-label {
    color: #9fe9ff;
    font-size: 13px;
}

.indicator-white {
    background: #ffffff;
    color: #111111;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 18px;
    border: 1px solid #d4d4d4;
}

.indicator-white,
.indicator-white * {
    color: black !important;
}

.info-blue {
    background: rgba(31, 111, 179, 0.35);
    border: 1px solid rgba(83, 185, 255, 0.3);
    border-radius: 12px;
    padding: 12px;
    color: #aeeaff;
    margin-bottom: 12px;
}

.stButton > button {
    background: linear-gradient(90deg, #1267df, #0b8df0);
    color: white;
    border: 0;
    border-radius: 12px;
    font-weight: 800;
    padding: 0.65rem 1rem;
}

.stDownloadButton > button {
    background: linear-gradient(90deg, #0ea560, #1ad083);
    color: white;
    border: 0;
    border-radius: 12px;
    font-weight: 800;
}

hr {
    border: 0;
    border-top: 1px solid rgba(120, 200, 255, 0.22);
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA
# ============================================================

def interpretasi_srbh(skor):
    if skor >= 16:
        return "Baik/Stabil"
    elif skor >= 12:
        return "Sedang/Perlu Perhatian"
    return "Buruk/Indikasi Stres"


def has_gsheet_config():
    try:
        _ = st.secrets["SHEET_ID"]
        _ = st.secrets["gcp_service_account"]
        return GSHEETS_OK
    except Exception:
        return False


def connect_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["SHEET_ID"]).sheet1
    values = sheet.get_all_values()
    if not values:
        sheet.append_row(HEADERS)
    return sheet


def load_data():
    if has_gsheet_config():
        sheet = connect_sheet()
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
    else:
        if os.path.exists(LOCAL_CSV):
            df = pd.read_csv(LOCAL_CSV)
        else:
            df = pd.DataFrame(columns=HEADERS)

    for col in ["salinitas", "do", "orp", "ph", "suhu", "amonia", "nitrit", "nitrat",
                "feed", "act", "resp", "phys", "soc", "rest", "srbh"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def save_data(row):
    if has_gsheet_config():
        sheet = connect_sheet()
        sheet.append_row([row.get(h, "") for h in HEADERS])
    else:
        df_old = load_data()
        df_new = pd.concat([df_old, pd.DataFrame([row])], ignore_index=True)
        df_new.to_csv(LOCAL_CSV, index=False)


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data Monitoring")
    return output.getvalue()


def filter_df(df, spesies, kolam, hiu, fase):
    d = df.copy()

    if spesies != "Semua":
        d = d[d["spesies"].astype(str).str.contains(spesies, case=False, na=False)]

    if kolam != "Semua":
        d = d[d["kolam"].astype(str).str.contains(kolam, case=False, na=False)]

    if hiu != "Semua":
        d = d[d["id_hiu"].astype(str).str.contains(hiu, case=False, na=False)]

    if fase != "Semua":
        d = d[d["fase_makan"] == fase]

    return d


# ============================================================
# ANALYSIS
# ============================================================

def analysis_text(df):
    if df.empty:
        return "Belum ada data."

    lines = []
    lines.append("RINGKASAN ANALISIS PENELITIAN")
    lines.append(f"Jumlah data: {len(df)}")
    lines.append("")

    lines.append("Rata-rata Parameter Air:")
    for p, unit in UNITS.items():
        lines.append(f"- {p.upper()}: {df[p].mean():.2f} {unit}")

    lines.append("")
    lines.append("Rata-rata Skor Perilaku:")
    for p in ["feed", "act", "resp", "phys", "soc", "rest", "srbh"]:
        lines.append(f"- {p.upper()}: {df[p].mean():.2f}")

    lines.append("")
    lines.append("Distribusi SRBH:")
    lines.append(f"- Baik/Stabil: {(df['srbh'] >= 16).sum()} data")
    lines.append(f"- Sedang: {((df['srbh'] >= 12) & (df['srbh'] <= 15)).sum()} data")
    lines.append(f"- Buruk: {(df['srbh'] <= 11).sum()} data")

    lines.append("")
    lines.append("Perbandingan Sebelum vs Sesudah Makan:")
    before = df[df["fase_makan"] == "Sebelum Makan"]
    after = df[df["fase_makan"] == "Sesudah Makan"]

    lines.append(f"- Sebelum Makan: n={len(before)}, rata-rata SRBH={before['srbh'].mean():.2f}" if len(before) else "- Sebelum Makan: belum ada data")
    lines.append(f"- Sesudah Makan: n={len(after)}, rata-rata SRBH={after['srbh'].mean():.2f}" if len(after) else "- Sesudah Makan: belum ada data")

    if len(before) and len(after):
        diff = after["srbh"].mean() - before["srbh"].mean()
        lines.append(f"- Selisih sesudah - sebelum: {diff:.2f}")
        if diff > 0:
            lines.append("- Interpretasi: SRBH cenderung membaik setelah makan.")
        elif diff < 0:
            lines.append("- Interpretasi: SRBH cenderung menurun setelah makan.")
        else:
            lines.append("- Interpretasi: tidak ada perubahan rata-rata.")

    lines.append("")
    lines.append("Uji Normalitas Shapiro-Wilk SRBH:")
    if len(df) >= 3:
        w, p = shapiro(df["srbh"].dropna())
        lines.append(f"- W={w:.3f}, p={p:.4f}")
    else:
        lines.append("- Minimal 3 data diperlukan.")

    lines.append("")
    lines.append("Korelasi Pearson terhadap SRBH:")
    for p in list(UNITS.keys()) + ["rest"]:
        if len(df) >= 3 and df[p].nunique() > 1 and df["srbh"].nunique() > 1:
            r, pv = pearsonr(df[p], df["srbh"])
            lines.append(f"- {p.upper()}: r={r:.3f}, p={pv:.4f}")
        else:
            lines.append(f"- {p.upper()}: data belum cukup")

    lines.append("")
    lines.append("Regresi Linear terhadap SRBH:")
    for p in ["do", "ph", "suhu", "amonia", "nitrit", "nitrat", "rest"]:
        if len(df) >= 3 and df[p].nunique() > 1 and df["srbh"].nunique() > 1:
            reg = linregress(df[p], df["srbh"])
            lines.append(f"- {p.upper()}: SRBH = {reg.intercept:.2f} + {reg.slope:.2f}*{p}; R²={reg.rvalue**2:.3f}; p={reg.pvalue:.4f}")
        else:
            lines.append(f"- {p.upper()}: data belum cukup")

    lines.append("")
    lines.append("ANOVA SRBH per Spesies:")
    groups = [g["srbh"].dropna().values for _, g in df.groupby("spesies") if len(g) >= 2]
    if len(groups) >= 2:
        f, p = f_oneway(*groups)
        lines.append(f"- F={f:.3f}, p={p:.4f}")
    else:
        lines.append("- Butuh minimal 2 spesies, masing-masing minimal 2 data.")

    lines.append("")
    lines.append("ANOVA SRBH per Kolam:")
    groups = [g["srbh"].dropna().values for _, g in df.groupby("kolam") if len(g) >= 2]
    if len(groups) >= 2:
        f, p = f_oneway(*groups)
        lines.append(f"- F={f:.3f}, p={p:.4f}")
    else:
        lines.append("- Butuh minimal 2 kolam, masing-masing minimal 2 data.")

    return "\n".join(lines)


# ============================================================
# PLOTS
# ============================================================

def empty_chart_message(text):
    st.info(text)


def plot_trend(df, col):
    fig, ax = plt.subplots(figsize=(10, 4))
    x = df["tanggal"].astype(str) + " " + df["jam"].astype(str)
    ax.plot(x, df[col], marker="o")
    ax.set_title(f"Tren {col.upper()}")
    ax.set_xlabel("Waktu")
    ax.set_ylabel(f"{col.upper()} {UNITS.get(col, '')}")
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


def plot_scatter(df, col):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(df[col], df["srbh"])

    if len(df) >= 3 and df[col].nunique() > 1 and df["srbh"].nunique() > 1:
        reg = linregress(df[col], df["srbh"])
        pred = reg.intercept + reg.slope * df[col]
        ax.plot(df[col], pred)
        ax.set_title(f"{col.upper()} vs SRBH | R²={reg.rvalue**2:.3f}, p={reg.pvalue:.4f}")
    else:
        ax.set_title(f"{col.upper()} vs SRBH")

    ax.set_xlabel(f"{col.upper()} {UNITS.get(col, '')}")
    ax.set_ylabel("SRBH")
    plt.tight_layout()
    return fig


def plot_box(df, group):
    fig, ax = plt.subplots(figsize=(7, 4))
    vals, labels = [], []

    for name, g in df.groupby(group):
        vals.append(g["srbh"])
        labels.append(str(name))

    ax.boxplot(vals, labels=labels)
    ax.set_title(f"Boxplot SRBH per {group}")
    ax.set_ylabel("SRBH")
    plt.xticks(rotation=30)
    plt.tight_layout()
    return fig


def plot_heatmap(df):
    cols = list(UNITS.keys()) + ["rest", "srbh"]
    corr = df[cols].corr().fillna(0)

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


# ============================================================
# COMPONENTS
# ============================================================

def show_logo(path, width):
    if os.path.exists(path):
        st.image(path, width=width)


def hero():
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    a, b, c, d = st.columns([0.7, 0.9, 4, 2])

    with a:
        show_logo("logo_undip.jpg", 86)

    with b:
        show_logo("logo_bxsea.jpg", 105)

    with c:
        st.markdown('<div class="hero-title">MONITORING PARAMETER AIR<br>DAN PERILAKU HIU</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Universitas Diponegoro — BXSEA | Dashboard penelitian kualitas air dan perilaku hiu</div>', unsafe_allow_html=True)

    with d:
        st.markdown('<div class="shark-big">🦈</div>', unsafe_allow_html=True)
        st.caption(datetime.now().strftime("%d %B %Y | %H:%M WIB"))

    st.markdown('</div>', unsafe_allow_html=True)


def indicator_side_panel():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ℹ️ Penjelasan Indikator")
    choice = st.selectbox("Pilih indikator", list(INDIKATOR.keys()), key="side_indicator")

    for skor, kategori, definisi in INDIKATOR[choice]:
        if skor == 3:
            color = "#1aa76c"
        elif skor == 2:
            color = "#d59b23"
        else:
            color = "#d64545"

        st.markdown(
            f"""
            <div style="display:flex;gap:12px;margin:12px 0;">
                <div style="background:{color};padding:8px 12px;border-radius:8px;font-weight:900;color:white;height:38px;">{skor}</div>
                <div>
                    <b>{kategori}</b><br>
                    <span style="color:#c7e8ff;">{definisi}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# APP
# ============================================================

hero()

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Beranda",
        "📝 Input Data",
        "📋 Data Tersimpan",
        "📊 Analisis & Statistik",
        "📈 Grafik & Visualisasi",
        "📘 Penjelasan Indikator",
        "⬇️ Export Excel"
    ]
)

df = load_data()


# ============================================================
# BERANDA
# ============================================================

if menu == "🏠 Beranda":
    st.markdown("## 🏠 Dashboard Ringkasan")

    if df.empty:
        st.warning("Belum ada data.")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Data", len(df))
        m2.metric("Sebelum Makan", len(df[df["fase_makan"] == "Sebelum Makan"]))
        m3.metric("Sesudah Makan", len(df[df["fase_makan"] == "Sesudah Makan"]))
        m4.metric("ID Hiu Terpantau", df["id_hiu"].nunique())
        m5.metric("Rata-rata SRBH", f"{df['srbh'].mean():.2f}")

        st.markdown("---")

        g1, g2 = st.columns(2)
        with g1:
            st.pyplot(plot_trend(df, "srbh"))
        with g2:
            if df["fase_makan"].nunique() > 1:
                st.pyplot(plot_before_after(df))
            else:
                empty_chart_message("Data fase makan belum cukup.")

        g3, g4 = st.columns(2)
        with g3:
            if len(df) >= 3:
                st.pyplot(plot_heatmap(df))
            else:
                empty_chart_message("Heatmap membutuhkan minimal 3 data.")
        with g4:
            if df["spesies"].nunique() >= 2:
                st.pyplot(plot_box(df, "spesies"))
            else:
                empty_chart_message("Boxplot spesies butuh minimal 2 spesies.")


# ============================================================
# INPUT
# ============================================================

elif menu == "📝 Input Data":
    st.markdown("## 📝 Form Input Pengamatan")

    left, right = st.columns([3, 1.15])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        with st.form("form_input"):
            c1, c2, c3 = st.columns(3)

            with c1:
                tanggal = st.date_input("Tanggal", datetime.now())
                jam = st.time_input("Jam", datetime.now().time())
                fase_makan = st.selectbox("Fase Makan", ["Sebelum Makan", "Sesudah Makan"])
                pengamat = st.text_input("Nama Pengamat")
                lokasi = st.text_input("Lokasi")

            with c2:
                kolam = st.text_input("Kode Kolam/Tank")
                id_hiu = st.text_input("ID Hiu")
                spesies = st.text_input("Spesies")
                interaksi_khusus = st.text_area("Interaksi / Perilaku Khusus", placeholder="Contoh: berenang berkelompok, mendekati kaca, agresif terhadap hiu lain.")
                event_khusus = st.text_area("Kejadian Khusus / Event", placeholder="Contoh: pergantian air, pemberian obat, cuaca ekstrem, handling.")

            with c3:
                st.markdown("### 💧 Parameter Air")
                salinitas = st.number_input("Salinitas (ppt)", value=0.0)
                do = st.number_input("DO / Dissolved Oxygen (mg/L)", value=0.0)
                orp = st.number_input("ORP (mV)", value=0.0)
                ph = st.number_input("pH", value=0.0)
                suhu = st.number_input("Suhu (°C)", value=0.0)
                amonia = st.number_input("Amonia (ppm)", value=0.0)
                nitrit = st.number_input("Nitrit (ppm)", value=0.0)
                nitrat = st.number_input("Nitrat (ppm)", value=0.0)

            st.markdown("### 🦈 Skor Perilaku Hiu")
            st.markdown('<div class="info-blue">Skor: 1 = buruk, 2 = sedang, 3 = baik/normal. REST: 1=diam di dasar, 2=berenang santai, 3=berenang tanpa berhenti.</div>', unsafe_allow_html=True)

            s1, s2, s3, s4, s5, s6 = st.columns(6)
            feed = s1.selectbox("FEED", [1, 2, 3], index=2)
            act = s2.selectbox("ACT", [1, 2, 3], index=2)
            resp = s3.selectbox("RESP", [1, 2, 3], index=2)
            phys = s4.selectbox("PHYS", [1, 2, 3], index=2)
            soc = s5.selectbox("SOC", [1, 2, 3], index=2)
            rest = s6.selectbox("REST", [1, 2, 3], index=1)

            catatan = st.text_area("Catatan Tambahan")

            submitted = st.form_submit_button("💾 SIMPAN DATA")

            if submitted:
                srbh = feed + act + resp + phys + soc + rest
                row = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "tanggal": str(tanggal),
                    "jam": jam.strftime("%H:%M"),
                    "fase_makan": fase_makan,
                    "waktu_input": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "pengamat": pengamat,
                    "lokasi": lokasi,
                    "kolam": kolam,
                    "id_hiu": id_hiu,
                    "spesies": spesies,
                    "salinitas": salinitas,
                    "do": do,
                    "orp": orp,
                    "ph": ph,
                    "suhu": suhu,
                    "amonia": amonia,
                    "nitrit": nitrit,
                    "nitrat": nitrat,
                    "feed": feed,
                    "act": act,
                    "resp": resp,
                    "phys": phys,
                    "soc": soc,
                    "rest": rest,
                    "interaksi_khusus": interaksi_khusus,
                    "event_khusus": event_khusus,
                    "srbh": srbh,
                    "interpretasi": interpretasi_srbh(srbh),
                    "catatan": catatan,
                }
                save_data(row)
                st.success(f"Data berhasil disimpan. SRBH = {srbh} ({interpretasi_srbh(srbh)})")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        indicator_side_panel()


# ============================================================
# DATA
# ============================================================

elif menu == "📋 Data Tersimpan":
    st.markdown("## 📋 Data Tersimpan")

    if df.empty:
        st.warning("Belum ada data.")
    else:
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "⬇️ Download Excel",
            data=to_excel(df),
            file_name="data_monitoring_hiu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ============================================================
# ANALYSIS
# ============================================================

elif menu == "📊 Analisis & Statistik":
    st.markdown("## 📊 Analisis & Statistik")

    if df.empty:
        st.warning("Belum ada data.")
    else:
        f1, f2, f3, f4 = st.columns(4)
        spesies_f = f1.text_input("Filter Spesies", "Semua")
        kolam_f = f2.text_input("Filter Kolam", "Semua")
        hiu_f = f3.text_input("Filter ID Hiu", "Semua")
        fase_f = f4.selectbox("Filter Fase", ["Semua", "Sebelum Makan", "Sesudah Makan"])

        dff = filter_df(df, spesies_f, kolam_f, hiu_f, fase_f)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Data", len(dff))
        m2.metric("Rata-rata SRBH", f"{dff['srbh'].mean():.2f}" if not dff.empty else "0")
        m3.metric("Sebelum Makan", len(dff[dff["fase_makan"] == "Sebelum Makan"]) if not dff.empty else 0)
        m4.metric("Sesudah Makan", len(dff[dff["fase_makan"] == "Sesudah Makan"]) if not dff.empty else 0)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.text(analysis_text(dff))
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# GRAFIK
# ============================================================

elif menu == "📈 Grafik & Visualisasi":
    st.markdown("## 📈 Grafik & Visualisasi")

    if df.empty:
        st.warning("Belum ada data.")
    else:
        f1, f2, f3, f4 = st.columns(4)
        spesies_f = f1.text_input("Filter Spesies", "Semua", key="g_sp")
        kolam_f = f2.text_input("Filter Kolam", "Semua", key="g_ko")
        hiu_f = f3.text_input("Filter ID Hiu", "Semua", key="g_hi")
        fase_f = f4.selectbox("Filter Fase", ["Semua", "Sebelum Makan", "Sesudah Makan"], key="g_fa")

        dff = filter_df(df, spesies_f, kolam_f, hiu_f, fase_f)

        g1, g2 = st.columns(2)
        with g1:
            trend = st.selectbox("Grafik Tren", ["srbh", "suhu", "do", "ph", "salinitas", "amonia", "nitrit", "nitrat", "rest"])
            st.pyplot(plot_trend(dff, trend))

        with g2:
            scatter = st.selectbox("Scatter SRBH vs", ["do", "ph", "suhu", "amonia", "nitrit", "nitrat", "rest"])
            st.pyplot(plot_scatter(dff, scatter))

        g3, g4 = st.columns(2)
        with g3:
            if dff["fase_makan"].nunique() > 1:
                st.pyplot(plot_before_after(dff))
            else:
                empty_chart_message("Grafik fase makan butuh data sebelum dan sesudah makan.")

        with g4:
            if len(dff) >= 3:
                st.pyplot(plot_heatmap(dff))
            else:
                empty_chart_message("Heatmap butuh minimal 3 data.")

        b1, b2, b3 = st.columns(3)
        if dff["spesies"].nunique() >= 2:
            b1.pyplot(plot_box(dff, "spesies"))
        else:
            b1.info("Boxplot spesies butuh minimal 2 spesies.")

        if dff["kolam"].nunique() >= 2:
            b2.pyplot(plot_box(dff, "kolam"))
        else:
            b2.info("Boxplot kolam butuh minimal 2 kolam.")

        if dff["id_hiu"].nunique() >= 2:
            b3.pyplot(plot_box(dff, "id_hiu"))
        else:
            b3.info("Boxplot ID hiu butuh minimal 2 individu.")


# ============================================================
# INDIKATOR
# ============================================================

elif menu == "📘 Penjelasan Indikator":
    st.markdown("## 📘 Penjelasan Indikator Skor 1–3")

    for name, rows in INDIKATOR.items():
        st.markdown(f'<div class="indicator-white"><h3>{name}</h3>', unsafe_allow_html=True)
        table = pd.DataFrame(rows, columns=["Skor", "Kategori", "Definisi"])
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.info("Interaksi/perilaku khusus dan kejadian/event dicatat sebagai data observasi tambahan, tetapi tidak masuk ke skor SRBH.")


# ============================================================
# EXPORT
# ============================================================

elif menu == "⬇️ Export Excel":
    st.markdown("## ⬇️ Export Excel")

    if df.empty:
        st.warning("Belum ada data.")
    else:
        st.download_button(
            "Download Semua Data Excel",
            data=to_excel(df),
            file_name="data_monitoring_hiu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
