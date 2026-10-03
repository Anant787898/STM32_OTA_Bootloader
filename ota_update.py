import serial
import sys
import os

# Configuration
COM_PORT = "COM3"      # We will need to update this!
BAUD_RATE = 115200
FILE_PATH = "H7_Main_App_CM7.bin"
CHUNK_SIZE = 1024

def flash_firmware():
    if not os.path.exists(FILE_PATH):
        print(f"Error: Could not find {FILE_PATH}")
        return

    with open(FILE_PATH, "rb") as file:
        firmware_data = file.read()
        
    total_size = len(firmware_data)
    print(f"Loaded {FILE_PATH} ({total_size} bytes)")

    try:
        ser = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=20)
        print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")
    except Exception as e:
        print(f"Failed to open port: {e}")
        return

    print("Starting firmware update...")

     # 1. Send the 'Start' command
    ser.write(b'S')

    # 2. THE HANDSHAKE: Wait for the STM32 to finish erasing and send 'R'
    print("Waiting for STM32 to erase Flash memory (this takes up to 15 seconds)...")
    ready_byte = ser.read(1)
    
    if ready_byte != b'R':
        print("\nError: Did not receive Ready signal from STM32.")
        ser.close()
        return
        
    print("STM32 is ready! Sending data chunks...")
    
    for i in range(0, total_size, CHUNK_SIZE):
        chunk = firmware_data[i : i + CHUNK_SIZE]

        # --- NEW PADDING LOGIC ---
        if len(chunk) < CHUNK_SIZE:
            padding_needed = CHUNK_SIZE - len(chunk)
            chunk += b'\xFF' * padding_needed
        # -------------------------

        # 1. Send the 'Write' command
        ser.write(b'W')
        
        # 2. Send the chunk
        ser.write(chunk)
        
        # 3. Wait for the 'Acknowledge'
        ack = ser.read(1)
        if ack != b'A':
            print(f"\nError: Bootloader failed to acknowledge at byte {i}.")
            ser.close()
            return
            
        progress = min(100, int((i + len(chunk)) / total_size * 100))
        sys.stdout.write(f"\rProgress: {progress}% ")
        sys.stdout.flush()

    # 4. Send the 'Done' command
    ser.write(b'D')
    print("\nFirmware update complete! Bootloader jumping to Main App.")
    ser.close()

if __name__ == "__main__":
    flash_firmware()