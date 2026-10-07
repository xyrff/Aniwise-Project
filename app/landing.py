import streamlit as st

AVATAR_SVG = (
    '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" '
    'stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="8" r="4"/>'
    '<path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>'
    '</svg>'
)

TEAM_MEMBERS = [
    {"name": "Name", "role": "Role"},
    {"name": "Name", "role": "Role"},
    {"name": "Name", "role": "Role"},
]


def render_landing_page():
    # --- Nav ---
    st.markdown(
        '<div class="landing-nav">'
        '<div class="landing-nav-brand">🍃 AniWise</div>'
        '<div class="landing-nav-links">'
        '<a href="#how-it-works">How it Works</a>'
        '<a href="#meet-the-team">Meet the Team</a>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --- Hero (everything inside ONE real container) ---
    with st.container(key="hero_section"):
        st.markdown(
            '<div class="hero-copy-landing">'
            '<span class="hero-badge-landing">Machine Learning-Based Crop Recommendation</span>'
            '<h1 class="hero-title-landing">Smarter planting decisions<br>with AniWise</h1>'
            '</div>',
            unsafe_allow_html=True,
        )

        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            get_started = st.button(
                "→ Get Started", use_container_width=True, type="primary")

        st.markdown(
            '<div class="icon-chip-row">'
            '<div class="icon-chip-small">🍃</div>'
            '<div class="icon-chip-main">🌱</div>'
            '<div class="icon-chip-small">🍃</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # --- How it Works ---
    st.markdown('<div id="how-it-works" class="section-title-landing">How it Works</div>',
                unsafe_allow_html=True)
    steps = [
        ("🎛", "1. Enter your soil & climate data",
         "Add your soil test and local climate values."),
        ("⚙️", "2. Our model analyzes the inputs",
         "Let machine learning find the best crop fit."),
        ("🌱", "3. Get ranked crop recommendations",
         "Explore the crops best suited to your farm."),
    ]
    cols = st.columns(3, gap="large")
    for col, (icon, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f'<div class="step-card-landing">'
                f'<div class="step-icon-chip">{icon}</div>'
                f'<div class="step-title-landing">{title}</div>'
                f'<div class="step-desc-landing">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # --- Meet the Team (everything inside ONE real container) ---
    st.markdown('<div id="meet-the-team"></div>', unsafe_allow_html=True)
    with st.container(key="team_section"):
        st.markdown('<div class="section-title-landing" style="margin-top:0;">Meet the Team</div>',
                    unsafe_allow_html=True)
        team_cols = st.columns(3, gap="large")
        for col, member in zip(team_cols, TEAM_MEMBERS):
            with col:
                st.markdown(
                    f'<div class="team-card-landing">'
                    f'<div class="team-avatar-placeholder">{AVATAR_SVG}</div>'
                    f'<div class="team-name-landing">{member["name"]}</div>'
                    f'<div class="team-role-landing">{member["role"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # --- Footer ---
    st.markdown(
        '<div class="footer-landing">'
        '<div>'
        '<div class="footer-brand-landing">🍃 AniWise</div>'
        '<p style="font-size:12px; color:#94a3b8; margin-top:4px;">Smarter choices. Better harvests.</p>'
        '</div>'
        '<div style="text-align:right; font-size:12px; color:#94a3b8;">'
        'Made for Filipino farmers<br>© 2026 AniWise. All rights reserved.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    return get_started
