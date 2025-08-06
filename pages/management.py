"""
Management page for JMP Tracker
Password protected administrative functions
"""

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from config import get_text, format_time
from database import (
    get_personnel,
    get_all_departures,
    get_active_departures,
    get_groups,
    safe_dataframe_for_display,
    update_group,
    mark_returned,
    extend_departure,
)
from location import create_personnel_map
from auth import check_password


def render_management():
    """Render the management page"""
    lang = st.session_state.get("language", "en")

    # Password protection
    if not check_password():
        return

    st.markdown(
        f'<p class="main-header">{get_text("app_title", lang)} - {get_text("management", lang)}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="sub-header">{get_text("monitor_manage", lang)}</p>',
        unsafe_allow_html=True,
    )

    # Tabs
    tabs = st.tabs(
        [
            get_text("active_deps_tab", lang),
            get_text("map_view_tab", lang),
            get_text("manifest_tab", lang),
            get_text("groups_tab", lang),
            get_text("statistics_tab", lang),
        ]
    )

    with tabs[0]:
        render_active_departures_tab(lang)

    with tabs[1]:
        render_map_view_tab(lang)

    with tabs[2]:
        render_personnel_manifest_tab(lang)

    with tabs[3]:
        render_groups_tab(lang)

    with tabs[4]:
        render_statistics_tab(lang)


def render_active_departures_tab(lang):
    """Render active departures management tab"""
    st.subheader(get_text("active_deps_tab", lang))

    active_departures = get_active_departures()

    if active_departures.empty:
        st.success(get_text("all_in_camp", lang))
    else:
        # Add action selector
        action = st.selectbox(
            get_text("select_action", lang),
            [
                get_text("view_only", lang),
                get_text("mark_returned", lang),
                get_text("extend_time", lang),
            ],
        )

        # Prepare display dataframe
        display_df = safe_dataframe_for_display(active_departures)

        # Add status column
        display_df["Status"] = display_df.apply(
            lambda row: (
                "🔴 " + get_text("overdue", lang)
                if row["is_overdue"]
                else (
                    "🟡 " + get_text("due_soon", lang)
                    if row["time_remaining"] < 0.5
                    else "🟢 " + get_text("on_time", lang)
                )
            ),
            axis=1,
        )

        # Format time columns
        display_df["Departed"] = pd.to_datetime(display_df["departed_at"]).dt.strftime(
            "%I:%M %p"
        )
        display_df["Expected"] = pd.to_datetime(
            display_df["expected_return"]
        ).dt.strftime("%I:%M %p")
        display_df["Time Remaining"] = display_df["time_remaining"].apply(
            lambda x: (
                f"{int(x)}h {int((x % 1) * 60)}m"
                if x > 0
                else f"Overdue {abs(int(x))}h"
            )
        )

        # Select columns to display
        columns_to_show = [
            "Status",
            "person_name",
            "destination",
            "Departed",
            "Expected",
            "Time Remaining",
            "phone",
            "supervisor",
        ]

        if action == get_text("mark_returned", lang):
            selected_indices = st.multiselect(
                get_text("select_to_return", lang),
                options=display_df.index,
                format_func=lambda x: f"{display_df.loc[x, 'person_name']} - {display_df.loc[x, 'destination']}",
            )

            if st.button(get_text("mark_selected_returned", lang), type="primary"):
                for idx in selected_indices:
                    dep_id = active_departures.loc[idx, "id"]
                    mark_returned(dep_id)
                st.success(
                    f"{len(selected_indices)} {get_text('marked_returned', lang)}"
                )
                st.rerun()

        elif action == get_text("extend_time", lang):
            selected_person_idx = st.selectbox(
                get_text("select_person", lang),
                options=display_df.index,
                format_func=lambda x: f"{display_df.loc[x, 'person_name']} - {display_df.loc[x, 'destination']}",
            )

            if selected_person_idx is not None:
                hours_to_extend = st.slider(get_text("hours_to_extend", lang), 1, 24, 2)

                if st.button(get_text("extend_selected", lang), type="primary"):
                    dep_id = active_departures.loc[selected_person_idx, "id"]
                    extend_departure(dep_id, hours_to_extend)
                    st.success(
                        get_text(
                            "extended_success",
                            lang,
                            name=display_df.loc[selected_person_idx, "person_name"],
                            hours=hours_to_extend,
                        )
                    )
                    st.rerun()

        # Display the dataframe
        st.dataframe(display_df[columns_to_show], use_container_width=True)

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(get_text("total_out", lang), len(active_departures))
        with col2:
            overdue_count = len(active_departures[active_departures["is_overdue"]])
            st.metric(get_text("overdue", lang), overdue_count, delta_color="inverse")
        with col3:
            due_soon = len(active_departures[active_departures["time_remaining"] < 0.5])
            st.metric(get_text("due_soon", lang), due_soon)
        with col4:
            avg_time = active_departures["time_remaining"].mean()
            st.metric(get_text("avg_time_remaining", lang), f"{int(avg_time)}h")


