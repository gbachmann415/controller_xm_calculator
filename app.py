import streamlit as st
from itertools import combinations

# --- Data ---
controllers = [
    {"name": "SYM210", "UI": 2, "AI": 3, "BI": 1, "AO_BI": 2, "UIO": 0, "BO_Dry": 0, "BO_Wet": 5, "comments": ""},
    {"name": "SYM400b", "UI": 2, "AI": 5, "BI": 3, "AO_BI": 2, "UIO": 0, "BO_Dry": 3, "BO_Wet": 6, "comments": "Same as SYM500, but no IP and no internal scheduling clock - Factory installed board"},
    {"name": "SYM500", "UI": 2, "AI": 5, "BI": 3, "AO_BI": 2, "UIO": 0, "BO_Dry": 3, "BO_Wet": 6, "comments": "* includes the separate pressure AI's"},
    {"name": "UC600", "UI": 8, "AI": 0, "BI": 0, "AO_BI": 0, "UIO": 6, "BO_Dry": 0, "BO_Wet": 4, "comments": ""},
    {"name": "SYM700", "UI": 0, "AI": 1, "BI": 0, "AO_BI": 0, "UIO": 0, "BO_Dry": 5, "BO_Wet": 0, "comments": "For BAS system communication ALWAYS buy the 'Advanced Board'. Thermostat or sensor application is typical"}
]

xms = [
    {"name": "XM30", "UI": 0, "AI": 0, "BI": 0, "AO_BI": 0, "UIO": 4, "BO_Dry": 0, "BO_Wet": 0, "comments": "Mix and match for up to 4 qty I/O's"},
    {"name": "XM32", "UI": 0, "AI": 0, "BI": 0, "AO_BI": 0, "UIO": 0, "BO_Dry": 0, "BO_Wet": 4, "comments": "Only BO's"},
    {"name": "XM70", "UI": 8, "AI": 0, "BI": 0, "AO_BI": 0, "UIO": 6, "BO_Dry": 0, "BO_Wet": 4, "comments": "Mix and match for up to 19 qty I/O's"},
    {"name": "XM90", "UI": 16, "AI": 0, "BI": 0, "AO_BI": 0, "UIO": 8, "BO_Dry": 0, "BO_Wet": 8, "comments": "Mix and match for up to 32 qty I/O's"}
]

# --- UI ---
st.title("Controller & XM Point Calculator")

ai = st.number_input("Analog Inputs (AI)", min_value=0, value=0)
bi = st.number_input("Binary Inputs (BI)", min_value=0, value=0)
ao = st.number_input("Analog Outputs (AO)", min_value=0, value=0)
bo_dry = st.number_input("BO Dry", min_value=0, value=0)
bo_wet = st.number_input("BO Wet", min_value=0, value=0)
headroom_pct = st.number_input("Headroom (%) [optional]", min_value=0.0, max_value=100.0, value=0.0) / 100

selected_controllers = st.multiselect("Select Controllers", [c['name'] for c in controllers], default=[c['name'] for c in controllers])
selected_xms = st.multiselect("Select Expansion Modules", [xm['name'] for xm in xms], default=[xm['name'] for xm in xms])

