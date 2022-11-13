# Define the base image as alpine linux with python 3.9
FROM python:3.9-slim
# Create and set the working directory in the image
WORKDIR /app
# Copy the dependencies of the microservice into the working directory
COPY requirements.txt .
# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy the application code into the subdirectory service
COPY service ./service/
# Switch to a non-root user
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia
# Expose port 8080 to the outside
EXPOSE 8080
# Run the accounts microservice on port 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]