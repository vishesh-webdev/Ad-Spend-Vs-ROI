"""
Ad Spend vs ROI Analysis - Streamlit app
Vishesh Yadav | Roll No. 2500320140165 | MCA Data Analytics, ABES Engineering College
Mentor: Anjali Pandey Ma'am | Dataset: synthetic, fictional organisation BrightReach Digital

Run:  pip install streamlit pandas numpy scipy
      streamlit run app.py

Two data modes (sidebar):
  1. Report summary  - the published figures from the project report (no files needed).
  2. Upload CSV      - your own campaign-day file. Required columns:
       date, campaign, channel, region, category, type, spend, impressions,
       clicks, conversions, revenue
     Optional column: daily_budget (enables the "spend > 6x daily budget" rule).
"""
import numpy as np
import pandas as pd
import streamlit as st

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

st.set_page_config(page_title="Ad Spend vs ROI Analysis", page_icon="📈", layout="wide")

# ----------------------------------------------------------------- metrics
def safe_div(a, b):
    """Ratio on totals; missing or zero divisor gives NaN (shown as n/a), never 0."""
    return a / b if b and not pd.isna(b) and b != 0 else np.nan

def fmt_pct(x):  return "n/a" if pd.isna(x) else f"{x * 100:,.0f}%"
def fmt_num(x, d=2): return "n/a" if pd.isna(x) else f"{x:,.{d}f}"
def fmt_rs(x):
    if pd.isna(x): return "n/a"
    if abs(x) >= 1e7: return f"Rs {x / 1e7:.2f} Cr"
    if abs(x) >= 1e5: return f"Rs {x / 1e5:.1f} L"
    return f"Rs {x:,.0f}"

def metrics(df):
    """Compute every metric from totals. Missing values are skipped, not zeroed."""
    spend, rev = df["spend"].sum(), df["revenue"].sum()
    imp = df["impressions"].sum(min_count=1)
    clk = df["clicks"].sum(min_count=1)
    cnv = df["conversions"].sum(min_count=1)
    return {
        "Spend": spend, "Revenue": rev,
        "ROI": safe_div(rev - spend, spend), "ROAS": safe_div(rev, spend),
        "CTR": safe_div(clk, imp), "CPC": safe_div(spend, clk),
        "Conv. rate": safe_div(cnv, clk), "CPA": safe_div(spend, cnv),
    }

def metric_table(df, by):
    rows = []
    for key, g in df.groupby(by):
        m = metrics(g); m[by] = key; rows.append(m)
    return pd.DataFrame(rows).set_index(by).sort_values("ROAS", ascending=False)

def show_metric_table(t):
    out = t.copy()
    out["Spend"] = out["Spend"].map(fmt_rs); out["Revenue"] = out["Revenue"].map(fmt_rs)
    out["ROI"] = out["ROI"].map(fmt_pct); out["ROAS"] = out["ROAS"].map(fmt_num)
    for c in ["CTR", "Conv. rate"]:
        out[c] = out[c].map(lambda v: "n/a" if pd.isna(v) else f"{v * 100:.2f}%")
    out["CPC"] = out["CPC"].map(lambda v: "n/a" if pd.isna(v) else f"Rs {v:,.2f}")
    out["CPA"] = out["CPA"].map(lambda v: "n/a" if pd.isna(v) else f"Rs {v:,.0f}")
    st.dataframe(out, use_container_width=True)

# ------------------------------------------------------- built-in report data
CHANNELS = pd.DataFrame(
    [("Google Search", 3.17e7, 15.28e7, .0480, 14.16, .0341, 415),
     ("E-mail",        0.572e7, 2.73e7, .0321, 3.57, .0121, 296),
     ("LinkedIn",      1.50e7, 3.45e7, .0065, 38.97, .0470, 829),
     ("Meta (Facebook)", 2.32e7, 5.18e7, .0125, 9.18, .0129, 711),
     ("Instagram",     2.01e7, 3.80e7, .0091, 10.15, .0111, 918),
     ("YouTube",       2.63e7, 3.57e7, .0048, 6.05, .0048, 1249),
     ("Display Network", 1.35e7, 1.50e7, .0026, 4.05, .0025, 1639)],
    columns=["Channel", "Spend", "Revenue", "CTR", "CPC", "Conv. rate", "CPA"]).set_index("Channel")
