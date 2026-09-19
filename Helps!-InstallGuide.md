

# Create Virtual Environment (1ST time olny)
> CMD: cd UPDensity_ProgramPackage && python -m venv venv && venv\Scripts\activate

# Install Requirement Tools
> CMD: pip install ultralytics opencv-python requests fastapi uvicorn mysql-connector-python

# Install FastAPI, Uvicorn
> CMD: cd UPDensity_ProgramPackage/central && python -m pip install fastapi uvicorn && python -m pip show uvicorn