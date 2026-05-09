# Antigravity Prompts for Redis Migration Assessment Tool

Use the following prompts sequentially or combined in Antigravity to generate your comprehensive Redis migration assessment script.

## Prompt 1: Core Script and Assessment Engine

**Role:** You are a Principal Database Engineer and Automation Architect specializing in Redis Enterprise, Python, and GCP migrations.

**Objective:** Create a comprehensive, single-file Python script designed to assess Redis clusters for migration to Google Cloud Platform (GCP). This tool should function similarly to the GCP Database Assessment Tool, but specifically tailored for Redis.

**Core Requirements & Advanced Discovery:**
1. **Target Input:** The user will provide a cluster DNS name or IP address, along with a port.
2. **Auto-Resolution:** If a DNS name is provided, the script must automatically resolve it to its underlying IP addresses to identify the nodes in the cluster.
3. **Topology Auto-Detection:** The script must independently discover the topology of the target without user input. It needs to detect if it's hitting Redis Enterprise, Native Redis Cluster, Redis Sentinel, or a Standard Primary/Replica setup.
4. **Deep Node & Shard Discovery:** Once the entry point is established, the script should iterate over and identify all individual nodes and shards. The final goal is to assess each shard individually since they may be migrated individually.

**Deep Metadata Collection (Per Shard):**
For every identified shard/node, gather the following metrics and save them into a structured format:
*   **System & Hardware:** Size, Memory usage (Total, Used, RSS).
*   **Activity Metrics:** Total Keys, Operations per second, Client Connections.
*   **Versions & Config:** Specific Redis/Enterprise server version.
*   **Databases:** Automatically identify all active logical databases (e.g., DB 0, DB 1) without user input, including key counts per DB.
*   **Modules:** Detect any active Redis Enterprise modules in use (e.g., RediSearch, RedisJSON, RedisBloom) using Redis commands or endpoints (`MODULE LIST`).
*   **Persistence:** Check the persistence configuration, specifically confirming if Append Only Files (AOF) are configured.

**Connection & Security Flexibility:**
*   Implement a robust connection handler.
*   **Authentication:** Must support optional Username and Password inputs.
*   **TLS/SSL:** Must have a flexible toggle (enabled/disabled) for TLS/SSL connections. If enabled, it must allow the user to provide a path to a custom SSL certificate file.

**Environment Context:**
*   Assume the script will be executed from a machine with direct network access to all Redis nodes (no VPN/Bastion tunneling logic required in the script).

Generate the Python code that implements this core discovery and assessment engine. Use standard libraries where possible, and clearly indicate any required external libraries (like `redis` or `dnspython`).

---

## Prompt 2: Automated Gathering and Report Generation

**Role:** You are a Principal Database Engineer and Automation Architect.

**Objective:** Extend the Redis Assessment script from the previous prompt to automate the gathering process and generate professional, migration-ready documentation.

**Requirements:**
1. **Concurrency:** Since a cluster may have many shards, implement a concurrent approach (e.g., Python's `ThreadPoolExecutor`) to automate and speed up the gathering of metadata across all discovered nodes/shards.
2. **GCP Migration Readiness Report:**
    *   Aggregate all the collected data from the shards.
    *   Generate a structured document (Markdown and/or CSV) that lists every shard and its corresponding values (Size, Memory, Activity, Version, Logical DBs, Modules, Persistence, etc.).
    *   The output format should resemble professional assessment tools (like the GCP Database Assessment tool), clearly highlighting actionable data for a GCP migration plan.
3. **Output Generation:** Ensure the script automatically saves this document to the local filesystem upon completion.

Provide the complete, updated Python script combining the assessment engine with these reporting and automation features.
