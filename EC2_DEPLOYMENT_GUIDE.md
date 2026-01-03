# EC2 Deployment Guide for HRMS Application

This guide will help you host your HRMS application on an AWS EC2 instance using Docker and Docker Compose.

## Prerequisites
1. An AWS Account
2. An EC2 Instance (Recommended: t2.medium or t3.small with Ubuntu 22.04 LTS)
3. Domain Name (Optional, but recommended)

## Step 1: Prepare the EC2 Instance
Update the system and install Docker:
```bash
# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Add your user to the docker group
sudo usermod -aG docker $USER
# (Log out and log back in for this to take effect)
```

## Step 2: Protocol Support (Security Groups)
Ensure your EC2 Security Group has the following ports open:
- **SSH (22)**: For remote access
- **HTTP (80)**: For the web application
- **HTTPS (443)**: For secure access
- **Custom TCP (5000)**: If you want to access the app directly on port 5000

## Step 3: Deploy the Application
1. **Clone your repository** or upload your files to the EC2 instance using SCP/SFTP.
2. **Navigate to the project directory**:
   ```bash
   cd HR
   ```
3. **Environment setup**:
   Create a `.env` file (see `.env.example` in files created).
4. **Build and Start the containers**:
   ```bash
   docker compose up -d --build
   ```

## Step 4: Setup a Reverse Proxy (Optional but Recommended)
For production, it's better to use Nginx as a reverse proxy to handle SSL and serve the app on port 80.

```bash
sudo apt-get install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/hrms
```

Add this config:
```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/hrms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: Maintenance
- **View Logs**: `docker compose logs -f`
- **Restart App**: `docker compose restart hrms-app`
- **Update App**:
  ```bash
  git pull
  docker compose up -d --build
  ```

---
**Status**: Ready for production deployment.