CHANNELS["ROAS"] = CHANNELS["Revenue"] / CHANNELS["Spend"]
CHANNELS["ROI"] = CHANNELS["ROAS"] - 1
CHANNELS = CHANNELS[["Spend", "Revenue", "ROI", "ROAS", "CTR", "CPC", "Conv. rate", "CPA"]]

TYPES = pd.DataFrame({"Spend": [7.42e7 * 1, 6.13e7], "Revenue": [25.85e7, 9.66e7],
                      "CPA": [506, 1203]}, index=["Performance", "Awareness"])
TYPES["ROI"] = TYPES["Revenue"] / TYPES["Spend"] - 1
TYPES["ROAS"] = TYPES["Revenue"] / TYPES["Spend"]
TYPES["Spend"] = [7.42e7, 6.13e7]  # Rs 7.42 Cr / Rs 6.13 Cr

HEAT = pd.DataFrame(
    {"Electronics Accessories": [62, 89, 211, 198, 62], "Fashion & Apparel": [180, 32, 85, 89, 102],
     "Health & Wellness": [139, 92, 43, 211, 309], "Home & Kitchen": [396, 75, 129, 158, 379]},
    index=["Central", "East", "North", "South", "West"])
REGION = pd.Series({"West": 242, "Central": 208, "South": 177, "North": 94, "East": 70}, name="ROI %")
CATEGORY = pd.Series({"Home & Kitchen": 275, "Health & Wellness": 135,
                      "Electronics Accessories": 111, "Fashion & Apparel": 102}, name="ROI %")
