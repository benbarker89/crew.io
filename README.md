# Auto Button Presser

A simple Python application that automatically presses the down arrow key at a configurable rate.

## Features

- 🕐 10-second delay before starting
- ⬇️ Presses down arrow key 150 times per minute (every 400ms)
- ⛔ Press **ESC** to stop at any time
- 📊 Real-time press counter

## Requirements

- Python 3.6+
- pynput library

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python auto_presser.py
```

Or make it executable and run directly:

```bash
chmod +x auto_presser.py
./auto_presser.py
```

### What happens:

1. The program starts with a 10-second countdown
2. After the countdown, it begins pressing the down arrow key automatically
3. Press **ESC** at any time to stop the program
4. The program displays a real-time counter of total key presses

## Configuration

You can modify these constants in the script:

- `PRESSES_PER_MINUTE`: Number of presses per minute (default: 150)
- `DELAY_BEFORE_START`: Seconds to wait before starting (default: 10)

## Notes

- Make sure the window you want to send key presses to is in focus
- The program requires appropriate permissions to simulate keyboard input
- On some systems, you may need to run with elevated privileges

## Safety

- The ESC key provides a quick way to stop the program
- You can also use Ctrl+C to force quit if needed
