"""
Departures page for JMP Tracker
Log personnel departures
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from config import (
    get_text,
    get_current_time,
    LOCAL_TIMEZONE,
    DEFAULT_DEPARTURE_HOURS,
    LOGO_URL,
)
from database import (
    get_personnel,
    get_groups,
    add_personnel,
    add_departure,
    add_group,
    get_active_departures,
)
from location import simple_gps_button
import time


def render_departures():
    """Render the departures page"""
    lang = st.session_state.get("language", "en")

    # Header
    col1, col2 = st.columns([0.5, 11.5])
    with col1:
        st.image(LOGO_URL, width=50)
    with col2:
        st.markdown(
            f'<p class="main-header">{get_text("app_title", lang)} - {get_text("departures", lang)}</p>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<p class="sub-header">{get_text("log_departure", lang)}</p>',
        unsafe_allow_html=True,
    )

    # Get data
    personnel_df = get_personnel()
    groups_df = get_groups()

    # Departure type selection
    dep_type = st.radio(
        get_text("departure_type", lang),
        [get_text("individual", lang), get_text("group", lang)],
        horizontal=True,
    )

    if dep_type == get_text("individual", lang):
        render_individual_departure(personnel_df, lang)
    else:
        render_group_departure(personnel_df, groups_df, lang)


def render_individual_departure(personnel_df, lang):
    """Render individual departure form"""
    col1, col2 = st.columns([3, 1])

    with col1:
        # Searchable dropdown for names
        all_names = (
            [get_text("add_new_person", lang)] + personnel_df["name"].tolist()
            if not personnel_df.empty
            else [get_text("add_new_person", lang)]
        )

        selected_name = st.selectbox(
            get_text("name", lang),
            options=all_names,
            index=0,
            help=(
                get_text("start_typing", lang)
                if lang == "en"
                else "Commencez à taper pour filtrer"
            ),
        )

        if selected_name == get_text("add_new_person", lang):
            new_name = st.text_input(get_text("enter_name", lang))
            person_data = None
        else:
            new_name = None
            person_data = (
                personnel_df[personnel_df["name"] == selected_name].iloc[0]
                if not personnel_df.empty
                else None
            )

        # Always show these fields
        destination = st.text_input(get_text("destination", lang), key="destination")

        # Duration selection (simpler than date/time pickers for mobile)
        st.subheader(get_text("expected_duration", lang))
        duration_hours = st.slider(
            get_text("hours", lang),
            min_value=1,
            max_value=24,
            value=DEFAULT_DEPARTURE_HOURS,
            key="duration_slider",
        )

        # Calculate expected arrival
        now_local = get_current_time()
        expected_arrival = now_local + timedelta(hours=duration_hours)

        st.info(
            f"📅 {get_text('departure_time', lang)}: {now_local.strftime('%I:%M %p')} → {get_text('expected_return', lang)}: {expected_arrival.strftime('%I:%M %p')}"
        )

        # GPS location capture (automatic)
        from location import get_automatic_gps

        get_automatic_gps()

        # Store GPS coordinates in session state
        gps_data = None
        if "auto_gps_lat" in st.session_state and "auto_gps_lon" in st.session_state:
            gps_data = {
                "lat": st.session_state.auto_gps_lat,
                "lon": st.session_state.auto_gps_lon,
            }
            st.success(
                f"📍 Location captured: {gps_data['lat']:.6f}, {gps_data['lon']:.6f}"
            )

        # Only show additional fields if they're missing from records
        if selected_name == get_text("add_new_person", lang) or (
            person_data is not None and not person_data.get("phone")
        ):
            phone = st.text_input(get_text("phone", lang))
        else:
            phone = person_data.get("phone") if person_data is not None else None

        if selected_name == get_text("add_new_person", lang) or (
            person_data is not None and not person_data.get("supervisor")
        ):
            supervisor = st.text_input(get_text("supervisor", lang))
        else:
            supervisor = (
                person_data.get("supervisor") if person_data is not None else None
            )

        if selected_name == get_text("add_new_person", lang) or (
            person_data is not None and not person_data.get("company")
        ):
            company = st.text_input(get_text("company", lang))
        else:
            company = person_data.get("company") if person_data is not None else None

        # Submit button
        if st.button(
            get_text("log_departure", lang), type="primary", use_container_width=True
        ):
            # Prepare GPS data
            location_data = None
            if gps_data:
                location_data = {
                    "lat": gps_data["lat"],
                    "lon": gps_data["lon"],
                    "timestamp": get_current_time().isoformat(),
                }

            if new_name:  # New person
                if new_name.strip() and destination.strip():
                    if add_personnel(new_name, phone, supervisor, None, company):
                        if add_departure(
                            new_name,
                            destination,
                            expected_arrival,
                            phone,
                            supervisor,
                            company,
                            initial_location=location_data,
                        ):
                            st.success(
                                get_text(
                                    "success_departure",
                                    lang,
                                    name=new_name,
                                    destination=destination,
                                )
                            )
                            if location_data:
                                st.info(get_text("location_captured", lang))
                            time.sleep(1)
                            st.rerun()
                else:
                    st.error(get_text("error_name_dest", lang))
            elif selected_name != get_text("add_new_person", lang):  # Existing person
                if destination.strip():
                    if add_departure(
                        selected_name,
                        destination,
                        expected_arrival,
                        phone or person_data.get("phone"),
                        supervisor or person_data.get("supervisor"),
                        company or person_data.get("company"),
                        initial_location=location_data,
                    ):
                        st.success(
                            get_text(
                                "success_departure",
                                lang,
                                name=selected_name,
                                destination=destination,
                            )
                        )
                        if location_data:
                            st.info(get_text("location_captured", lang))
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error(get_text("error_destination", lang))
            else:
                st.error(get_text("error_select_name", lang))

    with col2:
        # Quick stats
        st.markdown(f"### {get_text('current_status', lang)}")
        active_departures = get_active_departures()

        total_out = len(active_departures)
        overdue_count = (
            len(active_departures[active_departures["is_overdue"] == True])
            if not active_departures.empty
            else 0
        )

        st.metric(get_text("currently_out", lang), total_out)
        st.metric(get_text("overdue", lang), overdue_count, delta_color="inverse")

        if overdue_count > 0:
            st.error(f"⚠️ {overdue_count} {get_text('overdue', lang).lower()}!")


def render_group_departure(personnel_df, groups_df, lang):
    """Render group departure form"""
    st.subheader(get_text("group_departure", lang))

    # Option to select existing group or create new
    group_option = st.radio(
        get_text("group_option", lang),
        [get_text("select_group", lang), get_text("create_group", lang)],
        horizontal=True,
    )

    if group_option == get_text("select_group", lang) and not groups_df.empty:
        selected_group = st.selectbox(
            get_text("select_group", lang), groups_df["group_name"].tolist()
        )
        group_data = groups_df[groups_df["group_name"] == selected_group].iloc[0]
        members = group_data["members"].split(",")
        responsible_person = group_data["responsible_person"]

        st.info(f"**{get_text('members', lang)}:** {', '.join(members)}")
        st.info(f"**{get_text('responsible_person', lang)}:** {responsible_person}")

        destination = st.text_input(get_text("destination_for_group", lang))

        # Duration selection
        duration_hours = st.slider(
            get_text("expected_duration", lang),
            min_value=1,
            max_value=24,
            value=DEFAULT_DEPARTURE_HOURS,
            key="group_duration",
        )

        now_local = get_current_time()
        expected_arrival = now_local + timedelta(hours=duration_hours)

        st.info(
            f"📅 {get_text('expected_return', lang)}: {expected_arrival.strftime('%I:%M %p')}"
        )

        if st.button(get_text("log_group_departure", lang), type="primary"):
            if destination.strip():
                group_id = group_data["id"]
                # Log departure for each member
                success = True
                for member in members:
                    member = member.strip()
                    if not add_departure(
                        member, destination, expected_arrival, group_id=group_id
                    ):
                        success = False

                if success:
                    st.success(
                        get_text(
                            "group_departure_success",
                            lang,
                            name=selected_group,
                            destination=destination,
                        )
                    )
                    time.sleep(1)
                    st.rerun()
            else:
                st.error(get_text("error_destination", lang))

    else:  # Create new group
        group_name = st.text_input(get_text("group_name", lang))

        # Multi-select for members from personnel manifest
        if not personnel_df.empty:
            selected_members = st.multiselect(
                get_text("select_members", lang),
                options=personnel_df["name"].tolist(),
                help=(
                    get_text("select_multiple", lang)
                    if lang == "en"
                    else "Sélectionnez plusieurs personnes"
                ),
            )

            # Option to add new members not in manifest
            with st.expander(get_text("add_new_members", lang)):
                new_members_input = st.text_area(
                    get_text("new_members", lang)
                    + " "
                    + get_text("one_per_line", lang),
                    height=100,
                )
        else:
            selected_members = []
            new_members_input = st.text_area(
                get_text("members", lang) + " " + get_text("one_per_line", lang),
                height=150,
            )

        # Responsible person selection
        all_members = selected_members.copy()
        if "new_members_input" in locals() and new_members_input:
            new_members = [
                m.strip() for m in new_members_input.split("\n") if m.strip()
            ]
            all_members.extend(new_members)

        if all_members:
            responsible_person = st.selectbox(
                get_text("responsible_person", lang), options=all_members
            )
        else:
            responsible_person = st.text_input(get_text("responsible_person", lang))

        if st.button(get_text("create_group", lang), type="secondary"):
            if group_name and all_members and responsible_person:
                members_str = ",".join(all_members)

                # Add all members to personnel if they don't exist
                for member in all_members:
                    if member not in personnel_df["name"].values:
                        add_personnel(member)

                group_id = add_group(group_name, members_str, responsible_person)
                if group_id:
                    st.success(
                        get_text(
                            "group_created",
                            lang,
                            name=group_name,
                            count=len(all_members),
                        )
                    )
                    time.sleep(1)
                    st.rerun()
            else:
                st.error(get_text("fill_all_fields", lang))
