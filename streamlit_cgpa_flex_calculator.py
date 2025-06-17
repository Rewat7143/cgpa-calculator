import streamlit as st
import pandas as pd

# --- Page Config (Must be the first Streamlit command) ---
st.set_page_config(
    page_title="CGPA Calculator",
    page_icon=":mortar_board:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* General Body Styles */
    body { background-color: #f8f9fa; color: #343a40; font-family: 'Roboto', sans-serif; }
    .stApp { background-color: #f8f9fa; }

    /* Header Styling */
    .st-emotion-cache-10qzyy6 { /* Target for main app title */
        color: #0056b3; /* Muted blue */
        font-weight: 700;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Subheader Styling */
    h2, h3 { color: #004085; font-weight: 600; margin-top: 1.5em; margin-bottom: 0.8em; }
    
    /* Container Styling - applies to st.container generally */
    .st-emotion-cache-nahz7x.e1g8pov61 { 
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #e9ecef;
    }

    /* Button Styling */
    .stButton > button { 
        background-color: #007bff; /* Muted blue */
        color: white;
        border-radius: 5px;
        border: none;
        padding: 8px 15px;
        font-weight: 500;
        transition: background-color 0.2s, transform 0.1s;
    }
    .stButton > button:hover { 
        background-color: #0056b3; /* Darker blue on hover */
        transform: translateY(-1px);
    }
    .stButton > button:active { 
        transform: translateY(0);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input, .stNumberInput > div > div > input { 
        border-radius: 5px;
        border: 1px solid #ced4da;
        padding: 8px 12px;
    }

    /* Info/Warning/Success Messages */
    .stAlert { border-radius: 8px; }
    .stAlert.info { background-color: #e7f3ff; color: #004085; border-left: 5px solid #007bff; }
    .stAlert.success { background-color: #e6ffed; color: #0f5132; border-left: 5px solid #28a745; }
    .stAlert.warning { background-color: #fff3cd; color: #664d03; border-left: 5px solid #ffc107; }
    .stAlert.error { background-color: #f8d7da; color: #842029; border-left: 5px solid #dc3545; }

    /* Sidebar */
    .sidebar .sidebar-content { background-color: #e9ecef; padding: 20px; }

    /* Metric (CGPA display) */
    [data-testid="stMetric"] > div > div:first-child { 
        color: #495057; 
        font-size: 1.1em;
        font-weight: 500;
    }
    [data-testid="stMetric"] > div > div:nth-child(2) { 
        color: #28a745; /* Green for CGPA */
        font-size: 2em;
        font-weight: 700;
    }
    
    /* No specific card-style for semesters anymore, only general container styles apply */

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .st-emotion-cache-10qzyy6 { margin-bottom: 10px; padding-bottom: 5px; }
        .st-emotion-cache-nahz7x.e1g8pov61 { padding: 15px; margin-bottom: 10px; }
        .stButton > button { padding: 6px 12px; font-size: 0.9em; }
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration and Constants ---
MAX_SEMESTERS = 8
SGPA_MIN = 0.0
SGPA_MAX = 10.0
CREDITS_MIN_DISPLAY = 0.01 # Used for min_value in number_input to enforce >0

# Custom semester labels as requested
SEMESTER_LABELS = [
    "Semester 1-1", "Semester 1-2",
    "Semester 2-1", "Semester 2-2",
    "Semester 3-1", "Semester 3-2",
    "Semester 4-1", "Semester 4-2"
]

# --- Session State Initialization ---
# Initialize session state variables if they don't exist
if 'semesters' not in st.session_state:
    st.session_state.semesters = []
if 'current_semester_index' not in st.session_state:
    st.session_state.current_semester_index = 0 # Use 0-based index for SEMESTER_LABELS
if 'sgpa_input_key_counter' not in st.session_state:
    st.session_state.sgpa_input_key_counter = 0 # To force re-render of input fields
if 'editing_semester_index' not in st.session_state:
    st.session_state.editing_semester_index = None
if 'is_resetting' not in st.session_state:
    st.session_state.is_resetting = False

# --- Helper Functions ---
def calculate_cgpa(semesters_data):
    """
    Calculates the Cumulative Grade Point Average (CGPA) based on semester data.
    Each semester entry should be a dictionary with 'SGPA (Si)' and 'Credits (Ci)'.
    """
    total_weighted_sgpa = 0
    total_overall_credits = 0

    for semester in semesters_data:
        # Ensure that 'SGPA (Si)' and 'Credits (Ci)' are treated as numbers
        # and handle potential None or NaN values from data_editor
        sgpa = semester.get('SGPA (Si)')
        credits = semester.get('Credits (Ci)')

        if pd.isna(sgpa) or sgpa is None:
            sgpa = 0.0
        if pd.isna(credits) or credits is None:
            credits = 0.0

        total_weighted_sgpa += float(sgpa) * float(credits)
        total_overall_credits += float(credits)

    if total_overall_credits == 0:
        return 0.0 # Avoid division by zero
    return total_weighted_sgpa / total_overall_credits

def add_semester_data(new_sgpa, new_credits):
    """
    Adds a new semester entry or updates an existing one in session state.
    """
    if st.session_state.editing_semester_index is not None:
        # Update existing semester
        index_to_edit = st.session_state.editing_semester_index
        st.session_state.semesters[index_to_edit]['SGPA (Si)'] = new_sgpa
        st.session_state.semesters[index_to_edit]['Credits (Ci)'] = new_credits
        st.session_state.editing_semester_index = None # Exit edit mode
        st.success(f"Semester {st.session_state.semesters[index_to_edit]['Semester']} data updated!")
    elif st.session_state.current_semester_index < MAX_SEMESTERS:
        # Add new semester
        semester_label = SEMESTER_LABELS[st.session_state.current_semester_index]
        st.session_state.semesters.append({
            'Semester': semester_label,
            'SGPA (Si)': new_sgpa,
            'Credits (Ci)': new_credits
        })
        st.session_state.current_semester_index += 1
        st.success(f"Data for {semester_label} added successfully!")
    else:
        st.warning("All 8 semesters have been entered. You can edit existing entries in the table below.")
    st.session_state.sgpa_input_key_counter += 1 # Increment key to clear form fields

def delete_semester(index):
    """
    Deletes a semester entry from session state.
    """
    if 0 <= index < len(st.session_state.semesters):
        deleted_semester_label = st.session_state.semesters[index]['Semester']
        del st.session_state.semesters[index]
        # If the deleted semester was before the current_semester_index, decrement it
        if index < st.session_state.current_semester_index:
            st.session_state.current_semester_index = max(0, st.session_state.current_semester_index - 1)
        st.session_state.editing_semester_index = None # Exit edit mode
        st.success(f"Semester {deleted_semester_label} data deleted.")

def edit_semester(index):
    """
    Sets the session state to enable editing of a specific semester.
    """
    st.session_state.editing_semester_index = index
    st.session_state.sgpa_input_key_counter += 1 # Force re-render of input fields with new values

def reset_all_data():
    """
    Resets all semester data and current semester number in session state.
    """
    st.session_state.semesters = []
    st.session_state.current_semester_index = 0 # Reset to the first semester label index
    st.session_state.sgpa_input_key_counter = 0 # Reset key to clear input fields
    st.session_state.editing_semester_index = None # Exit edit mode
    st.success("All semester data has been cleared!")

def convert_df_to_csv(df):
    """
    Converts a pandas DataFrame to CSV format for download.
    """
    return df.to_csv(index=False).encode('utf-8')

# --- UI Rendering Functions ---
def render_sidebar():
    """
    Renders the sidebar content.
    """
    with st.sidebar:
        st.markdown("## College CGPA Calculator")
        st.write("") # Spacing
        st.markdown(
            """
            This tool helps you calculate your Cumulative Grade Point Average (CGPA)
            by entering your Semester Grade Point Average (SGPA) and Total Credits (Ci)
            for each academic semester.
            
            **Instructions:**
            1.  Enter SGPA and Credits for the displayed semester.
            2.  Click "Add Semester Data".
            3.  The next semester in sequence will automatically appear.
            4.  Review, Edit, or Remove semester entries in the "Your Semesters" table.
            5.  Your overall CGPA updates live!
            6.  Export your data anytime.
            """
        )
        st.write("") # Spacing
        st.button(
            "🔄 Clear All Data",
            on_click=reset_all_data,
            help="Clear all entered semester data and reset the calculator."
        )
        st.write("") # Spacing
        st.markdown("<small>CGPA Calculator v1.0</small>", unsafe_allow_html=True)
        st.markdown("<small>Developed by Reddy Rewat</small>", unsafe_allow_html=True)

def render_add_semester_form():
    """
    Renders the form for adding/editing semester data.
    """
    current_semester_label = SEMESTER_LABELS[st.session_state.current_semester_index] if st.session_state.current_semester_index < MAX_SEMESTERS else "N/A"

    if st.session_state.editing_semester_index is not None:
        # Pre-fill form for editing
        edit_sem = st.session_state.semesters[st.session_state.editing_semester_index]
        initial_sgpa = edit_sem['SGPA (Si)']
        initial_credits = edit_sem['Credits (Ci)']
        form_title = f"Edit Data for {edit_sem['Semester']}"
        button_label = "Update Semester Data"
    else:
        initial_sgpa = None
        initial_credits = None
        form_title = f"Add Data for {current_semester_label}"
        button_label = "Add Semester Data"

    st.markdown(f"### {form_title}")
    with st.form(key='semester_form', clear_on_submit=(st.session_state.editing_semester_index is None)):
        col1, col2 = st.columns([0.4, 0.6]) # Adjust column width for better spacing
        
        with col1:
            # Display current semester label
            st.text_input(
                "Semester",
                value=current_semester_label if st.session_state.editing_semester_index is None else edit_sem['Semester'],
                disabled=True,
                key="display_semester_label"
            )

        with col2:
            # Input for Credits
            new_credits = st.number_input(
                "Total Credits (Ci)",
                min_value=CREDITS_MIN_DISPLAY,
                max_value=50.0, # A reasonable upper limit
                value=initial_credits if initial_credits is not None else CREDITS_MIN_DISPLAY, # Default to min_value if adding new
                step=0.5,
                format="%.1f",
                key=f"credits_input_{st.session_state.sgpa_input_key_counter}",
                help="Enter the total credits for this semester (e.g., 21.0)."
            )
            # Input for SGPA
            new_sgpa = st.number_input(
                "Semester SGPA (Si)",
                min_value=SGPA_MIN,
                max_value=SGPA_MAX,
                value=initial_sgpa if initial_sgpa is not None else SGPA_MIN, # Default to min_value if adding new
                step=0.01,
                format="%.2f",
                key=f"sgpa_input_{st.session_state.sgpa_input_key_counter}",
                help="Enter your SGPA for this semester (0.00 to 10.00)."
            )

        # Submit button for the form (placed directly inside the form)
        submit_button = st.form_submit_button(button_label)

        if submit_button:
            # --- Input Validation ---
            if not (SGPA_MIN <= new_sgpa <= SGPA_MAX):
                st.error(f"SGPA must be between {SGPA_MIN:.1f} and {SGPA_MAX:.1f}.")
            elif new_credits <= 0:
                st.error("Total Credits must be greater than zero.")
            else:
                add_semester_data(new_sgpa, new_credits)

def render_semester_table_and_actions():
    """
    Renders the table of entered semesters and associated action buttons (Edit, Delete).
    """
    st.markdown("### Your Semesters")

    if st.session_state.semesters:
        # Define column widths for the manual table layout
        # Wider columns for Semester, SGPA, Credits, then narrower for buttons
        col_widths = [0.3, 0.2, 0.15, 0.1, 0.1] 

        # Header Row
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.markdown("**Semester**")
        with header_cols[1]:
            st.markdown("**SGPA**")
        with header_cols[2]:
            st.markdown("**Credits**")
        with header_cols[3]:
            st.markdown(" ") # Placeholder for Edit button header
        with header_cols[4]:
            st.markdown(" ") # Placeholder for Remove button header
        st.markdown("--- ") # Separator below header

        # Data Rows with Buttons
        for i, semester in enumerate(st.session_state.semesters):
            # Ensure values are float for calculation and handle potential NaN for display
            sgpa_val = semester.get('SGPA (Si)')
            credits_val = semester.get('Credits (Ci)')

            # Format values for display, handling NaN gracefully
            display_sgpa = f"{sgpa_val:.2f}" if pd.notna(sgpa_val) else "N/A"
            display_credits = f"{credits_val:.1f}" if pd.notna(credits_val) else "N/A"

            row_cols = st.columns(col_widths)
            with row_cols[0]:
                st.markdown(f"**{semester['Semester']}**")
            with row_cols[1]:
                st.markdown(f"{display_sgpa}")
            with row_cols[2]:
                st.markdown(f"{display_credits}")
            with row_cols[3]:
                st.button(
                    "✏️",
                    key=f"edit_btn_{i}",
                    on_click=edit_semester, args=(i,),
                    help=f"Edit data for {semester['Semester']}"
                )
            with row_cols[4]:
                st.button(
                    "🗑️",
                    key=f"delete_btn_{i}",
                    on_click=delete_semester, args=(i,),
                    type="secondary",
                    help=f"Remove {semester['Semester']}"
                )
            # Add a subtle separator between rows for visual clarity
            if i < len(st.session_state.semesters) - 1:
                st.markdown("--- ") # Use a subtle line between entries

    else:
        st.info("No semester data entered yet.")

def render_cgpa_display():
    """
    Renders the calculated CGPA and total credits.
    """
    cgpa = calculate_cgpa(st.session_state.semesters)
    total_credits = sum(s['Credits (Ci)'] for s in st.session_state.semesters if pd.notna(s.get('Credits (Ci)')))

    st.markdown("---") # Visual separator
    
    cols = st.columns(2) # Create two columns
    with cols[0]:
        st.metric(label="Your Cumulative CGPA", value=f"{cgpa:.2f}")
    with cols[1]:
        st.metric(label="Total Credits Earned", value=f"{total_credits:.1f}")

    st.markdown("---") # Visual separator

def render_export_button():
    """
    Renders the export to CSV button.
    """
    if st.session_state.semesters:
        df_export = pd.DataFrame(st.session_state.semesters)
        csv = convert_df_to_csv(df_export)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="cgpa_data.csv",
            mime="text/csv",
            help="Download all entered semester data as a CSV file."
        )
    else:
        st.button("Download Data as CSV", disabled=True, help="No data to export yet.")

# --- Main Application Function ---
def app():
    # This function now orchestrates the rendering of different components

    # Handle reset action first to ensure clean state on rerun
    if st.session_state.is_resetting:
        st.session_state.is_resetting = False
        st.rerun()

    render_sidebar()

    st.title("Flexible CGPA Calculator :mortar_board:")

    render_add_semester_form()
    st.write("---") # Separator

    render_semester_table_and_actions()
    
    render_cgpa_display()

    render_export_button()

# --- Run the App ---
if __name__ == "__main__":
    app() 