def render_map_view_tab(lang):
    """Render map view management tab"""
    st.subheader(get_text("map_view_tab", lang))

    active_departures = get_active_departures()

    if active_departures.empty:
        st.info(get_text("no_active_personnel", lang))
    else:
        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            show_overdue = st.checkbox(get_text("show_overdue", lang), value=True)
        with col2:
            show_on_time = st.checkbox(get_text("show_on_time", lang), value=True)
        with col3:
            show_no_gps = st.checkbox(get_text("show_no_gps", lang), value=False)

        # Filter departures based on selections
        filtered_deps = active_departures.copy()
        if not show_overdue:
            filtered_deps = filtered_deps[filtered_deps["is_overdue"] == False]
        if not show_on_time:
            filtered_deps = filtered_deps[filtered_deps["is_overdue"] == True]

        # Create and display map
        personnel_map = create_personnel_map(filtered_deps, lang)

        map_data = st_folium(
            personnel_map,
            width=None,
            height=600,
            returned_objects=["last_object_clicked"],
            key="management_map",
        )

        # Show list of personnel without GPS
        if show_no_gps:
            st.subheader(get_text("personnel_no_gps", lang))
            no_gps = active_departures[
                active_departures["last_location"].isna()
                | (active_departures["last_location"] == "")
            ]
            if not no_gps.empty:
                st.dataframe(
                    safe_dataframe_for_display(
                        no_gps[["person_name", "destination", "phone"]]
                    ),
                    use_container_width=True,
                )


def render_personnel_manifest_tab(lang):
    """Render personnel manifest management tab"""
    st.subheader(get_text("manifest_tab", lang))

    # Add upload functionality
    uploaded_file = st.file_uploader(
        "Upload Personnel CSV",
        type=["csv"],
        help="Upload a CSV file with columns: Name, Phone, Supervisor, SupervisorPhone, Company",
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            # Standardize column names
            df.columns = df.columns.str.strip()

            # Map columns if needed
            column_mapping = {
                "name": "Name",
                "Name": "Name",
                "phone": "Phone",
                "Phone": "Phone",
                "supervisor": "Supervisor",
                "Supervisor": "Supervisor",
                "supervisorphone": "SupervisorPhone",
                "SupervisorPhone": "SupervisorPhone",
                "company": "Company",
                "Company": "Company",
            }

            # Rename columns to match expected format
            df.rename(
                columns={k: v for k, v in column_mapping.items() if k in df.columns},
                inplace=True,
            )

            # Process each row
            success_count = 0
            for _, row in df.iterrows():
                if pd.notna(row.get("Name", "")):
                    from database import add_personnel

                    if add_personnel(
                        name=str(row.get("Name", "")),
                        phone=(
                            str(row.get("Phone", ""))
                            if pd.notna(row.get("Phone"))
                            else None
                        ),
                        supervisor=(
                            str(row.get("Supervisor", ""))
                            if pd.notna(row.get("Supervisor"))
                            else None
                        ),
                        supervisor_phone=(
                            str(row.get("SupervisorPhone", ""))
                            if pd.notna(row.get("SupervisorPhone"))
                            else None
                        ),
                        company=(
                            str(row.get("Company", ""))
                            if pd.notna(row.get("Company"))
                            else None
                        ),
                    ):
                        success_count += 1

            st.success(f"Successfully imported {success_count} personnel records")
            st.rerun()

        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")

    personnel_df = get_personnel()

    if personnel_df.empty:
        st.info(get_text("no_personnel", lang))
    else:
        # Search/filter
        search_term = st.text_input(get_text("search_personnel", lang))

        if search_term:
            mask = (
                personnel_df["name"].str.contains(search_term, case=False, na=False)
                | personnel_df["company"].str.contains(
                    search_term, case=False, na=False
                )
                | personnel_df["supervisor"].str.contains(
                    search_term, case=False, na=False
                )
            )
            filtered_df = personnel_df[mask]
        else:
            filtered_df = personnel_df

        # Display dataframe
        st.dataframe(safe_dataframe_for_display(filtered_df), use_container_width=True)

        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(get_text("total_personnel", lang), len(personnel_df))
        with col2:
            companies = personnel_df["company"].nunique()
            st.metric(get_text("companies", lang), companies)
        with col3:
            supervisors = personnel_df["supervisor"].nunique()
            st.metric(get_text("supervisors", lang), supervisors)

        # Export option
        if st.button(get_text("export_csv", lang)):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label=get_text("download_csv", lang),
                data=csv,
                file_name="jmp_personnel.csv",
                mime="text/csv",
            )