# --- Run Calculation ---
if st.button("Calculate"):
    ai_adj = int(ai * (1 + headroom_pct))
    bi_adj = int(bi * (1 + headroom_pct))
    ao_adj = int(ao * (1 + headroom_pct))
    bo_dry_adj = int(bo_dry * (1 + headroom_pct))
    bo_wet_adj = int(bo_wet * (1 + headroom_pct))

    results = []
    st.session_state['results'] = []  # Clear previous

    active_controllers = [c for c in controllers if c['name'] in selected_controllers]
    active_xms = [xm for xm in xms if xm['name'] in selected_xms]

    for controller in active_controllers:
        for r in range(0, len(active_xms) + 1):
            for xm_combo in combinations(active_xms, r):
                combined = controller.copy()
                for xm in xm_combo:
                    for key in ["UI", "AI", "BI", "AO_BI", "UIO", "BO_Dry", "BO_Wet"]:
                        combined[key] += xm[key]

                remaining = combined.copy()
                alloc = {k: {"AI": 0, "BI": 0, "AO": 0, "BO_Dry": 0, "BO_Wet": 0} for k in remaining}

                ai_req, bi_req, ao_req, bo_dry_req, bo_wet_req = ai_adj, bi_adj, ao_adj, bo_dry_adj, bo_wet_adj

                for src in ["AI", "UI", "UIO"]:
                    used = min(ai_req, remaining[src])
                    alloc[src]['AI'] = used
                    remaining[src] -= used
                    ai_req -= used

                for src in ["BI", "UI", "AO_BI", "UIO"]:
                    used = min(bi_req, remaining[src])
                    alloc[src]['BI'] = used
                    remaining[src] -= used
                    bi_req -= used

                for src in ["AO_BI", "UIO"]:
                    used = min(ao_req, remaining[src])
                    alloc[src]['AO'] = used
                    remaining[src] -= used
                    ao_req -= used

                for src in ["BO_Dry", "UIO"]:
                    used = min(bo_dry_req, remaining[src])
                    alloc[src]['BO_Dry'] = used
                    remaining[src] -= used
                    bo_dry_req -= used

                for src in ["BO_Wet", "UIO"]:
                    used = min(bo_wet_req, remaining[src])
                    alloc[src]['BO_Wet'] = used
                    remaining[src] -= used
                    bo_wet_req -= used

                if all(x <= 0 for x in [ai_req, bi_req, ao_req, bo_dry_req, bo_wet_req]):
                    combo_names = controller['name'] + (" + " + " + ".join(xm['name'] for xm in xm_combo) if xm_combo else "")
                    results.append({
                        "combo": combo_names,
                        "alloc": alloc,
                        "remaining": remaining.copy(),
                        "comments": controller["comments"],
                        "xm_count": len(xm_combo)
                    })

    if results:
        st.session_state['results'] = results
    else:
        st.error("❌ No valid combinations found with the selected controllers/modules and required points.")
        st.session_state.pop('results', None)

# --- Display Results if Available ---
if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']
    sorted_results = sorted(results, key=lambda x: x["xm_count"])
    best = sorted_results[0]

    st.markdown("## ✅ Recommended Option")
    st.success(f"**{best['combo']}**")
    if best['comments']:
        st.markdown(f"💬 **Comments:** {best['comments']}")

    st.markdown("### 🔹 Used Points (by source)")
    used_table = []
    for src, usage in best["alloc"].items():
        total = sum(usage.values())
        if total > 0:
            row = {"Source": src}
            row.update({k: v for k, v in usage.items() if v > 0})
            used_table.append(row)
    st.table(used_table)

    st.markdown("### 🔹 Remaining Points")
    col1, col2 = st.columns(2)
    keys = list(best["remaining"].keys())
    mid = len(keys) // 2
    with col1:
        for key in keys[:mid]:
            st.markdown(f"**{key}**: {best['remaining'][key]}")
    with col2:
        for key in keys[mid:]:
            st.markdown(f"**{key}**: {best['remaining'][key]}")

    # Dropdown to explore all options
    st.markdown("---")
    st.markdown("### 🔽 Explore All Valid Options")
    option_labels = [r["combo"] for r in sorted_results]
    selected_label = st.selectbox("Select an option to view details:", option_labels, index=0)

    selected_result = next(r for r in sorted_results if r["combo"] == selected_label)

    st.markdown(f"**🧩 Option:** {selected_result['combo']}")
    if selected_result["comments"]:
        st.markdown(f"💬 **Comments:** {selected_result['comments']}")

    st.markdown("#### 🔹 Used Points (by source)")
    used_table_alt = []
    for src, usage in selected_result["alloc"].items():
        total = sum(usage.values())
        if total > 0:
            row = {"Source": src}
            row.update({k: v for k, v in usage.items() if v > 0})
            used_table_alt.append(row)
    st.table(used_table_alt)

    st.markdown("#### 🔹 Remaining Points")
    col1, col2 = st.columns(2)
    keys = list(selected_result["remaining"].keys())
    mid = len(keys) // 2
    with col1:
        for key in keys[:mid]:
            st.markdown(f"**{key}**: {selected_result['remaining'][key]}")
    with col2:
        for key in keys[mid:]:
            st.markdown(f"**{key}**: {selected_result['remaining'][key]}")

# --- Optional: Reset ---
if st.button("Reset Results"):
    st.session_state.pop('results', None)
