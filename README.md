# AI-Powered Network Monitoring System

A comprehensive network monitoring solution with AI-powered analytics, automated remediation, and real-time alerting. Built with Zabbix, TimescaleDB, and a modern React frontend.

## 🌟 Featuress

### 📊 Real-time Monitoring
- Host status tracking with visual indicators
- Performance metrics (CPU, Memory, Network)
- Custom metric collection and visualization

### 🤖 AI-Powered Analysis
- Automated anomaly detection
- Smart alert analysis with root cause identification
- Predictive analytics for capacity planning

### 🔔 Alert Management
- Configurable alert thresholds
- Email notifications
- Alert prioritization by severity

### 🛠️ Automated Remediation
- One-click fixes for common issues
- Custom remediation scripts
- Action history and results tracking

### 📈 Dashboard & Visualization
- Interactive charts and graphs
- Customizable time ranges (24h/7d/30d)
- Host-specific metrics view

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- Node.js 16+ (for frontend development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/molr298/network-monitoring.git
   cd network-monitoring
   ```

2. Configure environment variables:
   ```bash
   cp docker/.env.example docker/.env
   # Edit the .env file with your configuration
   ```

3. Start the services:
   ```bash
   cd docker
   docker compose up -d
   ```

4. Access the applications:
   - Frontend: http://localhost
   - Zabbix Web: http://localhost:8080 (Admin/zabbix)

## 📋 Usage Guide

### Monitoring Hosts
1. Navigate to the dashboard
2. View host status in the "Host Status" section
3. Click on a host to see detailed metrics

### Setting Up Alerts
1. Go to Alert Settings
2. Configure alert thresholds and conditions
3. Set up email notifications

### Email Notification Setup

#### Option 1: Using MailHog (Development)
MailHog is included in the Docker setup for testing email functionality without a real SMTP server.

1. **Access MailHog Web UI**:
   - Open http://localhost:8025 in your browser

2. **Configure SMTP in Application**:
   - **SMTP Server**: `mailhog`
   - **Port**: `1025`
   - **Username**: (leave blank)
   - **Password**: (leave blank)
   - **Recipients**: Any email address (emails will be captured by MailHog)

#### Option 2: Using Gmail SMTP (Production)
For production use, configure Gmail's SMTP server:

1. ***Generate App Password***:
   - Go to your Google Account > Security
   - Enable 2-Step Verification if not already enabled
   - Under "Signing in to Google," select App passwords
   - Generate a new 16-character app password

2. ***Configure SMTP in Application***:
   - **SMTP Server**: `smtp.gmail.com`
   - **Port**: `587` (TLS) or `465` (SSL)
   - **Username**: Your full Gmail address
   - **Password**: Your 16-character app password
   - **Recipients**: Comma-separated list of recipient emails

3. ***Security Note***:
   - Never commit your actual password to version control
   - Use environment variables for sensitive data
   - Consider using a dedicated email service for production

### Anomaly Detection

#### Viewing Anomalies
1. Navigate to the "Anomalies" tab in the dashboard
2. View detected anomalies with timestamps and severity
3. Click on an anomaly for detailed analysis

#### AI-Powered Analysis
1. Select an anomaly from the list
2. Click "Analyze" to get AI-powered insights including:
   - Root cause analysis
   - Impact assessment
   - Recommended actions
3. Review confidence scores for each finding

#### Anomaly Types
- **Performance Anomalies**: Unusual CPU, memory, or network usage
- **Availability Issues**: Unexpected service or host downtime
- **Configuration Drift**: Changes from baseline configurations
- **Security Incidents**: Suspicious patterns or unauthorized changes

## 🎥 Video Demos

### Quick Start & Application Overview
[Dashboard Tour](https://drive.google.com/file/d/1r0Fjbc1bVjxNoVU0hwUA6mtP9-ZOeS0P/view?usp=sharing)
