import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path


RAW_PATH   = "data/raw_crowd_data.csv"
CLEAN_PATH = "data/clean_crowd_data.csv"
PLOT_DIR   = Path("data/eda_plots")
PLOT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
PALETTE = {"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"}

def section1_raw_overview(df_raw):
    print("\n" + "═" * 60)
    print("  SECTION 1 — RAW DATA OVERVIEW")
    print("═" * 60)

    print(f"\n📦 Shape            : {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
    print(f"🔢 Duplicate rows   : {df_raw.duplicated().sum()}")

    print("\n── Column Dtypes ───────────────────────────────────────────")
    print(df_raw.dtypes.to_string())

    total_cells = df_raw.shape[0] * df_raw.shape[1]
    null_counts = df_raw.isnull().sum()
    print(f"\n── Missing Values ──────────────────────────────────────────")
    print(f"   Total missing cells : {null_counts.sum()} / {total_cells}"
          f"  ({null_counts.sum()/total_cells*100:.2f}%)")
    for col, cnt in null_counts.items():
        if cnt > 0:
            print(f"   {col:<15} : {cnt:>4}  ({cnt/len(df_raw)*100:.1f}%)")

    print("\n── Dirty Values (sample) ───────────────────────────────────")
    for col in ["day", "place_type", "popularity", "area_type"]:
        uniq = df_raw[col].dropna().unique()
        print(f"   {col:<15}: {sorted(uniq)}")

    print("\n── Raw Crowd Label Distribution ────────────────────────────")
    vc = df_raw["crowd"].value_counts()
    for label, cnt in vc.items():
        print(f"   {label:<10}: {cnt:>5}  ({cnt/len(df_raw)*100:.1f}%)")

def section2_clean_stats(df):
    print("\n" + "═" * 60)
    print("  SECTION 2 — POST-CLEAN DESCRIPTIVE STATISTICS")
    print("═" * 60)

    print(f"\n📦 Shape            : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"✅ Missing values   : {df.isnull().sum().sum()}  (all cleaned)")

    print("\n── Numeric Summary ─────────────────────────────────────────")
    print(df.describe().round(2).to_string())

    print("\n── Categorical Columns ─────────────────────────────────────")
    cat_cols = df.select_dtypes(include="object").columns
    for col in cat_cols:
        print(f"\n   {col}:")
        vc = df[col].value_counts()
        for val, cnt in vc.items():
            print(f"     {str(val):<12}: {cnt:>5}  ({cnt/len(df)*100:.1f}%)")

    print("\n── Encoded Column Ranges ───────────────────────────────────")
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        mn, mx = df[col].min(), df[col].max()
        print(f"   {col:<15}: min={mn}  max={mx}  unique={df[col].nunique()}")

    raw = pd.read_csv(RAW_PATH)
    pct = len(df) / len(raw) * 100
    print(f"\n── Data Retention Rate ─────────────────────────────────────")
    print(f"   Raw rows    : {len(raw):,}")
    print(f"   Clean rows  : {len(df):,}")
    print(f"   Retained    : {pct:.1f}%")
    print(f"   Removed     : {len(raw)-len(df):,} rows")

def section3_plots(df):
    print("\n" + "═" * 60)
    print("  SECTION 3 — CORRELATION & FEATURE ANALYSIS")
    print("═" * 60)

    # Correlation matrix 
    num_df = df.select_dtypes(include=[np.number])
    corr   = num_df.corr()

    print("\n── Pearson Correlation with 'crowd' ───────────────────────")
    crowd_corr = corr["crowd"].drop("crowd").sort_values(key=abs, ascending=False)
    for feat, val in crowd_corr.items():
        bar = "█" * int(abs(val) * 20)
        sign = "+" if val >= 0 else "-"
        print(f"   {feat:<15}: {sign}{abs(val):.4f}  {bar}")

    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="RdYlGn", center=0, linewidths=0.5,
        ax=ax, annot_kws={"size": 9}
    )
    ax.set_title("Feature Correlation Matrix (Encoded Values)", fontsize=13, pad=12)
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "01_correlation_heatmap.png", dpi=150)
    plt.close(fig)
    print("\n   📊 Saved: 01_correlation_heatmap.png")

    #  Crowd distribution
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    crowd_labels = {0: "Low", 1: "Medium", 2: "High"}
    crowd_series = df["crowd"].map(crowd_labels)
    colors = [PALETTE[crowd_labels[i]] for i in sorted(crowd_labels)]

    crowd_series.value_counts(sort=False).plot(
        kind="bar", ax=axes[0], color=colors, edgecolor="white", width=0.6
    )
    axes[0].set_title("Crowd Label Distribution")
    axes[0].set_xlabel("Crowd Level"); axes[0].set_ylabel("Count")
    axes[0].tick_params(axis="x", rotation=0)

    crowd_series.value_counts().plot(
        kind="pie", ax=axes[1], autopct="%1.1f%%",
        colors=colors, startangle=90, wedgeprops={"edgecolor": "white"}
    )
    axes[1].set_title("Crowd Level Share"); axes[1].set_ylabel("")

    plt.tight_layout()
    fig.savefig(PLOT_DIR / "02_crowd_distribution.png", dpi=150)
    plt.close(fig)
    print("   📊 Saved: 02_crowd_distribution.png")

    # Crowd by hour 
    fig, ax = plt.subplots(figsize=(12, 4))
    hour_crowd = df.groupby("hour")["crowd"].mean()
    ax.plot(hour_crowd.index, hour_crowd.values, marker="o", color="#3498db", linewidth=2)
    ax.fill_between(hour_crowd.index, hour_crowd.values, alpha=0.15, color="#3498db")
    ax.set_title("Average Crowd Score by Hour of Day")
    ax.set_xlabel("Hour"); ax.set_ylabel("Mean Crowd (0=Low, 2=High)")
    ax.set_xticks(hour_crowd.index)
    ax.set_xticklabels([f"{h}:00" for h in hour_crowd.index], rotation=45)
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "03_crowd_by_hour.png", dpi=150)
    plt.close(fig)
    print("   📊 Saved: 03_crowd_by_hour.png")

    # Crowd by day
    day_order   = [0, 1, 2, 3, 4, 5, 6]
    day_names   = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_crowd   = df.groupby("day")["crowd"].mean().reindex(day_order)

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(day_names, day_crowd.values, color="#9b59b6", edgecolor="white", width=0.6)
    for b, v in zip(bars, day_crowd.values):
        ax.text(b.get_x() + b.get_width()/2, v + 0.02, f"{v:.2f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_title("Average Crowd Score by Day of Week")
    ax.set_xlabel("Day"); ax.set_ylabel("Mean Crowd Score")
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "04_crowd_by_day.png", dpi=150)
    plt.close(fig)
    print("   📊 Saved: 04_crowd_by_day.png")

    # Feature distributions
    n_cols = len(num_df.columns)
    n_rows = (n_cols + 3) // 4   # ceiling division
    fig, axes = plt.subplots(n_rows, 4, figsize=(16, 4 * n_rows))
    axes = axes.flatten()
    num_cols = num_df.columns.tolist()

    for i, col in enumerate(num_cols):
        sns.histplot(df[col], ax=axes[i], kde=True, color="#1abc9c", edgecolor="white")
        axes[i].set_title(f"Distribution: {col}")
        axes[i].set_xlabel(col); axes[i].set_ylabel("Count")

    for j in range(len(num_cols), len(axes)):
        axes[j].set_visible(False)

    plt.suptitle("Feature Distributions (After Encoding)", fontsize=13, y=1.01)
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "05_feature_distributions.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("   📊 Saved: 05_feature_distributions.png")

    #  Pairwise key features vs crowd
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    # hour vs crowd (boxplot)
    sns.boxplot(data=df, x="crowd", y="hour", ax=axes[0],
                palette=["#2ecc71", "#f39c12", "#e74c3c"])
    axes[0].set_title("Hour vs Crowd Level")
    axes[0].set_xticklabels(["Low", "Med", "High"])

    # peak_hour vs crowd (count)
    peak_crowd = df.groupby(["peak_hour", "crowd"]).size().unstack(fill_value=0)
    peak_crowd.index = ["Off-Peak", "Peak"]
    peak_crowd.columns = ["Low", "Medium", "High"]
    peak_crowd.plot(kind="bar", ax=axes[1], color=["#2ecc71", "#f39c12", "#e74c3c"],
                    edgecolor="white", width=0.6)
    axes[1].set_title("Peak Hour vs Crowd Level")
    axes[1].set_xlabel(""); axes[1].tick_params(axis="x", rotation=0)
    axes[1].legend(title="Crowd")

    # weekend vs crowd
    wk_crowd = df.groupby(["weekend", "crowd"]).size().unstack(fill_value=0)
    wk_crowd.index = ["Weekday", "Weekend"]
    wk_crowd.columns = ["Low", "Medium", "High"]
    wk_crowd.plot(kind="bar", ax=axes[2], color=["#2ecc71", "#f39c12", "#e74c3c"],
                  edgecolor="white", width=0.6)
    axes[2].set_title("Weekend vs Crowd Level")
    axes[2].set_xlabel(""); axes[2].tick_params(axis="x", rotation=0)
    axes[2].legend(title="Crowd")

    plt.suptitle("Key Feature Interactions with Crowd Level", fontsize=13)
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "06_feature_vs_crowd.png", dpi=150)
    plt.close(fig)
    print("   📊 Saved: 06_feature_vs_crowd.png")

    print("\n── Feature Means by Crowd Class ───────────────────────────")
    group_means = df.groupby("crowd")[num_cols].mean().round(3)
    group_means.index = group_means.index.map({0: "Low", 1: "Medium", 2: "High"})
    print(group_means.to_string())


if __name__ == "__main__":
    df_raw   = pd.read_csv(RAW_PATH)
    df_clean = pd.read_csv(CLEAN_PATH)

    section1_raw_overview(df_raw)
    section2_clean_stats(df_clean)
    section3_plots(df_clean)

    print("\n" + "═" * 60)
    print("  EDA COMPLETE")
    print(f"  All plots saved to → {PLOT_DIR}/")
    print("═" * 60 + "\n")