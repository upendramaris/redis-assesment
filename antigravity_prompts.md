# Antigravity Prompts for Redis Migration Assessment Tool

Use the following prompts sequentially or combined in Antigravity to generate your comprehensive Redis migration assessment script.

## Prompt 1: The "Discovery & Connectivity" Engine
This prompt focuses on the "Advanced" requirement: starting with just a DNS name and handling the various connection security layers.

**Prompt:** "Write a Python script using redis-py and dnspython that acts as a Redis discovery engine. The script should:
- Accept a cluster DNS name and custom port as input.
- Resolve the DNS to identify all associated IP addresses/nodes.
- Implement a flexible connection function that handles optional TLS/SSL (with a toggle for ssl_cert_reqs) and Password/Username authentication.
- Once connected, automatically detect the setup type: Redis Enterprise, Native Redis Cluster, or Sentinel.
- Print a summary of the connectivity status for each node to ensure the execution environment has the required direct access."

## Prompt 2: The "Deep Assessment" Data Collector
This prompt focuses on the "GCP-style" assessment, pulling metadata for shards, memory, and modules.

**Prompt:** "Develop a Python-based assessment tool for Redis Enterprise that generates a comprehensive report for migration planning. For each identified node and shard, the tool must:
- Execute INFO ALL and CLUSTER SLOTS to extract: Total Memory, Used Memory, RSS, and Ops per second.
- Identify all Logical Databases (e.g., DB 0, DB 1, etc.) and their respective key counts.
- Query the Redis Enterprise API (or use MODULE LIST) to identify active modules like RediSearch, RedisJSON, and RedisBloom.
- Verify persistence settings, specifically confirming AOF (Append Only File) status and configuration details.
- Detect the Redis Version and uptime for every shard.
- Output the final data into a structured Markdown table or JSON file that can be used as a migration manifest."

## Prompt 3: The "Migration Automator" (Shard-Level)
This prompt addresses your need to automate the gathering process for individual shard migration to Google Cloud.

**Prompt:** "Create an automation wrapper for the Redis Assessment tool that prepares shards for individual migration to GCP. The script should:
- Group shards by their primary/replica roles.
- Calculate a 'Migration Complexity Score' for each shard based on its size and activity (ops/sec).
- Generate a CSV list where each row represents a single shard with its specific connection string, memory footprint, and logical database mapping.
- Include a 'Checklist' column for GCP compatibility (e.g., checking if the version is supported by Memorystore or Cloud Bigtable)."

## Key Technical Considerations for your Script
Since you are dealing with Redis Enterprise, here are a few tips to ensure the code generated is "DBA-grade":
- **REST API vs. Redis Protocol:** While the Redis protocol (redis-cli style) is great for shard data, Redis Enterprise provides a REST API (usually on port 9443) that is often better for gathering cluster-wide metadata like license info, multi-tenancy settings, and endpoint definitions.
- **The "Advanced" Resolution:** If you provide a single Cluster Endpoint DNS, the script should use the CLUSTER NODES command. Even if you connect to one node, that command returns the IPs and IDs of every other node in the cluster.
- **Handling Logical DBs:** Note that in a native Redis Cluster, multiple logical databases (DB 0 through DB N) are not supported (only DB 0 is allowed). However, Redis Enterprise can emulate this or manage multiple databases differently. Your script should explicitly check the databases value in the INFO Keyspace section.

## Recommended Tooling Integration
Given your experience with Ansible and Terraform, you might want to ask the AI to:
"Convert the output of the assessment script into an Ansible Inventory file so I can automate the migration of each shard using a playbook."
This will allow you to bridge the gap between "Assessment" and "Action," much like the GCP database assessment tool does when it feeds into the Database Migration Service.