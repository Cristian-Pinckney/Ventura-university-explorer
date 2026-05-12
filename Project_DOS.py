import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import html as _html

st.set_page_config(layout="wide", page_title="University Explorer")

# CSS Styling
st.markdown("""
<style>

/* Title */
h1 {
    font-size: 2.6rem !important;
    font-weight: 800 !important;
}

/* Metric Cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: transform 0.2s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
}

/* Metric labels */
div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 12px !important;
    text-transform: uppercase;
}

/* Tabs */
button[data-baseweb="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 2px solid #ef4444 !important;
}

/* Sliders */
div[data-testid="stSlider"] label {
    color: #94a3b8 !important;
}

/* Remove footer */
footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# Loading Data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/cpinckney-salad/PROJECT2W-COORDINATES/main/PROJECT1%20(W%3ACoordinates).CSV"    data = pd.read_csv(url)
    data.columns = data.columns.str.strip().str.lower()
    
    cols = ['completion rate','retention rate','tuition','earnings 10yr',
            'median student debt','roi','avg_rating','avg_difficulty']

    for col in cols:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col].astype(str)
                .str.replace('%','')
                .str.replace('$','')
                .str.replace(',',''),
                errors='coerce'
            ).fillna(0)

            if 'rate' in col and data[col].max() > 1:
                data[col] /= 100

    data['school_display'] = data['school'].str.title()
    data['city_display'] = data['city'].str.title()
    data['state_display'] = data['state'].str.upper()

    data['roi_str'] = data['roi'].map(lambda x: f"{x:,.0f}")
    data['earnings_str'] = data['earnings 10yr'].map(lambda x: f"{x:,.0f}")
    data['debt_str'] = data['median student debt'].map(lambda x: f"{x:,.0f}")
    data['tuition_str'] = data['tuition'].map(lambda x: f"{x:,.0f}")
    data['rating_str'] = data['avg_rating'].map(lambda x: f"{x:.2f}")
    data['diff_str'] = data['avg_difficulty'].map(lambda x: f"{x:.2f}")
    data['comp_str'] = data['completion rate'].map(lambda x: f"{x*100:.1f}%")
    data['ret_str'] = data['retention rate'].map(lambda x: f"{x*100:.1f}%")

    school_info = {
        'california lutheran university': {
            'color': [102, 0, 153], 'accent': '#FFD700',
            'img': 'https://www.callutheran.edu/_resources/img/ldp/.private_ldp/a721/production/master/ed9a74f5-2693-452c-b9de-464c1bdad26a.jpg'
        },
        'pepperdine university': {
            'color': [0, 0, 255], 'accent': '#F97316',
            'img': 'https://www.pepperdine.edu/about/images/222375-malibu-campus-full.jpg'
        },
        'california state university-northridge': {
            'color': [210, 0, 0], 'accent': "#FFFFFF",
            'img': 'https://nse.org/hubfs/Campus%20Images/California%20State%20University%20Northridge/campus-profile-hero.jpg'
        },
        'california state university-channel islands': {
            'color': [192, 192, 192], 'accent': "#6A717CFF",
            'img': 'https://www.csuci.edu/img/launch-virtual-tour-16x9.jpg'
        },
        'university of california-santa barbara': {
            'color': [40, 90, 136], 'accent': "#2E48F7FF",
            'img': 'https://www.alumni.ucsb.edu/sites/default/files/images/welcome/stay-connected-campus-aerial.jpg'
        }
    }
    data['fill_color'] = data['school'].str.lower().map(lambda x: school_info.get(x, {'color':[255,165,0]})['color'])
    data['accent_color'] = data['school'].str.lower().map(lambda x: school_info.get(x, {'accent':'#38bdf8'})['accent'])
    data['image_url'] = data['school'].str.lower().map(lambda x: school_info.get(x, {'img':'https://via.placeholder.com/200'})['img'])

    return data

# Loading Professor Data
@st.cache_data
def load_rmp():
    url = "https://raw.githubusercontent.com/cpinckney-salad/ALLRMP/main/RMP.csv"
    rmp = pd.read_csv(url)
    rmp.columns = rmp.columns.str.strip()

    rmp['Score'] = pd.to_numeric(rmp['Score'], errors='coerce')
    rmp['Difficulty'] = pd.to_numeric(rmp['Difficulty'], errors='coerce')
    rmp['Would Take Again'] = pd.to_numeric(
        rmp['Would Take Again'].astype(str).str.replace('%',''), errors='coerce'
    )
    rmp['Num Ratings'] = pd.to_numeric(rmp['Num Ratings'], errors='coerce')

    rmp = rmp[
        (rmp['Score'] > 0) & 
        (rmp['Difficulty'] > 0) & 
        (rmp['Num Ratings'] > 0)
    ].copy()
    
    return rmp

df = load_data()
rmp = load_rmp()

# School Names
short_names = {
    'california lutheran university': 'Cal Lutheran',
    'pepperdine university': 'Pepperdine',
    'california state university-northridge': 'CSUN',
    'california state university-channel islands': 'CSUCI',
    'university of california-santa barbara': 'UCSB',
}

rmp_school_display = {
    'Cal Lutheran': 'California Lutheran University',
    'Pepperdine': 'Pepperdine University',
    'CSU Northridge': 'California State University-Northridge',
    'CSU Channel Islands': 'California State University-Channel Islands',
    'UC Santa Barbara': 'University Of California-Santa Barbara',
}
rmp['School_Display'] = rmp['School'].map(rmp_school_display).fillna(rmp['School'])

rmp_short = {
    'Cal Lutheran': 'Cal Lutheran',
    'Pepperdine': 'Pepperdine',
    'CSU Northridge': 'CSUN',
    'CSU Channel Islands': 'CSUCI',
    'UC Santa Barbara': 'UCSB',
}

def abbrev(row):
    return short_names.get(row['school'].lower(), row['school_display'])

school_colors = {
    'Cal Lutheran':'#6600cc',
    'Pepperdine':'#0000ff',
    'CSUN':"#a20606",
    'CSUCI':"#FF0000",
    'UCSB':'#002244',
}

# Metric Cards
best_roi_row      = df.loc[df['roi'].idxmax()]
best_rating_row   = df.loc[df['avg_rating'].idxmax()]
lowest_tuition_row = df.loc[df['tuition'].idxmin()]
best_completion_row = df.loc[df['completion rate'].idxmax()]

# Title
st.markdown("""
<h1 style="margin-bottom:6px;">Ventura County University Exploration</h1>
<p style="color:#f0f2f5; font-size:18px; margin-top:0;">
Compare Ventura County universities by earnings, debt, and professor quality.
<p style="color:#94a3b8; font-size:15px; margin-top:0;">
Data sourced from the U.S. Department of Education College Scorecard API and RateMyProfessor.com
</p>
""", unsafe_allow_html=True)

# School selection
if 'selected_school' not in st.session_state:
    st.session_state['selected_school'] = "Overview (All Schools)"

school_list = ["Overview (All Schools)"] + sorted(df['school_display'].unique())

st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

# Tabs 
tab_map, tab_profile, tab_dept, tab_viz = st.tabs([
    "Campus Map", "School Profile", "Departments", "Visuals"
])


# TAB 1: Map

with tab_map:

    # Metric cards at the very top of the map tab
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(" Highest ROI",      abbrev(best_roi_row),       f"${int(best_roi_row['roi']):,}")
    m2.metric("Best Rated Profs", abbrev(best_rating_row),    f"{best_rating_row['avg_rating']:.2f} stars")
    m3.metric(" Lowest Tuition",   abbrev(lowest_tuition_row), f"${int(lowest_tuition_row['tuition']):,}")
    m4.metric("Top Completion",   abbrev(best_completion_row),f"{best_completion_row['completion rate']*100:.1f}%")

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    # School selector inside map tab
    fly_to_target = st.selectbox(
        "Select a School",
        school_list,
        index=school_list.index(st.session_state['selected_school']),
        key='map_school_select'
    )
    # Keep session state in sync
    st.session_state['selected_school'] = fly_to_target

    # Map controls row
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        roi_range = st.slider(
            "ROI Range",
            int(df.roi.min()), int(df.roi.max()),
            (int(df.roi.min()), int(df.roi.max()))
        )
    with col2:
        rating_range = st.slider(
            "Avg Rating",
            float(df.avg_rating.min()), float(df.avg_rating.max()),
            (float(df.avg_rating.min()), float(df.avg_rating.max()))
        )
    with col3:
        map_styles = {"Dark": "dark", "Light": "light", "Road": "road"}
        map_style = st.selectbox("Style", list(map_styles.keys()))

    st.markdown("""
<div style="display:flex; gap:18px; font-size:13px; color:#cbd5e1;">
  <span><span style="color:#a855f7;">●</span> Cal Lutheran</span>
  <span><span style="color:#3b82f6;">●</span> Pepperdine</span>
  <span><span style="color:#ef4444;">●</span> CSUN</span>
  <span><span style="color:#9ca3af;">●</span> CSUCI</span>
  <span><span style="color:#1e3a8a;">●</span> UCSB</span>
</div>
<hr style="border:none; border-top:1px solid #1e293b; margin:8px 0;">
""", unsafe_allow_html=True)

    df_map = df[(df.roi >= roi_range[0]) & (df.roi <= roi_range[1])]
    df_map = df_map[(df_map.avg_rating >= rating_range[0]) & (df_map.avg_rating <= rating_range[1])]

    if fly_to_target == "Overview (All Schools)":
        v_lat, v_lon, v_zoom = 34.25, -119.1, 8.5
        v_pitch, v_bearing = 0, 0
    else:
        target_row = df_map[df_map['school_display'] == fly_to_target]
        if len(target_row) == 0:
            v_lat, v_lon, v_zoom = 34.25, -119.1, 8.5
            v_pitch, v_bearing = 0, 0
        else:
            target_row = target_row.iloc[0]
            v_lat, v_lon, v_zoom = target_row['latitude'], target_row['longitude'], 14.5
            v_pitch, v_bearing = 55, -15

    view_state = pdk.ViewState(
        latitude=v_lat, longitude=v_lon, zoom=v_zoom,
        pitch=v_pitch, bearing=v_bearing,
        transitionDuration=3000, transitionInterruption=0
    )

    layer = pdk.Layer(
        "ScatterplotLayer", df_map,
        get_position=['longitude', 'latitude'],
        get_color='fill_color', get_radius='roi',
        radius_scale=0.04, radius_min_pixels=12, radius_max_pixels=40,
        pickable=True, auto_highlight=True, stroked=True,
        get_line_color=[255,255,255], line_width_min_pixels=2
    )

    tooltip = {
        "html": """
        <div style="display:flex; flex-direction:row; background:#1e293b; color:white; 
        border-radius:12px; border:1.5px solid white; width:520px; height:270px; font-family:sans-serif; box-shadow: 0 8px 32px rgba(0,0,0,0.8); overflow:hidden;">
            <div style="width:220px; height:100%; flex-shrink:0;">
                <img src="{image_url}" style="width:100%; height:100%; object-fit:cover;">
            </div>
            <div style="padding:20px; flex-grow:1; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <p style="margin:0; font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">Identity</p>
                    <b style="color:{accent_color}; font-size:19px; line-height:1.2; display:block;">{school_display}</b>
                    <span style="font-size:13px; color:#cbd5e1;">{city_display}, {state_display}</span>
                </div>
                <div style="display:flex; gap:15px; margin-top:10px;">
                    <div style="flex:1;"> 
                        <p style="margin:0 0 4px 0; font-size:13px; font-weight:bold; color:#94a3b8; text-transform:uppercase;">Financial</p>
                        <div style="font-size:12px; line-height:1.5;">Tuition: ${tuition_str}<br>ROI: {roi_str}</div>
                        <p style="margin:15px 0 4px 0; font-size:13px; font-weight:bold; color:#94a3b8; text-transform:uppercase;">Faculty</p>
                        <div style="font-size:12px; line-height:1.5;">Rating: {rating_str}<br>Difficulty: {diff_str}</div>
                    </div>
                    <div style="flex:1;">
                        <p style="margin:0 0 4px 0; font-size:13px; font-weight:bold; color:#94a3b8; text-transform:uppercase;">Outcomes</p>
                        <div style="font-size:12px; line-height:1.5;">Completion: {comp_str}<br>Retention: {ret_str}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        "style": {"backgroundColor": "transparent", "zIndex": "1000",
                  "padding": "0", "border": "none", "overflow": "visible", "pointerEvents": "none"}
    }

    st.markdown("""
                <div style="background:#020617; padding:18px; border-radius:14px; border:1px solid #1e293b;">
                """, unsafe_allow_html=True)

    st.pydeck_chart(
        pdk.Deck(map_style=map_styles[map_style], initial_view_state=view_state,
                 layers=[layer], tooltip=tooltip),
        height=700, use_container_width=True, key="map-main"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if fly_to_target != "Overview (All Schools)":
        st.info("Switch to the School Profile tab to see the full breakdown for this school.")


# TAB 2 —School Profile

with tab_profile:

    # School selector inside profile tab
    chosen = st.selectbox(
        "Select a School",
        school_list,
        index=school_list.index(st.session_state['selected_school']),
        key='profile_school_select'
    )
    # Keep session state in sync so map tab stays consistent too
    st.session_state['selected_school'] = chosen

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    if chosen == "Overview (All Schools)":
        st.markdown("""
        <div style="text-align:center; padding: 60px 0; color:#94a3b8;">
            <h2>No school selected</h2>
            <p>Use the dropdown above to pick a school.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        row = df[df['school_display'] == chosen].iloc[0]
        accent = row['accent_color']
        img = row['image_url']

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:28px; background:#1e293b;
                    border-radius:14px; padding:24px 28px; margin-bottom:24px;
                    border-left: 5px solid {accent};">
            <img src="{img}" style="width:140px; height:90px; object-fit:cover; border-radius:8px; flex-shrink:0;">
            <div>
                <p style="margin:0; font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">School Profile</p>
                <h2 style="margin:4px 0; color:{accent}; font-family:'Syne',sans-serif;">{row['school_display']}</h2>
                <p style="margin:0; color:#cbd5e1; font-size:14px;">📍 {row['city_display']}, {row['state_display']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### College Scorecard Data")
        cs1, cs2, cs3, cs4 = st.columns(4)
        cs1.metric("Tuition", f"${int(row['tuition']):,}")
        cs2.metric("10yr Earnings", f"${int(row['earnings 10yr']):,}")
        cs3.metric("Median Debt", f"${int(row['median student debt']):,}")
        cs4.metric("ROI", f"${int(row['roi']):,}")

        cs5, cs6, _, __ = st.columns(4)
        cs5.metric("Completion Rate", f"{row['completion rate']*100:.1f}%")
        cs6.metric("Retention Rate", f"{row['retention rate']*100:.1f}%")

        st.markdown("<hr style='border-color:#1e293b; margin:20px 0;'>", unsafe_allow_html=True)

        st.markdown("###  RateMyProfessors Data")
        rmp1, rmp2, _ = st.columns(3)
        rmp1.metric("Avg Professor Rating", f"{row['avg_rating']:.2f} / 5.0")
        rmp2.metric("Avg Difficulty", f"{row['avg_difficulty']:.2f} / 5.0")

        rating_pct = (row['avg_rating'] / 5.0) * 100
        diff_pct = (row['avg_difficulty'] / 5.0) * 100

        st.markdown(f"""
        <div style="margin-top:16px;">
            <p style="font-size:13px; color:#94a3b8; margin-bottom:6px;">PROFESSOR RATING</p>
            <div style="background:#1e293b; border-radius:999px; height:12px; width:100%;">
                <div style="background:{accent}; width:{rating_pct:.0f}%; height:100%; border-radius:999px;"></div>
            </div>
            <p style="font-size:12px; color:#64748b; margin-top:4px;">{row['avg_rating']:.2f} out of 5.0</p>
            <p style="font-size:13px; color:#94a3b8; margin-bottom:6px; margin-top:14px;">COURSE DIFFICULTY</p>
            <div style="background:#1e293b; border-radius:999px; height:12px; width:100%;">
                <div style="background:#ff0000; width:{diff_pct:.0f}%; height:100%; border-radius:999px;"></div>
            </div>
            <p style="font-size:12px; color:#64748b; margin-top:4px;">{row['avg_difficulty']:.2f} out of 5.0</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1e293b; margin:20px 0;'>", unsafe_allow_html=True)

        roi_rank    = int(df['roi'].rank(ascending=False)[df['school_display'] == chosen].values[0])
        rating_rank = int(df['avg_rating'].rank(ascending=False)[df['school_display'] == chosen].values[0])
        tuition_rank = int(df['tuition'].rank(ascending=True)[df['school_display'] == chosen].values[0])

        st.markdown(f"""
        <div style="background:#1e293b; border-radius:12px; padding:20px 24px; border:1px solid #334155;">
            <p style="margin:0 0 10px 0; font-size:13px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">📌 How {abbrev(row)} Ranks Among the 5 Schools</p>
            <div style="display:flex; gap:32px; flex-wrap:wrap;">
                <div><span style="font-size:22px; font-weight:700; color:{accent};">#{roi_rank}</span><br><span style="font-size:12px; color:#94a3b8;">ROI</span></div>
                <div><span style="font-size:22px; font-weight:700; color:{accent};">#{rating_rank}</span><br><span style="font-size:12px; color:#94a3b8;">Prof Rating</span></div>
                <div><span style="font-size:22px; font-weight:700; color:{accent};">#{tuition_rank}</span><br><span style="font-size:12px; color:#94a3b8;">Affordability</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# TAB 3 — Departments

with tab_dept:

    st.markdown("### Department Explorer")
    st.markdown("Filter by school, department, or both to explore RMP stats at the department level.")

    d_col1, d_col2 = st.columns(2)

    all_schools_rmp = sorted(rmp['School'].unique())
    all_depts = sorted(rmp['Department'].dropna().unique())

    with d_col1:
        dept_school = st.selectbox(
            "Filter by School",
            ["All Schools"] + all_schools_rmp,
            key="dept_school"
        )

    with d_col2:
        dept_filter = st.selectbox(
            "Filter by Department",
            ["All Departments"] + all_depts,
            key="dept_filter"
        )

    filtered = rmp.copy()

    if dept_school != "All Schools":
        filtered = filtered[filtered['School'] == dept_school]

    if dept_filter != "All Departments":
        filtered = filtered[filtered['Department'] == dept_filter]

    if len(filtered) == 0:
        st.warning("No data found for that combination. Try a different filter.")
    else:
        if dept_school != "All Schools" or (dept_school != "All Schools" and dept_filter != "All Departments"):
            group_col = "Department"
            subtitle = "Department breakdown" + (f" at {dept_school}" if dept_school != "All Schools" else " across all schools")
        elif dept_filter != "All Departments":
            group_col = "School"
            subtitle = f"**{dept_filter}** department across all schools"
        else:
            group_col = "Department"
            subtitle = "All departments across all schools"

        st.markdown(f"*Showing: {subtitle}*")

        agg = (
            filtered
            .groupby(group_col)
            .agg(
                Avg_Score=('Score', 'mean'),
                Avg_Difficulty=('Difficulty', 'mean'),
                Avg_Would_Take_Again=('Would Take Again', 'mean'),
                Num_Professors=('Name', 'count'),
                Total_Ratings=('Num Ratings', 'sum')
            )
            .reset_index()
            .sort_values('Avg_Score', ascending=False)
        )

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Departments / Groups", len(agg))
        sm2.metric("Total Professors", int(filtered['Name'].count()))
        sm3.metric("Avg Rating", f"{filtered['Score'].mean():.2f}")
        sm4.metric("Avg Difficulty", f"{filtered['Difficulty'].mean():.2f}")

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

        def stat_block(col, title, value_str, bar_pct, bar_color):
            col.markdown(f"""
            <div style="padding: 0 4px;">
                <p style="font-size:10px; color:#94a3b8; margin:0 0 2px 0; text-transform:uppercase; letter-spacing:0.5px;">{title}</p>
                <p style="font-size:20px; font-weight:700; color:#f1f5f9; margin:0 0 6px 0;">{value_str}</p>
                <div style="background:#111111; border-radius:999px; height:6px; width:100%;">
                    <div style="background:{bar_color}; width:{bar_pct:.0f}%; height:100%; border-radius:999px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        for _, r in agg.iterrows():
            label     = _html.escape(str(r[group_col]))
            score     = r['Avg_Score']
            diff      = r['Avg_Difficulty']
            wta       = r['Avg_Would_Take_Again']
            n_profs   = int(r['Num_Professors'])
            n_ratings = int(r['Total_Ratings'])

            score_pct = (score / 5.0) * 100
            diff_pct  = (diff  / 5.0) * 100
            # Convert to a decimal
            if wta <= 1.0:
                wta = wta * 100
            wta_pct   = min(wta, 100)
            bar_color = "#22c55e" if score >= 4.0 else ("#6366f1" if score >= 3.0 else "#ff4646")

            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:16px 20px 20px 20px;
                        margin-bottom:4px; border:1px solid #334155;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <span style="font-size:16px; font-weight:700; color:#f1f5f9;">{label}</span>
                    <span style="font-size:12px; color:#94a3b8;">{n_profs} professors · {n_ratings:,} ratings</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            stat_block(c1, "AVG RATING",       f"{score:.2f} / 5.0", score_pct, bar_color)
            stat_block(c2, "AVG DIFFICULTY",   f"{diff:.2f} / 5.0",  diff_pct,  "#ff0000")
            stat_block(c3, "WOULD TAKE AGAIN", f"{wta:.0f}%",         wta_pct,   "#38bdf8")
            c4.markdown(f"""
            <div style="padding: 0 4px;">
                <p style="font-size:10px; color:#94a3b8; margin:0 0 2px 0; text-transform:uppercase; letter-spacing:0.5px;">PROFESSORS</p>
                <p style="font-size:20px; font-weight:700; color:#f1f5f9; margin:0 0 2px 0;">{n_profs}</p>
                <p style="font-size:10px; color:#94a3b8; margin:8px 0 2px 0; text-transform:uppercase; letter-spacing:0.5px;">TOTAL RATINGS</p>
                <p style="font-size:20px; font-weight:700; color:#f1f5f9; margin:0;">{n_ratings:,}</p>
            </div>
            """, unsafe_allow_html=True)

            card_data = filtered[filtered[group_col] == r[group_col]]
            display_cols = ['School', 'Name', 'Department', 'Score', 'Difficulty', 'Would Take Again', 'Num Ratings']
            with st.expander(f"View professors — {r[group_col]}"):
                display_df = card_data[display_cols].sort_values('Score', ascending=False).reset_index(drop=True).copy()
                display_df['Would Take Again'] = display_df['Would Take Again'].apply(lambda x: f"{x:.0f}%" if pd.notna(x) else 'N/A')
                st.dataframe(display_df, use_container_width=True)

            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)


# TAB 4 — Visuals

with tab_viz:

    st.markdown("# Data Visualizations")
    st.markdown("Explore how the 5 schools compare across financial, academic, and professor quality metrics.")

    df_viz = df.copy()
    df_viz['short'] = df_viz['school'].map(short_names)

    st.markdown("---")

    st.markdown("## College Scorecard Visuals")

        # 1.Parallel Coordinates (advanced insight)
    st.markdown("#### 〰️ Parallel Coordinates — School Tradeoffs")
    st.markdown(
        "Each line is a school. Follow a line across all axes to see its full profile. "
        "Lines that cross reveal tradeoffs, like a school might win on earnings but lose on tuition."
    )

    pc_metrics = ['tuition', 'earnings 10yr', 'roi', 'completion rate', 'avg_rating']
    pc_labels  = ['Tuition', '10yr Earnings', 'ROI', 'Completion', 'Prof Rating']

    df_pc = df_viz[['short'] + pc_metrics].copy()

    invert = {'tuition', 'median student debt', 'avg_difficulty'}
    for m in pc_metrics:
        mn, mx = df_pc[m].min(), df_pc[m].max()
        df_pc[m + '_n'] = (df_pc[m] - mn) / (mx - mn + 1e-9)
        if m in invert:
            df_pc[m + '_n'] = 1 - df_pc[m + '_n']

    school_order = ['Cal Lutheran', 'Pepperdine', 'CSUN', 'CSUCI', 'UCSB']
    color_index  = {s: i for i, s in enumerate(school_order)}
    df_pc['color_idx'] = df_pc['short'].map(color_index)

    dimensions = []
    for m, lbl in zip(pc_metrics, pc_labels):
        n_col = m + '_n'
        raw_vals  = df_pc[m].values
        norm_vals = df_pc[n_col].values
        tick_vals = np.linspace(norm_vals.min(), norm_vals.max(), 5)
        raw_range = raw_vals.max() - raw_vals.min()
        if m in invert:
            raw_ticks = raw_vals.max() - tick_vals * raw_range
        else:
            raw_ticks = raw_vals.min() + tick_vals * raw_range
        if 'rate' in m:
            tick_text = [f"{v*100:.0f}%" for v in raw_ticks]
        elif m in ['avg_rating', 'avg_difficulty']:
            tick_text = [f"{v:.2f}" for v in raw_ticks]
        else:
            tick_text = [f"${v/1000:.0f}k" for v in raw_ticks]
        dimensions.append(dict(
            range=[0, 1],
            label=lbl + (" ↓better" if m in invert else " ↑better"),
            values=df_pc[n_col].tolist(),
            tickvals=tick_vals.tolist(),
            ticktext=tick_text,
        ))

    colorscale = [
        [0.0,  '#6600cc'], [0.25, '#0000ff'], [0.5,  "#6f0000"],
        [0.75, "#FF0000"], [1.0,  "#0963BC"],
    ]

    fig_pc = go.Figure(go.Parcoords(
        line=dict(color=df_pc['color_idx'], colorscale=colorscale, showscale=False),
        dimensions=dimensions,
        labelfont=dict(color='#ffffff', size=12),
        tickfont=dict(color='#ffffff', size=10),
        rangefont=dict(color='#ffffff', size=9),
    ))
    fig_pc.update_layout(
        paper_bgcolor='#111111', font_color='#cbd5e1', font_family='Inter',
        margin=dict(t=60, b=40, l=60, r=60), height=440,
    )
    st.plotly_chart(fig_pc, use_container_width=True)

    legend_html = "".join([
        f'<span style="display:inline-flex; align-items:center; gap:6px; margin-right:20px;">'
        f'<span style="width:28px; height:3px; background:{school_colors[s]}; display:inline-block; border-radius:2px;"></span>'
        f'<span style="font-size:13px; color:#cbd5e1;">{s}</span></span>'
        for s in school_order
    ])
    st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">{legend_html}</div>', unsafe_allow_html=True)
    st.caption("💡 UCSB dominates on earnings and ROI but costs more. CSU and CSUCI cluster as the most affordable options but sit lower on the outcome scales — the clearest value tradeoff in the dataset.")

    st.markdown("---")

       # 2. Scatterpltos (relationships) 
    st.markdown("### Scatter Plots")
    sc1, sc2 = st.columns(2)

    with sc1:
        st.markdown("**ROI vs Professor Rating**")
        fig_s1 = px.scatter(
            df_viz, x='avg_rating', y='roi', text='short', color='short',
            color_discrete_map=school_colors, trendline='ols',
            trendline_color_override='#6366f1',
            labels={'avg_rating': 'Avg Professor Rating', 'roi': 'ROI ($)'},
            height=350, custom_data=['short'],
        )
        fig_s1.update_traces(selector=dict(mode='markers+text'),
            textposition='top center', marker_size=14,
            hovertemplate="<b>%{text}</b><br>Rating: %{x:.2f}<br>ROI: $%{y:,.0f}<extra></extra>")
        fig_s1.update_traces(selector=dict(type='scatter', mode='lines'),
            hovertemplate="Trendline<extra></extra>")
        fig_s1.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111',
            font_color='#cbd5e1', font_family='Inter',
            margin=dict(t=20, b=20, l=20, r=20), showlegend=False,
            xaxis=dict(gridcolor='#1e293b'), yaxis=dict(gridcolor='#1e293b'),
        )
        st.plotly_chart(fig_s1, use_container_width=True)
        st.caption("💡 There isn't a direct correlation between Professor Ratings and ROI. For instance, CSUN has the hghest student-rated faculty despite having a lower financial ROI compare to Pepperdine.")

    with sc2:
        st.markdown("**Tuition vs 10yr Earnings**")
        fig_s2 = px.scatter(
            df_viz, x='tuition', y='earnings 10yr', text='short', color='short',
            color_discrete_map=school_colors, trendline='ols',
            trendline_color_override='#6366f1',
            labels={'tuition': 'Tuition ($)', 'earnings 10yr': '10yr Earnings ($)'},
            height=350,
        )
        fig_s2.update_traces(selector=dict(mode='markers+text'),
            textposition='top center', marker_size=14,
            hovertemplate="<b>%{text}</b><br>Tuition: $%{x:,.0f}<br>Earnings: $%{y:,.0f}<extra></extra>")
        fig_s2.update_traces(selector=dict(type='scatter', mode='lines'),
            hovertemplate="Trendline<extra></extra>")
        fig_s2.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111',
            font_color='#cbd5e1', font_family='Inter',
            margin=dict(t=20, b=20, l=20, r=20), showlegend=False,
            xaxis=dict(gridcolor='#1e293b'), yaxis=dict(gridcolor='#1e293b'),
        )
        st.plotly_chart(fig_s2, use_container_width=True)
        st.caption("💡 Higher tuition schools generally produce higher earnings — but CSUN delivers solid earnings at a fraction of the cost.")

    st.markdown("---")


    # ── 3.School Caomprisons (the main takeaway)
    st.markdown("#### School Comparisons")

    v_col1, v_col2, v_col3, v_col4 = st.columns([2, 2, 1, 1])
    with v_col1:
        bar_metric = st.selectbox(
            "Select metric",
            ["ROI", "Tuition", "10yr Earnings", "Median Debt", "Completion Rate", "Retention Rate"],
            key="bar_metric"
        )
    with v_col2:
        bar_sort = st.selectbox("Sort", ["High → Low", "Low → High", "Alphabetical"], key="bar_sort")
    with v_col3:
        show_top_only = st.toggle("Top 3 only", value=False, key="top_only")
    with v_col4:
        bar_horizontal = st.toggle("Horizontal", value=False, key="bar_horiz")

    metric_map = {
        "ROI": "roi", "Tuition": "tuition", "10yr Earnings": "earnings 10yr",
        "Median Debt": "median student debt", "Completion Rate": "completion rate",
        "Retention Rate": "retention rate",
    }
    col_key = metric_map[bar_metric]

    if bar_sort == "High → Low":
        df_bar = df_viz.sort_values(col_key, ascending=False)
    elif bar_sort == "Low → High":
        df_bar = df_viz.sort_values(col_key, ascending=True)
    else:
        df_bar = df_viz.sort_values('short')

    if show_top_only:
        df_bar = df_bar.head(3)

    bar_colors = [school_colors.get(s, '#6366f1') for s in df_bar['short']]
    bar_labels = df_bar[col_key].map(
        lambda v: f"{v*100:.1f}%" if "rate" in col_key else f"${v:,.0f}"
    )

    if bar_horizontal:
        fig_bar = go.Figure(go.Bar(
            y=df_bar['short'], x=df_bar[col_key], orientation='h',
            marker_color=bar_colors, text=bar_labels, textposition='outside',
        ))
        fig_bar.update_layout(height=300,
            xaxis=dict(gridcolor='#1e293b', zeroline=False),
            yaxis=dict(gridcolor='#1e293b'))
    else:
        fig_bar = go.Figure(go.Bar(
            x=df_bar['short'], y=df_bar[col_key],
            marker_color=bar_colors, text=bar_labels, textposition='outside',
        ))
        fig_bar.update_layout(height=360,
            yaxis=dict(gridcolor='#1e293b', zeroline=False),
            xaxis=dict(gridcolor='#1e293b'))

    fig_bar.update_layout(
        plot_bgcolor='#111111', paper_bgcolor='#111111',
        font_color='#cbd5e1', font_family='Inter',
        margin=dict(t=30, b=20, l=20, r=60), showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Tried to use python logic but that was a pain so I hardcoded these takeaways
    bar_insights = {
        "ROI": "💡 UCSB and Pepperdine lead in ROI — suggesting stronger long-term financial returns relative to cost.",
        "Tuition": "💡 CSUN and CSUCI are the most affordable options, making them strong value picks for cost-conscious students.",
        "10yr Earnings": "💡 UCSB graduates earn the most 10 years out, reflecting the premium placed on UC degrees by employers.",
        "Median Debt": "💡 Lower debt schools like CSUN leave graduates with more financial flexibility after graduation.",
        "Completion Rate": "💡 Pepperdine leads in completion rate, suggesting strong student support and retention programs.",
        "Retention Rate": "💡 Higher retention schools tend to have stronger campus communities and student satisfaction.",
    }
    st.caption(bar_insights.get(bar_metric, ""))

    st.markdown("---")

    st.markdown("# Rate My Professor Visuals")

    #  4. Box plot (depth)
    st.markdown("#### Professor Score Distribution — Box Plot")
    st.markdown("Shows the spread of individual professor scores per school (median, quartiles, outliers).")

    box_col1, box_col2 = st.columns([1, 3])
    with box_col1:
        box_dept = st.selectbox(
            "Filter by department",
            ["All Departments"] + sorted(rmp['Department'].dropna().unique()),
            key="box_dept"
        )

    box_data = rmp.copy()
    if box_dept != "All Departments":
        box_data = box_data[box_data['Department'] == box_dept]

    box_data['short'] = box_data['School'].map(rmp_short).fillna(box_data['School'])

    fig_box = go.Figure()
    for school_name in ['Cal Lutheran', 'Pepperdine', 'CSUN', 'CSUCI', 'UCSB']:
        group = box_data[box_data['short'] == school_name]['Score'].dropna()
        if len(group) == 0:
            continue
        fig_box.add_trace(go.Box(
            y=group, name=school_name,
            marker_color=school_colors.get(school_name, '#6366f1'),
            line_color=school_colors.get(school_name, '#6366f1'),
            fillcolor=school_colors.get(school_name, '#6366f1'),
            opacity=0.7, boxmean=True,
            hovertemplate="<b>" + school_name + "</b><br>Score: %{y:.2f}<extra></extra>",
        ))

    fig_box.update_layout(
        plot_bgcolor='#111111', paper_bgcolor='#111111',
        font_color='#cbd5e1', font_family='Inter',
        margin=dict(t=20, b=20, l=20, r=20),
        yaxis=dict(title='Professor Score', range=[0, 5.2], gridcolor='#1e293b'),
        xaxis=dict(gridcolor='#1e293b'),
        height=420, showlegend=False,
    )
    st.plotly_chart(fig_box, use_container_width=True)
    st.caption("💡 CSUN shows the widest spread in professor quality, meaning experience can vary significantly depending on which professor you get.")

    st.markdown("---")


    #5. Departments 
    st.markdown("#### Top Departments by Avg Rating")
    st.markdown("Drill down into which departments are rated highest — filter by school to see where each campus excels.")

    hb_col1, hb_col2 = st.columns([1, 3])
    with hb_col1:
        hb_school = st.selectbox(
            "Filter by school",
            ["All Schools"] + sorted(rmp['School'].unique()),
            key="hb_school"
        )
    with hb_col2:
        top_n = st.slider("Number of departments to show", 5, 30, 15, key="top_n")

    hb_data = rmp.copy()
    if hb_school != "All Schools":
        hb_data = hb_data[hb_data['School'] == hb_school]

    dept_agg = (
        hb_data.groupby('Department')
        .agg(Avg_Score=('Score', 'mean'), Count=('Name', 'count'))
        .reset_index()
        .query('Count >= 3')
        .sort_values('Avg_Score', ascending=True)
        .tail(top_n)
    )

    fig_hbar = go.Figure(go.Bar(
        x=dept_agg['Avg_Score'], y=dept_agg['Department'],
        orientation='h', marker_color='#6366f1',
        text=dept_agg['Avg_Score'].map(lambda v: f"{v:.2f}"),
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Avg Rating: %{x:.2f}<extra></extra>",
    ))
    fig_hbar.update_layout(
        plot_bgcolor='#111111', paper_bgcolor='#111111',
        font_color='#cbd5e1', font_family='Inter',
        margin=dict(t=20, b=20, l=20, r=60),
        xaxis=dict(title='Avg Rating', gridcolor='#1e293b', range=[0, 5.5]),
        yaxis=dict(gridcolor='#1e293b'),
        height=max(350, top_n * 28), showlegend=False,
    )
    st.plotly_chart(fig_hbar, use_container_width=True)
    st.caption("💡 Smaller or specialized departments often rate highest — use the school filter to find the strongest programs at a specific campus.")
    # ── About This Project ──────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="background:#0f172a; border-radius:14px; border:1px solid #1e293b; padding:28px 32px; margin-top:8px;">
  <p style="font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; margin:0 0 12px 0;">About This Project</p>
  <h3 style="color:#f1f5f9; font-family:'Syne',sans-serif; margin:0 0 16px 0;">Ventura County University Explorer</h3>
  <p style="color:#94a3b8; font-size:14px; line-height:1.7; margin:0 0 20px 0;">
    This dashboard compares five Ventura County-area universities across financial outcomes,
    academic metrics, and professor quality which combines federal education data with
    sourced faculty ratings to give students an all-in-one view of their options.
  </p>

  <div style="display:flex; gap:40px; flex-wrap:wrap;">
    <div>
      <p style="font-size:11px; color:#6366f1; text-transform:uppercase; letter-spacing:0.8px; font-weight:600; margin:0 0 8px 0;">Data Sources</p>
      <ul style="color:#94a3b8; font-size:13px; line-height:2; margin:0; padding-left:16px;">
        <li><span style="color:#cbd5e1;">College Scorecard API</span> — U.S. Dept. of Education</li>
        <li><span style="color:#cbd5e1;">RateMyProfessors Dataset</span> — Crowdsourced faculty ratings</li>
      </ul>
    </div>
    <div>
      <p style="font-size:11px; color:#6366f1; text-transform:uppercase; letter-spacing:0.8px; font-weight:600; margin:0 0 8px 0;">Built With</p>
      <ul style="color:#94a3b8; font-size:13px; line-height:2; margin:0; padding-left:16px;">
        <li><span style="color:#cbd5e1;">Streamlit</span> — App framework</li>
        <li><span style="color:#cbd5e1;">Plotly</span> — Interactive charts</li>
        <li><span style="color:#cbd5e1;">PyDeck</span> — 3D campus map</li>
        <li><span style="color:#cbd5e1;">Pandas</span> — Data processing</li>
      </ul>
    </div>
    <div>
      <p style="font-size:11px; color:#6366f1; text-transform:uppercase; letter-spacing:0.8px; font-weight:600; margin:0 0 8px 0;">Schools Covered</p>
      <ul style="color:#94a3b8; font-size:13px; line-height:2; margin:0; padding-left:16px;">
        <li>California Lutheran University</li>
        <li>Pepperdine University</li>
        <li>Cal State Northridge (CSUN)</li>
        <li>Cal State Channel Islands (CSUCI)</li>
        <li>UC Santa Barbara (UCSB)</li>
      </ul>
    </div>
  </div>

  <div style="margin-top:20px; padding-top:16px; border-top:1px solid #1e293b;">
    <p style="font-size:12px; color:#475569; margin:0; line-height:1.6;">
      <strong style="color:#64748b;">Disclaimer:</strong> Professor ratings are subjective and may not represent overall instructional quality.
      ROI figures are estimates derived from publicly available data and should be treated as directional indicators only,
      not financial guarantees. This tool is intended for educational exploration purposes.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)
