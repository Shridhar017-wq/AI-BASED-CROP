# Create virtual environment if it doesn't exist
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\activate

# Install requirements
Write-Host "Installing dependencies..."
pip install -r requirements.txt

# Run the app
Write-Host "Starting Flask application..."
python app.py
