
# fuzzy_matcher.py
import pandas as pd
import difflib

class FuzzyStationResolver:
    def __init__(self, station_coords_path="station_coords.csv"):
        self.df = pd.read_csv(station_coords_path)
        self.df["StationName"] = self.df["StationName"].str.strip().str.upper()
        self.coord_dict = self.df.set_index("StationName")[["Latitude", "Longitude"]].to_dict(orient="index")
        self.station_names = list(self.coord_dict.keys())

    def fuzzy_match(self, name):
        name = name.strip().upper()
        matches = difflib.get_close_matches(name, self.station_names, n=1, cutoff=0.75)
        return matches[0] if matches else None

    def resolve_path(self, path):
        resolved = []
        missing = []
        for station in path:
            match = self.fuzzy_match(station)
            if match:
                resolved.append(match)
            else:
                missing.append(station)
        return resolved, missing

    def get_coords(self, name):
        return self.coord_dict.get(name, None)
