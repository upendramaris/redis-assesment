# Redis Migration Expert

The **Redis Migration Expert** is a comprehensive, self-contained Python framework designed for Principal Database Engineers to seamlessly assess and validate Redis environments for migration to Google Cloud Platform (GCP).

It acts as a zero-dependency tool—meaning it handles the installation of its own Python requirements upon the first run—and automates everything from DNS discovery and deep-metadata collection to infrastructure-as-code test validations.

## Features

- **Self-Bootstrapping**: Automatically detects and installs required dependencies (`redis`, `docker`, `dnspython`, `pandas`, `tabulate`, `requests`).
- **Advanced Discovery**: Provide a DNS name or an IP address. The script will use DNS resolution to automatically identify all IPs/nodes and attempt to map the entire cluster without manual configuration.
- **Topology Auto-Detection**: Dynamically detects the Redis topology (Standalone, Sentinel, Native Redis Cluster, or Redis Enterprise).
- **Deep Metadata Collection**: Connects to each identified node/shard to pull configuration details: Memory usage (Total, Used, RSS), Ops/sec, connection limits, Redis Version, Uptime, persistence settings (AOF), Logical Databases, and Modules (e.g. RediSearch).
- **Migration Automator**: Calculates a "Migration Complexity Score", checks GCP compatibility (e.g., Memorystore), and exports outputs in JSON, Markdown, CSV, and directly generates an Ansible Inventory file for your automation playbooks.
- **Flexible Security**: Supports TLS/SSL toggles, custom certificate paths, and standard username/password authentication mechanisms.
- **Automated Test Harness**: Includes a built-in Docker automation harness to rapidly provision test environments (Standalone, Sentinel, Cluster, Enterprise) locally, validate the logic, and tear them down—perfect for testing changes to the script safely.

## Prerequisites

Before executing the code, ensure the following prerequisites are met:

1. **Python Installation**: You must have Python 3.8 or newer installed on your machine.
   ```bash
   python3 --version
   ```
2. **Network Access**: The machine running this script must have direct network access to the target Redis cluster IPs or DNS names. Ensure no firewalls are blocking the Redis ports (default 6379, or 9443 for Enterprise).
3. **Docker (Optional)**: If you intend to run the script's automated test harness to simulate different Redis topologies locally, you must have a running Docker daemon.

*Note: The script is designed to be "zero-dependency". When you execute it for the first time, it will automatically use `pip` to install the required Python libraries (`redis`, `docker`, `dnspython`, `pandas`, `tabulate`, `requests`).*

## How to Execute the Code

You can run the script directly from your terminal or command prompt.

### 1. Assessing a Real Redis Cluster

To assess a cluster, execute the script and pass the `--host` parameter. You can optionally provide `--port`, TLS configurations, and authentication credentials.

```bash
# Basic execution using a DNS name
python3 redis_migration_expert.py --host my-redis-cluster.internal.example.com

# Execution requiring a custom port and password
python3 redis_migration_expert.py --host 10.0.0.5 --port 12000 --password "mysecretpass"

# Execution requiring TLS/SSL with specific CA Certificates
python3 redis_migration_expert.py --host secure-cluster.example.com --port 6379 --tls --ssl-ca-certs /path/to/ca.pem
```

#### Output Artifacts

Upon successful execution of the assessment, the script will generate four files in your current working directory:
- `gcp_report_user_target_cluster.md`: A human-readable Markdown summary table.
- `gcp_manifest_user_target_cluster.json`: A raw JSON manifest containing deep metrics.
- `gcp_shards_user_target_cluster.csv`: A CSV file containing a shard-by-shard breakdown.
- `ansible_inventory_user_target_cluster.ini`: An Ansible inventory file grouping nodes by role (primary/replica) for automated migrations.

### 2. Executing the Automated Test Harness

If you want to validate the tool's logic without hitting a real cluster, you can execute its built-in test harness. **(Requires Docker)**.

```bash
python3 redis_migration_expert.py --run-tests
```

This will:
1. Spin up Standalone, Sentinel, Native Cluster, and Redis Enterprise containers.
2. Run the assessment engine against each container.
3. Validate the collected data against "ground truth" expectations.
4. Output the reports.
5. Strictly destroy all created containers.

## Available Arguments

| Argument | Description |
|---|---|
| `--host` | Target cluster DNS or IP to assess. |
| `--port` | Target cluster port (Default: 6379). |
| `--tls` | Flag to enable TLS/SSL connection. |
| `--ssl-cert-reqs` | SSL cert requirements (e.g. required, none) (Default: required). |
| `--ssl-ca-certs` | Path to CA certs for SSL. |
| `--username` | Redis username for authentication. |
| `--password` | Redis password for authentication. |
| `--run-tests` | Flag to run the automated Docker test harness instead of assessing a real target. |
