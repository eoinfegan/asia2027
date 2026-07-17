import streamlit as st
import pandas as pd
import gspread
import os
import re
from google.oauth2.service_account import Credentials

# 1. Google Sheets Connection (Robust Auth)
@st.cache_resource
def get_gs_client():
    # Verify the secrets exist
    if "gcp_service_account" not in st.secrets:
        st.error("Section 'gcp_service_account' not found in secrets!")
        st.stop()
        
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Ensure private_key exists
    if "private_key" not in creds_dict:
        st.error("Key 'private_key' not found in secrets!")
        st.stop()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Authorize using modern Google Auth
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

client = get_gs_client()

@st.cache_data(ttl=600)
def get_sheet_data(sheet_name):
    sh = client.open("Asia 2027")
    worksheet = sh.worksheet(sheet_name)
    return worksheet.get_all_values()

# Robust URL extraction using Regex
def clean_url(url_val):
    val = str(url_val).strip()
    if not val or val.lower() in ['nan', 'none', '']:
        return None
    match = re.search(r'(https?://[^\s"\'\)]+)', val)
    if match:
        return match.group(1)
    return None

# 2. Navigation State
if 'page' not in st.session_state: st.session_state.page = 'Home'

def navigate_to(page, country=None, destination=None):
    st.session_state.page = page
    st.session_state.current_country = country
    st.session_state.selected_destination = destination
    st.rerun()

# 3. UI Pages
if st.session_state.page == 'Home':
    st.title("Travel Planner 2027")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cambodia"): navigate_to('Country', 'Cambodia')
        if st.button("Laos"): navigate_to('Country', 'Laos')
        if st.button("Vietnam"): navigate_to('Country', 'Vietnam')
    with col2:
        if st.button("Japan"): navigate_to('Country', 'Japan')
        if st.button("Overview"): navigate_to('Overview')

elif st.session_state.page == 'Overview':
    st.title("Overview")
    if st.button("Back to Home"): navigate_to('Home')
    rows = get_sheet_data("overall itinerary")
    df_overview = pd.DataFrame(rows[37:102], columns=["Date", "Activity", "Information"] + [""]*(len(rows[0])-3))
    df_overview = df_overview.iloc[:, 0:3]
    df_overview['Date'] = pd.to_datetime(df_overview['Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
    st.dataframe(df_overview, use_container_width=True, hide_index=True)

elif st.session_state.page == 'Country':
    country = st.session_state.current_country
    st.title(f"{country} Destinations")
    if st.button("Back to Home"): navigate_to('Home')
    rows = get_sheet_data(f"{country} Itinerary")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    destinations = df.iloc[:, 3].dropna().unique()
    for i, dest in enumerate(destinations):
        if str(dest).strip() == "": continue
        display_text = f"🚌 {dest}" if str(dest).lower().startswith("travel") else dest
        if st.button(display_text, key=f"{dest}_{i}"): navigate_to('Destination', country, dest)

elif st.session_state.page == 'Destination':
    country, dest = st.session_state.current_country, st.session_state.selected_destination
    st.title(dest)
    if st.button("Back to Country"): navigate_to('Country', country)
    
    rows = get_sheet_data(f"{country} Itinerary")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    df.iloc[:, 3] = df.iloc[:, 3].str.strip()
    dest_df = df[df.iloc[:, 3] == dest.strip()]
    
    if dest_df.empty:
        st.error(f"No data found for '{dest}'.")
    else:
        st.subheader("Stay & Eat")
        c1, c2 = st.columns([1, 2])
        acc_link = clean_url(dest_df.iloc[0, 9])
        acc_name = dest_df.iloc[0, 7]
        with c1:
            if acc_link: st.link_button("🏨 Accommodation", acc_link)
            else: st.write("🏨 *No Link*")
        with c2:
            st.write(f"**{acc_name if pd.notna(acc_name) else 'N/A'}**")
            
        c1, c2 = st.columns([1, 2])
        food_link = clean_url(dest_df.iloc[0, 11])
        food_name = dest_df.iloc[0, 10]
        with c1:
            if food_link: st.link_button("🍽️ Food", food_link)
            else: st.write("🍽️ *No Link*")
        with c2:
            st.write(f"**{food_name if pd.notna(food_name) else 'N/A'}**")
            
        st.divider()
        st.subheader("Activities")
        col_act, col_comm = st.columns([2, 3])
        col_act.write("**Activity**")
        col_comm.write("**Notes**")
        
        for idx, row in dest_df.iterrows():
            activity_name = row.iloc[4]
            activity_comment = row.iloc[5]
            activity_link = clean_url(row.iloc[6])
            
            if pd.notna(activity_name) and str(activity_name).strip() != "":
                c1, c2 = st.columns([2, 3])
                with c1:
                    if activity_link: st.link_button(f"📍 {activity_name}", activity_link)
                    else: st.write(f"**{activity_name}**")
                with c2:
                    st.write(activity_comment if pd.notna(activity_comment) and activity_comment != "" else "-")
