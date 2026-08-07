import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Powerlink Sales Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  .main { background-color: #F8F9FA; }
  .metric-card {
    background: white; border-radius: 10px; padding: 16px 20px;
    border-left: 5px solid #1B2A4A;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); margin-bottom: 8px;
  }
  .metric-value { font-size: 2.2rem; font-weight: 700; color: #1B2A4A; line-height: 1.1; }
  .metric-label { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: .06em; margin-top: 2px; }
  .hot-card  { border-left-color: #991B1B; }
  .warm-card { border-left-color: #854D0E; }
  .disp-card { border-left-color: #166534; }
  .info-card { border-left-color: #1B2A4A; }
  div[data-testid="stSidebarContent"] { background-color: #1B2A4A; }
  div[data-testid="stSidebarContent"] label,
  div[data-testid="stSidebarContent"] p,
  div[data-testid="stSidebarContent"] .stMarkdown { color: white !important; }
  div[data-testid="stSidebarContent"] h1,
  div[data-testid="stSidebarContent"] h2,
  div[data-testid="stSidebarContent"] h3 { color: #AAC4DE !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("Powerlink_PowerBI_Data.csv", dtype=str, low_memory=False)

    # ── Normalize column names ──────────────────────────────
    # Map whatever columns exist in the CSV to the names the app expects
    rename = {}
    col_lower = {c.lower().strip(): c for c in df.columns}

    mappings = {
        "cms certification number (ccn)": "CCN",
        "ccn": "CCN",
        "facility name": "Facility_Name",
        "facility_name": "Facility_Name",
        "provider name": "Facility_Name",
        "provider address": "Address",
        "address": "Address",
        "city/town": "City",
        "city": "City",
        "state": "State",
        "zip code": "ZIP",
        "zip": "ZIP",
        "telephone number": "Phone",
        "phone": "Phone",
        "ownership type": "Ownership_Type",
        "ownership_type": "Ownership_Type",
        "number of certified beds": "Certified_Beds",
        "certified_beds": "Certified_Beds",
        "average number of residents per day": "Avg_Daily_Residents",
        "avg_daily_residents": "Avg_Daily_Residents",
        "overall rating": "Overall_Stars",
        "overall_rating": "Overall_Stars",
        "overall_stars": "Overall_Stars",
        "health inspection rating": "Health_Inspection_Stars",
        "health_inspection_rating": "Health_Inspection_Stars",
        "health_inspection_stars": "Health_Inspection_Stars",
        "qm rating": "QM_Stars",
        "qm_rating": "QM_Stars",
        "qm_stars": "QM_Stars",
        "staffing rating": "Staffing_Stars",
        "staffing_stars": "Staffing_Stars",
        "number of fines": "Num_Fines",
        "num_fines": "Num_Fines",
        "total amount of fines in dollars": "Fine_Amount_USD",
        "fine_amount_usd": "Fine_Amount_USD",
        "total number of penalties": "Num_Penalties",
        "num_penalties": "Num_Penalties",
        "number of citations from infection control inspections": "Infection_Control_Citations",
        "special focus status": "Special_Focus_Status",
        "special_focus_status": "Special_Focus_Status",
        "chain name": "Chain_Name",
        "chain_name": "Chain_Name",
        "evs_citation_count": "EVS_Citations_3yr",
        "evs_citations_3yr": "EVS_Citations_3yr",
        "dietary_citation_count": "Dietary_Citations_3yr",
        "dietary_citations_3yr": "Dietary_Citations_3yr",
        "f880_infection_citations": "F880_Infection_Citations",
        "f880_count": "F880_Infection_Citations",
        "hk_direct_labor_usd": "HK_Direct_Labor_USD",
        "hk_contract_labor_usd": "HK_Contract_Labor_USD",
        "diet_direct_labor_usd": "Diet_Direct_Labor_USD",
        "diet_contract_labor_usd": "Diet_Contract_Labor_USD",
        "evs_opportunity": "EVS_Opportunity",
        "evs_opportunity_clean": "EVS_Opportunity_Clean",
        "dietary_opportunity": "Dietary_Opportunity",
        "dietary_opportunity_clean": "Dietary_Opportunity_Clean",
        "overall_priority": "Overall_Priority",
        "priority_sort": "Priority_Sort",
        "hot_hot_evs": "HOT_HOT_EVS",
        "hot_hot_dietary": "HOT_HOT_Dietary",
        "region": "Region",
        "latitude": "Latitude",
        "longitude": "Longitude",
    }

    for src_lower, target in mappings.items():
        if src_lower in col_lower:
            orig = col_lower[src_lower]
            if orig != target:
                rename[orig] = target

    if rename:
        df = df.rename(columns=rename)

    # Multiple source aliases can normalize to the same target name (for
    # example, both "Health Inspection Rating" and
    # "Health_Inspection_Rating"). Coalesce those columns before any code
    # selects them; otherwise pandas returns a DataFrame instead of a Series.
    if df.columns.duplicated().any():
        coalesced = {}
        for col in dict.fromkeys(df.columns):
            matching = df.loc[:, df.columns == col]
            if matching.shape[1] == 1:
                coalesced[col] = matching.iloc[:, 0]
            else:
                nonblank = matching.replace(r"^\s*$", pd.NA, regex=True)
                coalesced[col] = nonblank.bfill(axis=1).iloc[:, 0]
        df = pd.DataFrame(coalesced, index=df.index)

    # ── Ensure required columns exist ───────────────────────
    required = [
        "CCN","Facility_Name","City","State","ZIP","Phone",
        "Ownership_Type","Certified_Beds","Overall_Stars",
        "Health_Inspection_Stars","QM_Stars","Staffing_Stars",
        "Chain_Name","Special_Focus_Status","Region",
        "EVS_Citations_3yr","Dietary_Citations_3yr",
        "HOT_HOT_EVS","HOT_HOT_Dietary","Priority_Sort"
    ]
    for col in required:
        if col not in df.columns:
            df[col] = ""

    # ── Add missing derived columns if not present ──────────
    if "HK_Contract_Labor_USD" not in df.columns:
        df["HK_Contract_Labor_USD"] = 0
    if "HK_Direct_Labor_USD" not in df.columns:
        df["HK_Direct_Labor_USD"] = 0
    if "Diet_Contract_Labor_USD" not in df.columns:
        df["Diet_Contract_Labor_USD"] = 0
    if "Diet_Direct_Labor_USD" not in df.columns:
        df["Diet_Direct_Labor_USD"] = 0
    if "F880_Infection_Citations" not in df.columns:
        df["F880_Infection_Citations"] = 0

    if "EVS_Opportunity_Clean" not in df.columns:
        df["EVS_Opportunity_Clean"] = df.get("EVS_Opportunity", "Unknown")
    if "Dietary_Opportunity_Clean" not in df.columns:
        df["Dietary_Opportunity_Clean"] = df.get("Dietary_Opportunity", "Unknown")
    if "Overall_Priority" not in df.columns:
        df["Overall_Priority"] = "5 — Insufficient data"

    # ── Numeric conversions ─────────────────────────────────
    num_cols = [
        "Certified_Beds","Avg_Daily_Residents","Overall_Stars",
        "Health_Inspection_Stars","QM_Stars","Staffing_Stars",
        "Num_Fines","Fine_Amount_USD","Num_Penalties",
        "HK_Direct_Labor_USD","HK_Contract_Labor_USD",
        "Diet_Direct_Labor_USD","Diet_Contract_Labor_USD",
        "EVS_Citations_3yr","Dietary_Citations_3yr",
        "F880_Infection_Citations","Priority_Sort"
    ]
    for c in num_cols:
        if c in df.columns and isinstance(df[c], pd.Series):
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ── Rebuild HOT HOT flags if missing/wrong ──────────────
    if df["HOT_HOT_EVS"].isin(["Yes","No"]).sum() == 0:
        df["HOT_HOT_EVS"] = ((df["HK_Direct_Labor_USD"] > 0) &
                              (df["HK_Contract_Labor_USD"] == 0) &
                              (df["EVS_Citations_3yr"] > 0)).map({True:"Yes",False:"No"})
    if df["HOT_HOT_Dietary"].isin(["Yes","No"]).sum() == 0:
        df["HOT_HOT_Dietary"] = ((df["Diet_Direct_Labor_USD"] > 0) &
                                  (df["Diet_Contract_Labor_USD"] == 0) &
                                  (df["Dietary_Citations_3yr"] > 0)).map({True:"Yes",False:"No"})

    # Fallback HOT HOT based on citations alone if no cost data
    if df["HOT_HOT_EVS"].eq("Yes").sum() == 0:
        df["HOT_HOT_EVS"] = (df["EVS_Citations_3yr"] >= 3).map({True:"Yes",False:"No"})
    if df["HOT_HOT_Dietary"].eq("Yes").sum() == 0:
        df["HOT_HOT_Dietary"] = (df["Dietary_Citations_3yr"] >= 3).map({True:"Yes",False:"No"})

    # Region fallback
    region_map = {
        "ME":"Northeast","NH":"Northeast","VT":"Northeast","MA":"Northeast",
        "RI":"Northeast","CT":"Northeast","NY":"Northeast","NJ":"Northeast",
        "PA":"Northeast","DE":"Northeast","MD":"Northeast","DC":"Northeast",
        "WV":"Southeast","VA":"Southeast","NC":"Southeast","SC":"Southeast",
        "GA":"Southeast","FL":"Southeast","AL":"Southeast","MS":"Southeast",
        "TN":"Southeast","KY":"Southeast","AR":"Southeast","LA":"Southeast",
        "OH":"Midwest","IN":"Midwest","IL":"Midwest","MI":"Midwest",
        "WI":"Midwest","MN":"Midwest","IA":"Midwest","MO":"Midwest",
        "ND":"Midwest","SD":"Midwest","NE":"Midwest","KS":"Midwest",
        "TX":"South Central","OK":"South Central",
        "MT":"Mountain West","ID":"Mountain West","WY":"Mountain West",
        "CO":"Mountain West","NM":"Mountain West","AZ":"Mountain West",
        "UT":"Mountain West","NV":"Mountain West",
        "WA":"Pacific","OR":"Pacific","CA":"Pacific","AK":"Pacific","HI":"Pacific"
    }
    if df["Region"].eq("").all() or df["Region"].isna().all():
        df["Region"] = df["State"].map(region_map).fillna("Other")

    return df

df = load_data()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Powerlink")
    st.markdown("### Sales Intelligence")
    st.markdown("---")
    st.markdown("### 🔍 Filters")

    regions = ["All Regions"] + sorted(df["Region"].dropna().replace("","Other").unique().tolist())
    sel_region = st.selectbox("Region", regions)

    if sel_region != "All Regions":
        state_pool = df[df["Region"] == sel_region]["State"].dropna().unique()
    else:
        state_pool = df["State"].dropna().unique()
    states = ["All States"] + sorted([s for s in state_pool if s])
    sel_state = st.selectbox("State", states)

    sel_service = st.selectbox("Service Line",
        ["Both EVS & Dietary", "EVS Only", "Dietary Only"])

    sel_tier = st.selectbox("Opportunity Tier",
        ["All Tiers","HOT HOT Targets","Hot Leads","Incumbent Displacement","Warm Leads"])

    sel_stars = st.selectbox("Health Inspection Stars",
        ["All Ratings","1 Star (Worst)","2 Stars","3 Stars","4 Stars","5 Stars (Best)"])

    own_vals = sorted([o for o in df["Ownership_Type"].dropna().unique() if o])
    own_types = ["All Ownership"] + own_vals
    sel_own = st.selectbox("Ownership Type", own_types)

    st.markdown("---")
    st.caption("CMS HCRIS FY2024 + Care Compare")
    st.caption("Refreshes monthly automatically")

# ── Filters ──────────────────────────────────────────────────
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
    fdf = fdf[fdf["EVS_Citations_3yr"] > 0]
elif sel_service == "Dietary Only":
    fdf = fdf[fdf["Dietary_Citations_3yr"] > 0]

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style='background:#1B2A4A;padding:18px 24px;border-radius:10px;margin-bottom:18px'>
  <span style='color:white;font-size:1.5rem;font-weight:700'>POWERLINK</span>
  <span style='color:#AAC4DE;font-size:1rem;margin-left:12px'>SNF Sales Intelligence Dashboard</span>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────
hot_evs  = int((fdf["HOT_HOT_EVS"] == "Yes").sum())
hot_diet = int((fdf["HOT_HOT_Dietary"] == "Yes").sum())
hot_tot  = int((fdf["Priority_Sort"] == 1).sum())
disp     = int((fdf["Priority_Sort"] == 2).sum())

c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    st.markdown(f"""<div class='metric-card hot-card'>
      <div class='metric-value'>{hot_evs}</div>
      <div class='metric-label'>🔥🔥 HOT HOT EVS</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class='metric-card hot-card'>
      <div class='metric-value'>{hot_diet}</div>
      <div class='metric-label'>🔥🔥 HOT HOT Dietary</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class='metric-card warm-card'>
      <div class='metric-value'>{hot_tot}</div>
      <div class='metric-label'>🔥 Hot Leads</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class='metric-card disp-card'>
      <div class='metric-value'>{disp:,}</div>
      <div class='metric-label'>🔄 Incumbent Targets</div></div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class='metric-card info-card'>
      <div class='metric-value'>{len(fdf):,}</div>
      <div class='metric-label'>📋 Total Facilities</div></div>""", unsafe_allow_html=True)

# ── Map + Charts ──────────────────────────────────────────────
st.markdown("<div style='background:#1B2A4A;color:white;padding:10px 18px;border-radius:8px;margin:18px 0 10px'>📍 Geographic Distribution</div>", unsafe_allow_html=True)

map_col, chart_col = st.columns([3,2])

with map_col:
    map_data = fdf.groupby("State").agg(
        HOT_HOT_EVS_Count=("HOT_HOT_EVS", lambda x: (x=="Yes").sum()),
        Hot_Leads=("Priority_Sort", lambda x: (x==1).sum()),
        Total=("Facility_Name","count")
    ).reset_index()
    fig_map = px.choropleth(
        map_data, locations="State", locationmode="USA-states",
        color="HOT_HOT_EVS_Count", scope="usa",
        color_continuous_scale=[[0,"#E8EEF5"],[0.3,"#7899B4"],[0.7,"#CB9A00"],[1,"#991B1B"]],
        hover_data={"State":True,"HOT_HOT_EVS_Count":True,"Hot_Leads":True,"Total":True},
        labels={"HOT_HOT_EVS_Count":"HOT HOT EVS","Hot_Leads":"Hot Leads","Total":"Total Facilities"},
        title="HOT HOT EVS Targets by State"
    )
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor="white", geo_bgcolor="white")
    st.plotly_chart(fig_map, use_container_width=True)

with chart_col:
    tier_df = pd.DataFrame({
        "Tier":["HOT HOT EVS","HOT HOT Dietary","Hot Leads","Incumbent Targets","Warm Leads"],
        "Count":[hot_evs, hot_diet, hot_tot, disp, int((fdf["Priority_Sort"]==3).sum())],
        "Color":["#991B1B","#7F1D1D","#DC2626","#166534","#854D0E"]
    })
    fig_bar = go.Figure(go.Bar(
        x=tier_df["Count"], y=tier_df["Tier"], orientation="h",
        marker_color=tier_df["Color"],
        text=tier_df["Count"].apply(lambda x: f"{x:,}"), textposition="outside"
    ))
    fig_bar.update_layout(title="Opportunity Tiers", xaxis_title="Facilities",
        paper_bgcolor="white", plot_bgcolor="white",
        margin={"r":60,"t":40,"l":10,"b":40}, height=320)
    fig_bar.update_xaxes(showgrid=True, gridcolor="#EEE")
    st.plotly_chart(fig_bar, use_container_width=True)

    star_counts = (
        pd.to_numeric(fdf["Health_Inspection_Stars"], errors="coerce")
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
    )
    if len(star_counts) > 0:
        fig_donut = go.Figure(go.Pie(
            labels=[f"{i} ⭐" for i in star_counts.index],
            values=star_counts.values, hole=0.55,
            marker_colors=["#991B1B","#DC2626","#F59E0B","#22C55E","#166534"][:len(star_counts)]
        ))
        fig_donut.update_layout(title="Health Inspection Stars", paper_bgcolor="white",
            margin={"r":0,"t":40,"l":0,"b":0}, height=260, showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)

# ── Tabs ──────────────────────────────────────────────────────
st.markdown("<div style='background:#1B2A4A;color:white;padding:10px 18px;border-radius:8px;margin:18px 0 10px'>📋 Facility Records</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔥🔥 HOT HOT EVS", "🔥🔥 HOT HOT Dietary",
    "🔥 Hot & Warm Leads", "🔄 All Facilities"
])

def show_table(data, cols, rename=None):
    avail = [c for c in cols if c in data.columns]
    out = data[avail].copy()
    if rename:
        out = out.rename(columns={k:v for k,v in rename.items() if k in out.columns})
    st.dataframe(out.fillna(""), use_container_width=True, hide_index=True, height=420)
    st.caption(f"{len(out):,} facilities shown")

evs_cols = ["State","Facility_Name","City","Phone","Certified_Beds",
            "Health_Inspection_Stars","Overall_Stars","EVS_Citations_3yr",
            "F880_Infection_Citations","HK_Direct_Labor_USD","HK_Contract_Labor_USD",
            "Ownership_Type","Chain_Name","CCN"]
evs_rename = {"Facility_Name":"Facility","Health_Inspection_Stars":"HI ⭐",
              "Overall_Stars":"Overall ⭐","EVS_Citations_3yr":"EVS Citations",
              "F880_Infection_Citations":"F880","HK_Direct_Labor_USD":"HK Direct $",
              "HK_Contract_Labor_USD":"HK Contract $","Ownership_Type":"Ownership","Chain_Name":"Chain"}

diet_cols = ["State","Facility_Name","City","Phone","Certified_Beds",
             "QM_Stars","Health_Inspection_Stars","Dietary_Citations_3yr",
             "Diet_Direct_Labor_USD","Diet_Contract_Labor_USD",
             "Ownership_Type","Chain_Name","CCN"]
diet_rename = {"Facility_Name":"Facility","QM_Stars":"QM ⭐","Health_Inspection_Stars":"HI ⭐",
               "Dietary_Citations_3yr":"Dietary Citations","Diet_Direct_Labor_USD":"Diet Direct $",
               "Diet_Contract_Labor_USD":"Diet Contract $","Ownership_Type":"Ownership","Chain_Name":"Chain"}

with tab1:
    hot_evs_df = fdf[fdf["HOT_HOT_EVS"]=="Yes"].sort_values(
        ["Health_Inspection_Stars","EVS_Citations_3yr"], ascending=[True,False])
    if len(hot_evs_df)==0:
        st.info("No HOT HOT EVS facilities match current filters.")
    else:
        show_table(hot_evs_df, evs_cols, evs_rename)

with tab2:
    hot_diet_df = fdf[fdf["HOT_HOT_Dietary"]=="Yes"].sort_values(
        ["QM_Stars","Dietary_Citations_3yr"], ascending=[True,False])
    if len(hot_diet_df)==0:
        st.info("No HOT HOT Dietary facilities match current filters.")
    else:
        show_table(hot_diet_df, diet_cols, diet_rename)

with tab3:
    hw = fdf[fdf["Priority_Sort"].isin([1,3])].sort_values(["Priority_Sort","Health_Inspection_Stars"])
    all_cols = ["Overall_Priority","State","Facility_Name","City","Phone","Certified_Beds",
                "Health_Inspection_Stars","Overall_Stars","EVS_Opportunity_Clean",
                "Dietary_Opportunity_Clean","EVS_Citations_3yr","Dietary_Citations_3yr",
                "Ownership_Type","CCN"]
    show_table(hw, all_cols, {"Facility_Name":"Facility","Overall_Priority":"Priority",
        "Health_Inspection_Stars":"HI ⭐","Overall_Stars":"Overall ⭐",
        "EVS_Opportunity_Clean":"EVS Status","Dietary_Opportunity_Clean":"Dietary Status",
        "EVS_Citations_3yr":"EVS Cit.","Dietary_Citations_3yr":"Diet Cit.","Ownership_Type":"Ownership"})

with tab4:
    search = st.text_input("🔍 Search by facility name, city, or chain...", "")
    disp_df = fdf.copy()
    if search:
        mask = (
            disp_df["Facility_Name"].str.contains(search, case=False, na=False) |
            disp_df["City"].str.contains(search, case=False, na=False) |
            disp_df["Chain_Name"].str.contains(search, case=False, na=False)
        )
        disp_df = disp_df[mask]
    disp_df = disp_df.sort_values("Priority_Sort")
    all_cols2 = ["Overall_Priority","State","Facility_Name","City","Phone","Certified_Beds",
                 "Health_Inspection_Stars","QM_Stars","HOT_HOT_EVS","HOT_HOT_Dietary",
                 "EVS_Citations_3yr","Dietary_Citations_3yr","Ownership_Type","Chain_Name","CCN"]
    show_table(disp_df, all_cols2, {"Facility_Name":"Facility","Overall_Priority":"Priority",
        "Health_Inspection_Stars":"HI ⭐","QM_Stars":"QM ⭐",
        "EVS_Citations_3yr":"EVS Cit.","Dietary_Citations_3yr":"Diet Cit.","Ownership_Type":"Ownership","Chain_Name":"Chain"})

st.markdown("---")
st.caption("Data: CMS HCRIS FY2024 + Care Compare | 14,699 Medicare/Medicaid SNFs | Powerlink Sales Intelligence")
