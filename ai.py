import os

from analytics import PERFORMANCE_ORDER


def build_ai_prompt(df):
    """Build a strictly grounded prompt from analytics produced by Python."""
    total_videos = len(df)
    total_views = df["views"].sum()
    average_views = df["views"].mean()
    median_views = df["views"].median()
    average_likes = df["likes"].mean()
    average_comments = df["comments"].mean()
    average_shares = df["shares"].mean()
    average_engagement = df["engagement_rate"].mean()

    top_3_views = df.nlargest(3, "views")["views"].sum()

    if total_views > 0:
        top_3_contribution = (top_3_views / total_views) * 100
    else:
        top_3_contribution = 0

    performance_summary = (
        df.groupby("performance", observed=True)
        .agg(
            video_count=("title", "count"),
            average_views=("views", "mean"),
            average_likes=("likes", "mean"),
            average_engagement=("engagement_rate", "mean"),
            average_duration=("duration", "mean"),
        )
        .reindex(PERFORMANCE_ORDER)
        .fillna(0)
        .round(2)
        .to_dict(orient="index")
    )

    top_videos = (
        df.sort_values("views", ascending=False)
        .head(5)[
            [
                "title",
                "views",
                "likes",
                "comments",
                "shares",
                "duration",
                "engagement_rate",
                "performance",
            ]
        ]
        .round(2)
        .to_dict(orient="records")
    )

    return f"""
Kamu adalah analis performa konten TikTok yang harus sangat disiplin terhadap data.

Tugasmu: ubah hasil analytics Python di bawah menjadi insight yang berguna bagi creator.
ANALISIS HANYA BERDASARKAN DATA YANG BENAR-BENAR TERSEDIA.

ATURAN WAJIB:
1. Jangan mengarang angka, metric, event, perilaku audiens, karakteristik konten, atau informasi lain yang tidak ada di data.
2. Metric yang tersedia hanya: views, likes, comments, shares, duration, engagement_rate, performance, serta ringkasan turunannya.
3. JANGAN mengatakan bahwa data menunjukkan completion rate, retention, watch time, CTR, impressions, followers gained, atau metric lain yang tidak tersedia.
4. JANGAN mengklaim hubungan sebab-akibat. Jangan menggunakan atau menyiratkan bahwa suatu faktor "menyebabkan", "memicu", "menentukan", atau "pasti membuat" hasil tertentu, termasuk klaim tentang mekanisme algoritma TikTok.
5. Gunakan bahasa observasional seperti "terlihat pada dataset ini", "berasosiasi pada sampel ini", "cenderung", "tampak lebih tinggi", atau "perlu diuji lebih lanjut".
6. SELALU bedakan dengan jelas:
   - Fakta: angka atau pola yang langsung terlihat dari data.
   - Interpretasi: makna praktis yang masih masuk akal berdasarkan fakta.
   - Hipotesis: dugaan yang belum terbukti.
7. Jangan mengubah association menjadi causation.
8. Jangan menggunakan kata absolut seperti "selalu", "pasti", "terbukti", "jaminan", "formula", atau "secara pasti" ketika bukti tidak cukup.
9. Jangan menggunakan hanya 1-2 video sebagai bukti untuk membuat aturan umum. Sebutkan bila bukti suatu pola terbatas.
10. Rekomendasi harus berupa eksperimen yang bisa diuji, bukan resep pasti atau jaminan hasil.
11. Jangan mengasumsikan topik, format, hook, editing, gaya visual, atau isi video bila informasi tersebut tidak tersedia di dataset.
12. Jangan memberikan saran media sosial generik yang tidak terhubung dengan data.
13. Jika sebuah kesimpulan membutuhkan metric yang tidak tersedia, katakan secara eksplisit bahwa kesimpulan tersebut belum dapat dibuat dari dataset saat ini.
14. Jangan menyebut hasil eksperimen sebagai sesuatu yang sudah terbukti.

LARANGAN KHUSUS:
- Jangan mengasumsikan data memiliki completion rate, retention, atau watch time hanya karena ada duration.
- Jangan mengasumsikan video pendek otomatis mendapat distribusi algoritmik lebih besar.
- Jangan mengasumsikan likes, comments, atau shares tertentu menyebabkan sebuah video mendapat lebih banyak views.
- Jangan mengasumsikan kita mengetahui topik atau format video hanya dari title dan metric performanya.
- Jangan menggunakan 1-2 video sebagai bukti yang cukup untuk membuat aturan umum.
- Jangan menyarankan target durasi tertentu sebagai "formula" hanya berdasarkan rata-rata kategori performance.

ACCOUNT OVERVIEW
Total video: {total_videos}
Total views: {total_views}
Average views: {average_views:.2f}
Median views: {median_views:.2f}
Average likes: {average_likes:.2f}
Average comments: {average_comments:.2f}
Average shares: {average_shares:.2f}
Average engagement rate: {average_engagement:.2f}%
Top 3 view contribution: {top_3_contribution:.2f}%

PERFORMANCE ANALYSIS
{performance_summary}

TOP 5 VIDEOS BY VIEWS
{top_videos}

Gunakan struktur berikut dan tetap spesifik terhadap data:

## 1. Temuan Utama
Berikan 3-5 fakta/observasi terpenting dari dataset.

## 2. Pola Performa yang Kuat
Pisahkan menjadi:
- Fakta: apa yang benar-benar terlihat dari data.
- Interpretasi: arti praktis yang masuk akal tanpa klaim sebab-akibat.
- Hipotesis: dugaan yang masih harus diuji.

## 3. Hal yang Perlu Diteliti
Tunjukkan 2-3 hal menarik atau tidak biasa yang belum bisa disimpulkan dari dataset ini.
Sebutkan data tambahan yang akan membantu mengujinya.

## 4. Eksperimen yang Direkomendasikan
Berikan tepat 3 eksperimen praktis.
Untuk setiap eksperimen jelaskan: apa yang diubah, apa yang dibandingkan,
dan metric yang digunakan untuk mengevaluasi hasilnya dari data yang tersedia.

Ingat: bila metric yang dibutuhkan belum tersedia, katakan bahwa metric tersebut belum tersedia.
"""


def get_ai_insight(df):
    """Send the grounded analytics prompt to Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return (
            "GEMINI_API_KEY belum diset. "
            "Analytics tetap bisa digunakan."
        )

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=build_ai_prompt(df),
        )

        return response.text

    except Exception as exc:
        return f"AI request gagal: {exc}"
