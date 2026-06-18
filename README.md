# VYOMA

Vyoma is an AI-powered sports training app that helps athletes improve their performance by comparing their posture and movements with professional players. It provides real-time feedback, personalized corrections, and rewards for progress, making training more engaging and effective.


## Features

- Python-based codebase
- Clear, modular structure 
- Tests and CI
  

## Requirements

- Python 3.8+ 
- pip
 

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/milli-404/VYOMA.git
   cd VYOMA
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .venv\Scripts\activate     # Windows (PowerShell)
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```





## Tests

```bash
pip install -r requirements-dev.txt   # if you have a separate dev requirements file
pytest
```

If you use another test runner or have CI configured, update this section accordingly.


## Development

- Follow the project's coding style and linting rules.
- To run linters/formatters:

  ```bash
  black .
  flake8 .
  ```


## Contributing

Contributions are welcome! Please open issues for bugs or feature requests, and create pull requests for proposed changes. Add any required contribution guidelines or a CONTRIBUTING.md file.


## License

This repository does not include a license file yet. Consider adding a LICENSE (for example, MIT) to make the project's license explicit.


