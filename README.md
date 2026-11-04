# control-system-analyzer

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange)
![Plots](https://img.shields.io/badge/plots-Matplotlib-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

Interactive Root Locus and Step Response analyzer for control systems, built with Python, Tkinter and Matplotlib.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Step Response Metrics](#step-response-metrics)
- [Project Structure](#project-structure)
- [Libraries Used](#libraries-used)
- [Limitations](#limitations)
- [Authors](#authors)
- [License](#license)

## Overview
This desktop application helps students analyze linear time-invariant systems. You enter the numerator and denominator of a transfer function, and the program draws an interactive root locus and a step response with the main performance specifications. It was developed as a university control systems project.

## Features

### Root Locus
- Root locus plot for any transfer function G(s) = num(s) / den(s)
- Draggable poles and zeros: move them with the mouse and the locus is recomputed
- Click on the locus to read the **exact gain K** and the closed-loop poles at that K
- Scroll wheel zoom
- Live display of the transfer function, poles and zeros

### Step Response
- Step response of the entered transfer function (or the same one used for the root locus)
- Automatic calculation of the performance metrics (see below)
- Marked lines on the plot for peak time, rise time, delay time and settling time
- Comparison with an ideal **second-order model** using a custom damping ratio (ζ) and/or natural frequency (ωn)
- Draggable information box on the plot
- Results are also printed in the terminal

## Installation
**Requirements:** Python 3.9 or newer.

1. Clone the repository:
   ```bash
   git clone https://github.com/Heliakhalilirad/control-system-analyzer.git
   cd control-system-analyzer
   ```
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Linux / macOS
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   On some Linux systems Tkinter must be installed separately:
   ```bash
   sudo apt install python3-tk
   ```

## Usage
Run the program:
```bash
python projectclp.py
```

### Root Locus tab
1. Enter the **numerator** and **denominator** coefficients separated by spaces, from the highest power to the lowest.
   Example: `s + 2 / (s^2 + 3s + 2)` is entered as
   - Numerator: `1 2`
   - Denominator: `1 3 2`
2. Click **Draw Root Locus**.
3. Drag the red **X** (poles) or green **O** (zeros) to move them.
4. Click on the blue curve to see the value of K at that point.

### Step Response tab
1. Keep **Use same TF from Root Locus** checked, or uncheck it and enter another transfer function.
2. Optionally enable the comparison with a second-order model and set the new ζ and/or ωn.
3. Click **Plot Step Response**. The metrics appear on the plot and in the window.

## Step Response Metrics
| Metric | Definition |
|--------|------------|
| Overshoot | (peak - final value) / final value x 100 |
| Peak time (tp) | Time of the maximum value |
| Rise time (tr) | Time from 10% to 90% of the final value |
| Delay time (td) | Time to reach 50% of the final value |
| Settling time (2%, 5%) | First time the response is within 2% or 5% of the final value |
| Steady-state value | Final value of the response |
| ωn, ζ | Natural frequency and damping ratio estimated from the dominant pole |

## Project Structure
```
control-system-analyzer/
├── projectclp.py       Main application
├── requirements.txt    Python dependencies
├── image.jpg           (optional) Logo shown in the window
├── .gitignore
├── LICENSE
└── README.md
```
If `image.jpg` is not found, the program shows an emoji logo instead.

## Libraries Used
- [python-control](https://python-control.readthedocs.io/) for transfer functions, root locus and step response
- [Matplotlib](https://matplotlib.org/) for interactive plots
- [NumPy](https://numpy.org/) for numerical calculations
- [Pillow](https://python-pillow.org/) for the logo image
- Tkinter for the graphical interface

## Limitations
- The root locus assumes unity negative feedback with a gain K from 0.001 to 1000
- Settling time and overshoot are calculated from the simulated response, so they depend on the simulation time chosen automatically by the library
- Overshoot and rise time are not meaningful for unstable systems
- Tested with the standard python-control API; very new versions may change the `root_locus` function

## Authors
- **Helia Khalilirad** - [@Heliakhalilirad](https://github.com/Heliakhalilirad)

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