def render_groups_tab(lang):
    """Render groups management tab"""
    st.subheader(get_text("groups_tab", lang))

    groups_df = get_groups()
    personnel_df = get_personnel()

    if groups_df.empty:
        st.info(get_text("no_groups", lang))
    else:
        # Group selector
        selected_group_name = st.selectbox(
            get_text("select_group", lang), groups_df["group_name"].tolist()
        )

        if selected_group_name:
            group_data = groups_df[groups_df["group_name"] == selected_group_name].iloc[
                0
            ]
            members = [m.strip() for m in group_data["members"].split(",")]

            st.info(
                f"**{get_text('responsible_person', lang)}:** {group_data['responsible_person']}"
            )

            # Show current members
            st.write(f"**{get_text('current_members', lang)}:** ({len(members)})")

            # Create columns for member display
            cols = st.columns(3)
            for i, member in enumerate(members):
                with cols[i % 3]:
                    st.write(f"• {member}")

            # Edit group
            with st.expander(get_text("edit_group", lang)):
                # Multi-select for new members
                available_personnel = [
                    p for p in personnel_df["name"].tolist() if p not in members
                ]

                add_members = st.multiselect(
                    get_text("add_members", lang), available_personnel
                )

                remove_members = st.multiselect(
                    get_text("remove_members", lang), members
                )

                new_responsible = st.selectbox(
                    get_text("change_responsible", lang),
                    [group_data["responsible_person"]] + members,
                    index=0,
                )

                if st.button(get_text("update_group", lang), type="primary"):
                    # Update members list
                    updated_members = [
                        m for m in members if m not in remove_members
                    ] + add_members

                    if updated_members:
                        update_group(
                            group_data["id"],
                            members=",".join(updated_members),
                            responsible_person=new_responsible,
                        )
                        st.success(get_text("group_updated", lang))
                        st.rerun()
                    else:
                        st.error(get_text("group_empty", lang))


def render_statistics_tab(lang):
    """Render statistics tab"""
    st.subheader(get_text("statistics_tab", lang))

    # Get all necessary data
    all_departures = get_all_departures()
    active_departures = get_active_departures()
    personnel_df = get_personnel()

    # Overall statistics
    st.write(f"### {get_text('overall_statistics', lang)}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(get_text("total_departures", lang), len(all_departures))
    with col2:
        st.metric(get_text("currently_out", lang), len(active_departures))
    with col3:
        completed = len(all_departures[all_departures["actual_return"] != ""])
        st.metric(get_text("completed_trips", lang), completed)
    with col4:
        if not all_departures.empty:
            avg_extensions = all_departures["extensions_count"].mean()
            st.metric(get_text("avg_extensions", lang), f"{avg_extensions:.1f}")

    # Time-based statistics
    st.write(f"### {get_text('time_statistics', lang)}")

    if not all_departures.empty:
        # Calculate average trip duration for completed trips
        completed_trips = all_departures[all_departures["actual_return"] != ""].copy()

        if not completed_trips.empty:
            completed_trips["departed_at"] = pd.to_datetime(
                completed_trips["departed_at"]
            )
            completed_trips["actual_return"] = pd.to_datetime(
                completed_trips["actual_return"]
            )
            completed_trips["duration"] = (
                completed_trips["actual_return"] - completed_trips["departed_at"]
            ).dt.total_seconds() / 3600

            col1, col2, col3 = st.columns(3)
            with col1:
                avg_duration = completed_trips["duration"].mean()
                st.metric(get_text("avg_trip_duration", lang), f"{avg_duration:.1f}h")
            with col2:
                max_duration = completed_trips["duration"].max()
                st.metric(get_text("longest_trip", lang), f"{max_duration:.1f}h")
            with col3:
                overdue_count = len(
                    all_departures[all_departures["is_overdue"] == "True"]
                )
                st.metric(get_text("total_overdue_incidents", lang), overdue_count)

    # Destination statistics
    st.write(f"### {get_text('popular_destinations', lang)}")

    if not all_departures.empty:
        destination_counts = all_departures["destination"].value_counts().head(10)
        st.bar_chart(destination_counts)

    # Company statistics
    if not personnel_df.empty:
        st.write(f"### {get_text('company_statistics', lang)}")
        company_counts = personnel_df["company"].value_counts()

        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(company_counts)
        with col2:
            st.dataframe(company_counts.reset_index(), use_container_width=True)
