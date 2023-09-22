# Use a base image that includes Python
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the Python script and settings file to the container
COPY Sensor_doorbell.py doorbell_settings.json Requirements.txt /app/

# Make the script executable
RUN chmod +x Sensor_doorbell.py

# Install required dependencies
RUN pip install -r Requirements.txt

# Run the Python script when the container starts
CMD ["./Sensor_doorbell.py", "./doorbell_settings.json"]

