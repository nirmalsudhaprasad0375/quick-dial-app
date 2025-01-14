import streamlit as st
import pandas as pd
import phonenumbers
from phonenumbers import carrier
import csv
from pathlib import Path
import webbrowser
import json
import base64


def initialize_contact_data():
    """Initialize sample contact data if no CSV exists"""
    if not Path("contacts.csv").exists():
        sample_data = {
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'phone': ['+1234567890', '+1987654321', '+1122334455'],
            'category': ['Family', 'Work', 'Friends']
        }
        df = pd.DataFrame(sample_data)
        df.to_csv('contacts.csv', index=False)
    return pd.read_csv('contacts.csv')


def format_phone_number(phone):
    """Format phone number and get last 3 digits"""
    clean_number = ''.join(filter(str.isdigit, str(phone)))
    return clean_number, clean_number[-3:] if len(clean_number) >= 3 else clean_number


def create_contact_map(df):
    """Create a mapping of last 3 digits to full contact information"""
    contact_map = {}
    for _, row in df.iterrows():
        full_number, last_3_digits = format_phone_number(row['phone'])
        contact_map[last_3_digits] = {
            'name': row['name'],
            'full_number': full_number,
            'category': row['category']
        }
    return contact_map


def get_csv_download_link(df):
    """Generate a download link for the contacts CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="contacts.csv">Download Contacts CSV</a>'
    return href


def main():
    st.title("Quick Dial App")

    # Initialize session state for contact management
    if 'contacts_df' not in st.session_state:
        st.session_state.contacts_df = initialize_contact_data()

    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Quick Dial", "Manage Contacts", "Search", "Import/Export"])

    with tab1:
        st.subheader("Search by Last 3 Digits")
        search_digits = st.text_input("Enter last 3 digits:", max_chars=3, key="search_digits")

        if search_digits:
            contact_map = create_contact_map(st.session_state.contacts_df)
            if search_digits in contact_map:
                contact = contact_map[search_digits]
                st.success(f"Found: {contact['name']} ({contact['category']})")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📞 Call"):
                        tel_url = f"tel:{contact['full_number']}"
                        webbrowser.open(tel_url)
                        st.info(f"Initiating call to {contact['name']}")

                with col2:
                    st.write(f"Number: {contact['full_number']}")
            else:
                st.warning("No contact found with those digits")

    with tab2:
        st.subheader("Add New Contact")
        new_name = st.text_input("Name:", key="new_name")
        new_phone = st.text_input("Phone Number:", key="new_phone")
        new_category = st.selectbox("Category", ["Family", "Friends", "Work", "Other"])

        if st.button("Add Contact"):
            if new_name and new_phone:
                try:
                    parsed_number = phonenumbers.parse(new_phone, "US")
                    if phonenumbers.is_valid_number(parsed_number):
                        new_contact = pd.DataFrame({
                            'name': [new_name],
                            'phone': [new_phone],
                            'category': [new_category]
                        })
                        st.session_state.contacts_df = pd.concat([st.session_state.contacts_df, new_contact],
                                                                 ignore_index=True)
                        st.session_state.contacts_df.to_csv('contacts.csv', index=False)
                        st.success("Contact added successfully!")
                    else:
                        st.error("Invalid phone number format")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        st.subheader("Edit/Delete Contacts")
        if not st.session_state.contacts_df.empty:
            for idx, row in st.session_state.contacts_df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.text(row['name'])
                with col2:
                    st.text(row['phone'])
                with col3:
                    st.text(row['category'])
                with col4:
                    if st.button("Delete", key=f"del_{idx}"):
                        st.session_state.contacts_df = st.session_state.contacts_df.drop(idx)
                        st.session_state.contacts_df.to_csv('contacts.csv', index=False)
                        st.experimental_rerun()

    with tab3:
        st.subheader("Search Contacts")
        search_option = st.radio("Search by:", ["Name", "Category"])
        search_term = st.text_input("Enter search term:", key="search_term")

        if search_term:
            if search_option == "Name":
                matches = st.session_state.contacts_df[
                    st.session_state.contacts_df['name'].str.contains(search_term, case=False)]
            else:
                matches = st.session_state.contacts_df[
                    st.session_state.contacts_df['category'].str.contains(search_term, case=False)]

            if not matches.empty:
                st.write("Search Results:")
                st.dataframe(matches)
            else:
                st.warning("No matches found")

    with tab4:
        st.subheader("Import/Export Contacts")

        # Export
        st.markdown("### Export Contacts")
        st.markdown(get_csv_download_link(st.session_state.contacts_df), unsafe_allow_html=True)

        # Import
        st.markdown("### Import Contacts")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            try:
                imported_df = pd.read_csv(uploaded_file)
                if all(col in imported_df.columns for col in ['name', 'phone', 'category']):
                    if st.button("Import Contacts"):
                        st.session_state.contacts_df = pd.concat([st.session_state.contacts_df, imported_df],
                                                                 ignore_index=True)
                        st.session_state.contacts_df.to_csv('contacts.csv', index=False)
                        st.success("Contacts imported successfully!")
                else:
                    st.error("CSV must contain 'name', 'phone', and 'category' columns")
            except Exception as e:
                st.error(f"Error importing contacts: {str(e)}")


if __name__ == "__main__":
    st.set_page_config(page_title="Quick Dial App", page_icon="📞")
    main()