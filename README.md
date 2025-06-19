# 🚆 Indian Railway Management System (Streamlit + Graph + Instamojo)

A powerful and interactive railway management system built using **Python**, **Streamlit**, **NetworkX**, and **Folium**, supporting:

- User/Admin login system
- Ticket booking with seat selection and Instamojo payment integration
- Real-time route visualization using OpenRouteService
- All India CSV-based shortest path detection with map, time, fare estimation, and hop-wise breakdown

---

## 🌟 Features

### 🔐 Authentication
- **Admin & User Login**
- Secure password hashing using `SHA256`
- CSV-based user registration and storage

### 🎟️ Ticket Booking (User)
- Select train, seat class (First/Second)
- Add multiple passenger details
- Opens Instamojo payment gateway
- Bookings stored in CSV with `Pending` status

### 🧮 Admin Dashboard
- Add trains with metadata (route, seats, fare)
- View trains and booking summary reports
- Booking history with visualization

### 🗺️ Real Train Route (OpenRouteService)
- Enter any Indian cities (e.g., Delhi to Mumbai)
- Get visual route on map with polyline
- Robust error handling for unmappable cities

### 🇮🇳 All India CSV Graph (Shortest Path)
- Reads real Indian railway data from `Train_details_22122017.csv`
- Displays shortest path with:
  - Total distance and number of hops
  - Hop-wise breakdown with departure/arrival time and distance
  - Fare Estimator based on class (Sleeper, AC, etc.)
  - Time Estimator based on average speed or timetable
  - Folium map visualization of the route using coordinates

---

## 📁 Folder Structure

📦 Railway Management System/
├── rail.py # Main Streamlit app
├── station_coords.csv # Station coordinate data (lat/lon)
├── Train_details_22122017.csv # Indian Railway route database
├── fuzzy_matcher.py # Fuzzy matching for resolving station names
├── auth.py / admin.py # Optional UI modules (can be excluded)
├── bookings.csv # Stores confirmed bookings
├── users.csv # Stores registered users
├── requirements.txt # All dependencies