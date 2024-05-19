import mysql.connector
import random

class CarPark:
    def __init__(self, carparkbay, carparkname, location, bay_status):
        self.carparkbay = carparkbay
        self.carparkname = carparkname
        self.location = location
        self.bay_status = bay_status

    def has_available_space(self):
        return any(status == 0 for status in self.bay_status)

class ParkingAlgorithm:
    def __init__(self, connection, user_location, destination_location):
        self.connection = connection
        self.user_location = user_location
        self.destination_location = destination_location
        self.time_intervals = {
            'low': 5,
            'medium': 10,
            'high': 15
        }
        self.walk_time = 15
        self.matrix_size = 10  # Assuming a 10x10 matrix for simplicity
        self.traffic_density = 'medium'  # Default traffic condition

    def set_traffic_density(self, traffic_density):
        self.traffic_density = traffic_density

    def generate_matrix(self, user_location, destination_location, car_parks):
        matrix = [['-' for _ in range(self.matrix_size)] for _ in range(self.matrix_size)]
        for i, car_park in enumerate(car_parks, start=1):
            x, y = car_park.location
            matrix[int(x)][int(y)] = str(i)  # representing car park with numbers, cast to int
        ux, uy = user_location
        dx, dy = destination_location
        matrix[int(ux)][int(uy)] = 'U'  # representing user, cast to int
        matrix[int(dx)][int(dy)] = 'D'  # representing destination, cast to int
        return matrix

    def fetch_car_parks_from_database(self):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM carpark")
        car_parks = {}
        for row in cursor.fetchall():
            location_x = row['location_x'] if row['location_x'] is not None else 0
            location_y = row['location_y'] if row['location_y'] is not None else 0
            if row['carparkname'] not in car_parks:
                car_parks[row['carparkname']] = {
                    'location': (int(location_x), int(location_y)),
                    'bays': {}
                }
            if row['baystatus']:  # Ensure baystatus is not an empty string
                car_parks[row['carparkname']]['bays'][int(row['carparkbay'])] = list(map(int, row['baystatus'].split(',')))

        result = []
        for carparkname, data in car_parks.items():
            for carparkbay, baystatus in data['bays'].items():
                result.append(CarPark(carparkbay, carparkname, data['location'], baystatus))
        cursor.close()
        return result

    def calculate_time(self, start_location, end_location):
        x1, y1 = start_location
        x2, y2 = end_location
        time_interval = self.time_intervals[self.traffic_density]
        return abs(x2 - x1) * time_interval + abs(y2 - y1) * time_interval

    def find_optimal_car_park(self, requires_specialized_space=None):
        car_parks = self.fetch_car_parks_from_database()
        time_to_carpark = {}
        for car_park in car_parks:
            if car_park.has_available_space():
                drive_time = self.calculate_time(self.user_location, car_park.location)
                walk_time = self.calculate_time(car_park.location, self.destination_location)
                total_time = drive_time + walk_time
                time_to_carpark[car_park] = total_time
        sorted_carparks = sorted(time_to_carpark.items(), key=lambda x: x[1])
        available_carparks = [car_park for car_park, time in sorted_carparks if car_park.has_available_space()]
        return available_carparks

    def simulate(self, requires_specialized_space=None):
        # Set and print the traffic condition
        traffic_condition = random.choice(['low', 'medium', 'high'])
        self.set_traffic_density(traffic_condition)
        print(f"Traffic Condition: {traffic_condition.capitalize()}")
        car_parks = self.find_optimal_car_park(requires_specialized_space)
        if car_parks:
            print("List of car parks in order of best option:")
            for i, car_park in enumerate(car_parks, start=1):
                print(f"{i}. {car_park.carparkname}")
                print(f"Location: {car_park.location}")
                print(f"Bay Status: {car_park.bay_status}")
                print()
        else:
            print("No available parking spaces.")

    def run(self):
        print("Running algorithm with user location:", self.user_location, "and destination location:", self.destination_location)
        self.simulate()

def run_algorithm(user_location, destination_location):
    connection = mysql.connector.connect(
        host="146.148.2.155",
        user="database",
        password="",
        database="ParkingAppdatabase",
    )
    algorithm = ParkingAlgorithm(connection, user_location, destination_location)
    algorithm.run()
    connection.close()
    return algorithm
