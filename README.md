# Punchpass API

## Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)

## Setup Steps

1. **Clone the Project**:
    
    Clone the repository to your local machine.
    ```bash
    git clone https://github.com/victor1778/punchpass-api.git
    ```

2. **Build and Start Services**:

   Navigate to the project root and run:
   ```bash
   docker-compose up --build
   ```
   This command builds images and starts containers as defined in `docker-compose.yaml`.

3. **Access Services**:

   - **API**: Accessible at `http://localhost:8000`.

## Shutting Down

To stop and remove containers and networks, run:
```bash
docker-compose down
```
