import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Powerlink Sales Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
  .main { background-color: #F8F9FA; }
  .metric-card {
    background: white;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 5px solid #1B2A4A;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    margin-bottom: 8px;
  }
  .metric-value { font-size: 2.2rem; font-weight: 700; color: #1B2A4A; line-height: 1.1; }
  .metric-label { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: .06em; margin-top: 2px; }
  .hot-card  { border-left-color: #991B1B; }
  .warm-card { border-left-color: #854D0E; }
  .disp-card { border-left-color: #166534; }
  .info-card { border-left-color: #1B2A4A; }
  .section-header {
    background: #1B2A4A;
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    margin: 18px 0 10px 0;
  }
  .stDataFrame { border-radius: 8px; }
  div[data-testid="stSidebarContent"] { background-color: #1B2A4A; }
  div[data-testid="stSidebarContent"] .stMarkdown,
  div[data-testid="stSidebarContent"] label,
  div[data-testid="stSidebarContent"] .stSelectbox label,
  div[data-testid="stSidebarContent"] p { color: white !important; }
  div[data-testid="stSidebarContent"] h1,
  div[data-testid="stSidebarContent"] h2,
  div[data-testid="stSidebarContent"] h3 { color: #AAC4DE !important; }
</style>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Powerlink_PowerBI_Data.csv", dtype=str, low_memory=False)
    num_cols = [
        "Certified_Beds", "Avg_Daily_Residents", "Overall_Stars",
        "Health_Inspection_Stars", "QM_Stars", "Staffing_Stars",
        "Num_Fines", "Fine_Amount_USD", "Num_Penalties",
        "HK_Direct_Labor_USD", "HK_Contract_Labor_USD",
        "Diet_Direct_Labor_USD", "Diet_Contract_Labor_USD",
        "EVS_Citations_3yr", "F880_Infection_Citations",
        "Dietary_Citations_3yr", "Priority_Sort"
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

df = load_data()

# ── Sidebar filters ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Powerlink")
    st.markdown("### Sales Intelligence")
    st.markdown("---")

    st.markdown("### 🔍 Filters")

    # Region
    regions = ["All Regions"] + sorted(df["Region"].dropna().unique().tolist())
    sel_region = st.selectbox("Region", regions)

    # State
    if sel_region != "All Regions":
        state_pool = df[df["Region"] == sel_region]["State"].dropna().unique()
    else:
        state_pool = df["State"].dropna().unique()
    states = ["All States"] + sorted(state_pool.tolist())
    sel_state = st.selectbox("State", states)

    # Service line
    sel_service = st.selectbox(
        "Service Line",
        ["Both EVS & Dietary", "EVS Only", "Dietary Only"]
    )

    # Opportunity tier
    tiers = ["All Tiers", "HOT HOT Targets", "Hot Leads",
             "Incumbent Displacement", "Warm Leads"]
    sel_tier = st.selectbox("Opportunity Tier", tiers)

    # Star rating
    sel_stars = st.selectbox(
        "Health Inspection Stars",
        ["All Ratings", "1 Star (Worst)", "2 Stars", "3 Stars",
         "4 Stars", "5 Stars (Best)"]
    )

    # Ownership
    own_types = ["All Ownership"] + sorted(df["Ownership_Type"].dropna().unique().tolist())
    sel_own = st.selectbox("Ownership Type", own_types)

    st.markdown("---")
    st.markdown("**Data source**")
    st.markdown("CMS HCRIS FY2024")
    st.markdown("Care Compare Apr 2026")
    st.caption("Refresh monthly with new CMS data")

# ── Apply filters ────────────────────────────────────────────
fdf = df.copy()

if sel_region != "All Regions":
    fdf = fdf[fdf["Region"] == sel_region]
if sel_state != "All States":
    fdf = fdf[fdf["State"] == sel_state]
if sel_own != "All Ownership":
    fdf = fdf[fdf["Ownership_Type"] == sel_own]

if sel_stars != "All Ratings":
    star_num = int(sel_stars[0])
    fdf = fdf[fdf["Health_Inspection_Stars"] == star_num]

if sel_tier == "HOT HOT Targets":
    if sel_service == "Dietary Only":
        fdf = fdf[fdf["HOT_HOT_Dietary"] == "Yes"]
    else:
        fdf = fdf[fdf["HOT_HOT_EVS"] == "Yes"]
elif sel_tier == "Hot Leads":
    fdf = fdf[fdf["Priority_Sort"] == 1]
elif sel_tier == "Incumbent Displacement":
    fdf = fdf[fdf["Priority_Sort"] == 2]
elif sel_tier == "Warm Leads":
    fdf = fdf[fdf["Priority_Sort"] == 3]

if sel_service == "EVS Only":
    fdf = fdf[fdf["EVS_Citations_3yr"].fillna(0) > 0]
elif sel_service == "Dietary Only":
    fdf = fdf[fdf["Dietary_Citations_3yr"].fillna(0) > 0]

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div style='background:#1B2A4A;padding:18px 24px;border-radius:10px;margin-bottom:18px'>
  <span style='color:white;font-size:1.5rem;font-weight:700'>POWERLINK</span>
  <span style='color:#AAC4DE;font-size:1rem;margin-left:12px'>SNF Sales Intelligence Dashboard</span>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

hot_evs  = int((fdf["HOT_HOT_EVS"] == "Yes").sum())
hot_diet = int((fdf["HOT_HOT_Dietary"] == "Yes").sum())
hot_tot  = int((fdf["Priority_Sort"] == 1).sum())
disp     = int((fdf["Priority_Sort"] == 2).sum())
warm     = int((fdf["Priority_Sort"] == 3).sum())

with c1:
    st.markdown(f"""<div class='metric-card hot-card'>
      <div class='metric-value'>{hot_evs}</div>
      <div class='metric-label'>🔥🔥 HOT HOT EVS</div></div>""",
      unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class='metric-card hot-card'>
      <div class='metric-value'>{hot_diet}</div>
      <div class='metric-label'>🔥🔥 HOT HOT Dietary</div></div>""",
      unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class='metric-card warm-card'>
      <div class='metric-value'>{hot_tot}</div>
      <div class='metric-label'>🔥 Hot Leads</div></div>""",
      unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class='metric-card disp-card'>
      <div class='metric-value'>{disp:,}</div>
      <div class='metric-label'>🔄 Incumbent Targets</div></div>""",
      unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class='metric-card info-card'>
      <div class='metric-value'>{len(fdf):,}</div>
      <div class='metric-label'>📋 Total Facilities</div></div>""",
      unsafe_allow_html=True)

# ── Row 2: Map + Tier Chart ──────────────────────────────────
st.markdown("<div class='section-header'>📍 Geographic Distribution</div>",
            unsafe_allow_html=True)

map_col, chart_col = st.columns([3, 2])

with map_col:
    map_data = fdf.groupby("State").agg(
        HOT_HOT_EVS_Count=("HOT_HOT_EVS", lambda x: (x == "Yes").sum()),
        Hot_Leads=("Priority_Sort", lambda x: (x == 1).sum()),
        Total=("Facility_Name", "count"),
        Avg_Stars=("Overall_Stars", "mean")
    ).reset_index()

    fig_map = px.choropleth(
        map_data,
        locations="State",
        locationmode="USA-states",
        color="HOT_HOT_EVS_Count",
        scope="usa",
        color_continuous_scale=[
            [0, "#E8EEF5"], [0.3, "#7899B4"],
            [0.7, "#CB9A00"], [1, "#991B1B"]
        ],
        hover_data={
            "State": True,
            "HOT_HOT_EVS_Count": True,
            "Hot_Leads": True,
            "Total": True
        },
        labels={
            "HOT_HOT_EVS_Count": "HOT HOT EVS",
            "Hot_Leads": "Hot Leads",
            "Total": "Total Facilities"
        },
        title="HOT HOT EVS Targets by State"
    )
    fig_map.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="HOT HOT<br>EVS Count"),
        paper_bgcolor="white",
        geo_bgcolor="white"
    )
    st.plotly_chart(fig_map, use_container_width=True)

with chart_col:
    tier_counts = pd.DataFrame({
        "Tier": [
            "HOT HOT EVS", "HOT HOT Dietary",
            "Hot Leads", "Incumbent Targets",
            "Warm Leads"
        ],
        "Count": [
            hot_evs, hot_diet, hot_tot, disp, warm
        ],
        "Color": [
            "#991B1B", "#7F1D1D",
            "#DC2626", "#166534",
            "#854D0E"
        ]
    })

    fig_bar = go.Figure(go.Bar(
        x=tier_counts["Count"],
        y=tier_counts["Tier"],
        orientation="h",
        marker_color=tier_counts["Color"],
        text=tier_counts["Count"].apply(lambda x: f"{x:,}"),
        textposition="outside"
    ))
    fig_bar.update_layout(
        title="Opportunity Tiers",
        xaxis_title="Number of Facilities",
        yaxis_title="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"r": 60, "t": 40, "l": 10, "b": 40},
        height=320
    )
    fig_bar.update_xaxes(showgrid=True, gridcolor="#EEE")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Star rating donut
    star_counts = fdf["Health_Inspection_Stars"].dropna().astype(int).value_counts().sort_index()
    star_labels = [f"{i} ⭐" for i in star_counts.index]
    fig_donut = go.Figure(go.Pie(
        labels=star_labels,
        values=star_counts.values,
        hole=0.55,
        marker_colors=["#991B1B","#DC2626","#F59E0B","#22C55E","#166534"][:len(star_counts)]
    ))
    fig_donut.update_layout(
        title="Health Inspection Stars",
        paper_bgcolor="white",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=260,
        showlegend=True,
        legend=dict(orientation="v", x=1, y=0.5)
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ── Tabs ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Facility Records</div>",
            unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔥🔥 HOT HOT EVS",
    "🔥🔥 HOT HOT Dietary",
    "🔥 Hot Leads & Warm",
    "🔄 All Facilities"
])

def show_table(data, cols, rename=None):
    data = data[cols].copy()
    if rename:
        data = data.rename(columns=rename)
    data = data.fillna("")
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        height=420
    )
    st.caption(f"{len(data):,} facilities shown")

evs_cols = [
    "State", "Facility_Name", "City", "Phone",
    "Certified_Beds", "Health_Inspection_Stars", "Overall_Stars",
    "EVS_Citations_3yr", "F880_Infection_Citations",
    "HK_Direct_Labor_USD", "HK_Contract_Labor_USD",
    "Ownership_Type", "Chain_Name", "CCN"
]
evs_rename = {
    "Facility_Name": "Facility", "Health_Inspection_Stars": "HI ⭐",
    "Overall_Stars": "Overall ⭐", "EVS_Citations_3yr": "EVS Citations",
    "F880_Infection_Citations": "F880 Count",
    "HK_Direct_Labor_USD": "HK Direct $",
    "HK_Contract_Labor_USD": "HK Contract $",
    "Ownership_Type": "Ownership", "Chain_Name": "Chain"
}

diet_cols = [
    "State", "Facility_Name", "City", "Phone",
    "Certified_Beds", "QM_Stars", "Health_Inspection_Stars",
    "Dietary_Citations_3yr",
    "Diet_Direct_Labor_USD", "Diet_Contract_Labor_USD",
    "Ownership_Type", "Chain_Name", "CCN"
]
diet_rename = {
    "Facility_Name": "Facility", "QM_Stars": "QM ⭐",
    "Health_Inspection_Stars": "HI ⭐",
    "Dietary_Citations_3yr": "Dietary Citations",
    "Diet_Direct_Labor_USD": "Diet Direct $",
    "Diet_Contract_Labor_USD": "Diet Contract $",
    "Ownership_Type": "Ownership", "Chain_Name": "Chain"
}

with tab1:
    hot_evs_df = fdf[fdf["HOT_HOT_EVS"] == "Yes"].sort_values(
        ["Health_Inspection_Stars", "EVS_Citations_3yr"],
        ascending=[True, False]
    )
    if len(hot_evs_df) == 0:
        st.info("No HOT HOT EVS facilities match current filters.")
    else:
        valid = [c for c in evs_cols if c in hot_evs_df.columns]
        show_table(hot_evs_df, valid, evs_rename)

with tab2:
    hot_diet_df = fdf[fdf["HOT_HOT_Dietary"] == "Yes"].sort_values(
        ["QM_Stars", "Dietary_Citations_3yr"],
        ascending=[True, False]
    )
    if len(hot_diet_df) == 0:
        st.info("No HOT HOT Dietary facilities match current filters.")
    else:
        valid = [c for c in diet_cols if c in hot_diet_df.columns]
        show_table(hot_diet_df, valid, diet_rename)

with tab3:
    hot_warm_df = fdf[fdf["Priority_Sort"].isin([1, 3])].sort_values(
        ["Priority_Sort", "Health_Inspection_Stars"],
        ascending=[True, True]
    )
    all_cols = [
        "Overall_Priority", "State", "Facility_Name", "City", "Phone",
        "Certified_Beds", "Health_Inspection_Stars", "Overall_Stars",
        "EVS_Opportunity_Clean", "Dietary_Opportunity_Clean",
        "EVS_Citations_3yr", "Dietary_Citations_3yr",
        "Ownership_Type", "CCN"
    ]
    valid = [c for c in all_cols if c in hot_warm_df.columns]
    show_table(hot_warm_df, valid, {
        "Facility_Name": "Facility",
        "Overall_Priority": "Priority",
        "Health_Inspection_Stars": "HI ⭐",
        "Overall_Stars": "Overall ⭐",
        "EVS_Opportunity_Clean": "EVS Status",
        "Dietary_Opportunity_Clean": "Dietary Status",
        "EVS_Citations_3yr": "EVS Cit.",
        "Dietary_Citations_3yr": "Diet Cit.",
        "Ownership_Type": "Ownership"
    })

with tab4:
    search = st.text_input("🔍 Search by facility name, city, or chain...", "")
    display_df = fdf.copy()
    if search:
        mask = (
            display_df["Facility_Name"].str.contains(search, case=False, na=False) |
            display_df["City"].str.contains(search, case=False, na=False) |
            display_df["Chain_Name"].str.contains(search, case=False, na=False)
        )
        display_df = display_df[mask]

    display_df = display_df.sort_values("Priority_Sort", ascending=True)
    all_cols2 = [
        "Overall_Priority", "State", "Facility_Name", "City", "Phone",
        "Certified_Beds", "Health_Inspection_Stars", "QM_Stars",
        "HOT_HOT_EVS", "HOT_HOT_Dietary",
        "EVS_Opportunity_Clean", "Dietary_Opportunity_Clean",
        "EVS_Citations_3yr", "Dietary_Citations_3yr",
        "Ownership_Type", "Chain_Name", "CCN"
    ]
    valid2 = [c for c in all_cols2 if c in display_df.columns]
    show_table(display_df, valid2, {
        "Facility_Name": "Facility",
        "Overall_Priority": "Priority",
        "Health_Inspection_Stars": "HI ⭐",
        "QM_Stars": "QM ⭐",
        "EVS_Opportunity_Clean": "EVS Status",
        "Dietary_Opportunity_Clean": "Dietary Status",
        "EVS_Citations_3yr": "EVS Cit.",
        "Dietary_Citations_3yr": "Diet Cit.",
        "Ownership_Type": "Ownership",
        "Chain_Name": "Chain"
    })

# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Data: CMS HCRIS FY2024 + Care Compare April 2026  |  "
    "14,699 Medicare/Medicaid-certified SNFs  |  "
    "Powerlink Sales Intelligence  |  Built with Claude + Streamlit"
)
