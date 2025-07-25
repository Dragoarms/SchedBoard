"""
Configuration module for JMP Tracker
Contains all configuration settings and constants
"""

import pytz
from datetime import datetime

# Timezone configuration
LOCAL_TIMEZONE = pytz.timezone('Africa/Lagos')  # UTC+1 West Africa Time

# Language configuration
LANGUAGES = {
    'en': {
        'app_title': 'JMP Tracker',
        'dashboard': '🏠 Dashboard',
        'departures': '🚶 Departures',
        'arrivals': '🏃 Arrivals',
        'management': '📊 Management',
        'refresh': '🔄 Refresh',
        'show_map': '🗺️ Show Map View',
        'hide_map': 'Hide Map',
        'active_departures': 'Active Departures',
        'all_in_camp': '✅ All personnel are in camp!',
        'overdue_alert': '⚠️ **ALERT: {count} OVERDUE PERSONNEL**',
        'currently_out': 'Currently Out',
        'overdue': 'Overdue',
        'total_active': 'Total Active',
        'with_gps': 'With GPS',
        'no_gps': 'No GPS',
        'log_departure': 'Log Departure',
        'mark_returned': '✅ Returned',
        'extend_time': 'Extend Time',
        'name': 'Name',
        'destination': 'Destination',
        'phone': 'Phone Number',
        'supervisor': 'Supervisor',
        'company': 'Company',
        'expected_duration': 'Expected Duration',
        'hours': 'Hours',
        'departure_time': 'Departure',
        'expected_return': 'Expected Return',
        'add_new_person': '➕ Add New Person',
        'enter_name': 'Enter Name',
        'capture_location': '📍 Capture departure location (optional)',
        'get_current_location': '📍 Get Current Location',
        'success_departure': '✅ {name} logged as departed to {destination}',
        'location_captured': '📍 Location captured',
        'error_name_dest': 'Please enter name and destination',
        'error_destination': 'Please enter destination',
        'error_select_name': 'Please select or enter a name',
        'current_status': '📊 Current Status',
        'group_departure': 'Group Departure',
        'select_group': 'Select Existing Group',
        'create_group': 'Create New Group',
        'group_name': 'Group Name',
        'members': 'Members',
        'responsible_person': 'Responsible Person',
        'one_per_line': '(one per line)',
        'everyone_in_camp': '✅ Everyone is in camp!',
        'individual_returns': 'Individual Returns',
        'group_returns': 'Group Returns',
        'overdue_by': 'Overdue by {hours}h {minutes}m',
        'time_remaining': '{hours}h {minutes}m remaining',
        'due_now': 'Due now',
        'departed_at': 'Departed: {time}',
        'expected_at': 'Expected: {time}',
        'no_active_groups': 'No active group departures',
        'members_out': '{count} members out',
        'some_overdue': '⚠️ Some members are overdue!',
        'mark_group_returned': '✅ Mark Entire Group as Returned',
        'group_returned_success': 'All members of \'{name}\' marked as returned',
        'select_person': 'Select Person',
        'current_expected_return': 'Current Expected Return',
        'hours_to_extend': 'Hours to Extend',
        'share_location': 'Optional: Share current location',
        'extended_success': '✅ Extended {name}\'s return time by {hours} hours',
        'location_recorded': '📍 Location recorded: {lat:.6f}, {lon:.6f}',
        'password': 'Password',
        'password_incorrect': '😕 Password incorrect',
        'active_deps_tab': '📍 Active Departures',
        'map_view_tab': '🗺️ Map View',
        'manifest_tab': '📋 Personnel Manifest',
        'groups_tab': '👥 Groups',
        'statistics_tab': '📈 Statistics',
        'personnel_status': 'Personnel Status',
        'on_time': 'On Time',
        'due_soon': 'Due Soon (<30min)',
        'roads_tracks': 'Roads/Tracks',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'success': 'Success',
        'loading': 'Loading...',
        'no_data': 'No data available',
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'add': 'Add',
        'search': 'Search',
        'filter': 'Filter',
        'export': 'Export',
        'import': 'Import',
        'settings': 'Settings',
        'language': 'Language',
        'help': 'Help',
        'about': 'About',
        'logout': 'Logout',
        'welcome': 'Welcome',
        'scan_departure': 'Scan to log departure:',
        'scan_arrival': 'Scan to check in:',
        'getting_location': 'Getting location...',
        'geolocation_not_supported': 'Geolocation is not supported by this browser',
        'location_permission_denied': 'Location permission denied',
        'location_unavailable': 'Location information unavailable',
        'location_timeout': 'Location request timed out',
        'manual_gps_entry': 'Manual GPS Entry',
        'manual_gps_info': 'If automatic geolocation does not work, enter coordinates manually',
        'use_these_coordinates': 'Use these coordinates',
        'how_to_share_location': 'How to share your location',
        'on_phone': 'On Phone',
        'open_maps_app': 'Open Google Maps or Apple Maps',
        'long_press_location': 'Long press on your location',
        'copy_coordinates': 'Copy the coordinates',
        'paste_below': 'Paste below',
        'on_computer': 'On Computer',
        'open_google_maps': 'Open Google Maps',
        'right_click_location': 'Right-click on your location',
        'click_coordinates': 'Click on the coordinates shown',
        'or_paste_coordinates': 'Or paste coordinates',
        'paste_from_maps': 'Paste from Google Maps',
        'invalid_coordinates': 'Invalid coordinates format',
        'departure_type': 'Departure Type',
        'individual': 'Individual',
        'group': 'Group',
        'start_typing': 'Start typing to filter names',
        'destination_for_group': 'Destination for entire group',
        'log_group_departure': 'Log Group Departure',
        'group_departure_success': '{name} logged as departed to {destination}',
        'group_option': 'Group Option',
        'select_members': 'Select Members',
        'select_multiple': 'Select multiple people',
        'add_new_members': 'Add New Members',
        'new_members': 'New Members',
        'group_created': 'Group \'{name}\' created with {count} members',
        'fill_all_fields': 'Please fill in all fields',
        'marked_returned': 'marked as returned',
        'active_groups': 'Active Group Departures',
        'select_person_extend': 'Select a person to extend their expected return time',
        'error_connecting_sheets': 'Error connecting to Google Sheets',
        'select_action': 'Select Action',
        'view_only': 'View Only',
        'select_to_return': 'Select personnel to mark as returned',
        'mark_selected_returned': 'Mark Selected as Returned',
        'extend_selected': 'Extend Selected',
        'total_out': 'Total Out',
        'avg_time_remaining': 'Avg Time Remaining',
        'monitor_manage': 'Monitor and manage all personnel',
        'show_overdue': 'Show Overdue',
        'show_on_time': 'Show On Time',
        'show_no_gps': 'Show No GPS',
        'no_active_personnel': 'No active personnel to display',
        'personnel_no_gps': 'Personnel without GPS',
        'no_personnel': 'No personnel in manifest',
        'search_personnel': 'Search Personnel',
        'total_personnel': 'Total Personnel',
        'companies': 'Companies', 
        'supervisors': 'Supervisors',
        'export_csv': 'Export to CSV',
        'download_csv': 'Download CSV',
        'no_groups': 'No groups created yet',
        'current_members': 'Current Members',
        'edit_group': 'Edit Group',
        'add_members': 'Add Members to Group',
        'remove_members': 'Remove Members from Group',
        'change_responsible': 'Change Responsible Person',
        'update_group': 'Update Group',
        'group_updated': 'Group updated successfully',
        'group_empty': 'Group cannot be empty',
        'overall_statistics': 'Overall Statistics',
        'total_departures': 'Total Departures',
        'completed_trips': 'Completed Trips',
        'avg_extensions': 'Avg Extensions',
        'time_statistics': 'Time Statistics',
        'avg_trip_duration': 'Avg Trip Duration',
        'longest_trip': 'Longest Trip',
        'total_overdue_incidents': 'Total Overdue Incidents',
        'popular_destinations': 'Popular Destinations',
        'company_statistics': 'Company Statistics',
        'last_update': 'Last Update',
        'how_to_share_location': 'How to share location',
        'on_phone': 'On Phone',
        'open_maps_app': 'Open Maps app',
        'long_press_location': 'Long press your location',
        'copy_coordinates': 'Copy coordinates',
        'paste_below': 'Paste below',
        'on_computer': 'On Computer',
        'open_google_maps': 'Open Google Maps',
        'right_click_location': 'Right-click your location',
        'click_coordinates': 'Click the coordinates',
        'or_paste_coordinates': 'Or paste coordinates',
        'paste_from_maps': 'Paste from Maps',
        'invalid_coordinates': 'Invalid coordinate format'
    },
    'fr': {
        'app_title': 'Suivi JMP',
        'dashboard': '🏠 Tableau de bord',
        'departures': '🚶 Départs',
        'arrivals': '🏃 Arrivées',
        'management': '📊 Gestion',
        'refresh': '🔄 Actualiser',
        'show_map': '🗺️ Afficher la carte',
        'hide_map': 'Masquer la carte',
        'active_departures': 'Départs actifs',
        'all_in_camp': '✅ Tout le personnel est au camp!',
        'overdue_alert': '⚠️ **ALERTE: {count} PERSONNEL EN RETARD**',
        'currently_out': 'Actuellement sorti',
        'overdue': 'En retard',
        'total_active': 'Total actif',
        'with_gps': 'Avec GPS',
        'no_gps': 'Sans GPS',
        'log_departure': 'Enregistrer le départ',
        'mark_returned': '✅ Retourné',
        'extend_time': 'Prolonger le temps',
        'name': 'Nom',
        'destination': 'Destination',
        'phone': 'Numéro de téléphone',
        'supervisor': 'Superviseur',
        'company': 'Entreprise',
        'expected_duration': 'Durée prévue',
        'hours': 'Heures',
        'departure_time': 'Départ',
        'expected_return': 'Retour prévu',
        'add_new_person': '➕ Ajouter une nouvelle personne',
        'enter_name': 'Entrer le nom',
        'capture_location': '📍 Capturer la position de départ (optionnel)',
        'get_current_location': '📍 Obtenir la position actuelle',
        'success_departure': '✅ {name} enregistré comme parti vers {destination}',
        'location_captured': '📍 Position capturée',
        'error_name_dest': 'Veuillez entrer le nom et la destination',
        'error_destination': 'Veuillez entrer la destination',
        'error_select_name': 'Veuillez sélectionner ou entrer un nom',
        'current_status': '📊 Statut actuel',
        'group_departure': 'Départ de groupe',
        'select_group': 'Sélectionner un groupe existant',
        'create_group': 'Créer un nouveau groupe',
        'group_name': 'Nom du groupe',
        'members': 'Membres',
        'responsible_person': 'Personne responsable',
        'one_per_line': '(un par ligne)',
        'everyone_in_camp': '✅ Tout le monde est au camp!',
        'individual_returns': 'Retours individuels',
        'group_returns': 'Retours de groupe',
        'overdue_by': 'En retard de {hours}h {minutes}m',
        'time_remaining': '{hours}h {minutes}m restant',
        'due_now': 'Dû maintenant',
        'departed_at': 'Parti: {time}',
        'expected_at': 'Prévu: {time}',
        'no_active_groups': 'Aucun départ de groupe actif',
        'members_out': '{count} membres sortis',
        'some_overdue': '⚠️ Certains membres sont en retard!',
        'mark_group_returned': '✅ Marquer tout le groupe comme retourné',
        'group_returned_success': 'Tous les membres de \'{name}\' marqués comme retournés',
        'select_person': 'Sélectionner une personne',
        'current_expected_return': 'Retour prévu actuel',
        'hours_to_extend': 'Heures à prolonger',
        'share_location': 'Optionnel: Partager la position actuelle',
        'extended_success': '✅ Temps de retour de {name} prolongé de {hours} heures',
        'location_recorded': '📍 Position enregistrée: {lat:.6f}, {lon:.6f}',
        'password': 'Mot de passe',
        'password_incorrect': '😕 Mot de passe incorrect',
        'active_deps_tab': '📍 Départs actifs',
        'map_view_tab': '🗺️ Vue carte',
        'manifest_tab': '📋 Registre du personnel',
        'groups_tab': '👥 Groupes',
        'statistics_tab': '📈 Statistiques',
        'personnel_status': 'Statut du personnel',
        'on_time': 'À temps',
        'due_soon': 'Bientôt dû (<30min)',
        'roads_tracks': 'Routes/Pistes',
        'error': 'Erreur',
        'warning': 'Avertissement',
        'info': 'Information',
        'success': 'Succès',
        'loading': 'Chargement...',
        'no_data': 'Aucune donnée disponible',
        'confirm': 'Confirmer',
        'cancel': 'Annuler',
        'save': 'Enregistrer',
        'delete': 'Supprimer',
        'edit': 'Modifier',
        'add': 'Ajouter',
        'search': 'Rechercher',
        'filter': 'Filtrer',
        'export': 'Exporter',
        'import': 'Importer',
        'settings': 'Paramètres',
        'language': 'Langue',
        'help': 'Aide',
        'about': 'À propos',
        'logout': 'Déconnexion',
        'welcome': 'Bienvenue',
        'scan_departure': 'Scanner pour enregistrer le départ:',
        'scan_arrival': 'Scanner pour enregistrer l\'arrivée:',
        'getting_location': 'Obtention de la position...',
        'geolocation_not_supported': 'La géolocalisation n\'est pas supportée par ce navigateur',
        'location_permission_denied': 'Permission de localisation refusée',
        'location_unavailable': 'Information de localisation non disponible',
        'location_timeout': 'Délai de demande de localisation dépassé',
        'manual_gps_entry': 'Entrée GPS manuelle',
        'manual_gps_info': 'Si la géolocalisation automatique ne fonctionne pas, entrez les coordonnées manuellement',
        'use_these_coordinates': 'Utiliser ces coordonnées',
        'how_to_share_location': 'Comment partager votre position',
        'on_phone': 'Sur téléphone',
        'open_maps_app': 'Ouvrez Google Maps ou Apple Maps',
        'long_press_location': 'Appuyez longuement sur votre position',
        'copy_coordinates': 'Copiez les coordonnées',
        'paste_below': 'Collez ci-dessous',
        'on_computer': 'Sur ordinateur',
        'open_google_maps': 'Ouvrez Google Maps',
        'right_click_location': 'Clic droit sur votre position',
        'click_coordinates': 'Cliquez sur les coordonnées affichées',
        'or_paste_coordinates': 'Ou collez les coordonnées',
        'paste_from_maps': 'Collez depuis Google Maps',
        'invalid_coordinates': 'Format de coordonnées invalide',
        'departure_type': 'Type de départ',
        'individual': 'Individuel',
        'group': 'Groupe',
        'start_typing': 'Commencez à taper pour filtrer',
        'destination_for_group': 'Destination pour tout le groupe',
        'log_group_departure': 'Enregistrer le départ du groupe',
        'group_departure_success': '{name} enregistré comme parti vers {destination}',
        'group_option': 'Option de groupe',
        'select_members': 'Sélectionner les membres',
        'select_multiple': 'Sélectionnez plusieurs personnes',
        'add_new_members': 'Ajouter de nouveaux membres',
        'new_members': 'Nouveaux membres',
        'group_created': 'Groupe \'{name}\' créé avec {count} membres',
        'fill_all_fields': 'Veuillez remplir tous les champs',
        'marked_returned': 'marqué comme retourné',
        'active_groups': 'Départs de groupe actifs',
        'select_person_extend': 'Sélectionnez une personne pour prolonger son heure de retour prévue',
        'error_connecting_sheets': 'Erreur de connexion à Google Sheets',
        'select_action': 'Sélectionner une action',
        'view_only': 'Vue seule',
        'select_to_return': 'Sélectionner le personnel à marquer comme retourné',
        'mark_selected_returned': 'Marquer la sélection comme retournée',
        'extend_selected': 'Prolonger la sélection',
        'total_out': 'Total sorti',
        'avg_time_remaining': 'Temps restant moyen',
        'monitor_manage': 'Surveiller et gérer tout le personnel',
        'show_overdue': 'Afficher en retard',
        'show_on_time': 'Afficher à temps',
        'show_no_gps': 'Afficher sans GPS',
        'no_active_personnel': 'Aucun personnel actif à afficher',
        'personnel_no_gps': 'Personnel sans GPS',
        'no_personnel': 'Aucun personnel dans le registre',
        'search_personnel': 'Rechercher le personnel',
        'total_personnel': 'Personnel total',
        'companies': 'Entreprises',
        'supervisors': 'Superviseurs',
        'export_csv': 'Exporter en CSV',
        'download_csv': 'Télécharger CSV',
        'no_groups': 'Aucun groupe créé',
        'current_members': 'Membres actuels',
        'edit_group': 'Modifier le groupe',
        'add_members': 'Ajouter des membres au groupe',
        'remove_members': 'Retirer des membres du groupe',
        'change_responsible': 'Changer la personne responsable',
        'update_group': 'Mettre à jour le groupe',
        'group_updated': 'Groupe mis à jour avec succès',
        'group_empty': 'Le groupe ne peut pas être vide',
        'overall_statistics': 'Statistiques générales',
        'total_departures': 'Total des départs',
        'completed_trips': 'Voyages terminés',
        'avg_extensions': 'Extensions moyennes',
        'time_statistics': 'Statistiques temporelles',
        'avg_trip_duration': 'Durée moyenne du voyage',
        'longest_trip': 'Voyage le plus long',
        'total_overdue_incidents': 'Total des incidents en retard',
        'popular_destinations': 'Destinations populaires',
        'company_statistics': 'Statistiques par entreprise',
        'last_update': 'Dernière mise à jour',
        'how_to_share_location': 'Comment partager la position',
        'on_phone': 'Sur téléphone',
        'open_maps_app': 'Ouvrir Maps',
        'long_press_location': 'Appui long sur position',
        'copy_coordinates': 'Copier coordonnées',
        'paste_below': 'Coller ci-dessous',
        'on_computer': 'Sur ordinateur',
        'open_google_maps': 'Ouvrir Google Maps',
        'right_click_location': 'Clic droit sur position',
        'click_coordinates': 'Cliquer les coordonnées',
        'or_paste_coordinates': 'Ou coller coordonnées',
        'paste_from_maps': 'Coller depuis Maps',
        'invalid_coordinates': 'Format de coordonnées invalide'
    }
}

