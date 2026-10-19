import streamlit as st

from analytics import (
    load_data,
    get_account_metrics,
    get_performance_distribution,
    get_performance_summary,
    get_top_videos,
)
from ai import get_ai_insight
from utils import format_number, format_percentage


st.set_page_config(
    page_title="TikTok Creator Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Custom styling
# -----------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        .main-title {
            font-size: 2.25rem;
            font-weight: 750;
            margin-bottom: 0.1rem;
        }

        .subtitle {
            color: #6b7280;
            margin-bottom: 1.5rem;
        }

        .section-note {
            color: #6b7280;
            font-size: 0.92rem;
            margin-top: -0.35rem;
            margin-bottom: 0.8rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(128, 128, 128, 0.07);
            border: 1px solid rgba(128, 128, 128, 0.15);
            padding: 1rem;
            border-radius: 14px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.45rem;
        }

        .ai-box {
            border: 1px solid rgba(128, 128, 128, 0.18);
            border-radius: 14px;
            padding: 1rem 1.15rem;
            background: rgba(128, 128, 128, 0.055);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="main-title">📊 TikTok Creator Analyzer</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Analisis performa konten + AI insights</div>',
    unsafe_allow_html=True,
)


# -----------------------------
# Sidebar / data input
# -----------------------------
with st.sidebar:
    st.header("📁 Data")

    uploaded_file = st.file_uploader(
        "Upload CSV video",
        type=["csv"],
        help=(
            "Untuk V1, CSV digunakan sebagai sumber data. "
            "Integrasi TikTok API ditambahkan pada tahap berikutnya."
        ),
    )

    st.divider()
    st.caption("Kolom CSV yang wajib:")
    st.code(
        "title, views, likes, comments, shares, duration",
        language="text",
    )

    if uploaded_file:
        st.success("CSV aktif")
    else:
        st.info("Menggunakan data contoh dari data/videos.csv")


# -----------------------------
# Load and validate data
# -----------------------------
try:
    df = load_data(uploaded_file)
except ValueError as exc:
    st.error(f"Gagal membaca data: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Terjadi error tak terduga saat memproses data: {exc}")
    st.stop()

validation_summary = df.attrs.get("validation_summary", {})
validation_warnings = df.attrs.get("validation_warnings", [])

if validation_summary:
    if validation_warnings:
        st.warning(
            f"Data berhasil diproses: {validation_summary.get('rows', len(df))} video "
            f"dengan {validation_summary.get('warning_count', len(validation_warnings))} catatan validasi."
        )
        with st.expander("⚠️ Lihat catatan validasi data", expanded=False):
            for warning in validation_warnings:
                st.write(f"- {warning}")
    else:
        st.success(
            f"Data valid — {validation_summary.get('rows', len(df))} video siap dianalisis."
        )


# -----------------------------
# Account Overview
# -----------------------------
st.subheader("Account Overview")
st.markdown(
    '<div class="section-note">Ringkasan berdasarkan dataset yang sedang dianalisis.</div>',
    unsafe_allow_html=True,
)

metrics = get_account_metrics(df)

row1 = st.columns(5)
row1[0].metric("Total Videos", format_number(metrics["total_videos"]))
row1[1].metric("Total Views", format_number(metrics["total_views"]))
row1[2].metric("Total Likes", format_number(metrics["total_likes"]))
row1[3].metric("Avg Views", format_number(metrics["average_views"]))
row1[4].metric("Avg Engagement", format_percentage(metrics["average_engagement"]))

row2 = st.columns(2)
row2[0].metric("Median Views", format_number(metrics["median_views"]))
row2[1].metric(
    "Top 3 View Contribution",
    format_percentage(metrics["top_3_contribution"], 1),
)


# -----------------------------
# Performance Distribution
# -----------------------------
st.divider()
st.subheader("📊 Performance Distribution")
st.markdown(
    '<div class="section-note">Klasifikasi relatif terhadap video lain dalam dataset ini.</div>',
    unsafe_allow_html=True,
)

distribution = get_performance_distribution(df)
dist_cols = st.columns(4)

for col, label in zip(
    dist_cols,
    ["🔥 Viral", "🟢 High", "🟡 Normal", "🔴 Low"],
):
    col.metric(label, format_number(distribution.get(label, 0)))


# -----------------------------
# Performance Analysis
# -----------------------------
st.divider()
st.subheader("🔎 Performance Analysis")

