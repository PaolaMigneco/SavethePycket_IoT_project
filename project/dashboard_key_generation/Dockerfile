# Use a base image that includes Python
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the Python script and settings file to the container
COPY generate_keys.py Requirements.txt /app/

# Make the script executable
RUN chmod +x generate_keys.py

# Install required dependencies
RUN pip install -r Requirements.txt

# Run the Python script when the container starts
CMD ["./generate_keys.py"]

