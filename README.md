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
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py main.py
```

### Physics
Using energy to relate landing height offset Δy to speeds: `vf^2 = vi^2 + 2 g Δy`. Then solve vertical motion for time of flight with the selected angle, and compute range as `vx * t`.


