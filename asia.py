import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Google Sheets Connection
@st.cache_resource
def get_gs_client():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    return gspread.authorize(creds)

client = get_gs_client()

@st.cache_data(ttl=600)
def get_sheet_data(sheet_name):
    sh = client.open("Asia 2027")
    worksheet = sh.worksheet(sheet_name)
    return worksheet.get_all_values()

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
    # Slice rows 38-102 (Index 37 to 101)
    df_overview = pd.DataFrame(rows[37:102], columns=["Date", "Activity", "Information", *[""]*(len(rows[0])-3)])
    df_overview = df_overview.iloc[:, 0:3]
    
    # Format Date
    df_overview['Date'] = pd.to_datetime(df_overview['Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
    st.dataframe(df_overview, use_container_width=True, hide_index=True)

elif st.session_state.page == 'Country':
    country = st.session_state.current_country
    st.title(f"{country} Destinations")
    if st.button("Back to Home"): navigate_to('Home')
    
    rows = get_sheet_data(f"{country} Itinerary")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    destinations = df.iloc[:, 3].dropna().unique()
    
    for dest in destinations:
        display_text = f"🚌 {dest}" if str(dest).lower().startswith("travel") else dest
        if st.button(display_text, key=dest):
            navigate_to('Destination', country, dest)

elif st.session_state.page == 'Destination':
    country, dest = st.session_state.current_country, st.session_state.selected_destination
    st.title(dest)
    if st.button("Back to Country"): navigate_to('Country', country)
    
    rows = get_sheet_data(f"{country} Itinerary")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    dest_df = df[df.iloc[:, 3] == dest]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        # Note: G is column index 6, I is index 8 in 0-indexed list
        link = dest_df.iloc[0, 6] 
        if str(link).startswith("http"): st.link_button("Accommodation", link)
    with col2:
        link = dest_df.iloc[0, 8]
        if str(link).startswith("http"): st.link_button("Food", link)
    with col3:
        if st.button("Activities"): st.session_state.show_activities = True
            
    if getattr(st.session_state, 'show_activities', False):
        act_data = dest_df.iloc[:, [4, 5]]
        act_data.columns = ["Activity", "Comments"]
        st.table(act_data)