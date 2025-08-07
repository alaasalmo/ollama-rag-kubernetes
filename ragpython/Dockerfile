# Use a slim Python base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy app code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install beautifulsoup4

RUN mkdir /app/python
# Expose the port
EXPOSE 5000

# Command to run the app
ENTRYPOINT ["tail"]
CMD ["-f","/dev/null"]