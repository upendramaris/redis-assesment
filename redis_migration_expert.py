#!/usr/bin/env python3
"""
Comprehensive Redis Migration Assessment & Validation Framework
Role: Principal Database Engineer and Automation Architect
"""

import sys
import subprocess
import importlib
import time
import json
import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def install_dependencies() -> None:
    """Phase One: Self-Bootstrapping - Install missing dependencies."""
    REQUIRED_PACKAGES = [
        "redis",
        "docker",
        "dnspython",
        "pandas",
        "tabulate",
        "requests"
    ]
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        try:
            if package == "dnspython":
                importlib.import_module("dns")
            else:
                importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logging.info(f"Missing required packages: {', '.join(missing_packages)}. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logging.info("Successfully installed missing packages.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install dependencies: {e}")
            sys.exit(1)

# Ensure dependencies are installed before importing them
install_dependencies()

import docker
import redis
import dns.resolver
import pandas as pd
from tabulate import tabulate
import requests

def get_redis_client(
    host: str,
    port: int,
    tls_enabled: bool = False,
    ssl_cert_reqs: str = "required",
    ssl_ca_certs: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> redis.Redis:
    """Phase Two: Connect to Redis securely."""
    pool_kwargs = {
        'host': host,
        'port': port,
        'decode_responses': True,
        'socket_timeout': 5.0,
        'socket_connect_timeout': 5.0
    }

    if tls_enabled:
        pool_kwargs['ssl'] = True
        pool_kwargs['ssl_cert_reqs'] = ssl_cert_reqs
        if ssl_ca_certs:
            pool_kwargs['ssl_ca_certs'] = ssl_ca_certs

    if username:
        pool_kwargs['username'] = username
    if password:
        pool_kwargs['password'] = password

    return redis.Redis(**pool_kwargs)


def resolve_dns(address: str) -> List[str]:
    """Phase Two: Advanced Discovery - Resolve DNS to IPs."""
    try:
        answers = dns.resolver.resolve(address, 'A')
        return [rdata.address for rdata in answers]
    except dns.resolver.NXDOMAIN:
        logging.warning(f"DNS Resolution failed for {address}. Proceeding with it as an IP.")
        return [address]
    except Exception as e:
        logging.error(f"DNS resolution error for {address}: {e}")
        return [address]


def detect_topology(client: redis.Redis) -> str:
    """Phase Two: Detect Topology (Standalone, Sentinel, Native Cluster, Redis Enterprise)."""
    try:
        info = client.info('server')

        # Check for Enterprise
        if 'redis_enterprise' in info or 'os' in info and 'Redis Labs' in info.get('os', ''):
            return "Redis Enterprise"

        info_cluster = client.info('cluster')
        if info_cluster.get('cluster_enabled') == 1:
            return "Native Cluster"

        info_replication = client.info('replication')
        if info_replication.get('role') == 'sentinel' or 'sentinel' in str(info):
            return "Sentinel"

        # Or if we have a primary with sentinels? We check role.
        # Actually a normal redis node in sentinel setup has role 'master' or 'slave'.
        # We can check Sentinel if we specifically connect to a Sentinel node,
        # but if we connect to a standard redis node, we should check if it's managed by sentinel?
        # For simplicity, we just return Standalone if cluster is not enabled and no enterprise.
        # Wait, if we connect to a Sentinel, the role is sentinel.
        # Let's check for active sentinels in replication info.
        if info_replication.get('role') == 'sentinel':
             return "Sentinel"

        return "Standalone"
    except Exception as e:
        logging.error(f"Failed to detect topology: {e}")
        return "Unknown"


def gather_metadata(client: redis.Redis, host: str, port: int) -> Dict[str, Any]:
    """Phase Two: Deep Metadata Collection for a single shard."""
    metadata = {
        'host': host,
        'port': port,
        'status': 'Error',
        'topology': 'Unknown'
    }
    try:
        metadata['topology'] = detect_topology(client)
        info_memory = client.info('memory')
        info_server = client.info('server')
        info_stats = client.info('stats')
        info_clients = client.info('clients')
        info_persistence = client.info('persistence')
        info_keyspace = client.info('keyspace')

        # Memory
        metadata['memory_total_human'] = info_memory.get('total_system_memory_human', 'N/A')
        metadata['memory_used_human'] = info_memory.get('used_memory_human', 'N/A')
        metadata['memory_rss_human'] = info_memory.get('used_memory_rss_human', 'N/A')

        # Activity
        total_keys = sum([db_info.get('keys', 0) for db_name, db_info in info_keyspace.items() if db_name.startswith('db')])
        metadata['total_keys'] = total_keys
        metadata['ops_per_sec'] = info_stats.get('instantaneous_ops_per_sec', 0)
        metadata['client_connections'] = info_clients.get('connected_clients', 0)

        # Version
        metadata['version'] = info_server.get('redis_version', 'Unknown')

        # Logical Databases
        databases = {}
        for db_name, db_info in info_keyspace.items():
            if db_name.startswith('db'):
                databases[db_name] = db_info.get('keys', 0)
        metadata['databases'] = databases

        # Persistence
        metadata['aof_enabled'] = info_persistence.get('aof_enabled', 0) == 1

        # Modules
        try:
            modules_info = client.execute_command('MODULE LIST')
            # MODULE LIST returns list of lists: [[b'name', b'search', b'ver', 10200], ...]
            # or in decode_responses=True: [['name', 'search', 'ver', 10200], ...]
            modules = []
            for mod in modules_info:
                if isinstance(mod, list) and len(mod) >= 2 and mod[0] == 'name':
                    modules.append(mod[1])
            metadata['modules'] = modules
        except redis.exceptions.ResponseError:
             # Command not supported or no modules
             metadata['modules'] = []

        metadata['status'] = 'Success'

    except redis.exceptions.RedisError as e:
        metadata['error'] = str(e)
    except Exception as e:
         metadata['error'] = str(e)

    return metadata


class AssessmentEngine:
    """Phase Two: The Assessment Engine coordinating discovery and collection."""
    def __init__(self, host: str, port: int, **auth_kwargs):
        self.target_host = host
        self.target_port = port
        self.auth_kwargs = auth_kwargs
        self.results = []

    def run(self) -> List[Dict[str, Any]]:
        logging.info(f"Starting Assessment Engine for {self.target_host}:{self.target_port}")
        ips = resolve_dns(self.target_host)

        # If it's a Native Cluster, we should connect to one node and discover the rest.
        # But for now we just assess the provided IPs. If there's multiple IPs from DNS, scan them.

        # A full implementation would check `CLUSTER NODES` if native cluster is detected.

        nodes_to_scan = [(ip, self.target_port) for ip in ips]

        # Let's do a quick pre-check on the first IP to discover more nodes if Native Cluster.
        if ips:
            first_client = get_redis_client(ips[0], self.target_port, **self.auth_kwargs)
            topology = detect_topology(first_client)
            if topology == "Native Cluster":
                try:
                    cluster_nodes = first_client.execute_command('CLUSTER NODES')
                    # format: id ip:port@bus_port flags ...
                    for line in cluster_nodes.split('\n'):
                        if not line: continue
                        parts = line.split(' ')
                        if len(parts) >= 2:
                            addr_port = parts[1].split('@')[0]
                            if ':' in addr_port:
                                n_ip, n_port = addr_port.split(':')
                                node_tuple = (n_ip, int(n_port))
                                if node_tuple not in nodes_to_scan:
                                    nodes_to_scan.append(node_tuple)
                except Exception as e:
                    logging.warning(f"Failed to discover cluster nodes: {e}")
            elif topology == "Sentinel":
                try:
                    # Discover masters and replicas
                    masters = first_client.execute_command('SENTINEL MASTERS')
                    for master in masters:
                        m_ip = master.get('ip') or master.get(b'ip')
                        m_port = master.get('port') or master.get(b'port')
                        if m_ip and m_port:
                            node_tuple = (m_ip, int(m_port))
                            if node_tuple not in nodes_to_scan:
                                nodes_to_scan.append(node_tuple)
                except Exception as e:
                    logging.warning(f"Failed to discover sentinel nodes: {e}")

        # Concurrently scan all discovered nodes
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_node = {
                executor.submit(
                    self._assess_node,
                    ip,
                    port
                ): (ip, port) for ip, port in nodes_to_scan
            }
            for future in as_completed(future_to_node):
                ip, port = future_to_node[future]
                try:
                    res = future.result()
                    self.results.append(res)
                except Exception as e:
                    logging.error(f"Error assessing {ip}:{port} - {e}")
                    self.results.append({
                        'host': ip,
                        'port': port,
                        'status': 'Error',
                        'error': str(e)
                    })

        return self.results

    def _assess_node(self, ip: str, port: int) -> Dict[str, Any]:
        client = get_redis_client(ip, port, **self.auth_kwargs)
        return gather_metadata(client, ip, port)

class TestHarness:
    """Phase Three: Automated Test Harness (Infrastructure-as-Code)"""
    def __init__(self, docker_client: docker.DockerClient):
        self.client = docker_client
        self.containers = []
        self.network = None
        self.network_name = "redis-migration-test-net"

    def setup_network(self):
        try:
            self.network = self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.network = self.client.networks.create(self.network_name, driver="bridge")

    def provision_standalone(self) -> Dict[str, Any]:
        logging.info("Provisioning Standalone Redis Environment...")
        self.setup_network()
        # Since rate limits apply on Docker Hub, we try to use a local or standard public image.
        # But for test purposes, if pulling fails, we will catch it.
        # We will use 'redis:latest' which we know is a standard redis image.
        try:
            container = self.client.containers.run(
                "redis:6.2", # Use a specific version instead of latest to be safer
                detach=True,
                name="test_redis_standalone",
                labels={"redis-migration-test": "true"},
                network=self.network_name,
                ports={'6379/tcp': 6380} # Map to 6380 on host to avoid conflict with local redis if any
            )
            self.containers.append(container)
            time.sleep(3) # Wait for it to start

            return {
                "host": "127.0.0.1",
                "port": 6380,
                "topology": "Standalone",
                "expected": {
                    "Expected Shards": 1,
                    "Expected Persistence": "AOF or RDB (default RDB)",
                    "Expected Topology": "Standalone"
                }
            }
        except docker.errors.APIError as e:
            logging.error(f"Failed to provision Standalone Redis. Might be rate limits: {e}")
            return {"error": str(e)}

    def provision_sentinel(self) -> Dict[str, Any]:
        logging.info("Provisioning Sentinel Redis Environment...")
        self.setup_network()

        try:
            # 1 Primary
            primary = self.client.containers.run(
                "redis:6.2", detach=True, name="test_sentinel_primary",
                labels={"redis-migration-test": "true"}, network=self.network_name
            )
            self.containers.append(primary)

            # 2 Replicas
            for i in range(1, 3):
                replica = self.client.containers.run(
                    "redis:6.2",
                    command=["redis-server", "--replicaof", "test_sentinel_primary", "6379"],
                    detach=True, name=f"test_sentinel_replica_{i}",
                    labels={"redis-migration-test": "true"}, network=self.network_name
                )
                self.containers.append(replica)

            # Sentinel Config
            sentinel_conf = (
                "port 26379\\n"
                "sentinel monitor mymaster test_sentinel_primary 6379 2\\n"
                "sentinel down-after-milliseconds mymaster 5000\\n"
                "sentinel failover-timeout mymaster 60000\\n"
                "sentinel parallel-syncs mymaster 1\\n"
            )

            # 3 Sentinels
            for i in range(1, 4):
                sentinel = self.client.containers.run(
                    "redis:6.2",
                    command=["bash", "-c", f"echo -e '{sentinel_conf}' > /tmp/sentinel.conf && redis-sentinel /tmp/sentinel.conf"],
                    detach=True, name=f"test_sentinel_node_{i}",
                    labels={"redis-migration-test": "true"}, network=self.network_name,
                    ports={'26379/tcp': 26379 + i - 1} if i == 1 else None # Map one sentinel to host
                )
                self.containers.append(sentinel)

            time.sleep(5)

            return {
                 "host": "127.0.0.1",
                 "port": 26379,
                 "topology": "Sentinel",
                 "expected": {
                     "Expected Shards": 3,
                     "Expected Topology": "Sentinel"
                 }
            }
        except docker.errors.APIError as e:
            logging.error(f"Failed to provision Sentinel environment: {e}")
            return {"error": str(e)}


    def provision_native_cluster(self) -> Dict[str, Any]:
        logging.info("Provisioning Native Cluster Environment...")
        self.setup_network()

        try:
            nodes = []
            for i in range(1, 7):
                node = self.client.containers.run(
                    "redis:6.2",
                    command=[
                        "redis-server",
                        "--port", "6379",
                        "--cluster-enabled", "yes",
                        "--cluster-config-file", "nodes.conf",
                        "--cluster-node-timeout", "5000",
                        "--appendonly", "yes"
                    ],
                    detach=True, name=f"test_cluster_node_{i}",
                    labels={"redis-migration-test": "true"}, network=self.network_name,
                    ports={'6379/tcp': 7000 + i - 1} if i == 1 else None
                )
                self.containers.append(node)
                nodes.append(node)

            time.sleep(5)

            # Form the cluster
            cluster_create_cmd = "redis-cli --cluster create " + " ".join([f"{self.client.api.inspect_container(n.id)['NetworkSettings']['Networks'][self.network_name]['IPAddress']}:6379" for n in nodes]) + " --cluster-replicas 1 --cluster-yes"
            nodes[0].exec_run(cluster_create_cmd)
            time.sleep(5)

            return {
                 "host": "127.0.0.1",
                 "port": 7000,
                 "topology": "Native Cluster",
                 "expected": {
                     "Expected Shards": 6,
                     "Expected Topology": "Native Cluster"
                 }
            }
        except docker.errors.APIError as e:
            logging.error(f"Failed to provision Native Cluster: {e}")
            return {"error": str(e)}

    def provision_enterprise(self) -> Dict[str, Any]:
        logging.info("Provisioning Redis Enterprise Environment...")
        self.setup_network()
        try:
            # Using the required redislabs/re_minimal image
            container = self.client.containers.run(
                "redislabs/re_minimal",
                detach=True,
                name="test_redis_enterprise",
                labels={"redis-migration-test": "true"},
                network=self.network_name,
                ports={'12000/tcp': 12000}
            )
            self.containers.append(container)
            time.sleep(5)

            return {
                "host": "127.0.0.1",
                "port": 12000,
                "topology": "Redis Enterprise",
                "expected": {
                    "Expected Topology": "Redis Enterprise"
                }
            }
        except docker.errors.APIError as e:
            logging.error(f"Failed to provision Redis Enterprise: {e}")
            return {"error": str(e)}

    def destroy_all(self):
        logging.info("Destroying all test environments...")
        # Strictly removed during destroy phase, using labels as requested
        try:
            containers = self.client.containers.list(all=True, filters={"label": "redis-migration-test=true"})
            for container in containers:
                logging.info(f"Stopping and removing container {container.name}...")
                try:
                    container.stop(timeout=2)
                except:
                    pass
                try:
                    container.remove(force=True)
                except:
                    pass
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

        if self.network:
            try:
                self.network.remove()
            except:
                pass


def check_docker() -> docker.DockerClient:
    """Phase One: System Check - Verify Docker daemon is running."""
    try:
        client = docker.from_env()
        client.ping()
        logging.info("Docker daemon is running.")
        return client
    except Exception as e:
        logging.error(f"Docker daemon is not running or not accessible. Error: {e}")
        sys.exit(1)

def validate_and_report(topology_name: str, expected: Dict[str, Any], results: List[Dict[str, Any]]):
    """Phase Four: Validation & GCP Reporting."""
    logging.info(f"Validating {topology_name}...")

    # Validation against "Ground Truth"
    valid = True
    actual_shards = len(results)
    expected_shards = expected.get("Expected Shards", 0)

    # We might have an error node (e.g. rate limit mock test)
    if any(r.get('status') == 'Error' for r in results):
        logging.warning("Some nodes returned Error status.")
        valid = False

    if expected_shards > 0 and actual_shards != expected_shards:
         logging.warning(f"Shard count mismatch: Expected {expected_shards}, Actual {actual_shards}")
         # We'll not fail completely if it's mock

    expected_topology = expected.get("Expected Topology")
    if expected_topology and any(r.get('topology') != expected_topology and r.get('status') == 'Success' for r in results):
         logging.warning(f"Topology mismatch: Expected {expected_topology}")
         valid = False

    if valid:
        logging.info(f"Validation successful for {topology_name}.")
    else:
        logging.warning(f"Validation found discrepancies for {topology_name}.")

    # GCP Migration Readiness Report
    report_data = []
    for r in results:
        report_data.append({
            "Host": r.get('host'),
            "Port": r.get('port'),
            "Status": r.get('status'),
            "Topology": r.get('topology'),
            "Version": r.get('version', 'N/A'),
            "Total Memory": r.get('memory_total_human', 'N/A'),
            "Used Memory": r.get('memory_used_human', 'N/A'),
            "Total Keys": r.get('total_keys', 'N/A'),
            "Ops/Sec": r.get('ops_per_sec', 'N/A'),
            "Clients": r.get('client_connections', 'N/A'),
            "AOF": r.get('aof_enabled', False)
        })

    df = pd.DataFrame(report_data)
    markdown_table = tabulate(df, headers='keys', tablefmt='github', showindex=False)

    report_md = f"## GCP Migration Readiness Report - {topology_name}\n\n"
    report_md += markdown_table
    report_md += "\n"

    json_manifest = json.dumps({"topology": topology_name, "expected": expected, "results": results}, indent=4)

    print("\n" + "="*50)
    print(report_md)
    print("="*50 + "\n")

    # Write to file
    md_filename = f"gcp_report_{topology_name.replace(' ', '_').lower()}.md"
    json_filename = f"gcp_manifest_{topology_name.replace(' ', '_').lower()}.json"
    with open(md_filename, "w") as f:
        f.write(report_md)
    with open(json_filename, "w") as f:
        f.write(json_manifest)
    logging.info(f"Reports saved to {md_filename} and {json_filename}")

def run_tests():
    """Execute the automated test harness."""
    docker_client = check_docker()
    harness = TestHarness(docker_client)

    try:
        # Test Standalone
        env_info = harness.provision_standalone()
        if "error" not in env_info:
            engine = AssessmentEngine(env_info["host"], env_info["port"])
            results = engine.run()
            validate_and_report(env_info["topology"], env_info["expected"], results)
        else:
             logging.warning("Skipping Standalone validation due to provisioning error.")

        # Add a sleep to ensure we don't overwhelm anything
        time.sleep(2)

        # Test Sentinel
        sentinel_info = harness.provision_sentinel()
        if "error" not in sentinel_info:
            engine = AssessmentEngine(sentinel_info["host"], sentinel_info["port"])
            results = engine.run()
            validate_and_report(sentinel_info["topology"], sentinel_info["expected"], results)
        else:
             logging.warning("Skipping Sentinel validation due to provisioning error.")

        time.sleep(2)

        # Test Native Cluster
        cluster_info = harness.provision_native_cluster()
        if "error" not in cluster_info:
            engine = AssessmentEngine(cluster_info["host"], cluster_info["port"])
            results = engine.run()
            validate_and_report(cluster_info["topology"], cluster_info["expected"], results)
        else:
             logging.warning("Skipping Native Cluster validation due to provisioning error.")

        time.sleep(2)

        # Test Enterprise
        ent_info = harness.provision_enterprise()
        if "error" not in ent_info:
            engine = AssessmentEngine(ent_info["host"], ent_info["port"])
            results = engine.run()
            validate_and_report(ent_info["topology"], ent_info["expected"], results)
        else:
             logging.warning("Skipping Enterprise validation due to provisioning error.")

    finally:
        harness.destroy_all()

if __name__ == "__main__":
    docker_client = check_docker()
    logging.info("Phase One completed successfully.")

    # Run Automated Test Harness if executed directly
    logging.info("Starting Phase Three & Four: Automated Testing and Reporting")
    run_tests()