# UI Configuration
PAGE_CONFIG = {
    "page_title": "JMP Tracker",
    "page_icon": "🏕️",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# GitHub repository URLs
GITHUB_BASE_URL = "https://raw.githubusercontent.com/Dragoarms/SchedBoard/main"
LOGO_URL = f"{GITHUB_BASE_URL}/Icons/logo.ico"
KMZ_URL = f"{GITHUB_BASE_URL}/MapFeatures/tracks.kmz"

# QR Code URLs
QR_BASE_URL = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="
APP_BASE_URL = "https://jmpboard.streamlit.app"

# Map configuration
DEFAULT_MAP_CENTER = [-6.7924, 39.2083]  # Default to Dar es Salaam
DEFAULT_MAP_ZOOM = 11

# Time configuration
DEFAULT_DEPARTURE_HOURS = 3
MAX_EXTENSION_HOURS = 24
ALERT_INTERVAL_MINUTES = 10

# Data refresh intervals (seconds)
PERSONNEL_CACHE_TTL = 60
DEPARTURES_CACHE_TTL = 30
GROUPS_CACHE_TTL = 60

# Google Sheets configuration
SHEET_NAMES = {
    'personnel': 'Personnel',
    'departures': 'Departures',
    'extensions': 'Extensions',
    'groups': 'Groups'
}

SHEET_HEADERS = {
    'personnel': ["name", "phone", "supervisor", "supervisor_phone", "company", "created_at", "updated_at"],
    'departures': ["id", "person_name", "destination", "departed_at", "expected_return", "actual_return", 
                  "phone", "supervisor", "company", "extensions_count", "is_overdue", "group_id", "last_location"],
    'extensions': ["id", "departure_id", "hours_extended", "extended_at", "gps_location"],
    'groups': ["id", "group_name", "members", "responsible_person", "created_at"]
}

def get_text(key, lang='en', **kwargs):
    """Get translated text with optional formatting"""
    text = LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def get_current_time():
    """Get current time in local timezone"""
    return datetime.now(LOCAL_TIMEZONE)

def format_time(dt, format_str='%I:%M %p'):
    """Format datetime to string"""
    if dt.tzinfo is None:
        dt = LOCAL_TIMEZONE.localize(dt)
    return dt.strftime(format_str)
