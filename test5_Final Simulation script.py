import random
import json  # For JSON serialization
from datetime import datetime, timedelta
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
# MQTT_BROKER = "192.168.202.41"  # Replace with your MQTT broker address
MQTT_BROKER="192.168.0.39"
MQTT_PORT = 1883
MQTT_TOPIC = "/factory/assets"

def authenticate_employee():
    authorized_employees = {
        "E001": "Alice",
        "E002": "Bob",
        "E003": "Charlie",
        "E004": "Diana"
    }
    emp_id = input("Enter your Employee ID: ")
    if emp_id in authorized_employees:
        print(f"Welcome, {authorized_employees[emp_id]}!")
        return authorized_employees[emp_id]
    else:
        print("Unauthorized Employee. Exiting...")
        exit()

def main_menu():
    products = ["Coca Cola", "Fanta", "Sprite"]
    print("Select a product to start the run:")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product}")
    choice = int(input("Enter the number corresponding to your choice: "))
    if 1 <= choice <= len(products):
        return products[choice - 1]
    else:
        print("Invalid choice. Exiting...")
        exit()

def simulate_product_run(product_name, line_manager):
    # Operator inputs additional details
    job_id = input("Enter the Job ID (from ERP system): ")
    shift_id = input("Enter the Shift ID (e.g., Shift_1, Shift_2): ")
    priority = input("Enter the job priority (High, Medium, Low): ").capitalize()

    # Validate priority input
    if priority not in ["High", "Medium", "Low"]:
        print("Invalid priority. Please enter High, Medium, or Low. Exiting...")
        exit()

    # Input for Fixed Asset ID
    fixed_asset_id = input("Enter the Asset ID (e.g., Machine_001): ")

    # Collecting target quantity and estimated runtime
    target_quantity = int(input(f"Enter the target quantity for {product_name}: "))
    estimated_runtime_minutes = int(input(f"Enter the estimated runtime in minutes for {product_name}: "))

    # Calculate start and estimated end times
    start_time = datetime.now()
    estimated_end_time = start_time + timedelta(minutes=estimated_runtime_minutes)

    # Initialize counters
    good_count = 0
    scrap_count = 0
    actual_runtime_minutes = 0  # Track the actual time the machine was running

    print(f"Starting product run for {product_name}.")
    print(f"Job Details:\n - Job ID: {job_id}\n - Shift ID: {shift_id}\n - Priority: {priority}\n - Fixed Asset ID: {fixed_asset_id}")
    print(f"Target quantity: {target_quantity} units. Estimated runtime: {estimated_runtime_minutes} minutes.")

    # Initialize MQTT client
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    while good_count < target_quantity:
        # Simulate timestamp
        timestamp = datetime.now()

        # Simulate sensor states
        is_machine_running = random.choice([True, False])  # Whether the machine is running
        if is_machine_running:
            increment_good = random.randint(0, 20)
            increment_scrap = random.randint(0, 5)
            # Add to actual runtime if the machine is running
            actual_runtime_minutes += 1
        else:
            increment_good = 0
            increment_scrap = 0

        good_count += increment_good
        scrap_count += increment_scrap

        # Calculate yield dynamically
        yield_percentage = (good_count / (good_count + scrap_count) * 100) if (good_count + scrap_count) > 0 else 0

        # Calculate elapsed runtime in minutes
        elapsed_runtime_minutes = (datetime.now() - start_time).total_seconds() / 60

        # Ensure actual runtime never exceeds elapsed runtime
        actual_runtime_minutes = min(actual_runtime_minutes, elapsed_runtime_minutes)

        # Prepare sensor data
        sensor_data = {
            "JobID": job_id,
            "ShiftID": shift_id,
            "Priority": priority,
            "AssetID": fixed_asset_id,  # Added Fixed Asset ID
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "IsMachineRunning": is_machine_running,
            "LineManager": line_manager,
            "ProductName": product_name,
            "TargetQuantity": target_quantity,
            "GoodUnitsProduced": good_count,
            "ScrapUnitsProduced": scrap_count,
            "StartTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "EstimatedEndTime": estimated_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "ElapsedRuntimeMinutes": elapsed_runtime_minutes,
            "EstimatedRuntimeMinutes": estimated_runtime_minutes,
            "ActualRuntimeMinutes": actual_runtime_minutes  # Added the actual runtime
        }

        # Serialize the data to a JSON string
        sensor_data_json = json.dumps(sensor_data)

        # Publish data to MQTT topic
        client.publish(MQTT_TOPIC, sensor_data_json)
        print(f"Published to MQTT: {sensor_data_json}")

        # Simulate real-time delay
        time.sleep(60)

    print(f"Target quantity achieved for {product_name}! Ending run.")
    client.disconnect()

if __name__ == "__main__":
    while True:
        line_manager = authenticate_employee()
        product_name = main_menu()
        simulate_product_run(product_name, line_manager)
        print("Returning to main menu...")
