# 📊 Dependency Graph

A powerful Python tool that analyzes import dependencies in Python projects and generates beautiful SVG visualizations of module relationships.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **Automatic Project Analysis**: Automatically detects project structure and root package
- **Visualization Options**: Generate dependency graphs with customizable layout directions and algorithms
- **Configurable**: Use YAML configuration files for project-specific settings
- **Clustering Support**: Group related modules into logical clusters for better visualization
- **Easy to Use**: Simple CLI interface with sensible defaults

## 📋 Requirements

- Python 3.10+
- Graphviz (both Python package and system installation)
- PyYAML

## 🚀 Installation

```bash
# Install from PyPI
pip install dependency-graph

# Or install directly from the repository
git clone https://github.com/yourusername/dependency-graph.git
cd dependency-graph
poetry install
```

## 🔧 Usage

### Basic Usage

```bash
# Analyze current directory project
deps_graph

# Specify a project root directory
deps_graph --project-root /path/to/your/project

# Custom output filename
deps_graph --output my_dependency_diagram
```

### Advanced Options

```bash
# Change graph direction (top-to-bottom, left-to-right, etc.)
deps_graph --direction LR

# Change layout algorithm
deps_graph --engine fdp

# Use standard arrow direction (importers -> imported)
deps_graph --normal-arrows

# Verbose logging
deps_graph --verbose
```

## ⚙️ Configuration

Create a `deps.yml` file in your project root for persistent configuration:

```yaml
# Sample configuration file
root_package: my_package
cluster_mappings:
  api: API Layer
  core: Core Functionality
  utils: Utilities
  models: Data Models
```

## 📝 Command Line Options

| Option | Description |
|--------|-------------|
| `--project-root PATH` | Root directory of the project to analyze |
| `--output FILENAME` | Output filename for the diagram (without extension) |
| `--verbose`, `-v` | Enable detailed logging |
| `--direction {TB,LR,BT,RL}` | Graph layout direction |
| `--engine {dot,neato,fdp,twopi,circo}` | Graph layout algorithm |
| `--normal-arrows` | Use standard arrow direction |
| `--config PATH` | Path to YAML configuration file |
| `--root-package NAME` | Root package name (auto-detected if not specified) |

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📬 Contact

Alexander Kleimenov - nequamy@gmail.com