performance_summary = get_performance_summary(df)

summary_display = performance_summary.copy()
summary_display["video_count"] = summary_display["video_count"].apply(format_number)
summary_display["average_views"] = summary_display["average_views"].apply(format_number)
summary_display["average_likes"] = summary_display["average_likes"].apply(format_number)
summary_display["average_engagement"] = summary_display["average_engagement"].apply(
    lambda x: format_percentage(x)
)
summary_display["average_duration"] = summary_display["average_duration"].apply(
    lambda x: format_number(round(x, 1))
)
summary_display = summary_display.rename(
    columns={
        "video_count": "Videos",
        "average_views": "Avg Views",
        "average_likes": "Avg Likes",
        "average_engagement": "Avg Engagement",
        "average_duration": "Avg Duration (s)",
    }
)

st.dataframe(
    summary_display,
    use_container_width=True,
)

chart_left, chart_right = st.columns(2)

with chart_left:
    st.subheader("Average Views")
    st.bar_chart(performance_summary[["average_views"]])

with chart_right:
    st.subheader("Average Engagement")
    st.bar_chart(performance_summary[["average_engagement"]])


# -----------------------------
# Video Charts
# -----------------------------
st.divider()
st.subheader("Video Performance")
st.markdown(
    '<div class="section-note">Grafik menampilkan 10 video teratas agar tetap mudah dibaca saat dataset berisi banyak video. Semua video tetap tersedia di tabel di bawah.</div>',
    unsafe_allow_html=True,
)

video_chart_left, video_chart_right = st.columns(2)

# Limit the per-video charts so labels remain readable on larger datasets.
views_chart_df = (
    df.sort_values("views", ascending=False)
    .head(10)[["title", "views"]]
    .set_index("title")
)
engagement_chart_df = (
    df.sort_values("engagement_rate", ascending=False)
    .head(10)[["title", "engagement_rate"]]
    .set_index("title")
)

with video_chart_left:
    st.subheader("Views per Video — Top 10")
    st.bar_chart(views_chart_df)

with video_chart_right:
    st.subheader("Engagement Rate per Video — Top 10")
    st.bar_chart(engagement_chart_df)


# -----------------------------
# Top Performing Videos
# -----------------------------
st.divider()
st.subheader("🏆 Top Performing Videos")

sort_by = st.selectbox(
    "Urutkan berdasarkan",
    ["views", "likes", "comments", "shares", "engagement_rate"],
)

top_df = get_top_videos(df, sort_by=sort_by, limit=10)
top_display = top_df.copy()
top_display["views"] = top_display["views"].apply(format_number)
top_display["likes"] = top_display["likes"].apply(format_number)
top_display["comments"] = top_display["comments"].apply(format_number)
top_display["shares"] = top_display["shares"].apply(format_number)
top_display["duration"] = top_display["duration"].apply(lambda x: format_number(round(x, 1)))
top_display["engagement_rate"] = top_display["engagement_rate"].apply(
    lambda x: format_percentage(x)
)

top_display = top_display.drop(columns=["view_percentile"], errors="ignore")

top_display = top_display.rename(
    columns={
        "rank": "Rank",
        "title": "Video",
        "views": "Views",
        "likes": "Likes",
        "comments": "Comments",
        "shares": "Shares",
        "duration": "Duration (s)",
        "engagement_rate": "Engagement",
        "performance": "Performance",
    }
)

st.dataframe(
    top_display,
    use_container_width=True,
    hide_index=True,
)


# -----------------------------
# AI Insights
# -----------------------------
st.divider()
st.subheader("🤖 AI Insights")
st.markdown(
    '<div class="section-note">AI membaca hasil analytics yang dihitung Python, lalu mengubahnya menjadi insight dan eksperimen.</div>',
    unsafe_allow_html=True,
)

if st.button("Generate AI Insights", type="primary"):
    with st.spinner("Menganalisis data..."):
        insight = get_ai_insight(df)

    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown(insight)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Klik tombol di atas untuk meminta insight dari Gemini berdasarkan dataset ini.")


# -----------------------------
# Raw data
# -----------------------------
st.divider()
with st.expander("Lihat raw data"):
    raw_df = df.drop(columns=["view_percentile"], errors="ignore").copy()
    st.dataframe(
        raw_df,
        use_container_width=True,
        hide_index=True,
    )
