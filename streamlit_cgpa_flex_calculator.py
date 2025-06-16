import streamlit as st

# Predefined credits for different semester IDs
PREDEFINED_CREDITS = {
    "id0": 21.0,
    "id1": 18.0,
    "id2": 21.5,
    "id3": 22.5,
    "id4": 21.5,
    "id5": 21.5,
    "id6": 22.0,
    "id7": 12.0,
}

def calculate_cgpa(semesters_data):
    total_weighted_sgpa = 0
    total_overall_credits = 0

    for semester in semesters_data:
        total_weighted_sgpa += semester['sgpa'] * semester['total_credits']
        total_overall_credits += semester['total_credits']

    if total_overall_credits == 0:
        return 0
    return total_weighted_sgpa / total_overall_credits

def app():
    st.set_page_config(page_title="Flexible CGPA Calculator", layout="centered")
    st.title("Flexible CGPA Calculator")
    st.write("Select the Semester Type and enter the SGPA (Si) to calculate your Cumulative Grade Point Average.")
    st.write("The Total Credits for each Semester Type are predefined as per your request.")

    # Initialize session state for semesters data
    if 'semesters' not in st.session_state:
        st.session_state.semesters = []
    if 'current_semester_id_index' not in st.session_state:
        st.session_state.current_semester_id_index = 0 # Start with the first ID (id0)
    if 'sgpa_current_value' not in st.session_state:
        st.session_state.sgpa_current_value = 0.0 # Default value for the SGPA input field

    # Get the list of semester types
    semester_types = list(PREDEFINED_CREDITS.keys())
    
    # Check if all predefined semester types have been added
    all_semesters_added = len(st.session_state.semesters) >= len(semester_types) and \
                          all(st_type in [s['semester_type'] for s in st.session_state.semesters] for st_type in semester_types)

    if all_semesters_added:
        st.info("All predefined semester types have been entered.")
    else:
        # Input form for new semester
        st.subheader("Add New Semester Data")
        with st.form(key='new_semester_form'):
            col1, col2 = st.columns(2)
            with col1:
                # Ensure the index is within bounds and not already added
                available_semester_types = [st_type for st_type in semester_types if st_type not in [s['semester_type'] for s in st.session_state.semesters]]
                
                if not available_semester_types:
                    st.warning("All predefined semester types have been added.")
                    selected_semester_type = None # No selection possible
                else:
                    # Try to find the next available ID in the original order
                    next_available_index = st.session_state.current_semester_id_index
                    while next_available_index < len(semester_types) and semester_types[next_available_index] not in available_semester_types:
                        next_available_index += 1
                    if next_available_index >= len(semester_types):
                        next_available_index = 0 # Wrap around or reset
                        while next_available_index < len(semester_types) and semester_types[next_available_index] not in available_semester_types:
                            next_available_index += 1
                            if next_available_index >= len(semester_types): # All types added check
                                break

                    # Set the index for the selectbox to the next available type
                    initial_index = 0
                    try:
                        if semester_types[next_available_index] in available_semester_types:
                            initial_index = available_semester_types.index(semester_types[next_available_index])
                    except (IndexError, ValueError):
                        initial_index = 0 # Default to first if issue

                    selected_semester_type = st.selectbox(
                        "Select Semester Type",
                        options=available_semester_types,
                        index=initial_index,
                        key="semester_type_select"
                    )
            with col2:
                # Display predefined credits for the selected type
                predefined_credits = PREDEFINED_CREDITS.get(selected_semester_type, 0.0) if selected_semester_type else 0.0
                st.metric(label="Predefined Total Credits (Ci)", value=f"{predefined_credits:.1f}")
                
                sgpa_input = st.number_input(
                    "Semester SGPA (Si)",
                    min_value=0.0, max_value=10.0, step=0.01, format="%.2f",
                    disabled=selected_semester_type is None,
                    value=st.session_state.sgpa_current_value, # Control value with session state
                    key="sgpa_input_widget" # Unique key for this widget
                )

            add_semester_button = st.form_submit_button("Add Semester", disabled=selected_semester_type is None)

            if add_semester_button:
                if sgpa_input is not None and predefined_credits > 0 and selected_semester_type is not None:
                    st.session_state.semesters.append({
                        'semester_type': selected_semester_type,
                        'sgpa': sgpa_input,
                        'total_credits': predefined_credits
                    })
                    st.success(f"Semester added: Type '{selected_semester_type}', SGPA {sgpa_input:.2f}, Credits {predefined_credits:.1f}")
                    
                    # Increment the index for the next semester type, but don't go beyond the max
                    current_type_index = semester_types.index(selected_semester_type)
                    st.session_state.current_semester_id_index = (current_type_index + 1) % len(semester_types)
                    
                    # Reset the sgpa input value in session state to clear the field
                    st.session_state.sgpa_current_value = 0.0

                    st.rerun() # Rerun to update the displayed list and clear inputs
                else:
                    st.error("Please enter a valid SGPA and ensure a Semester Type is selected with credits.")

    # Display entered semesters and allow removal
    if st.session_state.semesters:
        st.subheader("Entered Semesters")
        display_semesters = []
        for i, sem in enumerate(st.session_state.semesters):
            display_semesters.append({
                "ID": i,
                "Semester Type": sem['semester_type'],
                "Semester SGPA": f"{sem['sgpa']:.2f}",
                "Total Credits": f"{sem['total_credits']:.1f}"
            })
        
        st.dataframe(display_semesters, use_container_width=True, hide_index=True)

        # Option to remove a semester
        col_remove, col_reset = st.columns(2)
        with col_remove:
            # Ensure the max_value for number_input is dynamic based on current semesters
            max_remove_id = len(st.session_state.semesters) - 1 if st.session_state.semesters else 0
            semester_to_remove = st.number_input("Enter ID to remove semester", min_value=0, max_value=max_remove_id, step=1, key="remove_id_input", disabled=not st.session_state.semesters)
            if st.button("Remove Selected Semester", disabled=not st.session_state.semesters): 
                if 0 <= semester_to_remove < len(st.session_state.semesters):
                    removed_sem = st.session_state.semesters.pop(int(semester_to_remove))
                    st.warning(f"Semester Type '{removed_sem['semester_type']}' (ID {int(semester_to_remove)}) removed.")
                    st.rerun() # Rerun to update the displayed list
                else:
                    st.error("Invalid Semester ID.")
        
        with col_reset:
            if st.button("Clear All Semesters", disabled=not st.session_state.semesters): 
                st.session_state.semesters = []
                st.info("All semester data cleared.")
                st.rerun() # Rerun to reset the UI

        # Calculate and display CGPA
        cgpa = calculate_cgpa(st.session_state.semesters)
        st.markdown(f"## Overall CGPA: <span style=\'color:green;\'>{cgpa:.2f}</span>", unsafe_allow_html=True)
    else:
        st.info("No semester data entered yet. Please add semester details above.")

# Run the app
if __name__ == "__main__":
    app() 