import pandas as pd


REQUIRED_COLUMNS = [
    "title",
    "views",
    "likes",
    "comments",
    "shares",
    "duration",
]

PERFORMANCE_ORDER = [
    "🔥 Viral",
    "🟢 High",
    "🟡 Normal",
    "🔴 Low",
]



def load_data(uploaded_file=None):
    """Load, validate, clean, and enrich TikTok video data."""
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_csv("data/videos.csv")
    except pd.errors.EmptyDataError as exc:
        raise ValueError("File CSV kosong. Upload CSV yang berisi data video.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            "Format CSV tidak valid. Pastikan file menggunakan struktur CSV yang benar."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Encoding CSV tidak didukung. Simpan file sebagai CSV UTF-8 lalu upload ulang."
        ) from exc
    except Exception as exc:
        raise ValueError(f"CSV tidak dapat dibaca: {exc}") from exc

    if df.empty:
        raise ValueError("CSV tidak memiliki baris data video.")

    # Normalize header spacing.
    df.columns = [str(col).strip() for col in df.columns]

    # Duplicate headers make downstream analysis ambiguous.
    duplicated_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicated_columns:
        raise ValueError(
            "CSV memiliki nama kolom duplikat: " + ", ".join(duplicated_columns)
        )

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError("Kolom wajib belum ditemukan: " + ", ".join(missing))

    warnings = []
    rows_before_cleaning = len(df)

    # Keep title readable even when some rows do not have one.
    title_as_text = df["title"].fillna("").astype(str).str.strip()
    blank_title_count = int(title_as_text.eq("").sum())
    if blank_title_count:
        df["title"] = title_as_text.mask(title_as_text.eq(""), "Untitled video")
        warnings.append(
            f"{blank_title_count} baris memiliki title kosong dan diberi nama 'Untitled video'."
        )
    else:
        df["title"] = title_as_text

    numeric_columns = [
        "views",
        "likes",
        "comments",
        "shares",
        "duration",
    ]

    invalid_cells = 0
    negative_cells = 0

    for col in numeric_columns:
        original = df[col]
        missing_mask = original.isna() | original.astype(str).str.strip().eq("")
        converted = pd.to_numeric(original, errors="coerce")

        invalid_mask = converted.isna() & ~missing_mask
        invalid_count = int(invalid_mask.sum())
        missing_count = int(missing_mask.sum())

        if invalid_count:
            warnings.append(
                f"{invalid_count} nilai non-numerik pada kolom '{col}' diubah menjadi 0."
            )
            invalid_cells += invalid_count

        if missing_count:
            warnings.append(
                f"{missing_count} nilai kosong pada kolom '{col}' diubah menjadi 0."
            )

        negative_mask = converted.notna() & converted.lt(0)
        negative_count = int(negative_mask.sum())
        if negative_count:
            warnings.append(
                f"{negative_count} nilai negatif pada kolom '{col}' dibatasi menjadi 0."
            )
            negative_cells += negative_count

        df[col] = converted.fillna(0).clip(lower=0)

    # Prevent a completely invalid core views column from producing a misleading dashboard.
    if (df["views"] == 0).all() and rows_before_cleaning > 0:
        raise ValueError(
            "Kolom 'views' tidak memiliki nilai views yang valid di dataset. "
            "Periksa kembali data views sebelum melanjutkan."
        )

    interactions = df["likes"] + df["comments"] + df["shares"]
    denominator = df["views"].mask(df["views"].eq(0), 1)
    df["engagement_rate"] = (interactions / denominator) * 100
    df.loc[df["views"].eq(0), "engagement_rate"] = 0.0

    # Relative performance based on view percentile inside this dataset.
    df["view_percentile"] = df["views"].rank(pct=True)

    df["performance"] = df["view_percentile"].apply(
        classify_performance
    )

    # Expose non-fatal validation notes to the UI without changing function outputs.
    df.attrs["validation_warnings"] = warnings
    df.attrs["validation_summary"] = {
        "rows": rows_before_cleaning,
        "columns": len(df.columns),
        "warning_count": len(warnings),
        "invalid_numeric_cells": invalid_cells,
        "negative_numeric_cells": negative_cells,
    }

    return df



def classify_performance(percentile):
    """Convert a view percentile into a readable performance label."""
    if percentile >= 0.90:
        return "🔥 Viral"
    if percentile >= 0.70:
        return "🟢 High"
    if percentile >= 0.30:
        return "🟡 Normal"
    return "🔴 Low"



def get_account_metrics(df):
    """Return the metrics shown in the account overview."""
    total_videos = len(df)
    total_views = df["views"].sum()
    total_likes = df["likes"].sum()

    average_views = df["views"].mean()
    average_engagement = df["engagement_rate"].mean()
    median_views = df["views"].median()

    top_3_views = df.nlargest(3, "views")["views"].sum()

    if total_views > 0:
        top_3_contribution = (top_3_views / total_views) * 100
    else:
        top_3_contribution = 0

    return {
        "total_videos": total_videos,
        "total_views": total_views,
        "total_likes": total_likes,
        "average_views": average_views,
        "average_engagement": average_engagement,
        "median_views": median_views,
        "top_3_contribution": top_3_contribution,
    }



def get_performance_distribution(df):
    """Return the number of videos in each performance tier."""
    counts = df["performance"].value_counts()

    return {label: int(counts.get(label, 0)) for label in PERFORMANCE_ORDER}



def get_performance_summary(df):
    """Aggregate key statistics by performance tier."""
    summary = (
        df.groupby("performance", observed=True)
        .agg(
            video_count=("title", "count"),
            average_views=("views", "mean"),
            average_likes=("likes", "mean"),
            average_engagement=("engagement_rate", "mean"),
            average_duration=("duration", "mean"),
        )
        .reindex(PERFORMANCE_ORDER)
    )

    return summary.fillna(0)



def get_top_videos(df, sort_by="views", limit=10):
    """Return the top videos using the selected metric."""
    allowed = {
        "views",
        "likes",
        "comments",
        "shares",
        "engagement_rate",
    }

    if sort_by not in allowed:
        raise ValueError(f"Sort metric tidak valid: {sort_by}")

    result = df.sort_values(sort_by, ascending=False).head(limit).copy()
    result.insert(0, "rank", range(1, len(result) + 1))
    return result
