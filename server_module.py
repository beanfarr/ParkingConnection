import socket
import threading
import mysql.connector
from algorithm_module import ParkingAlgorithm

SERVER_IP = '0.0.0.0'  # Bind to all interfaces on the laptop
SERVER_PORT = 12345

# Database connection details
DB_HOST = "146.148.2.155"
DB_USER = "database"
DB_PASSWORD = ""
DB_NAME = "ParkingAppdatabase"


# Establish a connection to the MySQL database
def connect_to_database():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def insert_parking_status(carparkname, carparkbay, status):
    connection = connect_to_database()
    cursor = connection.cursor()

    # Separate the update into two queries to avoid the error
    select_query = """
    SELECT location_x, location_y FROM carpark WHERE carparkname = %s LIMIT 1
    """
    cursor.execute(select_query, (carparkname,))
    result = cursor.fetchone()
    location_x, location_y = result if result else (None, None)

    query = """
    INSERT INTO carpark (carparkname, carparkbay, baystatus, location_x, location_y)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    baystatus = VALUES(baystatus)
    """
    cursor.execute(query, (carparkname, carparkbay, status, location_x, location_y))
    connection.commit()
    cursor.close()
    connection.close()


def insert_car_park_location(carparkname, location):
    connection = connect_to_database()
    cursor = connection.cursor()
    query = """
    INSERT INTO carpark (carparkname, carparkbay, location_x, location_y, baystatus)
    VALUES (%s, 0, %s, %s, '')
    ON DUPLICATE KEY UPDATE
    location_x = VALUES(location_x), location_y = VALUES(location_y)
    """
    cursor.execute(query, (carparkname, location[0], location[1]))
    connection.commit()
    cursor.close()
    connection.close()


def handle_client(client_socket, client_address, algorithm):
    print("Connection from:", client_address)
    try:
        buffer = ""
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                print("No data received. Closing connection:", client_address)
                break
            print("Received from {}: {}".format(client_address, data))

            # Append data to buffer and split based on newline
            buffer += data
            messages = buffer.split('\n')
            buffer = messages.pop()  # Last element is a partial message if any

            for message in messages:
                # Parse the received data
                try:
                    if "LOCATION" in message:
                        carparkname, location_data = message.split(':LOCATION:')
                        location_x, location_y = map(int, location_data.split(','))
                        insert_car_park_location(carparkname, (location_x, location_y))
                        print(f"Inserted location: {carparkname}: {location_x},{location_y}")
                    else:
                        carparkname, space_status = message.split('-')
                        carparkbay, status = space_status.split(': ')
                        carparkbay = int(carparkbay)  # Convert carparkbay to int
                        status = int(status)
                        insert_parking_status(carparkname, carparkbay, status)
                        print(f"Inserted data: {carparkname}-{carparkbay}: {status}")

                        # Trigger the algorithm after updating the database
                        algorithm.run()
                except ValueError as e:
                    print(f"Error parsing data from {client_address}: {e}")
    except Exception as e:
        print("Error receiving data from {}: {}".format(client_address, e))
    finally:
        client_socket.close()
        print("Connection closed:", client_address)


def start_server(algorithm):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)

    print("Server listening on {}:{}".format(SERVER_IP, SERVER_PORT))

    while True:
        client_socket, client_address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, algorithm))
        client_handler.start()
