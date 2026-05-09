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

- Python 3.8+
- (Optional but recommended) Direct network access to the target Redis instances.
- (Optional) A running Docker daemon is required *only* if you intend to run the automated test harness.

## Usage

You can run the script via the command line. Upon execution, the script will self-install any missing dependencies.

### Assessing a Real Redis Cluster

To assess a cluster, you must provide the `--host` parameter. You can optionally provide `--port`, TLS configurations, and credentials.

```bash
# Basic assessment using DNS
python3 redis_migration_expert.py --host my-redis-cluster.internal.example.com --port 6379

# Assessment requiring a password and custom port
python3 redis_migration_expert.py --host 10.0.0.5 --port 12000 --password "mysecretpass"

# Assessment requiring TLS/SSL with specific Certificates
python3 redis_migration_expert.py --host secure-cluster.example.com --port 6379 --tls --ssl-ca-certs /path/to/ca.pem
```

#### Output Artifacts

After running the assessment, the script will automatically generate the following reports in your current directory:
- `gcp_report_user_target_cluster.md`: A Markdown-formatted, human-readable summary table.
- `gcp_manifest_user_target_cluster.json`: The raw JSON dump of all shards and configurations.
- `gcp_shards_user_target_cluster.csv`: A CSV representation of the nodes.
- `ansible_inventory_user_target_cluster.ini`: An auto-generated Ansible inventory grouping nodes into primaries and replicas to be used with standard automation playbooks.

### Running the Test Harness

If you want to validate the assessment engine's logic against local mocked environments, use the `--run-tests` flag. Ensure Docker is running.

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
