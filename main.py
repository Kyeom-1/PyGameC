import math
import sys

import pygame


# Constants
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 600
FPS = 60

BACKGROUND_COLOR = (18, 18, 22)
TEXT_COLOR = (230, 230, 235)
ACCENT_COLOR = (100, 180, 255)
INPUT_BG = (35, 35, 42)
INPUT_BG_FOCUS = (50, 50, 62)
ERROR_COLOR = (255, 120, 120)
GRID_COLOR = (40, 44, 52)
SIM_COLOR = (255, 200, 100)
TRAIL_COLOR = (150, 200, 255)
VECTOR_COLOR = (255, 100, 100)

GRAVITY = 9.81  # m/s^2


class TextInput:

	def __init__(self, rect, font, placeholder="", numeric=True, allow_empty=True):
		self.rect = pygame.Rect(rect)
		self.font = font
		self.placeholder = placeholder
		self.numeric = numeric
		self.allow_empty = allow_empty
		self.text = ""
		self.focused = False
		self.cursor_visible = True
		self.cursor_timer = 0.0
		self.cursor_interval = 0.6
		self.invalid = False

	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN:
			self.focused = self.rect.collidepoint(event.pos)
			self.cursor_visible = True
			self.cursor_timer = 0.0
		elif self.focused and event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RETURN:
				self.focused = False
				return
			if event.key == pygame.K_BACKSPACE:
				self.text = self.text[:-1]
			elif event.key == pygame.K_MINUS and not self.numeric:
				self.text += "-"
			elif event.key == pygame.K_PERIOD or event.unicode == ".":
				if "." not in self.text:
					self.text += "."
			elif event.unicode:
				if self.numeric:
					if event.unicode.isdigit():
						self.text += event.unicode
				else:
					self.text += event.unicode

	def update(self, dt):
		if self.focused:
			self.cursor_timer += dt
			if self.cursor_timer >= self.cursor_interval:
				self.cursor_visible = not self.cursor_visible
				self.cursor_timer = 0.0
		else:
			self.cursor_visible = False

	def get_value(self):
		if self.text.strip() == "":
			return None
		try:
			return float(self.text)
		except ValueError:
			return None

	def draw(self, surface):
		bg = INPUT_BG_FOCUS if self.focused else INPUT_BG
		pygame.draw.rect(surface, bg, self.rect, border_radius=6)
		pygame.draw.rect(surface, GRID_COLOR if not self.invalid else ERROR_COLOR, self.rect, width=1, border_radius=6)

		display_text = self.text if self.text != "" else self.placeholder
		color = TEXT_COLOR if self.text != "" else (160, 160, 170)
		render = self.font.render(display_text, True, color)
		surface.blit(render, (self.rect.x + 10, self.rect.y + (self.rect.height - render.get_height()) // 2))

		if self.focused:
			cursor_x = self.rect.x + 10 + render.get_width()
			cursor_y = self.rect.y + 8
			if self.cursor_visible:
				pygame.draw.line(surface, TEXT_COLOR, (cursor_x, cursor_y), (cursor_x, self.rect.bottom - 8), 1)


def compute_delta_y_from_speeds(initial_speed, final_speed, gravity):
	"""
	Compute vertical displacement needed so that impact speed equals final_speed,
	given initial_speed and gravity. Positive Δy means landing above launch.
	Using energy: vf^2 = vi^2 + 2 g Δy  =>  Δy = (vf^2 - vi^2) / (2 g)
	"""
	return (final_speed * final_speed - initial_speed * initial_speed) / (2.0 * gravity)


def solve_time_of_flight(initial_speed, launch_angle_deg, delta_y, gravity):
	angle_rad = math.radians(launch_angle_deg)
	vy0 = initial_speed * math.sin(angle_rad)
	# Solve -0.5 g t^2 + vy0 t - delta_y = 0 -> take the larger positive root
	discriminant = vy0 * vy0 - 2.0 * gravity * delta_y
	if discriminant < 0:
		return None
	sqrt_disc = math.sqrt(discriminant)
	# positive time
	return (vy0 + sqrt_disc) / gravity


def sample_trajectory(initial_speed, launch_angle_deg, gravity, t_end, num_points=200):
	angle_rad = math.radians(launch_angle_deg)
	vx0 = initial_speed * math.cos(angle_rad)
	vy0 = initial_speed * math.sin(angle_rad)
	points = []
	for i in range(num_points + 1):
		t = t_end * (i / num_points)
		x = vx0 * t
		y = vy0 * t - 0.5 * gravity * t * t
		points.append((x, y))
	return points


def draw_grid(surface, rect, origin_px, scale):
	# Minor grid within rect
	step = 20
	x0, y0, w, h = rect
	for x in range(x0, x0 + w + 1, step):
		pygame.draw.line(surface, GRID_COLOR, (x, y0), (x, y0 + h))
	for y in range(y0, y0 + h + 1, step):
		pygame.draw.line(surface, GRID_COLOR, (x0, y), (x0 + w, y))

	# Axes within rect - only draw if origin is within the rect
	if x0 <= origin_px[0] <= x0 + w:
		pygame.draw.line(surface, (90, 90, 100), (origin_px[0], y0), (origin_px[0], y0 + h), 2)
	if y0 <= origin_px[1] <= y0 + h:
		pygame.draw.line(surface, (90, 90, 100), (x0, origin_px[1]), (x0 + w, origin_px[1]), 2)


def world_to_screen(origin_px, scale, x_world, y_world):
	x = origin_px[0] + x_world * scale
	y = origin_px[1] - y_world * scale
	return int(x), int(y)


def clamp(value, lo, hi):
	return max(lo, min(hi, value))


class ProjectileSimulation:
	def __init__(self):
		self.reset()
		self.trail_points = []
		self.max_trail_length = 200
		
	def reset(self):
		self.is_running = False
		self.is_paused = False
		self.time = 0.0
		self.position = (0.0, 0.0)
		self.velocity = (0.0, 0.0)
		self.initial_velocity = (0.0, 0.0)
		self.angle_deg = 0.0
		self.trail_points = []
		self.impact_time = None
		self.range_m = 0.0
		
	def launch(self, initial_speed, angle_deg, delta_y):
		self.reset()
		self.angle_deg = angle_deg
		angle_rad = math.radians(angle_deg)
		self.initial_velocity = (
			initial_speed * math.cos(angle_rad),
			initial_speed * math.sin(angle_rad)
		)
		self.velocity = self.initial_velocity
		self.position = (0.0, 0.0)
		self.is_running = True
		self.is_paused = False
		self.time = 0.0
		self.trail_points = [(0.0, 0.0)]
		
		# Calculate impact time and range
		vy0 = self.initial_velocity[1]
		discriminant = vy0 * vy0 - 2.0 * GRAVITY * delta_y
		if discriminant >= 0:
			sqrt_disc = math.sqrt(discriminant)
			self.impact_time = (vy0 + sqrt_disc) / GRAVITY
			self.range_m = self.initial_velocity[0] * self.impact_time
		else:
			self.impact_time = None
			self.range_m = 0.0
			
	def update(self, dt, speed_multiplier=1.0):
		if not self.is_running or self.is_paused:
			return
			
		dt *= speed_multiplier
		self.time += dt
		
		# Update position using physics
		self.position = (
			self.initial_velocity[0] * self.time,
			self.initial_velocity[1] * self.time - 0.5 * GRAVITY * self.time * self.time
		)
		
		# Update velocity
		self.velocity = (
			self.initial_velocity[0],
			self.initial_velocity[1] - GRAVITY * self.time
		)
		
		# Add to trail
		self.trail_points.append(self.position)
		if len(self.trail_points) > self.max_trail_length:
			self.trail_points.pop(0)
			
		# Check for impact
		if self.impact_time and self.time >= self.impact_time:
			self.is_running = False
			self.time = self.impact_time
			self.position = (self.range_m, 0.0)
			self.velocity = (self.initial_velocity[0], -math.sqrt(self.initial_velocity[1]**2 - 2*GRAVITY*self.position[1]))
			
	def get_speed(self):
		return math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
		
	def toggle_pause(self):
		if self.is_running:
			self.is_paused = not self.is_paused
			
	def stop(self):
		self.is_running = False
		self.is_paused = False


def main():
	pygame.init()
	pygame.display.set_caption("Projectile Range Calculator - Simulation")
	screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
	clock = pygame.time.Clock()

	font = pygame.font.SysFont("consolas", 20)
	big_font = pygame.font.SysFont("consolas", 24)
	small_font = pygame.font.SysFont("consolas", 16)

	# UI layout - will be updated on resize
	panel_w = 320
	window_width = WINDOW_WIDTH
	window_height = WINDOW_HEIGHT
	
	# Plot area margins
	margin_left = 40
	margin_right = 20
	margin_top = 20
	margin_bottom = 60
	
	# Initialize layout variables
	panel_rect = pygame.Rect(window_width - panel_w, 0, panel_w, window_height)
	plot_rect = pygame.Rect(0, 0, window_width - panel_w, window_height)
	usable_w = plot_rect.width - (margin_left + margin_right)
	usable_h = plot_rect.height - (margin_top + margin_bottom)
	
	# Initialize input fields
	input_vi = TextInput(pygame.Rect(panel_rect.x + 20, 80, panel_w - 40, 36), font, placeholder="Initial speed vi (m/s)")
	input_vf = TextInput(pygame.Rect(panel_rect.x + 20, 150, panel_w - 40, 36), font, placeholder="Final speed vf (m/s, empty = vi)")
	
	def update_layout():
		nonlocal panel_rect, plot_rect, usable_w, usable_h, input_vi, input_vf
		panel_rect = pygame.Rect(window_width - panel_w, 0, panel_w, window_height)
		plot_rect = pygame.Rect(0, 0, window_width - panel_w, window_height)
		usable_w = plot_rect.width - (margin_left + margin_right)
		usable_h = plot_rect.height - (margin_top + margin_bottom)
		
		# Update input positions
		input_vi.rect = pygame.Rect(panel_rect.x + 20, 80, panel_w - 40, 36)
		input_vf.rect = pygame.Rect(panel_rect.x + 20, 150, panel_w - 40, 36)

	angle_deg = 45.0
	angle_min = 0.0
	angle_max = 89.9

	# Simulation
	sim = ProjectileSimulation()
	speed_multiplier = 1.0
	show_vectors = True
	show_trail = True

	# Defaults for quick start
	input_vi.text = "30"
	input_vf.text = ""

	running = True
	while running:
		dt = clock.tick(FPS) / 1000.0

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.VIDEORESIZE:
				# Handle window resize with minimum constraints
				window_width = max(640, event.w)  # Minimum width
				window_height = max(480, event.h)  # Minimum height
				screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
				update_layout()
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				running = False
			# Angle controls: mouse wheel and arrow keys
			elif event.type == pygame.MOUSEWHEEL:
				angle_deg += event.y * 1.5
				angle_deg = clamp(angle_deg, angle_min, angle_max)
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_UP:
					angle_deg += 1.0
				elif event.key == pygame.K_DOWN:
					angle_deg -= 1.0
				elif event.key == pygame.K_SPACE:
					# Launch simulation
					vi = input_vi.get_value()
					vf = input_vf.get_value()
					if vi is not None and vi > 0:
						if vf is None:
							vf_effective = vi
						else:
							vf_effective = vf
						delta_y = compute_delta_y_from_speeds(vi, vf_effective, GRAVITY)
						sim.launch(vi, angle_deg, delta_y)
				elif event.key == pygame.K_p:
					# Pause/Resume
					sim.toggle_pause()
				elif event.key == pygame.K_r:
					# Reset
					sim.stop()
				elif event.key == pygame.K_v:
					# Toggle vectors
					show_vectors = not show_vectors
				elif event.key == pygame.K_t:
					# Toggle trail
					show_trail = not show_trail
				elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
					# Speed up
					speed_multiplier = min(5.0, speed_multiplier * 1.5)
				elif event.key == pygame.K_MINUS:
					# Slow down
					speed_multiplier = max(0.1, speed_multiplier / 1.5)
				angle_deg = clamp(angle_deg, angle_min, angle_max)

			# Input handling
			input_vi.handle_event(event)
			input_vf.handle_event(event)

		input_vi.update(dt)
		input_vf.update(dt)
		
		# Update simulation
		sim.update(dt, speed_multiplier)

		screen.fill(BACKGROUND_COLOR)

		# Draw left plot background
		pygame.draw.rect(screen, BACKGROUND_COLOR, plot_rect)

		# Side panel background
		pygame.draw.rect(screen, (24, 24, 30), panel_rect)
		pygame.draw.line(screen, (60, 60, 70), (panel_rect.x, 0), (panel_rect.x, window_height), 1)

		# Titles
		screen.blit(big_font.render("Projectile Range", True, TEXT_COLOR), (panel_rect.x + 20, 20))

		# Angle display
		angle_label = big_font.render(f"Angle: {angle_deg:.1f}°", True, ACCENT_COLOR)
		screen.blit(angle_label, (panel_rect.x + 20, 220))
		screen.blit(font.render("Use Mouse Wheel / Up / Down", True, (160, 160, 170)), (panel_rect.x + 20, 250))

		# Simulation controls
		screen.blit(font.render("Simulation Controls", True, (180, 180, 190)), (panel_rect.x + 20, 290))
		screen.blit(small_font.render("SPACE: Launch", True, TEXT_COLOR), (panel_rect.x + 20, 320))
		screen.blit(small_font.render("P: Pause/Resume", True, TEXT_COLOR), (panel_rect.x + 20, 340))
		screen.blit(small_font.render("R: Reset", True, TEXT_COLOR), (panel_rect.x + 20, 360))
		screen.blit(small_font.render("V: Toggle Vectors", True, TEXT_COLOR), (panel_rect.x + 20, 380))
		screen.blit(small_font.render("T: Toggle Trail", True, TEXT_COLOR), (panel_rect.x + 20, 400))
		screen.blit(small_font.render("+/-: Speed", True, TEXT_COLOR), (panel_rect.x + 20, 420))

		# Inputs
		screen.blit(font.render("Inputs", True, (180, 180, 190)), (panel_rect.x + 20, 60))
		input_vi.draw(screen)
		input_vf.draw(screen)

		# Parse inputs
		vi = input_vi.get_value()
		vf = input_vf.get_value()
		input_vi.invalid = vi is None or (vi is not None and vi <= 0)
		if vf is None and input_vf.text.strip() != "":
			input_vf.invalid = True
		else:
			input_vf.invalid = False

		info_y = 450
		message_lines = []

		# Calculate theoretical trajectory for visualization
		theoretical_trajectory = []
		theoretical_range = 0.0
		theoretical_t_flight = 0.0
		
		if vi is not None and vi > 0:
			if vf is None:
				vf_effective = vi
			else:
				vf_effective = vf

			# Determine landing height offset from speed difference
			delta_y = compute_delta_y_from_speeds(vi, vf_effective, GRAVITY)
			t_flight = solve_time_of_flight(vi, angle_deg, delta_y, GRAVITY)

			if t_flight is None or t_flight <= 0:
				message_lines.append(("No solution for given angle and speeds.", ERROR_COLOR))
				theoretical_trajectory = []
				theoretical_range = None
			else:
				vx = vi * math.cos(math.radians(angle_deg))
				theoretical_range = vx * t_flight
				theoretical_t_flight = t_flight
				theoretical_trajectory = sample_trajectory(vi, angle_deg, GRAVITY, t_flight, num_points=300)

		# Auto-fit scale and origin for visualization
		all_points = []
		if theoretical_trajectory:
			all_points.extend(theoretical_trajectory)
		if sim.trail_points:
			all_points.extend(sim.trail_points)
		if sim.position != (0, 0):
			all_points.append(sim.position)
			
		if all_points:
			xs = [p[0] for p in all_points]
			ys = [p[1] for p in all_points]
			min_x, max_x = min(xs), max(xs)
			min_y, max_y = min(ys), max(ys)
			# Ensure origin (0,0) is considered for better framing
			min_x = min(min_x, 0.0)
			min_y = min(min_y, 0.0)
			# Compute scales; avoid zero division
			width_world = max(1e-6, max_x - min_x)
			height_world = max(1e-6, max_y - min_y)
			scale_x = usable_w / width_world
			scale_y = usable_h / height_world
			scale = max(1.0, min(scale_x, scale_y))  # don't zoom in too far below 1 px/m

			# Compute origin so that (min_x, min_y) maps to top-left margin inside plot_rect
			origin_px = (
				plot_rect.x + margin_left - int(min_x * scale),
				plot_rect.y + margin_top + int(max_y * scale)
			)
		else:
			# Default view
			origin_px = (plot_rect.x + margin_left, plot_rect.bottom - margin_bottom)
			scale = 6.0

		# Draw grid
		draw_grid(screen, plot_rect, origin_px, scale)

		# Draw theoretical trajectory
		if theoretical_trajectory:
			points_px = [world_to_screen(origin_px, scale, x, y) for (x, y) in theoretical_trajectory]
			for i in range(1, len(points_px)):
				pygame.draw.line(screen, (100, 100, 120), points_px[i - 1], points_px[i], 1)

		# Draw simulation trail
		if show_trail and sim.trail_points:
			trail_px = [world_to_screen(origin_px, scale, x, y) for (x, y) in sim.trail_points]
			for i in range(1, len(trail_px)):
				alpha = i / len(trail_px)
				color = (int(TRAIL_COLOR[0] * alpha), int(TRAIL_COLOR[1] * alpha), int(TRAIL_COLOR[2] * alpha))
				pygame.draw.line(screen, color, trail_px[i - 1], trail_px[i], 2)

		# Draw projectile
		if sim.is_running or sim.position != (0, 0):
			proj_x, proj_y = world_to_screen(origin_px, scale, sim.position[0], sim.position[1])
			pygame.draw.circle(screen, SIM_COLOR, (proj_x, proj_y), 6)
			pygame.draw.circle(screen, (255, 255, 255), (proj_x, proj_y), 6, 2)

		# Draw velocity vector
		if show_vectors and sim.is_running and sim.velocity != (0, 0):
			proj_x, proj_y = world_to_screen(origin_px, scale, sim.position[0], sim.position[1])
			# Scale vector for visibility
			vector_scale = 0.1
			end_x = proj_x + int(sim.velocity[0] * vector_scale)
			end_y = proj_y - int(sim.velocity[1] * vector_scale)  # Flip Y for screen coordinates
			pygame.draw.line(screen, VECTOR_COLOR, (proj_x, proj_y), (end_x, end_y), 3)
			# Arrow head
			angle = math.atan2(sim.velocity[1], sim.velocity[0])
			arrow_size = 8
			head1_x = end_x - int(arrow_size * math.cos(angle - 0.5))
			head1_y = end_y + int(arrow_size * math.sin(angle - 0.5))
			head2_x = end_x - int(arrow_size * math.cos(angle + 0.5))
			head2_y = end_y + int(arrow_size * math.sin(angle + 0.5))
			pygame.draw.polygon(screen, VECTOR_COLOR, [(end_x, end_y), (head1_x, head1_y), (head2_x, head2_y)])

		# Draw landing point and range marker
		if theoretical_range is not None and theoretical_trajectory:
			land_x, land_y = theoretical_trajectory[-1]
			lx, ly = world_to_screen(origin_px, scale, land_x, land_y)
			pygame.draw.circle(screen, (255, 180, 100), (lx, ly), 5)

			# Range guide on x-axis at y=0 if inside plot
			axis_y = world_to_screen(origin_px, scale, 0, 0)[1]
			pygame.draw.line(screen, (120, 120, 140), (world_to_screen(origin_px, scale, 0, 0)[0], axis_y), (lx, axis_y), 1)
			pygame.draw.line(screen, (120, 120, 140), (lx, axis_y - 6), (lx, axis_y + 6), 1)
			pygame.draw.line(screen, (120, 120, 140), (world_to_screen(origin_px, scale, 0, 0)[0], axis_y - 6), (world_to_screen(origin_px, scale, 0, 0)[0], axis_y + 6), 1)

		# Simulation status and real-time data
		if sim.is_running:
			status_color = (100, 255, 100) if not sim.is_paused else (255, 255, 100)
			status_text = "RUNNING" if not sim.is_paused else "PAUSED"
			message_lines.append((f"Status: {status_text}", status_color))
			message_lines.append((f"Time: {sim.time:.2f} s", TEXT_COLOR))
			message_lines.append((f"Position: ({sim.position[0]:.1f}, {sim.position[1]:.1f}) m", TEXT_COLOR))
			message_lines.append((f"Velocity: ({sim.velocity[0]:.1f}, {sim.velocity[1]:.1f}) m/s", TEXT_COLOR))
			message_lines.append((f"Speed: {sim.get_speed():.1f} m/s", TEXT_COLOR))
			message_lines.append((f"Speed Multiplier: {speed_multiplier:.1f}x", TEXT_COLOR))
		else:
			message_lines.append(("Status: STOPPED", (200, 200, 200)))

		# Theoretical data
		if vi is not None and vi > 0:
			message_lines.append(("", TEXT_COLOR))  # Spacer
			message_lines.append(("Theoretical:", (180, 180, 190)))
			message_lines.append((f"vi = {vi:.3f} m/s", TEXT_COLOR))
			if vf is not None:
				message_lines.append((f"vf = {vf:.3f} m/s", TEXT_COLOR))
			else:
				message_lines.append(("vf = (assumed equal to vi)", (160, 160, 170)))
			if theoretical_trajectory:
				delta_y = compute_delta_y_from_speeds(vi, vf_effective if vf is not None else vi, GRAVITY)
				message_lines.append((f"Δy (land - launch) = {delta_y:.3f} m", TEXT_COLOR))
				message_lines.append((f"Time of flight = {theoretical_t_flight:.3f} s", TEXT_COLOR))
				message_lines.append((f"Range = {theoretical_range:.3f} m", (180, 255, 180)))
		else:
			message_lines.append(("Enter a valid initial speed (m/s).", (200, 200, 210)))

		# Render messages
		for i, (msg, col) in enumerate(message_lines):
			r = font.render(msg, True, col)
			screen.blit(r, (panel_rect.x + 20, info_y + i * 24))

		pygame.display.flip()

	pygame.quit()
	sys.exit(0)


if __name__ == "__main__":
	main()


