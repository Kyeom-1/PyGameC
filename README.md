## Projectile Range Calculator (PyGame)

Interactive PyGame app to explore projectile motion range based on initial velocity `vi`, desired final speed `vf` at landing, and launch angle adjusted by mouse wheel or arrow keys. The app computes time of flight, landing height offset implied by `vi` and `vf`, and the horizontal range, while drawing the trajectory.

### Controls
- **Mouse Wheel / Up / Down**: Adjust launch angle
- **Click input boxes** to edit `vi` and `vf`
- **Enter**: Commit input / defocus
- **Esc**: Quit
- **Drag window edges** to resize (minimum 640x480)

### Notes
- If `vf` is left empty, it's assumed equal to `vi` (landing at same height).
- If a combination of `vi`, `vf`, and angle is not physically valid, a warning is shown.

### Install and Run (Windows PowerShell)
## Projectile Range Calculator (PyGame)

An interactive PyGame application for exploring projectile motion and horizontal range given:

- Initial speed (vi)
- Desired landing speed (vf) — optional (defaults to vi)
- Launch angle (adjustable with mouse wheel or arrow keys)

The app visualizes the trajectory, computes the time of flight, the implied landing height offset Δy (from energy), and the horizontal range.

## Features

- Real-time trajectory drawing
- Editable numeric input for `vi` and `vf`
- Angle control via mouse wheel or Up/Down keys
- Warnings for physically invalid parameter combinations

## Controls

- Mouse wheel or Up / Down arrow: adjust launch angle
- Click input boxes: edit `vi` and `vf`
- Enter: commit input / defocus the input box
- Esc: quit the application
- Resize window by dragging edges (minimum 640×480)

## Physics (summary)

The app uses energy and kinematics to relate speeds and landing height. Key equations used:

- Energy relation for vertical offset Δy:

	$vf^2 = vi^2 + 2 g \Delta y$

- Decompose initial velocity into components: $v_{x}=vi\cos\theta$, $v_{y}=vi\sin\theta$

- Vertical motion to solve for time of flight t (using $v_y$, g, and Δy), then horizontal range:

	$\text{range} = v_x \cdot t$

All formulas use the gravitational acceleration constant g (positive number, typically 9.81 m/s^2 in SI units).

## Prerequisites

- Python 3.8+ (the project was developed and tested on Python 3.10+)
- `pip` available
- The project uses `pygame`. See `requirements.txt` for the exact dependency list.

## Install and run (Windows PowerShell)

Open PowerShell, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py main.py
```

Notes:

- If your system uses `python` instead of `py`, replace `py` with `python` in the commands above.
- If you get an execution policy error when activating the virtual environment, run PowerShell as Administrator and set the policy temporarily:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Usage tips

- Leave `vf` empty to assume landing at the same speed/height as launch (vf = vi).
- If the chosen inputs are not physically consistent (for example a negative time of flight), the app will display a warning — try changing angle, vi, or vf.

## Troubleshooting

- Window too small / rendering issues: ensure your display scale is standard (100%) or resize the window; the app enforces a 640×480 minimum.
- Missing dependency errors: re-run `pip install -r requirements.txt` inside the activated virtual environment.

## Development notes

- Source: `main.py`
- Edit controls and physics code there if you want to change default gravity, input validation, or visualization.

---

If you want, I can also:

- Add examples of typical input values and expected ranges
- Add screenshots or a short GIF showing the app in action
- Add a minimal `requirements.txt` entry if it's missing or update it to a pinned version

Changes made: improved structure, clearer install/run instructions for Windows PowerShell, expanded physics section, and troubleshooting tips.


