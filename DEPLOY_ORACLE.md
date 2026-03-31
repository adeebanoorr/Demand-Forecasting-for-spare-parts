# 🚀 Deployment Guide: KPCL Forecasting on Oracle VM

This guide provides step-by-step instructions for deploying the project on an Oracle Cloud Infrastructure (OCI) VM or any Linux-based virtual machine.

## 📋 Prerequisites

- **Host OS**: Oracle Linux 8/9, Ubuntu 22.04 LTS, or similar.
- **Resources**: Minimum 1 OCPU (Ampere/Intel) and 4GB RAM.
- **Tools**: Docker and Docker Compose installed.

---

## 🛠️ Step 1: Install Docker & Docker Compose

If not already installed, run these commands (for Ubuntu/Debian):

```bash
# Update package list
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

*(For Oracle Linux, use `dnf install docker-engine` and `dnf install docker-compose-plugin`.)*

---

## 📂 Step 2: Clone & Prepare

1. **Clone the repository**:
   ```bash
   git clone https://github.com/adeebanoorr/Demand-Forecasting-for-spare-parts.git
   cd Demand-Forecasting-for-spare-parts
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```

---

## ⚓ Step 3: Launch with Docker Compose

Build and start the services in detached mode:

```bash
sudo docker-compose up -d --build
```

- **Frontend**: Accessible on port **80**.
- **Backend API**: Accessible on `${VM_IP}/api`.
- **Analytics Dashboard**: Accessible on `${VM_IP}/analytics/`.

---

## 🛡️ Step 4: Firewall & VCN Security

You **MUST** open port 80 in your VM's firewall and the Oracle Cloud VCN Security List.

### 1. VM Firewall (iptables/firewalld)
If the VM is inaccessible, try opening port 80:
```bash
# For Ubuntu (ufw)
sudo ufw allow 80/tcp

# For Oracle Linux (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

### 2. OCI Security List
Go to your **VCN** in the Oracle Cloud Console:
- Find the **Security List** for your subnet.
- Add an **Ingress Rule**:
  - **Stateless**: No
  - **Source Type**: CIDR (`0.0.0.0/0`)
  - **IP Protocol**: TCP
  - **Destination Port Range**: `80`

---

## 🔄 Maintenance

### Update to Latest Version
```bash
git pull origin main
sudo docker-compose up -d --build
```

### Check Logs
```bash
sudo docker-compose logs -f backend
```

### Direct API Access
You can verify the backend health directly:
`curl http://localhost:8000/health`
