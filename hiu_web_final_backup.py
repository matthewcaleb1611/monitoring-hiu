import streamlit as st

st.set_page_config(
    page_title="Monitoring Hiu",
    layout="wide",
    page_icon="🦈"
)

# =========================
# CSS
# =========================

st.markdown("""
<style>

.stApp{
    background: linear-gradient(135deg,#03111f,#061f35,#020c18);
    color:white;
}

h1,h2,h3,h4,h5,h6{
    color:white !important;
}

.block-container{
    padding-top:1rem;
}

.hero{
    background:linear-gradient(90deg,#03101d,#072c4b);
    border-radius:20px;
    padding:20px;
    border:1px solid rgba(100,180,255,.3);
    margin-bottom:20px;
}

.card{
    background:rgba(5,20,35,.9);
    border:1px solid rgba(100,180,255,.2);
    border-radius:18px;
    padding:20px;
    margin-bottom:15px;
}

.indicator-card{
    background:white;
    border-radius:15px;
    padding:20px;
    color:black !important;
}

.indicator-card h3{
    color:black !important;
}

.indicator-card p{
    color:black !important;
}

.indicator-card div{
    color:black !important;
}

.stButton>button{
    width:100%;
    background:linear-gradient(90deg,#0d63ff,#00a2ff);
    color:white;
    border:none;
    border-radius:12px;
    font-weight:bold;
    height:50px;
}

.smalltext{
    color:#9ddfff;
    font-size:14px;
}

.metric-card{
    background:rgba(7,30,50,.9);
    padding:20px;
    border-radius:15px;
    border:1px solid rgba(100,180,255,.2);
    text-align:center;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

st.markdown("""
<div class="hero">
<h1>🦈 MONITORING PARAMETER AIR DAN PERILAKU HIU</h1>
<p class="smalltext">
Universitas Diponegoro — BXSEA
</p>
</div>
""", unsafe_allow_html=True)

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Input Data",
        "Analisis",
        "Penjelasan Indikator"
    ]
)

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":

    st.subheader("Dashboard Penelitian")

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        st.markdown("""
        <div class="metric-card">
        <h2>128</h2>
        <p>Total Data</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="metric-card">
        <h2>68</h2>
        <p>Sebelum Makan</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="metric-card">
        <h2>60</h2>
        <p>Sesudah Makan</p>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="metric-card">
        <h2>8</h2>
        <p>ID Hiu</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.info("Dashboard statistik dan grafik akan muncul di sini.")

# =========================
# INPUT DATA
# =========================

elif menu == "Input Data":

    kiri, kanan = st.columns([3,1])

    with kiri:

        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.subheader("FORM INPUT PENGAMATAN")

        a,b,c = st.columns(3)

        with a:
            tanggal = st.date_input("Tanggal")
            fase = st.selectbox(
                "Fase Makan",
                ["Sebelum Makan","Sesudah Makan"]
            )
            pengamat = st.text_input("Nama Pengamat")
            lokasi = st.text_input("Lokasi")

        with b:
            jam = st.time_input("Jam")
            kolam = st.text_input("Kode Kolam")
            id_hiu = st.text_input("ID Hiu")
            spesies = st.text_input("Spesies")

        with c:

            st.markdown("### Parameter Air")

            salinitas = st.number_input("Salinitas (ppt)")
            do = st.number_input("DO (mg/L)")
            orp = st.number_input("ORP (mV)")
            ph = st.number_input("pH")
            suhu = st.number_input("Suhu (°C)")
            amonia = st.number_input("Amonia (ppm)")
            nitrit = st.number_input("Nitrit (ppm)")
            nitrat = st.number_input("Nitrat (ppm)")

        st.markdown("---")

        st.subheader("Skor Perilaku Hiu")

        s1,s2,s3,s4,s5,s6 = st.columns(6)

        with s1:
            feed = st.selectbox("FEED",[1,2,3])

        with s2:
            act = st.selectbox("ACT",[1,2,3])

        with s3:
            resp = st.selectbox("RESP",[1,2,3])

        with s4:
            phys = st.selectbox("PHYS",[1,2,3])

        with s5:
            soc = st.selectbox("SOC",[1,2,3])

        with s6:
            rest = st.selectbox("REST",[1,2,3])

        interaksi = st.text_area(
            "Interaksi / Perilaku Khusus"
        )

        event = st.text_area(
            "Kejadian Khusus / Event"
        )

        if st.button("💾 SIMPAN DATA"):

            srbh = (
                feed +
                act +
                resp +
                phys +
                soc +
                rest
            )

            st.success(
                f"Data berhasil disimpan | SRBH = {srbh}"
            )

        st.markdown('</div>', unsafe_allow_html=True)

    with kanan:

        st.markdown("""
        <div class="indicator-card">

        <h3>Penjelasan Indikator</h3>

        <h4>3 = Baik / Normal</h4>
        <p>
        Hiu merespons normal dan aktif.
        </p>

        <h4>2 = Sedang</h4>
        <p>
        Ada perubahan perilaku ringan.
        </p>

        <h4>1 = Buruk</h4>
        <p>
        Menunjukkan tanda stres kuat.
        </p>

        </div>
        """, unsafe_allow_html=True)

# =========================
# ANALISIS
# =========================

elif menu == "Analisis":

    st.subheader("Analisis Statistik")

    st.info("""
    Fitur yang akan tersedia:

    • Uji Normalitas  
    • Uji ANOVA  
    • Korelasi Pearson  
    • Regresi Linear  
    • Boxplot  
    • Scatter Plot  
    • Heatmap Korelasi  
    • Analisis Sebelum vs Sesudah Makan  
    """)

# =========================
# PENJELASAN
# =========================

elif menu == "Penjelasan Indikator":

    st.markdown("""
    <div class="indicator-card">

    <h3>FEED — Respons Makan</h3>

    <p><b>3:</b> Respon makan baik.</p>

    <p><b>2:</b> Respon makan sedang.</p>

    <p><b>1:</b> Menolak makan.</p>

    </div>
    """, unsafe_allow_html=True)
