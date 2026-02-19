"""
Insights Dashboard — BI Copilot
Electric indigo/cyan neon theme · Bullet charts · Violin plots ·
Stacked area · Scatter matrix · Completely different from Supply Chain
"""
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.utils.db_connector import create_connector
from streamlit_app.components.metrics import format_currency, format_number

st.set_page_config(
    page_title="Insights Dashboard | BI Copilot",
    page_icon="💡",
    layout="wide",
)

# ─────────────────────────────────────────
# CSS — Electric Indigo / Neon Cyan
# completely different from Supply Chain amber/teal
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] {
  font-family: 'Space Grotesk', sans-serif;
}

.stApp { background: #07070f; color: #e2e8f0; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 0 0 3rem 0 !important; max-width: 100% !important; }

/* ── Page banner ── */
.page-banner {
  background: linear-gradient(135deg, #0f0f1a 0%, #12102a 50%, #0f0f1a 100%);
  border-bottom: 1px solid #1e1b4b;
  padding: 24px 36px 20px;
  display: flex; align-items: center; justify-content: space-between;
}
.banner-left  { display: flex; align-items: center; gap: 16px; }
.banner-icon  {
  width: 44px; height: 44px; background: linear-gradient(135deg, #7c3aed, #4f46e5);
  border-radius: 10px; display: flex; align-items: center; justify-content: center;
  font-size: 20px; box-shadow: 0 0 20px rgba(124,58,237,.4);
}
.banner-title { font-size: 22px; font-weight: 700; color: #e2e8f0; letter-spacing: -.3px; }
.banner-sub   { font-size: 12px; color: #6366f1; margin-top: 3px;
                font-family: 'JetBrains Mono', monospace; }
.live-badge   {
  display: flex; align-items: center; gap: 8px;
  background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.3);
  border-radius: 20px; padding: 6px 16px; font-size: 12px; color: #818cf8;
}
.pulse {
  width: 8px; height: 8px; background: #00d4ff; border-radius: 50%;
  box-shadow: 0 0 8px #00d4ff; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* ── Tab bar ── */
.stTabs [data-baseweb="tab-list"] {
  background: #0d0d1a !important;
  border-bottom: 1px solid #1e1b4b !important;
  padding: 0 36px !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  color: #4b5563 !important; background: transparent !important;
  border: none !important; border-bottom: 2px solid transparent !important;
  padding: 15px 22px !important; font-size: 13px !important; font-weight: 500 !important;
  margin-bottom: -1px !important;
}
.stTabs [aria-selected="true"] {
  color: #e2e8f0 !important; border-bottom-color: #7c3aed !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #c7d2fe !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── Panels ── */
.panel { padding: 28px 36px; }

/* ── KPI cards ── */
.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 28px; }
.kpi-card {
  background: #0d0d1a;
  border: 1px solid #1e1b4b;
  border-radius: 12px;
  padding: 18px 20px 16px;
  position: relative; overflow: hidden;
}
.kpi-card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
}
.kpi-card.violet::before { background: linear-gradient(90deg,#7c3aed,#4f46e5); }
.kpi-card.cyan::before   { background: linear-gradient(90deg,#00d4ff,#0ea5e9); }
.kpi-card.lime::before   { background: linear-gradient(90deg,#a3e635,#65a30d); }
.kpi-card.orange::before { background: linear-gradient(90deg,#fb923c,#ea580c); }
.kpi-card.rose::before   { background: linear-gradient(90deg,#f43f5e,#be123c); }
.kpi-label { font-size: 10px; font-weight: 600; text-transform: uppercase;
             letter-spacing: 1.2px; color: #4b5563; margin-bottom: 10px; }
.kpi-val   { font-size: 28px; font-weight: 700; color: #f1f5f9; letter-spacing: -1px;
             line-height: 1; font-family: 'JetBrains Mono', monospace; }
.kpi-foot  { font-size: 11px; color: #4b5563; margin-top: 8px; }
.kpi-foot .up   { color: #a3e635; font-weight: 600; }
.kpi-foot .down { color: #f43f5e; font-weight: 600; }
.kpi-foot .hi   { color: #7c3aed; font-weight: 600; }

/* ── Section label ── */
.sl {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 1.4px; color: #6366f1; margin-bottom: 14px;
}
.sl::after { content:''; flex:1; height:1px; background:#1e1b4b; }

/* ── Chart shell ── */
.cshell {
  background: #0d0d1a; border: 1px solid #1e1b4b;
  border-radius: 12px; padding: 20px 18px; margin-bottom: 18px;
}
.cshell-title { font-size: 13px; font-weight: 600; color: #c7d2fe; margin-bottom: 2px; }
.cshell-sub   { font-size: 11px; color: #4b5563; margin-bottom: 12px; }

/* ── Insight card ── */
.insight {
  background: linear-gradient(135deg,#12102a,#0f0f1a);
  border: 1px solid #312e81; border-radius: 12px; padding: 16px 20px;
  margin-bottom: 12px;
}
.insight-hdr { font-size: 13px; font-weight: 600; color: #a5b4fc; margin-bottom: 4px; }
.insight-body { font-size: 12px; color: #6366f1; line-height: 1.6; }
.tag {
  display: inline-block; font-size: 10px; font-weight: 600; border-radius: 4px;
  padding: 2px 8px; margin-right: 6px;
  font-family: 'JetBrains Mono', monospace; letter-spacing: .3px;
}
.tag-up  { background:#0f2810; color:#a3e635; border:1px solid rgba(163,230,53,.3); }
.tag-dn  { background:#1f0a12; color:#f43f5e; border:1px solid rgba(244,63,94,.3); }
.tag-neu { background:#12102a; color:#818cf8; border:1px solid rgba(129,140,248,.3); }

/* ── Selectbox ── */
.stSelectbox > div > div {
  background:#0d0d1a !important; border-color:#1e1b4b !important; color:#e2e8f0 !important;
}
.stRadio label { color: #6b7280; font-size: 13px; }
.stRadio [aria-checked="true"] + div { color: #e2e8f0 !important; }

/* ── Dataframe ── */
.stDataFrame thead th { background:#12102a !important; color:#6366f1 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# DATA
# ─────────────────────────────────────────
@st.cache_resource
def get_db():
    return create_connector()

try:
    db = get_db()
except Exception as e:
    st.error(f"Database not available: {e}")
    st.stop()

@st.cache_data(ttl=60)
def load_sales(_db):      return _db.execute_query_df("SELECT * FROM sales")
@st.cache_data(ttl=60)
def load_monthly(_db):    return _db.execute_query_df("SELECT * FROM monthly_revenue ORDER BY month")
@st.cache_data(ttl=60)
def load_daily(_db):      return _db.execute_query_df("SELECT * FROM daily_kpis ORDER BY date")
@st.cache_data(ttl=60)
def load_top_prod(_db):   return _db.execute_query_df("SELECT * FROM top_products LIMIT 20")
@st.cache_data(ttl=60)
def load_customers(_db):  return _db.execute_query_df("SELECT * FROM customer_summary LIMIT 500")

sales     = load_sales(db)
monthly   = load_monthly(db)
daily     = load_daily(db)
top_prods = load_top_prod(db)
customers = load_customers(db)

# Base KPIs
total_rev    = sales["revenue"].sum()
total_profit = sales["profit"].sum()
total_txns   = len(sales)
avg_order    = sales["revenue"].mean()
margin       = (total_profit / total_rev * 100) if total_rev > 0 else 0
unique_cust  = sales["customer_id"].nunique()

# Chart theme
BG   = "rgba(0,0,0,0)"
GRID = "#1e1b4b"
CT   = dict(
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="Space Grotesk", color="#4b5563", size=12),
    xaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
    yaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
    colorway=["#7c3aed","#00d4ff","#a3e635","#fb923c","#f43f5e","#f59e0b","#06b6d4"],
    margin=dict(l=0, r=0, t=28, b=0),
    legend=dict(bgcolor=BG, font=dict(color="#6b7280"), orientation="h", y=-0.18),
    hoverlabel=dict(bgcolor="#12102a", font_color="#e2e8f0", bordercolor="#312e81"),
)
def th(fig, h=None):
    fig.update_layout(**CT)
    if h: fig.update_layout(height=h)
    return fig

# ─────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────
st.markdown(f"""
<div class="page-banner">
  <div class="banner-left">
    <div class="banner-icon">💡</div>
    <div>
      <div class="banner-title">Insights Dashboard</div>
      <div class="banner-sub">BI_COPILOT.PUBLIC &nbsp;·&nbsp; {total_txns:,} transactions &nbsp;·&nbsp; updated {datetime.now().strftime('%H:%M:%S')}</div>
    </div>
  </div>
  <div class="live-badge"><div class="pulse"></div> Live · DuckDB</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
t1, t2, t3, t4 = st.tabs([
    "  Revenue & Profit  ",
    "  Products & Categories  ",
    "  Customers & Segments  ",
    "  Trends & Patterns  ",
])


# ══════════════════════════════════════════
# TAB 1 — REVENUE & PROFIT
# ══════════════════════════════════════════
with t1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    # KPI row
    margin_color = "lime" if margin >= 40 else "orange" if margin >= 25 else "rose"
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card violet">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-val">{format_currency(total_rev)}</div>
        <div class="kpi-foot"><span class="hi">All time</span></div>
      </div>
      <div class="kpi-card cyan">
        <div class="kpi-label">Gross Profit</div>
        <div class="kpi-val">{format_currency(total_profit)}</div>
        <div class="kpi-foot"><span class="up">{margin:.1f}%</span> margin</div>
      </div>
      <div class="kpi-card lime">
        <div class="kpi-label">Transactions</div>
        <div class="kpi-val">{format_number(total_txns)}</div>
        <div class="kpi-foot">Total orders</div>
      </div>
      <div class="kpi-card orange">
        <div class="kpi-label">Avg Order Value</div>
        <div class="kpi-val">{format_currency(avg_order)}</div>
        <div class="kpi-foot">Per transaction</div>
      </div>
      <div class="kpi-card rose">
        <div class="kpi-label">Unique Customers</div>
        <div class="kpi-val">{format_number(unique_cust)}</div>
        <div class="kpi-foot">Active buyers</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bullet charts: KPI vs target ──
    st.markdown('<div class="sl">KPI vs Target — Bullet Charts</div>', unsafe_allow_html=True)

    targets = {
        "Revenue":    (total_rev,    total_rev * 1.15, "M", 1e6),
        "Profit":     (total_profit, total_profit * 1.2, "M", 1e6),
        "Margin %":   (margin,       45,              "%", 1),
        "Avg Order":  (avg_order,    avg_order * 1.1, "",  1),
    }

    fig_b = go.Figure()
    for i, (label, (actual, target, suffix, div)) in enumerate(targets.items()):
        fig_b.add_trace(go.Indicator(
            mode="number+gauge+delta",
            value=actual / div,
            delta=dict(reference=target / div, relative=True,
                       increasing=dict(color="#a3e635"),
                       decreasing=dict(color="#f43f5e"),
                       font=dict(size=12)),
            number=dict(suffix=suffix, font=dict(size=18, color="#e2e8f0"),
                        valueformat=",.1f"),
            title=dict(text=label, font=dict(size=12, color="#6366f1")),
            gauge=dict(
                shape="bullet",
                axis=dict(range=[0, target / div * 1.2],
                          tickfont=dict(size=9, color="#4b5563")),
                bar=dict(color="#7c3aed", thickness=0.45),
                bgcolor="#12102a",
                borderwidth=0,
                steps=[dict(range=[0, target / div * 0.7], color="#0d0d1a"),
                       dict(range=[target / div * 0.7, target / div], color="#1e1b4b")],
                threshold=dict(line=dict(color="#00d4ff", width=2),
                               thickness=0.9, value=target / div),
            ),
            domain=dict(x=[0, 1], y=[i / len(targets), (i + 0.8) / len(targets)]),
        ))

    fig_b.update_layout(**CT, height=220,
        margin=dict(l=120, r=40, t=10, b=10))
    st.plotly_chart(fig_b, use_container_width=True)

    # ── Revenue by category — stacked area ──
    st.markdown('<div class="sl" style="margin-top:8px">Monthly Revenue by Category — Stacked Area</div>', unsafe_allow_html=True)

    if not monthly.empty:
        monthly["month"] = pd.to_datetime(monthly["month"].astype(str))
        pivot = monthly.pivot_table(
            index="month", columns="category", values="total_revenue", aggfunc="sum"
        ).fillna(0).reset_index()

        fig_sa = go.Figure()
        colors = ["#7c3aed","#00d4ff","#a3e635","#fb923c","#f43f5e"]
        cats   = [c for c in pivot.columns if c != "month"]
        for i, cat in enumerate(cats):
            fig_sa.add_trace(go.Scatter(
                x=pivot["month"], y=pivot[cat],
                name=cat, stackgroup="one",
                fillcolor=colors[i % len(colors)].replace(")", ",0.7)").replace("#", "rgba(").replace("rgba(", "rgba(") if False else colors[i % len(colors)],
                line=dict(width=0),
                hovertemplate=f"<b>{cat}</b><br>%{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>",
            ))
        th(fig_sa, 320)
        fig_sa.update_layout(
            yaxis=dict(tickprefix="$"),
            hovermode="x unified",
        )
        # Fix fill colors to have transparency
        for i, trace in enumerate(fig_sa.data):
            c = colors[i % len(colors)]
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
            trace.fillcolor = f"rgba({r},{g},{b},0.65)"
            trace.line.color = f"rgba({r},{g},{b},0.9)"

        st.plotly_chart(fig_sa, use_container_width=True)

    # ── Profit distribution — violin ──
    st.markdown('<div class="sl">Revenue Distribution by Category — Violin</div>', unsafe_allow_html=True)

    sample = sales.sample(min(3000, len(sales)), random_state=42)
    fig_v = go.Figure()
    cats_list = sorted(sales["category"].dropna().unique())
    colors_v  = ["#7c3aed","#00d4ff","#a3e635","#fb923c","#f43f5e"]
    for i, cat in enumerate(cats_list):
        sub = sample[sample["category"] == cat]["revenue"]
        r,g,b = (int(colors_v[i%len(colors_v)][j:j+2],16) for j in (1,3,5))
        fig_v.add_trace(go.Violin(
            y=sub, name=cat, box_visible=True,
            meanline_visible=True,
            fillcolor=f"rgba({r},{g},{b},0.2)",
            line_color=colors_v[i % len(colors_v)],
            points=False,
        ))
    th(fig_v, 320)
    fig_v.update_layout(
        yaxis=dict(tickprefix="$", type="log", title="Revenue (log scale)"),
        violingap=0.2, violinmode="overlay",
    )
    st.plotly_chart(fig_v, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB 2 — PRODUCTS & CATEGORIES
# ══════════════════════════════════════════
with t2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="sl">Top Products — Revenue with Profit Delta</div>', unsafe_allow_html=True)
        tp = top_prods.head(15).sort_values("total_revenue")
        fig = go.Figure()
        # Revenue bars (outline style)
        fig.add_trace(go.Bar(
            y=tp["product_name"], x=tp["total_revenue"],
            orientation="h", name="Revenue",
            marker=dict(
                color=[f"rgba(124,58,237,{0.15 + 0.65*(v/tp['total_revenue'].max())})"
                       for v in tp["total_revenue"]],
                line=dict(color="#7c3aed", width=1.5),
            ),
            hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>",
        ))
        # Profit overlay
        fig.add_trace(go.Bar(
            y=tp["product_name"], x=tp["total_profit"],
            orientation="h", name="Profit",
            marker=dict(color="#00d4ff", opacity=0.85),
            hovertemplate="%{y}<br>Profit: $%{x:,.0f}<extra></extra>",
        ))
        th(fig, 460)
        fig.update_layout(
            barmode="overlay",
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            xaxis=dict(tickprefix="$"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="sl">Revenue vs Profit Scatter</div>', unsafe_allow_html=True)
        fig2 = px.scatter(
            top_prods, x="total_revenue", y="total_profit",
            size="times_sold", color="category",
            hover_name="product_name",
            size_max=40,
            color_discrete_sequence=["#7c3aed","#00d4ff","#a3e635","#fb923c","#f43f5e"],
        )
        # 45° reference line
        max_v = max(top_prods["total_revenue"].max(), top_prods["total_profit"].max())
        fig2.add_shape(type="line", x0=0, y0=0, x1=max_v, y1=max_v,
                        line=dict(color=GRID, dash="dot", width=1))
        fig2.update_traces(marker=dict(line=dict(width=1.5, color="#07070f")))
        th(fig2, 460)
        fig2.update_layout(
            xaxis=dict(tickprefix="$"),
            yaxis=dict(tickprefix="$"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Category margin comparison — horizontal bullet-like grouped bars
    st.markdown('<div class="sl">Category — Revenue, Cost & Margin</div>', unsafe_allow_html=True)
    cat_agg = sales.groupby("category").agg(
        revenue=("revenue","sum"),
        cost=("cost","sum"),
        profit=("profit","sum"),
    ).reset_index()
    cat_agg["margin_pct"] = (cat_agg["profit"] / cat_agg["revenue"] * 100).round(1)
    cat_agg = cat_agg.sort_values("revenue", ascending=True)

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Bar(
        y=cat_agg["category"], x=cat_agg["revenue"],
        orientation="h", name="Revenue",
        marker=dict(color="rgba(124,58,237,0.25)", line=dict(color="#7c3aed", width=1.5)),
    ), secondary_y=False)
    fig3.add_trace(go.Bar(
        y=cat_agg["category"], x=cat_agg["cost"],
        orientation="h", name="Cost",
        marker=dict(color="rgba(244,63,94,0.3)", line=dict(color="#f43f5e", width=1)),
    ), secondary_y=False)
    fig3.add_trace(go.Scatter(
        y=cat_agg["category"], x=cat_agg["margin_pct"],
        mode="markers+text", name="Margin %",
        marker=dict(symbol="diamond", size=14, color="#a3e635",
                    line=dict(width=2, color="#07070f")),
        text=[f"{v}%" for v in cat_agg["margin_pct"]],
        textposition="middle right",
        textfont=dict(size=11, color="#a3e635"),
    ), secondary_y=True)
    th(fig3, 300)
    fig3.update_layout(
        barmode="overlay",
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickprefix="$"),
        yaxis2=dict(gridcolor="rgba(0,0,0,0)", overlaying="y", side="right",
                    ticksuffix="%", range=[0, 100]),
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB 3 — CUSTOMERS & SEGMENTS
# ══════════════════════════════════════════
with t3:
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sl">Revenue by Segment × Channel — Heatmap</div>', unsafe_allow_html=True)
        seg_chan = sales.groupby(["customer_segment","sales_channel"])["revenue"].sum().reset_index()
        seg_chan = seg_chan.dropna()
        pivot_sc = seg_chan.pivot(index="customer_segment", columns="sales_channel", values="revenue").fillna(0)

        fig = go.Figure(go.Heatmap(
            z=pivot_sc.values,
            x=pivot_sc.columns.tolist(),
            y=pivot_sc.index.tolist(),
            colorscale=[[0,"#07070f"],[0.3,"#1e1b4b"],[0.7,"#4f46e5"],[1,"#7c3aed"]],
            text=[[f"${v/1000:.0f}K" for v in row] for row in pivot_sc.values],
            texttemplate="%{text}",
            textfont=dict(size=12, color="white"),
            hovertemplate="Segment: %{y}<br>Channel: %{x}<br>Revenue: $%{z:,.0f}<extra></extra>",
            showscale=True,
            colorbar=dict(tickfont=dict(color="#4b5563"), bgcolor=BG,
                          outlinecolor=GRID, tickprefix="$"),
            xgap=4, ygap=4,
        ))
        th(fig, 300)
        fig.update_layout(
            xaxis=dict(side="top", showgrid=False, linecolor="rgba(0,0,0,0)"),
            yaxis=dict(showgrid=False, linecolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="sl">Segment Mix — Sunburst</div>', unsafe_allow_html=True)
        seg_region = sales.groupby(["customer_segment","region"])["revenue"].sum().reset_index().dropna()
        fig2 = px.sunburst(
            seg_region, path=["customer_segment","region"], values="revenue",
            color="revenue",
            color_continuous_scale=[[0,"#1e1b4b"],[0.5,"#4f46e5"],[1,"#7c3aed"]],
        )
        fig2.update_traces(
            textfont=dict(size=11, color="#e2e8f0"),
            insidetextorientation="radial",
            marker=dict(line=dict(width=2, color="#07070f")),
        )
        th(fig2, 300)
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Top customers table with sparkline indicator
    st.markdown('<div class="sl">Top 15 Customers by Lifetime Revenue</div>', unsafe_allow_html=True)
    top_cust = customers.head(15)[
        ["company_name","segment","region","total_orders","lifetime_revenue","avg_order_value"]
    ].copy().dropna(subset=["company_name"])
    top_cust["lifetime_revenue"] = top_cust["lifetime_revenue"].round(0)
    top_cust["avg_order_value"]  = top_cust["avg_order_value"].round(0)

    fig3 = go.Figure(go.Bar(
        y=top_cust["company_name"].str[:22],
        x=top_cust["lifetime_revenue"],
        orientation="h",
        marker=dict(
            color=top_cust["lifetime_revenue"],
            colorscale=[[0,"#1e1b4b"],[1,"#7c3aed"]],
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"${v/1000:.0f}K" for v in top_cust["lifetime_revenue"]],
        textposition="outside",
        textfont=dict(size=10, color="#6366f1"),
        hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>",
    ))
    th(fig3, 380)
    fig3.update_layout(
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickprefix="$"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB 4 — TRENDS & PATTERNS
# ══════════════════════════════════════════
with t4:
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    # Daily revenue with rolling average
    st.markdown('<div class="sl">Daily Revenue — With 30-Day Rolling Average</div>', unsafe_allow_html=True)
    if not daily.empty:
        daily["date"] = pd.to_datetime(daily["date"])
        daily_s = daily.sort_values("date").copy()
        daily_s["rolling_30"] = daily_s["revenue"].rolling(30, min_periods=1).mean()
        daily_s["rolling_7"]  = daily_s["revenue"].rolling(7,  min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily_s["date"], y=daily_s["revenue"],
            name="Daily Revenue",
            marker=dict(color="rgba(124,58,237,0.25)", line=dict(width=0)),
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily_s["date"], y=daily_s["rolling_7"],
            name="7-Day Avg", line=dict(color="#00d4ff", width=1.5, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=daily_s["date"], y=daily_s["rolling_30"],
            name="30-Day Avg", line=dict(color="#7c3aed", width=2.5),
            fill="tonexty", fillcolor="rgba(124,58,237,0.06)",
        ))
        th(fig, 300)
        fig.update_layout(yaxis=dict(tickprefix="$"), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sl">Revenue by Day of Week</div>', unsafe_allow_html=True)
        if not daily.empty:
            daily_s["dow"] = daily_s["date"].dt.day_name()
            dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            dow = daily_s.groupby("dow")["revenue"].mean().reindex(dow_order).reset_index()
            dow.columns = ["day","avg_revenue"]

            fig2 = go.Figure(go.Bar(
                x=dow["day"], y=dow["avg_revenue"],
                marker=dict(
                    color=dow["avg_revenue"],
                    colorscale=[[0,"#1e1b4b"],[1,"#7c3aed"]],
                    showscale=False,
                    line=dict(width=0),
                ),
                text=[f"${v/1000:.0f}K" for v in dow["avg_revenue"]],
                textposition="outside",
                textfont=dict(size=10, color="#6366f1"),
            ))
            th(fig2, 300)
            fig2.update_layout(yaxis=dict(tickprefix="$"))
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="sl">Revenue vs Profit — Monthly Scatter</div>', unsafe_allow_html=True)
        if not monthly.empty:
            monthly_agg = monthly.groupby("month").agg(
                revenue=("total_revenue","sum"),
                profit=("total_profit","sum"),
            ).reset_index()
            monthly_agg["month"] = pd.to_datetime(monthly_agg["month"].astype(str))
            monthly_agg["margin"] = (monthly_agg["profit"] / monthly_agg["revenue"] * 100).round(1)
            monthly_agg["month_label"] = monthly_agg["month"].dt.strftime("%b %Y")

            fig3 = px.scatter(
                monthly_agg, x="revenue", y="profit",
                size="margin", color="margin",
                hover_name="month_label",
                text="month_label",
                color_continuous_scale=[[0,"#f43f5e"],[0.5,"#fb923c"],[1,"#a3e635"]],
                size_max=30,
            )
            fig3.update_traces(
                textposition="top center",
                textfont=dict(size=9, color="#4b5563"),
                marker=dict(line=dict(width=1.5, color="#07070f")),
            )
            th(fig3, 300)
            fig3.update_layout(
                xaxis=dict(tickprefix="$"),
                yaxis=dict(tickprefix="$"),
                coloraxis_colorbar=dict(
                    title="Margin %",
                    tickfont=dict(color="#4b5563"),
                    bgcolor=BG, outlinecolor=GRID,
                ),
            )
            st.plotly_chart(fig3, use_container_width=True)

    # AI-style auto-generated insights
    st.markdown('<div class="sl" style="margin-top:8px">Auto Insights</div>', unsafe_allow_html=True)

    # Calculate real insights from data
    top_cat    = sales.groupby("category")["revenue"].sum().idxmax()
    top_chan   = sales.groupby("sales_channel")["revenue"].sum().idxmax()
    top_region = sales.groupby("region")["revenue"].sum().idxmax()
    top_seg    = sales.groupby("customer_segment")["revenue"].sum().idxmax() if "customer_segment" in sales.columns else "Enterprise"
    weekend_rev = sales[pd.to_datetime(sales["transaction_date"]).dt.dayofweek >= 5]["revenue"].mean() if not sales.empty else 0
    weekday_rev = sales[pd.to_datetime(sales["transaction_date"]).dt.dayofweek < 5]["revenue"].mean() if not sales.empty else 1
    weekend_drop = ((weekday_rev - weekend_rev) / weekday_rev * 100) if weekday_rev > 0 else 0

    ic1, ic2 = st.columns(2)
    with ic1:
        st.markdown(f"""
        <div class="insight">
          <div class="insight-hdr">
            <span class="tag tag-up">TOP CATEGORY</span> {top_cat}
          </div>
          <div class="insight-body">
            <b>{top_cat}</b> leads all categories by total revenue.
            Consider increasing inventory and marketing investment here.
          </div>
        </div>
        <div class="insight">
          <div class="insight-hdr">
            <span class="tag tag-dn">WEEKEND DIP</span> {weekend_drop:.0f}% lower
          </div>
          <div class="insight-body">
            Weekend average order value is <b>{weekend_drop:.0f}%</b> lower than weekdays.
            An automated weekend promotion could recover this gap.
          </div>
        </div>
        """, unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""
        <div class="insight">
          <div class="insight-hdr">
            <span class="tag tag-up">TOP CHANNEL</span> {top_chan}
          </div>
          <div class="insight-body">
            <b>{top_chan}</b> is the highest-revenue sales channel.
            Other channels may benefit from replicating these conversion tactics.
          </div>
        </div>
        <div class="insight">
          <div class="insight-hdr">
            <span class="tag tag-neu">TOP REGION</span> {top_region}
          </div>
          <div class="insight-body">
            <b>{top_region}</b> accounts for the largest regional revenue share.
            <b>{top_seg}</b> segment drives the most value within this region.
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