SEASON = pd.Series([1.05, .89, .91, .95, .97, .88, .90, 1.05, 1.17, 1.26, 1.15, 1.04],
                   index=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
LOSSES = pd.DataFrame(
    [("Valentine Specials - YouTube - Electronics #50", "YouTube", "Awareness", "Rs 29.8 L", "Rs 17.7 L", "-41%", "Rs 12.1 L"),
     ("Republic Day Sale - Display - Electronics #02", "Display Network", "Awareness", "Rs 19.5 L", "Rs 7.8 L", "-60%", "Rs 11.7 L"),
     ("Year End Mega Sale - Display - HomeKitchen #40", "Display Network", "Awareness", "Rs 12.8 L", "Rs 5.3 L", "-58%", "Rs 7.4 L"),
     ("Year End Mega Sale - Display - Wellness #59", "Display Network", "Awareness", "Rs 21.9 L", "Rs 15.2 L", "-30%", "Rs 6.6 L"),
     ("Summer Fresh - Insta - Fashion #30", "Instagram", "Awareness", "Rs 27.5 L", "Rs 24.6 L", "-10%", "Rs 2.9 L"),
     ("Monsoon Mania - Display - Fashion #23", "Display Network", "Awareness", "Rs 16.1 L", "Rs 14.6 L", "-9%", "Rs 1.5 L"),
     ("Holi Colours Offer - Display - Electronics #18", "Display Network", "Awareness", "Rs 10.1 L", "Rs 9.0 L", "-11%", "Rs 1.1 L")],
    columns=["Campaign", "Channel", "Type", "Spend", "Revenue", "ROI", "Net loss"])
CORR = pd.DataFrame(
    [("All channels", 13622, .613, .566, np.nan, np.nan), ("Display Network", 1788, .146, .140, .34, .02),
     ("E-mail", 1948, .493, .421, .66, .16), ("Google Search", 1904, .615, .673, .89, .44),
     ("Instagram", 2119, .255, .268, .42, .08), ("LinkedIn", 1951, .519, .539, .76, .29),
     ("Meta (Facebook)", 1987, .632, .634, .93, .39), ("YouTube", 1925, .531, .528, .81, .26)],
    columns=["Group", "Daily rows", "Pearson r", "Spearman rho", "Log-log slope", "R-squared"]).set_index("Group")
WHATIF = pd.DataFrame(
    [("Display Network", "Google Search", "Rs 28,391", "Rs 27,075", "Rs 1.3 L", "+Rs 1.0 L"),
     ("Display Network", "E-mail", "Rs 28,391", "Rs 27,075", "Rs 1.3 L", "+Rs 1.0 L"),
     ("YouTube", "Google Search", "Rs 51,625", "Rs 57,921", "Rs 2.4 L", "+Rs 1.8 L"),
     ("Instagram", "E-mail", "Rs 40,931", "Rs 50,813", "Rs 1.9 L", "+Rs 1.3 L")],
    columns=["From", "To (20% of weekly spend moved)", "Spend moved / wk", "Revenue lost", "Revenue gained", "Net / wk"])
MISSING = pd.DataFrame({"Missing rows": [272, 340, 272, 500], "Share of rows": ["2.0%", "2.49%", "2.0%", "3.67%"]},
                       index=["impressions", "clicks", "conversions", "campaign_manager"])
REJECTED = pd.DataFrame(
    [(622, "2025-01-12", 5, "Rs 12,368", "Rs 15.1 L", "revenue outlier (ROAS > 30)"),
     (4723, "2025-07-06", 8, "Rs 1.5 L", "Rs 26,561", "spend outlier (> 6x daily budget)"),
     (4966, "2025-07-17", 57, "Rs 29,696", "Rs 15,259", "spend outlier (> 6x daily budget)"),
     (4991, "2025-07-19", 7, "Rs 4,925", "Rs 2.0 L", "revenue outlier (ROAS > 30)"),
     (7552, "2025-12-05", 35, "Rs 81,694", "Rs 19,904", "spend outlier (> 6x daily budget)"),
     (7770, "2025-12-17", 39, "Rs 6,757", "Rs 8.8 L", "revenue outlier (ROAS > 30)"),
     (9542, "2026-03-22", 52, "Rs 1.1 L", "Rs 20,617", "spend outlier (> 6x daily budget)"),
     (10836, "2026-05-21", 26, "Rs 1.0 L", "Rs 31,070", "spend outlier (> 6x daily budget)"),
     (13631, "2025-02-11", 8, "Rs 6,919", "Rs 21,867", "duplicate campaign-day"),
     (13632, "2025-04-17", 8, "Rs 5,774", "Rs 22,232", "duplicate campaign-day"),
     (13633, "2025-04-17", 1, "Rs 31,202", "Rs 92,824", "duplicate campaign-day")],
    columns=["Row", "Date", "Campaign", "Spend", "Revenue", "Reason"])

# --------------------------------------------------------------- CSV pipeline
REQUIRED = ["date", "campaign", "channel", "region", "category", "type",
            "spend", "impressions", "clicks", "conversions", "revenue"]

@st.cache_data(show_spinner=False)
def clean(raw: pd.DataFrame):
    """Reject (never silently edit) bad rows and list them with the reason."""
    df = raw.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in ["spend", "impressions", "clicks", "conversions", "revenue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["reason"] = ""
    ratio = df["revenue"] / df["spend"].replace(0, np.nan)
    df.loc[ratio > 30, "reason"] = "revenue outlier (ROAS > 30)"
    if "daily_budget" in df.columns:
        over = df["spend"] > 6 * pd.to_numeric(df["daily_budget"], errors="coerce")
        df.loc[over & (df["reason"] == ""), "reason"] = "spend outlier (> 6x daily budget)"
    dup = df.duplicated(["campaign", "date"], keep="first")
    df.loc[dup & (df["reason"] == ""), "reason"] = "duplicate campaign-day"
    rejected = df[df["reason"] != ""]
    return df[df["reason"] == ""].drop(columns="reason"), rejected

def run_what_if(clean_df, src, dst, share):
    """Power curve revenue = a * spend^b per channel (weekly); estimate shifting budget."""
    wk = clean_df.assign(week=clean_df["date"].dt.to_period("W")) \
                 .groupby(["channel", "week"])[["spend", "revenue"]].sum().reset_index()
    fits = {}
    for ch in (src, dst):
        g = wk[(wk["channel"] == ch) & (wk["spend"] > 0) & (wk["revenue"] > 0)]
        if len(g) < 5:
            return None
        b, ln_a = np.polyfit(np.log(g["spend"]), np.log(g["revenue"]), 1)
        fits[ch] = (np.exp(ln_a), b, g["spend"].mean())
    a_s, b_s, s_s = fits[src]; a_d, b_d, s_d = fits[dst]
    moved = share * s_s
    lost = a_s * s_s ** b_s - a_s * (s_s - moved) ** b_s
    gained = a_d * (s_d + moved) ** b_d - a_d * s_d ** b_d
    return moved, lost, gained, gained - lost

# ----------------------------------------------------------------------- UI
st.title("Ad Spend vs ROI Analysis")
st.caption("Which channels, campaigns and regions earn back what they cost? "
           "Vishesh Yadav | Roll No. 2500320140165 | MCA Data Analytics, ABES Engineering College")

with st.sidebar:
    st.header("Data")
    mode = st.radio("Source", ["Report summary", "Upload CSV"])
    st.info("All data in the project is synthetic (fictional organisation BrightReach Digital). "
            "Findings demonstrate the method, not real market outcomes.")

df = rejected = None
if mode == "Upload CSV":
    up = st.sidebar.file_uploader("Campaign-day CSV", type="csv")
    st.sidebar.caption("Columns: " + ", ".join(REQUIRED) + " (optional: daily_budget)")
    if up is None:
        st.warning("Upload a CSV in the sidebar, or switch to 'Report summary'.")
        st.stop()
    raw = pd.read_csv(up)
    missing_cols = [c for c in REQUIRED if c not in raw.columns]
    if missing_cols:
        st.error(f"Missing columns: {', '.join(missing_cols)}")
        st.stop()
    df, rejected = clean(raw)
    with st.sidebar:
        st.header("Filters")
        chs = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
        rg = st.multiselect("Region", sorted(df["region"].unique()), default=sorted(df["region"].unique()))
        ct = st.multiselect("Category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))
        lo, hi = df["date"].min().date(), df["date"].max().date()
        d1, d2 = st.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
    f = df[df["channel"].isin(chs) & df["region"].isin(rg) & df["category"].isin(ct)
           & (df["date"].dt.date >= d1) & (df["date"].dt.date <= d2)]
    if f.empty:
        st.warning("No rows match the filters.")
        st.stop()

tabs = st.tabs(["Overview", "Compare", "Statistics", "Data quality"])

# ---- Overview
with tabs[0]:
    if mode == "Report summary":
        k = st.columns(6)
        for col, (lab, val) in zip(k, [("Spend", "Rs 13.56 Cr"), ("Revenue", "Rs 35.52 Cr"), ("ROI", "162%"),
                                       ("ROAS", "2.62"), ("CTR", "0.60%"), ("CPA", "Rs 686")]):
            col.metric(lab, val)
        st.subheader("ROAS by channel (break-even = 1.0)")
        st.bar_chart(CHANNELS["ROAS"])
        st.success("Google Search (4.82) and E-mail (4.78) lead; Display Network (1.11) barely breaks even. "
                   "Performance campaigns return 248% ROI vs 58% for Awareness.")
        st.subheader("Seasonality index (month ROAS / overall ROAS)")
        st.bar_chart(SEASON)
    else:
        m = metrics(f)
        k = st.columns(6)
        for col, (lab, val) in zip(k, [("Spend", fmt_rs(m["Spend"])), ("Revenue", fmt_rs(m["Revenue"])),
                                       ("ROI", fmt_pct(m["ROI"])), ("ROAS", fmt_num(m["ROAS"])),
                                       ("CTR", "n/a" if pd.isna(m["CTR"]) else f"{m['CTR'] * 100:.2f}%"),
                                       ("CPA", "n/a" if pd.isna(m["CPA"]) else f"Rs {m['CPA']:,.0f}")]):
            col.metric(lab, val)
        t = metric_table(f, "channel")
        st.subheader("ROAS by channel (break-even = 1.0)")
        st.bar_chart(t["ROAS"])
        monthly = f.assign(month=f["date"].dt.to_period("M").astype(str)).groupby("month")[["spend", "revenue"]].sum()
        monthly["ROI %"] = (monthly["revenue"] / monthly["spend"] - 1) * 100
        st.subheader("Monthly spend and revenue")
        st.line_chart(monthly[["spend", "revenue"]])
        st.subheader("Monthly ROI (%)")
        st.line_chart(monthly["ROI %"])

# ---- Compare
with tabs[1]:
    if mode == "Report summary":
        st.subheader("Channel metrics (ranked by ROAS)")
        show_metric_table(CHANNELS)
        st.subheader("Awareness vs Performance")
        tt = TYPES[["Spend", "ROI", "ROAS", "CPA"]].copy()
        tt["Spend"] = tt["Spend"].map(fmt_rs); tt["ROI"] = tt["ROI"].map(fmt_pct)
        tt["ROAS"] = tt["ROAS"].map(fmt_num); tt["CPA"] = tt["CPA"].map(lambda v: f"Rs {v:,.0f}")
        st.dataframe(tt, use_container_width=True)
        c1, c2 = st.columns(2)
        c1.subheader("ROI by region (%)"); c1.bar_chart(REGION)
        c2.subheader("ROI by category (%)"); c2.bar_chart(CATEGORY)
        st.subheader("ROI (%) by region and category")
        st.dataframe(HEAT.style.background_gradient(cmap="Reds").format("{:.0f}%"), use_container_width=True)
        st.subheader("Loss-making campaigns (7 of 60; Rs 43.4 L net loss)")
        st.dataframe(LOSSES, use_container_width=True, hide_index=True)
    else:
        st.subheader("Channel metrics")
        show_metric_table(metric_table(f, "channel"))
        st.subheader("Awareness vs Performance")
        show_metric_table(metric_table(f, "type"))
        c1, c2 = st.columns(2)
        c1.subheader("ROI by region"); c1.bar_chart(metric_table(f, "region")["ROI"] * 100)
        c2.subheader("ROI by category"); c2.bar_chart(metric_table(f, "category")["ROI"] * 100)
        heat = f.groupby(["region", "category"])[["spend", "revenue"]].sum()
        heat = ((heat["revenue"] / heat["spend"] - 1) * 100).unstack("category")
        st.subheader("ROI (%) by region and category")
        st.dataframe(heat.style.background_gradient(cmap="Reds").format("{:.0f}%"), use_container_width=True)
        cp = metric_table(f, "campaign")
        loss = cp[cp["ROAS"] < 1].copy()
        loss["Net loss"] = loss["Spend"] - loss["Revenue"]
        st.subheader(f"Loss-making campaigns ({len(loss)} of {len(cp)})")
        if loss.empty:
            st.write("None in the current selection.")
        else:
            st.dataframe(loss.sort_values("Net loss", ascending=False)[["Spend", "Revenue", "ROI", "ROAS", "Net loss"]],
                         use_container_width=True)

# ---- Statistics
with tabs[2]:
    if mode == "Report summary":
        st.subheader("Spend vs revenue correlation and diminishing returns")
        st.dataframe(CORR.style.format({"Pearson r": "{:.3f}", "Spearman rho": "{:.3f}",
                                        "Log-log slope": "{:.2f}", "R-squared": "{:.2f}", "Daily rows": "{:,.0f}"},
                                       na_rep="-"), use_container_width=True)
        st.caption("Slope below 1.0 means returns diminish. All seven channels are below 1.0. "
                   "Display and Instagram have low R-squared, so read their slopes with caution.")
        st.subheader("Is the ROI gap between channels real?")
        c1, c2 = st.columns(2)
        c1.metric("One-way ANOVA", "F = 489.6", "p < 0.0001")
        c2.metric("Kruskal-Wallis", "H = 1264.7", "p < 0.0001")
        st.success("Both p-values are below 0.05, so ROI differs significantly between channels (1,993 campaign-weeks).")
        st.subheader("Budget what-if (sample results)")
        st.dataframe(WHATIF, use_container_width=True, hide_index=True)
        st.caption("An estimate, not a forecast: assumes the past 24 months of spend-revenue curves keep holding.")
    elif not HAS_SCIPY:
        st.error("Install scipy to see the statistics: pip install scipy")
    else:
        st.subheader("Spend vs revenue (daily rows, full clean data)")
        rows = []
        for name, g in [("All channels", df)] + list(df.groupby("channel")):
            g = g[(g["spend"] > 0) & (g["revenue"] > 0)]
            if len(g) < 5:
                continue
            r, p = stats.pearsonr(g["spend"], g["revenue"])
            rho, _ = stats.spearmanr(g["spend"], g["revenue"])
            slope, _, rv, _, _ = stats.linregress(np.log(g["spend"]), np.log(g["revenue"]))
            rows.append((name, len(g), r, "< 0.0001" if p < 1e-4 else f"{p:.4f}", rho, slope, rv ** 2,
                         "Diminishing returns" if slope < 1 else "Constant or increasing"))
        st.dataframe(pd.DataFrame(rows, columns=["Group", "Rows", "Pearson r", "p-value", "Spearman rho",
                                                 "Log-log slope", "R-squared", "Verdict"]).set_index("Group")
                     .style.format({"Pearson r": "{:.3f}", "Spearman rho": "{:.3f}",
                                    "Log-log slope": "{:.2f}", "R-squared": "{:.2f}"}),
                     use_container_width=True)
        st.subheader("Is the ROI gap between channels real?")
        w = df.assign(week=df["date"].dt.to_period("W")).groupby(["campaign", "channel", "week"])[["spend", "revenue"]].sum()
        w = w[w["spend"] > 0]
        w["roi"] = w["revenue"] / w["spend"] - 1
        groups = [g["roi"].values for _, g in w.groupby("channel") if len(g) > 1]
        if len(groups) >= 2:
            F, pF = stats.f_oneway(*groups); H, pH = stats.kruskal(*groups)
            c1, c2 = st.columns(2)
            c1.metric("One-way ANOVA", f"F = {F:,.1f}", "p < 0.0001" if pF < 1e-4 else f"p = {pF:.4f}")
            c2.metric("Kruskal-Wallis", f"H = {H:,.1f}", "p < 0.0001" if pH < 1e-4 else f"p = {pH:.4f}")
            (st.success if max(pF, pH) < 0.05 else st.info)(
                "ROI differs significantly between channels (both p < 0.05)." if max(pF, pH) < 0.05
                else "The gap is called significant only when both tests give p < 0.05; it is not here.")
        st.subheader("Budget what-if")
        chl = sorted(df["channel"].unique())
        c1, c2, c3 = st.columns(3)
        src = c1.selectbox("Move budget from", chl, index=0)
        dst = c2.selectbox("Move budget to", chl, index=min(1, len(chl) - 1))
        share = c3.slider("Share of source weekly spend", 5, 50, 20, step=5) / 100
        if src == dst:
            st.info("Choose two different channels.")
        else:
            res = run_what_if(df, src, dst, share)
            if res is None:
                st.info("Not enough weekly data to fit a curve for these channels.")
            else:
                moved, lost, gained, net = res
                a, b, c, d = st.columns(4)
                a.metric("Spend moved / wk", fmt_rs(moved)); b.metric("Revenue lost", fmt_rs(lost))
                c.metric("Revenue gained", fmt_rs(gained)); d.metric("Net change / wk", fmt_rs(net))
                st.caption("An estimate, not a forecast. Ignores seasonality and audience limits.")

# ---- Data quality
with tabs[3]:
    if mode == "Report summary":
        c1, c2, c3 = st.columns(3)
        c1.metric("Raw rows", "13,633"); c2.metric("Rejected", "11"); c3.metric("Clean rows", "13,622")
        st.subheader("Missing values (kept as not available, never zero)")
        st.dataframe(MISSING, use_container_width=True)
        st.subheader("Rejected rows")
        st.dataframe(REJECTED, use_container_width=True, hide_index=True)
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Raw rows", f"{len(raw):,}"); c2.metric("Rejected", f"{len(rejected):,}"); c3.metric("Clean rows", f"{len(df):,}")
        st.subheader("Missing values (kept as not available, never zero)")
        mv = raw.isna().sum().rename("Missing rows").to_frame()
        mv["Share of rows"] = (mv["Missing rows"] / len(raw) * 100).round(2).astype(str) + "%"
        st.dataframe(mv[mv["Missing rows"] > 0], use_container_width=True)
        st.subheader("Rejected rows")
        st.dataframe(rejected[["date", "campaign", "spend", "revenue", "reason"]], use_container_width=True)
    st.markdown("**Rules:** revenue more than 30x spend; spend above 6x daily budget; duplicate campaign-day. "
                "Bad rows are listed, never silently edited.")
