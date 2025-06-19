import requests
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt
import openrouteservice
from openrouteservice import convert
import folium
from streamlit_folium import st_folium
import webbrowser
import json
from auth import auth_ui 
from admin import admin_login_ui
import hashlib
from fuzzy_matcher import FuzzyStationResolver
  
INSTAMOJO_API_KEY = "38759069bce2f803d5fabfb4e387faa4E"
INSTAMOJO_AUTH_TOKEN = "5a952a567ec210d30ade40dda5070b6c"
INSTAMOJO_ENDPOINT = "https://imjo.in/m2zZs4"
USER_FILE = "users.csv"
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def load_users():
    if os.path.exists(USER_FILE):
        if os.path.getsize(USER_FILE) > 0:
            df = pd.read_csv(USER_FILE)
            if "username" in df.columns and "password" in df.columns:
                return df.set_index("username").T.to_dict()
            else:
                os.remove(USER_FILE)
                return {}
        else:
            return {}
    return {}

def save_user(username, password):
    df = pd.DataFrame([[username, hash_password(password)]], columns=["username", "password"])
    if os.path.exists(USER_FILE):
        df.to_csv(USER_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(USER_FILE, index=False)

ADMINS = {
    "admin": {"password": hash_password("admin123"), "role": "Admin"}
}

# ========== Authentication Logic ==========
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

users = load_users()

if not st.session_state.logged_in:
    st.title("🚉 Railway Management Login")
    login_mode = st.radio("Login as:", ["User", "Admin"], horizontal=True)

    if login_mode == "User":
        st.subheader("👤 User Login / Sign Up")
        tab = st.radio("Select Option", ["Sign In", "Sign Up"])

        if tab == "Sign In":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if username in users and verify_password(users[username]['password'], password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "User"
                    st.success(f"Welcome {username}!")
                    st.rerun()
                else:
                    st.error("Invalid user credentials.")

        elif tab == "Sign Up":
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            if st.button("Register"):
                if new_user in users or new_user in ADMINS:
                    st.warning("Username already taken.")
                elif not new_user or not new_pass:
                    st.warning("Please fill all fields.")
                else:
                    save_user(new_user, new_pass)
                    st.success("Registration successful! Please sign in.")

    elif login_mode == "Admin":
        st.subheader("🛠️ Admin Login")
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")

        if st.button("Login as Admin"):
            if username in ADMINS and verify_password(ADMINS[username]['password'], password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = ADMINS[username]['role']
                st.success(f"Welcome Admin {username}!")
                st.rerun()
            else:
                st.error("Invalid admin credentials.")

    st.stop()

# ========== Your Existing Railway Code Begins ==========
# Now we assume the user is logged in...

# MENU OPTIONS BASED ON ROLE
if st.session_state.role == "Admin":
    menu = st.sidebar.selectbox("Choose Mode", ["Admin", "Real Train Route Google Maps", "All India CSV Graph", "Logout"])
elif st.session_state.role == "User":
    menu = st.sidebar.selectbox("Choose Mode", ["User", "Real Train Route Google Maps", "All India CSV Graph", "Logout"])

if menu == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()


class Train:
    def __init__(self, train_no, name, source, destination, first_class_seats, second_class_seats, first_class_fare, second_class_fare):
        self.train_no = train_no
        self.name = name
        self.source = source
        self.destination = destination
        self.first_class_seats = first_class_seats
        self.second_class_seats = second_class_seats
        self.first_class_fare = first_class_fare
        self.second_class_fare = second_class_fare

    def display(self):
        return f"Train No: {self.train_no}, Name: {self.name}, Route: {self.source} to {self.destination}, " \
               f"First Class Seats: {self.first_class_seats}, Second Class Seats: {self.second_class_seats}"

    def is_available(self, class_type, seats):
        if class_type.lower() == 'first':
            return self.first_class_seats >= seats
        elif class_type.lower() == 'second':
            return self.second_class_seats >= seats
        return False

class Graph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.add_initial_routes()

    def add_initial_routes(self):
        stations = ["CityA", "CityB", "CityC", "CityD"]
        for station in stations:
            self.graph.add_node(station)

        routes = [
            ("CityA", "CityB", 100),
            ("CityB", "CityC", 150),
            ("CityC", "CityD", 200),
            ("CityA", "CityD", 300)
        ]
        for source, dest, weight in routes:
            self.graph.add_edge(source, dest, weight=weight)

    def add_node(self, city):
        if city not in self.graph.nodes():
            self.graph.add_node(city)
            st.success(f"Added new city: {city} to the graph.")
            return True
        return False

    def add_edge(self, source, destination, weight):
        if source in self.graph.nodes() and destination in self.graph.nodes():
            self.graph.add_edge(source, destination, weight=weight)
            st.success(f"Added route from {source} to {destination} with distance {weight}.")
            return True
        return False

    def dijkstra(self, start, end):
        if start not in self.graph.nodes() or end not in self.graph.nodes():
            return None, float('inf'), "One or both cities are not in the graph!"

        try:
            shortest_path = nx.shortest_path(self.graph, source=start, target=end, weight='weight', method='dijkstra')
            path_length = nx.shortest_path_length(self.graph, source=start, target=end, weight='weight')
            return shortest_path, path_length, None
        except nx.NetworkXNoPath:
            return None, float('inf'), "No path exists between the selected cities!"

    def visualize_with_animation(self, path=None):
        fig, ax = plt.subplots(figsize=(10, 6))
        pos = nx.spring_layout(self.graph)
        
        # Draw the full graph
        ax.clear()
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', node_size=500, edge_color='gray', ax=ax)
        edge_labels = nx.get_edge_attributes(self.graph, 'weight')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, ax=ax)

        # If a path is provided, highlight it
        if path and len(path) > 1:
            nx.draw_networkx_nodes(self.graph, pos, nodelist=path, node_color='orange', node_size=600, ax=ax)
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(self.graph, pos, edgelist=path_edges, edge_color='red', width=3, ax=ax)

        st.pyplot(fig)

# Booking Class
class Booking:
    def __init__(self):
        self.bookings = pd.DataFrame(columns=['booking_id', 'train_no', 'passenger_name', 'seats', 'class_type', 'date', 'payment_status', 'payment_url'])
        self.load_bookings()

    def confirm_booking(self, train, passenger_name, seats, class_type, payment_url):
        booking_id = len(self.bookings) + 1
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_booking = pd.DataFrame({
            'booking_id': [booking_id],
            'train_no': [train.train_no],
            'passenger_name': [passenger_name],
            'seats': [seats],
            'class_type': [class_type],
            'date': [date],
            'payment_status': ["Pending"],
            'payment_url': [payment_url]
        })
        self.bookings = pd.concat([self.bookings, new_booking], ignore_index=True)
        self.save_bookings()
        return f"Booking Created! ID: {booking_id}"

    def save_bookings(self):
        self.bookings.to_csv('bookings.csv', index=False)

    def load_bookings(self):
        if os.path.exists('bookings.csv'):
            self.bookings = pd.read_csv('bookings.csv')

def sort_trains_by_number(trains_list):
    n = len(trains_list)
    for i in range(n):
        for j in range(0, n-i-1):
            if trains_list[j].train_no > trains_list[j+1].train_no:
                trains_list[j], trains_list[j+1] = trains_list[j+1], trains_list[j]
    return trains_list

# Initialize session
if 'trains' not in st.session_state:
    st.session_state.trains = [
        Train(123, "Express", "CityA", "CityB", 100, 200, 50.0, 30.0),
        Train(456, "SuperFast", "CityC", "CityD", 50, 150, 70.0, 40.0)
    ]
if 'booking_system' not in st.session_state:
    st.session_state.booking_system = Booking()

trains = st.session_state.trains
booking_system = st.session_state.booking_system

# UI
st.title("Railway Management System with Instamojo Button Link")
st.title("🚉 Railway Management Login")
  # 👈 This is what calls the UI from admin.py

if menu == "User":
    st.header("Book Your Ticket")
    train_no = st.number_input("Train Number", min_value=1)
    seats = st.number_input("Seats", min_value=1)
    class_type = st.selectbox("Class Type", ["First", "Second"])
    booking_date = st.text_input("Date of Booking (DD/MM/YYYY)", placeholder="e.g. 16/04/2025")

    passenger_details = []

    if seats > 0:
        st.subheader("Enter Passenger Details")
        for i in range(seats):
            st.markdown(f"*Passenger {i+1}*")
            passenger_name = st.text_input(f"Name", key=f"name_{i}")
            age = st.number_input(f"Age", min_value=6, key=f"age_{i}")
            gender = st.selectbox(f"Gender", ["Male", "Female", "Other"], key=f"gender_{i}")
            passenger_details.append({"name": passenger_name, "age": age, "gender": gender})

    if st.button("Generate Booking"):
        train = next((t for t in trains if t.train_no == train_no), None)
        if not train:
            st.error("Train not found.")
        elif not train.is_available(class_type, seats):
            st.warning("Not enough seats available.")
        else:
            # Use your actual Instamojo payment link
            instamojo_link = "https://www.instamojo.com/@gdg_geu_divyanshkharkwal_07122/l910247b180414dc99595beba4ccd7257/"
            webbrowser.open_new_tab(instamojo_link)
            result = booking_system.confirm_booking(train, passenger_name, seats, class_type, instamojo_link)
            st.success(result)
            st.markdown(f"[Click here to complete payment]({instamojo_link})")

    
elif menu == "Admin":
    st.header("Admin Dashboard")

    with st.form("add_train"):
        st.subheader("Add New Train")
        train_no = st.number_input("Train Number", min_value=1, key="admin_train_no")
        name = st.text_input("Train Name", key="admin_name")
        source = st.text_input("Source", key="admin_source")
        destination = st.text_input("Destination", key="admin_destination")
        first_class_seats = st.number_input("First Class Seats", min_value=0, key="admin_fc_seats")
        second_class_seats = st.number_input("Second Class Seats", min_value=0, key="admin_sc_seats")
        first_class_fare = st.number_input("First Class Fare", min_value=0.0, key="admin_fc_fare")
        second_class_fare = st.number_input("Second Class Fare", min_value=0.0, key="admin_sc_fare")

        if st.form_submit_button("Add Train"):
            new_train = Train(train_no, name, source, destination, first_class_seats, second_class_seats, first_class_fare, second_class_fare)
            trains.append(new_train)
            st.session_state.trains = trains
            st.success("Train added successfully!")

    if st.button("View All Trains"):
        sorted_trains = sort_trains_by_number(trains.copy())
        for train in sorted_trains:
            st.write(train.display())
            st.write("---")

    if st.button("Generate Report"):
        st.subheader("Booking Report")
        st.write(booking_system.bookings.groupby('class_type').size().reset_index(name='count'))
        st.bar_chart(booking_system.bookings.groupby('class_type').size())
    st.subheader("All Bookings")
    st.dataframe(booking_system.bookings)        
elif menu == "Real Train Route Google Maps":
    st.header("Real Train Route Finder (OpenRouteService)")
    ORS_API_KEY = "5b3ce3597851110001cf6248c94dccb969ed43fbafb3829e5da4f2e4"  # Replace with your actual OpenRouteService API key

    # Only initialize session state variables if they do not exist
    if 'ors_map' not in st.session_state:
        st.session_state.ors_map = None
    if 'ors_src' not in st.session_state:
        st.session_state.ors_src = "Delhi"
    if 'ors_dest' not in st.session_state:
        st.session_state.ors_dest = "Mumbai"
    if 'ors_last_search' not in st.session_state:
        st.session_state.ors_last_search = (None, None)

    # Place text inputs and button at the top
    source_city = st.text_input("Enter Source City", st.session_state.ors_src)
    destination_city = st.text_input("Enter Destination City", st.session_state.ors_dest)
    st.button("Find Route", key="find_route_btn", on_click=lambda: st.session_state.update({'find_route_pressed': True}))
    show_map = st.checkbox("Show Map", value=True)

    def geocode(city, api_key):
        url = f"https://api.openrouteservice.org/geocode/search?api_key={api_key}&text={city}"
        resp = requests.get(url)
        data = resp.json()
        if data['features']:
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]  # lat, lon
        return None

    if st.session_state.get('find_route_pressed', False) and source_city and destination_city:
        src_coords = geocode(source_city, ORS_API_KEY)
        dest_coords = geocode(destination_city, ORS_API_KEY)
        if src_coords and dest_coords:
            client = openrouteservice.Client(key=ORS_API_KEY)
            try:
                route = client.directions(
                    coordinates=[(src_coords[1], src_coords[0]), (dest_coords[1], dest_coords[0])],
                    profile='driving-car',
                    format='geojson'
                )
                # Check if route geometry exists and is not empty
                coords = route['features'][0]['geometry']['coordinates']
                if not coords or len(coords) < 2:
                    st.session_state.ors_map_html = None
                    st.warning("No train route is available between the selected cities.")
                else:
                    m = folium.Map(location=[(src_coords[0]+dest_coords[0])/2, (src_coords[1]+dest_coords[1])/2], zoom_start=6)
                    folium.Marker(src_coords, tooltip=source_city, icon=folium.Icon(color='green')).add_to(m)
                    folium.Marker(dest_coords, tooltip=destination_city, icon=folium.Icon(color='red')).add_to(m)
                    route_latlon = [(lat, lon) for lon, lat in coords]
                    folium.PolyLine(route_latlon, color='blue', weight=5, opacity=0.8).add_to(m)
                    map_html = m.get_root().render()
                    st.session_state.ors_map_html = map_html
                    st.session_state.ors_src = source_city
                    st.session_state.ors_dest = destination_city
                    st.session_state.ors_last_search = (source_city, destination_city)
            except Exception as e:
                st.session_state.ors_map_html = None
                # Robust error handling for ORS error code 2010 (unroutable point)
                import json
                err_json = None
                # Try to extract error JSON from exception
                if len(e.args) > 0:
                    if isinstance(e.args[0], dict):
                        err_json = e.args[0]
                    elif isinstance(e.args[0], str):
                        try:
                            err_json = json.loads(e.args[0].replace("'", '"'))
                        except Exception:
                            err_json = None
                if err_json and isinstance(err_json, dict):
                    code = err_json.get('error', {}).get('code')
                    if code == 2010:
                        st.warning("No route could be found for one or both cities. Please check the city names or try a nearby location.")
                    else:
                        st.error(f"Error fetching route: {err_json['error'].get('message', str(e))}")
                else:
                    st.error(f"Error fetching route: {e}")
        else:
            st.session_state.ors_map_html = None
            st.error("Could not geocode one or both cities. Please check the city names.")
        st.session_state.find_route_pressed = False

    # Only show the map if the checkbox is checked and the map HTML exists
    if show_map and st.session_state.get('ors_map_html'):
        st.markdown(f"### Route Visualization: {st.session_state.ors_src} to {st.session_state.ors_dest}")
        st.components.v1.html(st.session_state.ors_map_html, height=500, scrolling=False)
elif menu == "All India CSV Graph":
    st.header("🇮🇳 All India Train Route - Shortest Path Visualizer")

    # --- Initialize session state ---
    if "show_path_result" not in st.session_state:
        st.session_state.show_path_result = False

    # --- Load data ---
    train_data = pd.read_csv("Train_details_22122017.csv")
    coord_data = pd.read_csv("station_coords.csv")

    # --- Build Graph ---
    G = nx.Graph()
    for _, row in train_data.iterrows():
        src = str(row["Source Station Name"]).strip().upper()
        dest = str(row["Destination Station Name"]).strip().upper()
        try:
            distance = float(row["Distance"])
        except:
            continue
        if not src or not dest or src == dest or src == 'NAN' or dest == 'NAN':
            continue
        G.add_edge(src, dest, weight=distance)

    stations = sorted(G.nodes)

    col1, col2 = st.columns(2)
    with col1:
        src_station = st.selectbox("🏁 Select Source Station", stations)
    with col2:
        dest_station = st.selectbox("🎯 Select Destination Station", stations)

    # --- Button logic ---
    if st.button("🚆 Find Shortest Path"):
        st.session_state.show_path_result = True

    if st.button("🔄 Reset"):
        st.session_state.show_path_result = False
        st.rerun()

    # --- Show Results ---
    if st.session_state.show_path_result:

        if src_station == dest_station:
            st.warning("⚠️ Source and Destination cannot be the same.")
        elif nx.has_path(G, src_station, dest_station):
            path = nx.shortest_path(G, source=src_station, target=dest_station, weight="weight")
            total_dist = nx.shortest_path_length(G, source=src_station, target=dest_station, weight="weight")
            st.success(f"✅ Shortest path found with {len(path)-1} hops. Total distance: {total_dist:.1f} km.")

            # --- Route Breakdown ---
            st.markdown("### 🛤️ Route Breakdown (with timings):")
            for i in range(len(path) - 1):
                from_station = path[i]
                to_station = path[i + 1]

                try:
                    leg_distance = G[from_station][to_station]['weight']
                except:
                    leg_distance = "Unknown"

                leg_info = train_data[
                    (train_data["Source Station Name"].str.strip().str.upper() == from_station.strip().upper()) &
                    (train_data["Destination Station Name"].str.strip().str.upper() == to_station.strip().upper())
                ]

                if not leg_info.empty:
                    departure_time = leg_info.iloc[0]["Departure Time"]
                    arrival_time = leg_info.iloc[0]["Arrival time"]
                    st.markdown(
                        f"➡️ **{from_station} → {to_station}**  \n"
                        f"🕒 Departure: `{departure_time}` | 🕓 Arrival: `{arrival_time}`  \n"
                        f"📏 Distance: `{leg_distance} km`"
                    )
                else:
                    st.markdown(
                        f"➡️ **{from_station} → {to_station}**  \n"
                        f"🕒 Timing not found  \n"
                        f"📏 Distance: `{leg_distance} km`"
                    )

            # --- Fare & Time Estimator ---
            st.markdown("### 💰 Fare & Time Estimator")
            FARE_TABLE = {
                "Sleeper": {"base": 50, "rate": 0.30},
                "AC Chair Car": {"base": 80, "rate": 0.45},
                "AC 2-Tier": {"base": 120, "rate": 0.60},
                "AC 1-Tier": {"base": 150, "rate": 0.90}
            }
            travel_class = st.selectbox("Choose Travel Class", list(FARE_TABLE.keys()))
            fare_info = FARE_TABLE[travel_class]
            fare = fare_info["base"] + fare_info["rate"] * total_dist
            st.info(f"**Estimated Fare ({travel_class})**: ₹ {fare:.2f}")

            # --- Time Estimate ---
            from datetime import datetime, timedelta
            def parse_time(t):
                try:
                    return datetime.strptime(t.strip(), "%H:%M")
                except:
                    return None

            first_leg = train_data[
                (train_data["Source Station Name"].str.strip().str.upper() == path[0]) &
                (train_data["Destination Station Name"].str.strip().str.upper() == path[1])
            ]
            last_leg = train_data[
                (train_data["Source Station Name"].str.strip().str.upper() == path[-2]) &
                (train_data["Destination Station Name"].str.strip().str.upper() == path[-1])
            ]

            if not first_leg.empty and not last_leg.empty:
                dep = parse_time(first_leg.iloc[0]["Departure Time"])
                arr = parse_time(last_leg.iloc[0]["Arrival time"])
                if dep and arr:
                    if arr < dep:
                        arr += timedelta(days=1)
                    total_time = arr - dep
                    st.info(f"🕓 Estimated Journey Time: {str(total_time)}")
                else:
                    est_hours = total_dist / 50
                    st.info(f"🕓 Estimated Journey Time: {timedelta(hours=est_hours)}")
            else:
                est_hours = total_dist / 50
                st.info(f"🕓 Estimated Journey Time: {timedelta(hours=est_hours)}")

            # --- Map Drawing ---
            from fuzzy_matcher import FuzzyStationResolver
            resolver = FuzzyStationResolver("station_coords.csv")
            resolved_path, missing = resolver.resolve_path(path)

            if missing:
                st.warning(f"⚠️ Missing coordinates for: {', '.join(missing)}")
            else:
                coord_start = resolver.get_coords(resolved_path[0])
                m = folium.Map(location=[coord_start["Latitude"], coord_start["Longitude"]], zoom_start=6)

                for i in range(len(resolved_path) - 1):
                    start, end = resolved_path[i], resolved_path[i+1]
                    c1 = resolver.get_coords(start)
                    c2 = resolver.get_coords(end)

                    folium.Marker([c1["Latitude"], c1["Longitude"]],
                                  tooltip=start,
                                  icon=folium.Icon(color="blue")).add_to(m)

                    folium.PolyLine([[c1["Latitude"], c1["Longitude"]],
                                     [c2["Latitude"], c2["Longitude"]]],
                                    color="red", weight=4.5, opacity=0.8).add_to(m)

                c_end = resolver.get_coords(resolved_path[-1])
                folium.Marker([c_end["Latitude"], c_end["Longitude"]],
                              tooltip=resolved_path[-1],
                              icon=folium.Icon(color="green")).add_to(m)

                st.markdown("### 🗺️ Visualizing Path on Map...")
                st_folium(m, width=900, height=600)
        else:
            st.error("❌ No path found between the selected stations.")
