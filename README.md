# STM32H7 Custom UART OTA Bootloader

## 🎯 Project Overview
This project implements a custom bare-metal Over-The-Air (OTA) bootloader for the **STM32H747I-DISCO** development board. Instead of relying on an ST-Link hardware debugger, this system allows a compiled firmware binary (`.bin`) to be transmitted over a standard UART connection from a PC (via a Python script) and flashed directly into the microcontroller's memory. Once the flash process is complete, the bootloader securely transitions execution to the newly installed main application.

## ⚙️ Hardware & Software Stack
*   **Hardware:** STM32H747I-DISCO (Dual-core Cortex-M7 & Cortex-M4)
*   **Firmware Development:** STM32CubeIDE (C, HAL drivers)
*   **Host Scripting:** Python 3 (PySerial)
*   **Communication:** UART (Universal Asynchronous Receiver-Transmitter)

## 🏗️ System Architecture
The project is divided into three primary components:
1.  **Python Uploader (`ota_update.py`):** Reads the compiled `.bin` file, handles the communication state machine, and sends the binary in 1024-byte chunks over a serial port.
2.  **Bootloader Firmware:** Resides at the default flash origin (`0x08000000`). It receives the UART packets, writes them to Flash Sector 1 (`0x08020000`), performs hardware cleanup, and executes a memory jump.
3.  **Main Application:** Compiled to reside at `0x08020000`. It initializes its own peripherals, turns on the LED port, and executes the core application logic.

## 🛠️ Key Challenges & Solutions

### 1. The "Last Chunk" UART Hang (Data Padding)
*   **Problem:** The STM32 `HAL_UART_Receive()` function was configured to expect exactly 1024 bytes per chunk. If the final firmware chunk was smaller than 1024 bytes, the microcontroller would wait indefinitely, freezing the system.
*   **Solution:** Implemented dynamic data padding in the Python script. Any final chunk smaller than 1024 bytes is padded with `0xFF` (the default state of erased flash memory) to ensure the STM32 UART buffer is always successfully filled.

### 2. The Messy App Handoff (Peripheral Cleanup)
*   **Problem:** Jumping to the Main Application while the Bootloader's clocks, SysTick timer, and interrupts were still active caused the Main App to crash during its own initialization phase.
*   **Solution:** Called `HAL_DeInit()` to reset all hardware peripherals, manually cleared the SysTick timer registers, and executed `__disable_irq()` to completely lock out interrupts before performing the memory jump.

### 3. Memory Mapping & Application Identity
*   **Problem:** By default, CubeIDE compiles applications to run at `0x08000000`. Flashing standard code to `0x08020000` resulted in misaligned memory pointers and system hard faults.
*   **Solution:** Modified the Main Application's Linker Script (`.ld`) to set the `FLASH` origin to `0x08020000`. Updated the Vector Table offset (`SCB->VTOR`) in `system_stm32h7xx.c` to shift by `0x20000` so the core knows exactly where to find its interrupts and instructions. 

### 4. The Dual-Core Synchronization Trap (AMP Architecture)
*   **Problem:** The STM32H747 is a dual-core chip. The default CubeIDE initialization code forces the CM7 core to wait for a hardware semaphore from the CM4 core. Because the bootloader only initialized the CM7, the CM7 timed out waiting for the asleep CM4 and trapped itself in an infinite `Error_Handler()` loop before reaching the main `while(1)` block.
*   **Solution:** Commented out the `#define DUAL_CORE_BOOT_SYNC_SEQUENCE` directive in the Main Application to bypass the CM4 sync wait, allowing the CM7 to boot independently.

## 📂 Repository Structure
```text
STM32_OTA_Bootloader/
│
├── H7_Bootloader/          # CubeIDE workspace for the Bootloader firmware
├── H7_Main_App/            # CubeIDE workspace for the Main Application
├── ota_update.py           # Python script to transmit the firmware
└── .gitignore              # Ignores build artifacts (.bin, .o, /Debug)
