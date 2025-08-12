# Streamlit viewer for mitigation.db
# Run:  streamlit run app.py

import os
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "src/data/mitigation.db")
TABLE = "companies"

st.set_page_config(page_title="Mitigation Companies", layout="wide")

@st.cache_data(show_spinner=False)
def load_df(db_path: str) -> pd.DataFrame:
    if not Path(db_path).exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    # Works with sqlite:/// relative paths
    return pd.read_sql(f"SELECT * FROM {TABLE}", f"sqlite:///{db_path}")

def coalesce_text(x):
    return x if isinstance(x, str) else ""

def main():
    st.title("Mitigation Companies")

    try:
        df = load_df(DB_PATH)
    except Exception as e:
        st.error(str(e))
        st.stop()

    # Quick derived fields
    df["city"] = df["address"].fillna("").str.extract(r",\s*([^,]+),\s*[A-Z]{2}", expand=False)
    df["state"] = df["address"].fillna("").str.extract(r",\s*([A-Z]{2})\s*\d{0,5}$", expand=False)
    df["categories"] = df["categories"].apply(coalesce_text)

    with st.sidebar:
        st.header("Filters")
        text_query = st.text_input("Search (name/address/website)")
        category_q = st.text_input("Category contains", placeholder="mold, fire, water…")
        cities = sorted([c for c in df["city"].dropna().unique() if c])
        city_sel = st.multiselect("City", options=cities)
        min_score = st.number_input("Min score", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
        max_reviews = st.number_input("Max reviews", min_value=0, value=1000, step=50)
        min_reviews = st.number_input("Min reviews", min_value=0, value=0, step=1)
        sort_by = st.selectbox("Sort by", options=["score","rating","review_count","years_in_business","permits_24mo","name"])
        ascending = st.checkbox("Ascending", value=False)
        top_n = st.slider("Rows to show", 10, 1000, 200, step=10)
        st.markdown("---")
        if st.button("Reload data (clear cache)"):
            load_df.clear()  # type: ignore
            st.experimental_rerun() # type: ignore

    # Apply filters
    view = df.copy()
    if text_query:
        tq = text_query.lower()
        mask = (
            view["name"].fillna("").str.lower().str.contains(tq) |
            view["address"].fillna("").str.lower().str.contains(tq) |
            view["website"].fillna("").str.lower().str.contains(tq)
        )
        view = view[mask]

    if category_q:
        for token in [t.strip() for t in category_q.split(",") if t.strip()]:
            view = view[view["categories"].str.contains(token, case=False, na=False)]

    if city_sel:
        view = view[view["city"].isin(city_sel)]

    if min_score:
        view = view[(view["score"].fillna(0) >= float(min_score))]
    if max_reviews:
        view = view[(view["review_count"].fillna(0) <= int(max_reviews))]
    if min_reviews:
        view = view[(view["review_count"].fillna(0) >= int(min_reviews))]

    # Sort + show
    if sort_by not in view.columns:
        sort_by = "score"
    view = view.sort_values(by=sort_by, ascending=ascending)

    # Summary tiles
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Companies", len(view))
    with k2: st.metric("Avg score", round(view["score"].fillna(0).mean(), 3))
    with k3: st.metric("Avg rating", round(view["rating"].fillna(0).mean(), 3))
    with k4: st.metric("Total reviews", int(view["review_count"].fillna(0).sum()))

    st.dataframe(
        view.head(top_n)[[
            "name","score","rating","review_count","address","categories","website","phone","years_in_business","permits_24mo","license_status"
        ]],
        use_container_width=True,
    )

    # Download current view
    csv = view.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", data=csv, file_name="companies_filtered.csv", mime="text/csv")

if __name__ == "__main__":
    main()
