# 2D Laplace Equation Visualizer

A sophisticated GUI application that creates animated visualizations of the 2D Laplace equation solution using the Jacobi iterative method. Built with PyQt5 and Manim, this tool provides an intuitive interface for exploring partial differential equations through interactive animations.

## Features

### 🎥 **Animated Visualizations**
- Real-time heatmap animation showing temperature/potential field evolution
- Color-coded visualization with blue (cold) to red (hot) gradient
- Iteration counter and convergence tracking during solving process
- Optional convergence history plots

### ⚙️ **Flexible Solver Parameters**
- Adjustable grid size (10×10 to 100×100)
- Configurable maximum iterations (10 to 1000)
- Customizable convergence tolerance (1e-6 to 1e-2)
- Optimized for performance with reasonable computational limits

### 🎯 **Boundary Condition Support**
- **Dirichlet boundaries**: Fixed temperature/potential values
- **Neumann boundaries**: Fixed gradient (heat flux) conditions
- Independent configuration for all four edges (top, bottom, left, right)
- Visual boundary condition labels in animations

### 🖥️ **User-Friendly Interface**
- Tabbed interface separating solver parameters and boundary conditions
- Real-time status updates during rendering
- Error handling with informative messages
- Threaded rendering to prevent GUI freezing

## Prerequisites

### Required Dependencies
```bash
# Core Python packages
pip install PyQt5 numpy
```

**Manim Installation**: Follow the complete installation guide at [manim.community](https://docs.manim.community/en/stable/installation.html) - includes all system dependencies and platform-specific instructions.

### Verification
Test your installations:
```bash
python -c "import PyQt5; print('PyQt5 OK')"
manim --version
```

## Installation

1. **Clone or download** the application files
2. **Install dependencies** as listed above
3. **Run the application**:
   ```bash
   python laplace_visualizer.py
   ```

## Usage Guide

### Getting Started

1. **Launch the application**
   ```bash
   python laplace_visualizer.py
   ```

2. **Configure solver parameters** (Solver tab):
   - **Grid Size**: Computational resolution (30×30 recommended for quick results)
   - **Max Iterations**: Maximum solving steps (200 default)
   - **Tolerance**: Convergence precision (1e-4 default)
   - **Show Convergence Plot**: Enable/disable convergence analysis

3. **Set boundary conditions** (Boundary Conditions tab):
   - Choose **Dirichlet** for fixed values (e.g., fixed temperature)
   - Choose **Neumann** for fixed gradients (e.g., insulation/heat flux)
   - Set numerical values for each boundary

4. **Generate visualization**:
   - Click "Generate Visualization"
   - Monitor progress in the status bar
   - Find output video in the `media/` folder

### Example Scenarios

#### **Heat Conduction Problem**
- Top boundary: Dirichlet, 100°C (hot surface)
- Bottom boundary: Dirichlet, 0°C (cold surface)  
- Left/Right boundaries: Neumann, 0 (insulated sides)

#### **Electrostatic Potential**
- Left boundary: Dirichlet, -50V
- Right boundary: Dirichlet, +50V
- Top/Bottom boundaries: Neumann, 0 (no charge flow)

#### **Steady-State Diffusion**
- All boundaries: Dirichlet with different concentrations
- Observe how the field equilibrates between boundary values

## Technical Details

### Numerical Method
- **Jacobi Iteration**: Stable, parallelizable finite difference method
- **5-point Stencil**: Second-order accurate discretization
- **Convergence Criterion**: Maximum absolute change between iterations

### Boundary Condition Implementation
- **Dirichlet**: Direct value assignment `u[boundary] = value`
- **Neumann**: Finite difference approximation `∂u/∂n = value`

## Output Files

Generated animations are saved in:
```
media/videos/[temp_filename]/[quality]/LaplaceScene.mp4
```

The application automatically opens the output directory upon completion.

## Troubleshooting

### Common Issues

**"Command 'manim' not found"**
- Ensure Manim is properly installed: `pip install manim`
- Check PATH configuration for command-line access

**"Rendering timed out"**
- Reduce grid size or maximum iterations
- Check system resources (CPU/memory usage)

**"PyQt5 import error"**
- Install PyQt5: `pip install PyQt5`
- On Linux: `sudo apt install python3-pyqt5`

**Animation appears frozen**
- Rendering is processor-intensive; check status bar for progress
- Large grids may take several minutes to complete

### Performance Optimization

- Start with smaller grids (20×20) for testing
- Use relaxed tolerance (1e-3 to 1e-4) for faster convergence
- Disable convergence plots for quicker rendering
- Close other resource-intensive applications during rendering

## Support

For technical issues:
1. Verify all dependencies are correctly installed
2. Check system compatibility (Python 3.7+)
3. Review error messages in the console output
4. Test with default parameters first

---

**Created for mathematical visualization and education** 🔬📊