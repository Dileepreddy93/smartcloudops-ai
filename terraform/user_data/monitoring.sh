#!/bin/bash
# User Data Script for Monitoring Instance (Phase 1.2)
# Installs: Prometheus + Grafana + Node Exporter

set -e

# Update system
yum update -y
yum install -y wget curl unzip

# Install Docker for easier service management
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Create monitoring user
useradd --no-create-home --shell /bin/false prometheus
useradd --no-create-home --shell /bin/false node_exporter

# Install Node Exporter (Phase 1.2.2)
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create systemd service for Node Exporter
cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Install Prometheus (Phase 1.2.1)
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xvfz prometheus-2.48.0.linux-amd64.tar.gz
cp prometheus-2.48.0.linux-amd64/prometheus /usr/local/bin/
cp prometheus-2.48.0.linux-amd64/promtool /usr/local/bin/
chown prometheus:prometheus /usr/local/bin/prometheus
chown prometheus:prometheus /usr/local/bin/promtool

# Create Prometheus directories
mkdir -p /etc/prometheus /var/lib/prometheus
chown prometheus:prometheus /etc/prometheus
chown prometheus:prometheus /var/lib/prometheus

# Configure Prometheus (Phase 1.2.1)
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:${prometheus_port:-9090}']

  - job_name: 'monitoring_node'
    static_configs:
      - targets: ['localhost:${node_exporter_port:-9100}']

  - job_name: 'application_node'
    static_configs:
      - targets: ['${application_private_ip}:${node_exporter_port:-9100}']
EOF

chown prometheus:prometheus /etc/prometheus/prometheus.yml

# Create systemd service for Prometheus
cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

# Install Grafana (Phase 1.2.3)
cat > /etc/yum.repos.d/grafana.repo << 'EOF'
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

yum install -y grafana

# Configure Grafana (secure defaults)
cat > /etc/grafana/grafana.ini << EOF
[server]
http_port = ${grafana_port:-3000}

[security]
admin_user = admin
admin_password = ${grafana_admin_password}
cookie_secure = true
strict_transport_security = true
x_content_type_options = true
x_xss_protection = true

[auth.anonymous]
enabled = false
EOF

# Install CloudWatch agent for log shipping
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/aws/ec2/${project_name}-monitoring",
            "log_stream_name": "system-logs"
          }
        ]
      }
    }
  }
}
EOF

# Start services
systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter
systemctl start prometheus
systemctl enable prometheus
systemctl start grafana-server
systemctl enable grafana-server

# Create Grafana Prometheus datasource provisioning
mkdir -p /etc/grafana/provisioning/datasources
cat > /etc/grafana/provisioning/datasources/prometheus.yaml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:${prometheus_port:-9090}
    isDefault: true
    editable: false
EOF

systemctl restart grafana-server

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Create a simple health check script
cat > /home/ec2-user/health-check.sh << 'EOF'
#!/bin/bash
echo "=== SmartCloudOps AI Monitoring Instance Health Check ==="
echo "Date: $(date)"
echo ""
echo "Services Status:"
systemctl is-active node_exporter && echo "✓ Node Exporter: Running" || echo "✗ Node Exporter: Stopped"
systemctl is-active prometheus && echo "✓ Prometheus: Running" || echo "✗ Prometheus: Stopped"
systemctl is-active grafana-server && echo "✓ Grafana: Running" || echo "✗ Grafana: Stopped"
echo ""
echo "URLs:"
echo "- Grafana: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${grafana_port:-3000}"
echo "- Prometheus: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${prometheus_port:-9090}"
echo ""
echo "Grafana Login: admin/admin123"
EOF

chmod +x /home/ec2-user/health-check.sh
chown ec2-user:ec2-user /home/ec2-user/health-check.sh

# Create welcome message
cat > /etc/motd << 'EOF'
   ____                      _    ____ _                 _  ___            
  / ___| _ __ ___   __ _ _ __| |_ / ___| | ___  _   _  __| |/ _ \ _ __  ___  
  \___ \| '_ ` _ \ / _` | '__| __| |   | |/ _ \| | | |/ _` | | | | '_ \/ __| 
   ___) | | | | | | (_| | |  | |_| |___| | (_) | |_| | (_| | |_| | |_) \__ \ 
  |____/|_| |_| |_|\__,_|_|   \__|\____|_|\___/ \__,_|\__,_|\___/| .__/|___/ 
                                                                |_|        
  
  🔍 MONITORING INSTANCE - Phase 1 Setup Complete
  
  Services:
  - Grafana Dashboard: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${grafana_port:-3000}
  - Prometheus: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):${prometheus_port:-9090}
  - Node Exporter: :${node_exporter_port:-9100}
  
  Run './health-check.sh' to check service status
  
EOF

echo "Monitoring instance setup completed successfully!" > /var/log/user-data.log
