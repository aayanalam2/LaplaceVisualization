import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QSpinBox, QPushButton, QTextEdit,
                             QGroupBox, QGridLayout, QDoubleSpinBox, QCheckBox,
                             QComboBox, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import subprocess
import os
import tempfile

class RenderThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, grid_size, max_iterations, tolerance, boundary_conditions, show_convergence):
        super().__init__()
        self.grid_size = grid_size
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.boundary_conditions = boundary_conditions
        self.show_convergence = show_convergence
    
    def run(self):
        try:
            self.progress.emit("Creating Manim scene...")
            
            # Create temporary file for the scene
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                scene_code = f'''
from manim import *
import numpy as np

class LaplaceScene(Scene):
    def construct(self):
        # Initialize grid
        n = {self.grid_size}
        u = np.zeros((n, n))
        
        # Set boundary conditions from GUI
        bc = {self.boundary_conditions}
        
        # Apply initial boundary conditions
        try:
            if bc['top']['type'] == 'dirichlet':
                u[0, :] = bc['top']['value']
            if bc['bottom']['type'] == 'dirichlet':
                u[-1, :] = bc['bottom']['value']
            if bc['left']['type'] == 'dirichlet':
                u[:, 0] = bc['left']['value']
            if bc['right']['type'] == 'dirichlet':
                u[:, -1] = bc['right']['value']
        except Exception as e:
            print(f"Boundary condition error: {{e}}")
        
        # Store boundary mask
        boundary_mask = np.zeros((n, n), dtype=bool)
        if bc['top']['type'] == 'dirichlet':
            boundary_mask[0, :] = True
        if bc['bottom']['type'] == 'dirichlet':
            boundary_mask[-1, :] = True
        if bc['left']['type'] == 'dirichlet':
            boundary_mask[:, 0] = True
        if bc['right']['type'] == 'dirichlet':
            boundary_mask[:, -1] = True
        
        # Create title
        title = Text("2D Laplace Equation Solution", font_size=28)
        title.to_edge(UP)
        self.add(title)
        
        # Create info display
        info_text = Text(f"Grid: {{n}}x{{n}}, Tolerance: {self.tolerance:.2e}", font_size=18)
        info_text.next_to(title, DOWN, buff=0.1)
        self.add(info_text)
        
        # Create iteration counter
        iteration_text = Text("Iteration: 0", font_size=20)
        iteration_text.next_to(info_text, DOWN, buff=0.1)
        
        # Create convergence display
        convergence_text = Text("Max Change: N/A", font_size=18)
        convergence_text.next_to(iteration_text, DOWN, buff=0.1)
        
        # Fixed domain size
        domain_size = 3.5
        
        def create_heatmap(data):
            # Ensure data is valid
            if np.all(np.isnan(data)) or np.all(np.isinf(data)):
                data = np.zeros_like(data)
            
            vmin, vmax = np.nanmin(data), np.nanmax(data)
            if abs(vmax - vmin) < 1e-12:
                vmax = vmin + 1.0
            
            normalized = (data - vmin) / (vmax - vmin)
            normalized = np.clip(normalized, 0, 1)  # Ensure values are in [0,1]
            
            squares = VGroup()
            square_size = domain_size / n
            
            for i in range(n):
                for j in range(n):
                    val = normalized[i, j]
                    
                    # Safe color interpolation
                    try:
                        if val <= 0.25:
                            color = interpolate_color(BLUE, TEAL, val * 4)
                        elif val <= 0.5:
                            color = interpolate_color(TEAL, GREEN, (val - 0.25) * 4)
                        elif val <= 0.75:
                            color = interpolate_color(GREEN, YELLOW, (val - 0.5) * 4)
                        else:
                            color = interpolate_color(YELLOW, RED, (val - 0.75) * 4)
                    except:
                        color = BLUE  # Fallback color
                    
                    square = Square(side_length=square_size)
                    square.set_fill(color, opacity=0.8)
                    square.set_stroke(WHITE, width=max(0.3/n, 0.01))
                    
                    # Position square (corrected orientation)
                    x_pos = (j - n/2 + 0.5) * square_size
                    y_pos = (n/2 - i - 0.5) * square_size  # Flipped: array[0,:] should be at top
                    square.move_to([x_pos, y_pos - 0.5, 0])
                    squares.add(square)
            
            return squares, vmin, vmax
        
        # Initial heatmap
        heatmap, vmin, vmax = create_heatmap(u)
        self.add(heatmap)
        
        # Create colorbar
        def create_colorbar(vmin, vmax):
            colorbar_group = VGroup()
            
            # Color squares
            legend_squares = VGroup()
            colors = [BLUE, TEAL, GREEN, YELLOW, RED]
            for i, color in enumerate(colors):
                square = Square(side_length=0.25)
                square.set_fill(color, opacity=0.8)
                square.set_stroke(WHITE, width=0.5)
                square.shift(RIGHT * 4.5 + UP * (2 - i * 0.4))
                legend_squares.add(square)
            
            # Value labels (corrected: blue=cold, red=hot)
            temp_labels = VGroup()
            for i in range(5):
                val = vmin + (vmax - vmin) * i / 4  # Changed: i instead of (4-i)
                label = Text(f"{{val:.1f}}", font_size=12)
                label.next_to(legend_squares[i], RIGHT, buff=0.1)
                temp_labels.add(label)
            
            colorbar_group.add(legend_squares, temp_labels)
            return colorbar_group
        
        colorbar = create_colorbar(vmin, vmax)
        self.add(colorbar)
        
        # Add current displays to scene
        self.add(iteration_text, convergence_text)
        
        # Boundary condition labels
        bc_labels = VGroup()
        try:
            if bc['top']['type'] == 'dirichlet':
                top_label = Text(f"Top: {{bc['top']['value']:.1f}}", font_size=14, color=YELLOW)
                top_label.move_to([0, 1.2, 0])
                bc_labels.add(top_label)
            
            if bc['bottom']['type'] == 'dirichlet':
                bottom_label = Text(f"Bottom: {{bc['bottom']['value']:.1f}}", font_size=14, color=YELLOW)
                bottom_label.move_to([0, -2.8, 0])
                bc_labels.add(bottom_label)
            
            if bc['left']['type'] == 'dirichlet':
                left_label = Text(f"Left: {{bc['left']['value']:.1f}}", font_size=14, color=YELLOW)
                left_label.move_to([-2.5, -0.8, 0])
                bc_labels.add(left_label)
            
            if bc['right']['type'] == 'dirichlet':
                right_label = Text(f"Right: {{bc['right']['value']:.1f}}", font_size=14, color=YELLOW)
                right_label.move_to([2.5, -0.8, 0])
                bc_labels.add(right_label)
            
            self.add(bc_labels)
        except Exception as e:
            print(f"Label creation error: {{e}}")
        
        # Solve using Jacobi iteration
        tolerance = {self.tolerance}
        max_iterations = {self.max_iterations}
        converged = False
        convergence_history = []
        
        print(f"Starting simulation with {{n}}x{{n}} grid, tolerance={{tolerance}}")
        
        for iteration in range(max_iterations):
            u_new = u.copy()
            
            # Jacobi iteration for interior points only
            for i in range(1, n-1):
                for j in range(1, n-1):
                    if not boundary_mask[i, j]:
                        u_new[i, j] = 0.25 * (u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1])
            
            # Apply Neumann boundary conditions
            try:
                if bc['top']['type'] == 'neumann':
                    u_new[0, 1:-1] = u_new[1, 1:-1] + bc['top']['value']
                if bc['bottom']['type'] == 'neumann':
                    u_new[-1, 1:-1] = u_new[-2, 1:-1] - bc['bottom']['value']
                if bc['left']['type'] == 'neumann':
                    u_new[1:-1, 0] = u_new[1:-1, 1] + bc['left']['value']
                if bc['right']['type'] == 'neumann':
                    u_new[1:-1, -1] = u_new[1:-1, -2] - bc['right']['value']
            except Exception as e:
                print(f"Neumann BC error: {{e}}")
            
            # Check convergence
            max_change = np.max(np.abs(u_new - u))
            convergence_history.append(max_change)
            
            if max_change < tolerance and iteration > 10:  # Minimum iterations
                converged = True
                final_iteration = iteration + 1
            
            u = u_new
            
            # Update visualization every few iterations
            update_freq = max(1, max_iterations // 25)  # Show ~25 frames
            if iteration % update_freq == 0 or converged or iteration == max_iterations - 1:
                
                new_heatmap, new_vmin, new_vmax = create_heatmap(u)
                
                new_iteration_text = Text(f"Iteration: {{iteration + 1}}", font_size=20)
                new_iteration_text.next_to(info_text, DOWN, buff=0.1)
                
                new_convergence_text = Text(f"Max Change: {{max_change:.2e}}", font_size=18)
                new_convergence_text.next_to(new_iteration_text, DOWN, buff=0.1)
                
                # Simple transform without complex colorbar updates
                self.play(
                    Transform(heatmap, new_heatmap),
                    Transform(iteration_text, new_iteration_text),
                    Transform(convergence_text, new_convergence_text),
                    run_time=0.3
                )
                
                print(f"Iteration {{iteration+1}}: max_change = {{max_change:.2e}}")
            
            if converged:
                print(f"Converged after {{final_iteration}} iterations!")
                break
        
        # Final message
        if converged:
            final_text = Text(f"Converged after {{final_iteration}} iterations!", 
                            font_size=20, color=GREEN)
        else:
            final_text = Text(f"Max iterations ({{max_iterations}}) reached", 
                            font_size=20, color=ORANGE)
        
        final_text.to_edge(DOWN)
        self.play(Write(final_text))
        
        # Show convergence plot if requested
        if {self.show_convergence} and len(convergence_history) > 2:
            self.wait(1)
            
            # Clear screen for convergence plot
            self.clear()
            
            plot_title = Text("Convergence History", font_size=32)
            plot_title.to_edge(UP)
            self.add(plot_title)
            
            try:
                # Simple convergence plot
                max_conv = max(convergence_history)
                min_conv = min([x for x in convergence_history if x > 0] + [tolerance])
                
                # Create simple axes without complex scaling
                axes = Axes(
                    x_range=[0, len(convergence_history), max(1, len(convergence_history)//5)],
                    y_range=[min_conv/10, max_conv*2, 1],
                    x_length=8,
                    y_length=5,
                    axis_config={{"color": WHITE}}
                )
                axes.shift(DOWN * 0.5)
                self.add(axes)
                
                # Plot points
                points = []
                for i, val in enumerate(convergence_history):
                    if val > 0:  # Only positive values
                        point = axes.coords_to_point(i, max(val, min_conv/10))
                        points.append(point)
                
                if len(points) > 1:
                    convergence_curve = VMobject()
                    convergence_curve.set_points_as_corners(points)
                    convergence_curve.set_color(BLUE)
                    self.add(convergence_curve)
                
                # Add labels
                conv_label = Text("Convergence History", font_size=16, color=BLUE)
                conv_label.next_to(axes, UP)
                self.add(conv_label)
                
            except Exception as e:
                print(f"Convergence plot error: {{e}}")
                error_text = Text("Convergence plot failed", font_size=24, color=RED)
                error_text.move_to(ORIGIN)
                self.add(error_text)
        
        self.wait(2)
        print("Animation completed successfully!")
'''
                f.write(scene_code)
                temp_file = f.name
            
            self.progress.emit("Running Manim renderer...")
            
            # Run manim with error handling
            cmd = ['manim', '-pqh', temp_file, 'LaplaceScene']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
            
            if result.returncode != 0:
                error_msg = f"Manim failed with return code {result.returncode}\\n"
                error_msg += f"STDOUT: {result.stdout}\\n"
                error_msg += f"STDERR: {result.stderr}"
                self.error.emit(error_msg)
            else:
                self.finished.emit()
                
        except subprocess.TimeoutExpired:
            self.error.emit("Manim rendering timed out after 5 minutes")
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")

class LaplaceVisualizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Laplace Equation Visualizer")
        self.setGeometry(100, 100, 600, 500)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Title
        title = QLabel("2D Laplace Equation Visualizer")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Solver parameters tab
        solver_tab = QWidget()
        solver_layout = QVBoxLayout(solver_tab)
        
        # Grid and convergence parameters
        params_group = QGroupBox("Solver Parameters")
        params_layout = QGridLayout(params_group)
        
        # Grid size (reduced max to prevent timeout)
        params_layout.addWidget(QLabel("Grid Size:"), 0, 0)
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(10, 100)  # Reduced from 200
        self.grid_size_spin.setValue(30)       # Reduced from 50
        params_layout.addWidget(self.grid_size_spin, 0, 1)
        
        # Max iterations (reduced)
        params_layout.addWidget(QLabel("Max Iterations:"), 1, 0)
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(10, 1000)  # Reduced from 5000
        self.iterations_spin.setValue(200)       # Reduced from 1000
        params_layout.addWidget(self.iterations_spin, 1, 1)
        
        # Tolerance
        params_layout.addWidget(QLabel("Convergence Tolerance:"), 2, 0)
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(1e-6, 1e-2)  # Relaxed from 1e-8
        self.tolerance_spin.setValue(1e-4)        # Relaxed from 1e-5
        self.tolerance_spin.setDecimals(8)
        self.tolerance_spin.setSingleStep(1e-5)
        params_layout.addWidget(self.tolerance_spin, 2, 1)
        
        # Show convergence plot
        self.show_convergence_check = QCheckBox("Show convergence plot")
        self.show_convergence_check.setChecked(True)
        params_layout.addWidget(self.show_convergence_check, 3, 0, 1, 2)
        
        solver_layout.addWidget(params_group)
        tabs.addTab(solver_tab, "Solver")
        
        # Boundary conditions tab
        bc_tab = QWidget()
        bc_layout = QVBoxLayout(bc_tab)
        
        self.boundary_widgets = {}
        
        for edge, name in [('top', 'Top'), ('bottom', 'Bottom'), ('left', 'Left'), ('right', 'Right')]:
            edge_group = QGroupBox(f"{name} Boundary")
            edge_layout = QGridLayout(edge_group)
            
            # Boundary type
            edge_layout.addWidget(QLabel("Type:"), 0, 0)
            type_combo = QComboBox()
            type_combo.addItems(["Dirichlet (Fixed Value)", "Neumann (Fixed Gradient)"])
            edge_layout.addWidget(type_combo, 0, 1)
            
            # Boundary value
            edge_layout.addWidget(QLabel("Value:"), 1, 0)
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-1000, 1000)
            value_spin.setValue(0 if edge in ['bottom', 'left', 'right'] else 100)
            edge_layout.addWidget(value_spin, 1, 1)
            
            self.boundary_widgets[edge] = {'type': type_combo, 'value': value_spin}
            bc_layout.addWidget(edge_group)
        
        tabs.addTab(bc_tab, "Boundary Conditions")
        
        layout.addWidget(tabs)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.render_button = QPushButton("Generate Visualization")
        self.render_button.clicked.connect(self.start_render)
        button_layout.addWidget(self.render_button)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Ready to generate visualization")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.render_thread = None
    
    def get_boundary_conditions(self):
        bc = {}
        for edge, widgets in self.boundary_widgets.items():
            bc_type = 'dirichlet' if widgets['type'].currentIndex() == 0 else 'neumann'
            bc_value = widgets['value'].value()
            bc[edge] = {'type': bc_type, 'value': bc_value}
        return bc
    
    def start_render(self):
        if self.render_thread and self.render_thread.isRunning():
            return
        
        self.render_button.setEnabled(False)
        self.status_label.setText("Starting render...")
        
        grid_size = self.grid_size_spin.value()
        max_iterations = self.iterations_spin.value()
        tolerance = self.tolerance_spin.value()
        boundary_conditions = self.get_boundary_conditions()
        show_convergence = self.show_convergence_check.isChecked()
        
        self.render_thread = RenderThread(grid_size, max_iterations, tolerance, 
                                        boundary_conditions, show_convergence)
        self.render_thread.finished.connect(self.on_render_finished)
        self.render_thread.error.connect(self.on_render_error)
        self.render_thread.progress.connect(self.on_progress)
        self.render_thread.start()
    
    def on_progress(self, message):
        self.status_label.setText(message)
    
    def on_render_finished(self):
        self.render_button.setEnabled(True)
        self.status_label.setText("Animation completed! Check the media folder for output.")
    
    def on_render_error(self, error_msg):
        self.render_button.setEnabled(True)
        self.status_label.setText(f"Error occurred - check console for details")
        print("MANIM ERROR:")
        print(error_msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LaplaceVisualizerGUI()
    window.show()
    sys.exit(app.exec_())