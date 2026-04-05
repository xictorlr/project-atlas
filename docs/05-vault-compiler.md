# Vault compiler

Define how raw data becomes a linked Markdown wiki with stable structure.

## Document intent

This document supports implementation of Project Atlas.
It should be treated as a living reference that informs code, prompts, tests, and operator workflows.

## Executive summary

- The product should behave like a knowledge compiler rather than a thin retrieval UI.
- The vault is a product surface and an integration contract.
- Every major workflow should produce inspectable artifacts.
- External agent runtimes should be isolated behind adapters and feature flags.
- Deterministic checks and evals are as important as model quality.

## Core glossary

- **Workspace**: A tenant-scoped area containing sources, a vault, indexes, outputs, jobs, and policies.
- **Source**: A user-provided or imported artifact such as an article, PDF, repository, image set, dataset, or transcript.
- **Manifest**: A structured record describing what was ingested, from where, when, and how it was normalized.
- **Vault**: The Markdown knowledge base on disk, organized for both machine maintenance and human browsing in Obsidian.
- **Compiler**: The pipeline that converts raw and normalized source data into linked notes, indexes, and derived artifacts.
- **Entity**: A real-world object such as a person, company, project, paper, dataset, or product tracked in the vault.
- **Concept**: An abstract topic synthesized from multiple sources and represented as an article in the vault.
- **Evidence pack**: A structured bundle of source excerpts, note references, and ranking metadata used to ground answers.
- **Output artifact**: A generated report, deck, image, simulation package, or publishable page derived from vault content.
- **Health check**: A deterministic or model-assisted review that detects stale links, missing metadata, contradictions, or integrity gaps.

## Canonical requirements

- REQ-001: The system must handle **workspace creation** with explicit expectations for correctness.
- REQ-002: The system must handle **workspace creation** with explicit expectations for groundedness.
- REQ-003: The system must handle **workspace creation** with explicit expectations for coverage.
- REQ-004: The system must handle **workspace creation** with explicit expectations for clarity.
- REQ-005: The system must handle **workspace creation** with explicit expectations for latency.
- REQ-006: The system must handle **source upload** with explicit expectations for correctness.
- REQ-007: The system must handle **source upload** with explicit expectations for groundedness.
- REQ-008: The system must handle **source upload** with explicit expectations for coverage.
- REQ-009: The system must handle **source upload** with explicit expectations for clarity.
- REQ-010: The system must handle **source upload** with explicit expectations for latency.
- REQ-011: The system must handle **web clipping import** with explicit expectations for correctness.
- REQ-012: The system must handle **web clipping import** with explicit expectations for groundedness.
- REQ-013: The system must handle **web clipping import** with explicit expectations for coverage.
- REQ-014: The system must handle **web clipping import** with explicit expectations for clarity.
- REQ-015: The system must handle **web clipping import** with explicit expectations for latency.
- REQ-016: The system must handle **git repository ingest** with explicit expectations for correctness.
- REQ-017: The system must handle **git repository ingest** with explicit expectations for groundedness.
- REQ-018: The system must handle **git repository ingest** with explicit expectations for coverage.
- REQ-019: The system must handle **git repository ingest** with explicit expectations for clarity.
- REQ-020: The system must handle **git repository ingest** with explicit expectations for latency.
- REQ-021: The system must handle **dataset ingest** with explicit expectations for correctness.
- REQ-022: The system must handle **dataset ingest** with explicit expectations for groundedness.
- REQ-023: The system must handle **dataset ingest** with explicit expectations for coverage.
- REQ-024: The system must handle **dataset ingest** with explicit expectations for clarity.
- REQ-025: The system must handle **dataset ingest** with explicit expectations for latency.
- REQ-026: The system must handle **image ingest** with explicit expectations for correctness.
- REQ-027: The system must handle **image ingest** with explicit expectations for groundedness.
- REQ-028: The system must handle **image ingest** with explicit expectations for coverage.
- REQ-029: The system must handle **image ingest** with explicit expectations for clarity.
- REQ-030: The system must handle **image ingest** with explicit expectations for latency.
- REQ-031: The system must handle **OCR fallback** with explicit expectations for correctness.
- REQ-032: The system must handle **OCR fallback** with explicit expectations for groundedness.
- REQ-033: The system must handle **OCR fallback** with explicit expectations for coverage.
- REQ-034: The system must handle **OCR fallback** with explicit expectations for clarity.
- REQ-035: The system must handle **OCR fallback** with explicit expectations for latency.
- REQ-036: The system must handle **metadata extraction** with explicit expectations for correctness.
- REQ-037: The system must handle **metadata extraction** with explicit expectations for groundedness.
- REQ-038: The system must handle **metadata extraction** with explicit expectations for coverage.
- REQ-039: The system must handle **metadata extraction** with explicit expectations for clarity.
- REQ-040: The system must handle **metadata extraction** with explicit expectations for latency.
- REQ-041: The system must handle **chunking** with explicit expectations for correctness.
- REQ-042: The system must handle **chunking** with explicit expectations for groundedness.
- REQ-043: The system must handle **chunking** with explicit expectations for coverage.
- REQ-044: The system must handle **chunking** with explicit expectations for clarity.
- REQ-045: The system must handle **chunking** with explicit expectations for latency.
- REQ-046: The system must handle **deduplication** with explicit expectations for correctness.
- REQ-047: The system must handle **deduplication** with explicit expectations for groundedness.
- REQ-048: The system must handle **deduplication** with explicit expectations for coverage.
- REQ-049: The system must handle **deduplication** with explicit expectations for clarity.
- REQ-050: The system must handle **deduplication** with explicit expectations for latency.
- REQ-051: The system must handle **source note generation** with explicit expectations for correctness.
- REQ-052: The system must handle **source note generation** with explicit expectations for groundedness.
- REQ-053: The system must handle **source note generation** with explicit expectations for coverage.
- REQ-054: The system must handle **source note generation** with explicit expectations for clarity.
- REQ-055: The system must handle **source note generation** with explicit expectations for latency.
- REQ-056: The system must handle **entity note generation** with explicit expectations for correctness.
- REQ-057: The system must handle **entity note generation** with explicit expectations for groundedness.
- REQ-058: The system must handle **entity note generation** with explicit expectations for coverage.
- REQ-059: The system must handle **entity note generation** with explicit expectations for clarity.
- REQ-060: The system must handle **entity note generation** with explicit expectations for latency.
- REQ-061: The system must handle **concept article synthesis** with explicit expectations for correctness.
- REQ-062: The system must handle **concept article synthesis** with explicit expectations for groundedness.
- REQ-063: The system must handle **concept article synthesis** with explicit expectations for coverage.
- REQ-064: The system must handle **concept article synthesis** with explicit expectations for clarity.
- REQ-065: The system must handle **concept article synthesis** with explicit expectations for latency.
- REQ-066: The system must handle **timeline synthesis** with explicit expectations for correctness.
- REQ-067: The system must handle **timeline synthesis** with explicit expectations for groundedness.
- REQ-068: The system must handle **timeline synthesis** with explicit expectations for coverage.
- REQ-069: The system must handle **timeline synthesis** with explicit expectations for clarity.
- REQ-070: The system must handle **timeline synthesis** with explicit expectations for latency.
- REQ-071: The system must handle **backlink generation** with explicit expectations for correctness.
- REQ-072: The system must handle **backlink generation** with explicit expectations for groundedness.
- REQ-073: The system must handle **backlink generation** with explicit expectations for coverage.
- REQ-074: The system must handle **backlink generation** with explicit expectations for clarity.
- REQ-075: The system must handle **backlink generation** with explicit expectations for latency.
- REQ-076: The system must handle **index note generation** with explicit expectations for correctness.
- REQ-077: The system must handle **index note generation** with explicit expectations for groundedness.
- REQ-078: The system must handle **index note generation** with explicit expectations for coverage.
- REQ-079: The system must handle **index note generation** with explicit expectations for clarity.
- REQ-080: The system must handle **index note generation** with explicit expectations for latency.
- REQ-081: The system must handle **vault diff review** with explicit expectations for correctness.
- REQ-082: The system must handle **vault diff review** with explicit expectations for groundedness.
- REQ-083: The system must handle **vault diff review** with explicit expectations for coverage.
- REQ-084: The system must handle **vault diff review** with explicit expectations for clarity.
- REQ-085: The system must handle **vault diff review** with explicit expectations for latency.
- REQ-086: The system must handle **manual approval queue** with explicit expectations for correctness.
- REQ-087: The system must handle **manual approval queue** with explicit expectations for groundedness.
- REQ-088: The system must handle **manual approval queue** with explicit expectations for coverage.
- REQ-089: The system must handle **manual approval queue** with explicit expectations for clarity.
- REQ-090: The system must handle **manual approval queue** with explicit expectations for latency.
- REQ-091: The system must handle **job retry** with explicit expectations for correctness.
- REQ-092: The system must handle **job retry** with explicit expectations for groundedness.
- REQ-093: The system must handle **job retry** with explicit expectations for coverage.
- REQ-094: The system must handle **job retry** with explicit expectations for clarity.
- REQ-095: The system must handle **job retry** with explicit expectations for latency.
- REQ-096: The system must handle **job cancel** with explicit expectations for correctness.
- REQ-097: The system must handle **job cancel** with explicit expectations for groundedness.
- REQ-098: The system must handle **job cancel** with explicit expectations for coverage.
- REQ-099: The system must handle **job cancel** with explicit expectations for clarity.
- REQ-100: The system must handle **job cancel** with explicit expectations for latency.
- REQ-101: The system must handle **lexical search** with explicit expectations for correctness.
- REQ-102: The system must handle **lexical search** with explicit expectations for groundedness.
- REQ-103: The system must handle **lexical search** with explicit expectations for coverage.
- REQ-104: The system must handle **lexical search** with explicit expectations for clarity.
- REQ-105: The system must handle **lexical search** with explicit expectations for latency.
- REQ-106: The system must handle **semantic search optional** with explicit expectations for correctness.
- REQ-107: The system must handle **semantic search optional** with explicit expectations for groundedness.
- REQ-108: The system must handle **semantic search optional** with explicit expectations for coverage.
- REQ-109: The system must handle **semantic search optional** with explicit expectations for clarity.
- REQ-110: The system must handle **semantic search optional** with explicit expectations for latency.
- REQ-111: The system must handle **graph traversal** with explicit expectations for correctness.
- REQ-112: The system must handle **graph traversal** with explicit expectations for groundedness.
- REQ-113: The system must handle **graph traversal** with explicit expectations for coverage.
- REQ-114: The system must handle **graph traversal** with explicit expectations for clarity.
- REQ-115: The system must handle **graph traversal** with explicit expectations for latency.
- REQ-116: The system must handle **query understanding** with explicit expectations for correctness.
- REQ-117: The system must handle **query understanding** with explicit expectations for groundedness.
- REQ-118: The system must handle **query understanding** with explicit expectations for coverage.
- REQ-119: The system must handle **query understanding** with explicit expectations for clarity.
- REQ-120: The system must handle **query understanding** with explicit expectations for latency.
- REQ-121: The system must handle **citation formatting** with explicit expectations for correctness.
- REQ-122: The system must handle **citation formatting** with explicit expectations for groundedness.
- REQ-123: The system must handle **citation formatting** with explicit expectations for coverage.
- REQ-124: The system must handle **citation formatting** with explicit expectations for clarity.
- REQ-125: The system must handle **citation formatting** with explicit expectations for latency.
- REQ-126: The system must handle **answer generation** with explicit expectations for correctness.
- REQ-127: The system must handle **answer generation** with explicit expectations for groundedness.
- REQ-128: The system must handle **answer generation** with explicit expectations for coverage.
- REQ-129: The system must handle **answer generation** with explicit expectations for clarity.
- REQ-130: The system must handle **answer generation** with explicit expectations for latency.
- REQ-131: The system must handle **brief generation** with explicit expectations for correctness.
- REQ-132: The system must handle **brief generation** with explicit expectations for groundedness.
- REQ-133: The system must handle **brief generation** with explicit expectations for coverage.
- REQ-134: The system must handle **brief generation** with explicit expectations for clarity.
- REQ-135: The system must handle **brief generation** with explicit expectations for latency.
- REQ-136: The system must handle **slide deck generation** with explicit expectations for correctness.
- REQ-137: The system must handle **slide deck generation** with explicit expectations for groundedness.
- REQ-138: The system must handle **slide deck generation** with explicit expectations for coverage.
- REQ-139: The system must handle **slide deck generation** with explicit expectations for clarity.
- REQ-140: The system must handle **slide deck generation** with explicit expectations for latency.
- REQ-141: The system must handle **matplotlib export** with explicit expectations for correctness.
- REQ-142: The system must handle **matplotlib export** with explicit expectations for groundedness.
- REQ-143: The system must handle **matplotlib export** with explicit expectations for coverage.
- REQ-144: The system must handle **matplotlib export** with explicit expectations for clarity.
- REQ-145: The system must handle **matplotlib export** with explicit expectations for latency.
- REQ-146: The system must handle **web publish** with explicit expectations for correctness.
- REQ-147: The system must handle **web publish** with explicit expectations for groundedness.
- REQ-148: The system must handle **web publish** with explicit expectations for coverage.
- REQ-149: The system must handle **web publish** with explicit expectations for clarity.
- REQ-150: The system must handle **web publish** with explicit expectations for latency.
- REQ-151: The system must handle **obsidian sync** with explicit expectations for correctness.
- REQ-152: The system must handle **obsidian sync** with explicit expectations for groundedness.
- REQ-153: The system must handle **obsidian sync** with explicit expectations for coverage.
- REQ-154: The system must handle **obsidian sync** with explicit expectations for clarity.
- REQ-155: The system must handle **obsidian sync** with explicit expectations for latency.
- REQ-156: The system must handle **download export** with explicit expectations for correctness.
- REQ-157: The system must handle **download export** with explicit expectations for groundedness.
- REQ-158: The system must handle **download export** with explicit expectations for coverage.
- REQ-159: The system must handle **download export** with explicit expectations for clarity.
- REQ-160: The system must handle **download export** with explicit expectations for latency.
- REQ-161: The system must handle **workspace sharing** with explicit expectations for correctness.
- REQ-162: The system must handle **workspace sharing** with explicit expectations for groundedness.
- REQ-163: The system must handle **workspace sharing** with explicit expectations for coverage.
- REQ-164: The system must handle **workspace sharing** with explicit expectations for clarity.
- REQ-165: The system must handle **workspace sharing** with explicit expectations for latency.
- REQ-166: The system must handle **role management** with explicit expectations for correctness.
- REQ-167: The system must handle **role management** with explicit expectations for groundedness.
- REQ-168: The system must handle **role management** with explicit expectations for coverage.
- REQ-169: The system must handle **role management** with explicit expectations for clarity.
- REQ-170: The system must handle **role management** with explicit expectations for latency.
- REQ-171: The system must handle **billing limits** with explicit expectations for correctness.
- REQ-172: The system must handle **billing limits** with explicit expectations for groundedness.
- REQ-173: The system must handle **billing limits** with explicit expectations for coverage.
- REQ-174: The system must handle **billing limits** with explicit expectations for clarity.
- REQ-175: The system must handle **billing limits** with explicit expectations for latency.
- REQ-176: The system must handle **usage metering** with explicit expectations for correctness.
- REQ-177: The system must handle **usage metering** with explicit expectations for groundedness.
- REQ-178: The system must handle **usage metering** with explicit expectations for coverage.
- REQ-179: The system must handle **usage metering** with explicit expectations for clarity.
- REQ-180: The system must handle **usage metering** with explicit expectations for latency.
- REQ-181: The system must handle **admin dashboard** with explicit expectations for correctness.
- REQ-182: The system must handle **admin dashboard** with explicit expectations for groundedness.
- REQ-183: The system must handle **admin dashboard** with explicit expectations for coverage.
- REQ-184: The system must handle **admin dashboard** with explicit expectations for clarity.
- REQ-185: The system must handle **admin dashboard** with explicit expectations for latency.
- REQ-186: The system must handle **audit log viewer** with explicit expectations for correctness.
- REQ-187: The system must handle **audit log viewer** with explicit expectations for groundedness.
- REQ-188: The system must handle **audit log viewer** with explicit expectations for coverage.
- REQ-189: The system must handle **audit log viewer** with explicit expectations for clarity.
- REQ-190: The system must handle **audit log viewer** with explicit expectations for latency.
- REQ-191: The system must handle **health check dashboard** with explicit expectations for correctness.
- REQ-192: The system must handle **health check dashboard** with explicit expectations for groundedness.
- REQ-193: The system must handle **health check dashboard** with explicit expectations for coverage.
- REQ-194: The system must handle **health check dashboard** with explicit expectations for clarity.
- REQ-195: The system must handle **health check dashboard** with explicit expectations for latency.
- REQ-196: The system must handle **evaluation dashboard** with explicit expectations for correctness.
- REQ-197: The system must handle **evaluation dashboard** with explicit expectations for groundedness.
- REQ-198: The system must handle **evaluation dashboard** with explicit expectations for coverage.
- REQ-199: The system must handle **evaluation dashboard** with explicit expectations for clarity.
- REQ-200: The system must handle **evaluation dashboard** with explicit expectations for latency.
- REQ-201: The system must handle **deerflow adapter** with explicit expectations for correctness.
- REQ-202: The system must handle **deerflow adapter** with explicit expectations for groundedness.
- REQ-203: The system must handle **deerflow adapter** with explicit expectations for coverage.
- REQ-204: The system must handle **deerflow adapter** with explicit expectations for clarity.
- REQ-205: The system must handle **deerflow adapter** with explicit expectations for latency.
- REQ-206: The system must handle **hermes bridge** with explicit expectations for correctness.
- REQ-207: The system must handle **hermes bridge** with explicit expectations for groundedness.
- REQ-208: The system must handle **hermes bridge** with explicit expectations for coverage.
- REQ-209: The system must handle **hermes bridge** with explicit expectations for clarity.
- REQ-210: The system must handle **hermes bridge** with explicit expectations for latency.
- REQ-211: The system must handle **mirofish simulation** with explicit expectations for correctness.
- REQ-212: The system must handle **mirofish simulation** with explicit expectations for groundedness.
- REQ-213: The system must handle **mirofish simulation** with explicit expectations for coverage.
- REQ-214: The system must handle **mirofish simulation** with explicit expectations for clarity.
- REQ-215: The system must handle **mirofish simulation** with explicit expectations for latency.
- REQ-216: The system must handle **MCP connectors** with explicit expectations for correctness.
- REQ-217: The system must handle **MCP connectors** with explicit expectations for groundedness.
- REQ-218: The system must handle **MCP connectors** with explicit expectations for coverage.
- REQ-219: The system must handle **MCP connectors** with explicit expectations for clarity.
- REQ-220: The system must handle **MCP connectors** with explicit expectations for latency.
- REQ-221: The system must handle **scheduled jobs** with explicit expectations for correctness.
- REQ-222: The system must handle **scheduled jobs** with explicit expectations for groundedness.
- REQ-223: The system must handle **scheduled jobs** with explicit expectations for coverage.
- REQ-224: The system must handle **scheduled jobs** with explicit expectations for clarity.
- REQ-225: The system must handle **scheduled jobs** with explicit expectations for latency.
- REQ-226: The system must handle **notifications** with explicit expectations for correctness.
- REQ-227: The system must handle **notifications** with explicit expectations for groundedness.
- REQ-228: The system must handle **notifications** with explicit expectations for coverage.
- REQ-229: The system must handle **notifications** with explicit expectations for clarity.
- REQ-230: The system must handle **notifications** with explicit expectations for latency.
- REQ-231: The system must handle **public link sharing** with explicit expectations for correctness.
- REQ-232: The system must handle **public link sharing** with explicit expectations for groundedness.
- REQ-233: The system must handle **public link sharing** with explicit expectations for coverage.
- REQ-234: The system must handle **public link sharing** with explicit expectations for clarity.
- REQ-235: The system must handle **public link sharing** with explicit expectations for latency.
- REQ-236: The system must handle **private workspace mode** with explicit expectations for correctness.
- REQ-237: The system must handle **private workspace mode** with explicit expectations for groundedness.
- REQ-238: The system must handle **private workspace mode** with explicit expectations for coverage.
- REQ-239: The system must handle **private workspace mode** with explicit expectations for clarity.
- REQ-240: The system must handle **private workspace mode** with explicit expectations for latency.
- REQ-241: The system must handle **retention policy** with explicit expectations for correctness.
- REQ-242: The system must handle **retention policy** with explicit expectations for groundedness.
- REQ-243: The system must handle **retention policy** with explicit expectations for coverage.
- REQ-244: The system must handle **retention policy** with explicit expectations for clarity.
- REQ-245: The system must handle **retention policy** with explicit expectations for latency.
- REQ-246: The system must handle **backup restore** with explicit expectations for correctness.
- REQ-247: The system must handle **backup restore** with explicit expectations for groundedness.
- REQ-248: The system must handle **backup restore** with explicit expectations for coverage.
- REQ-249: The system must handle **backup restore** with explicit expectations for clarity.
- REQ-250: The system must handle **backup restore** with explicit expectations for latency.

## User perspectives

### Solo researcher

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the solo researcher workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the solo researcher workflow.

### Founder

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the founder workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the founder workflow.

### Analyst

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the analyst workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the analyst workflow.

### Consultant

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the consultant workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the consultant workflow.

### Editorial lead

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the editorial lead workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the editorial lead workflow.

### Policy team member

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the policy team member workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the policy team member workflow.

### Lab operator

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the lab operator workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the lab operator workflow.

### Workspace admin

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the workspace admin workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the workspace admin workflow.

### Reviewer

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the reviewer workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the reviewer workflow.

### Observer

- Primary job: use Project Atlas to transform messy source material into reusable knowledge and outputs.
- Key expectation: the system explains what it ingested, what it generated, and how reliable the result is for the observer workflow.
- Main risk: hidden automation or unstable artifacts that create distrust for the observer workflow.

## Service view

### Web App

- Responsibility: provide the narrowest useful contract for the web app layer.
- Inputs: typed requests, events, or files relevant to the web app layer.
- Outputs: records, artifacts, or side effects owned by the web app layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the web app layer.

### Api Service

- Responsibility: provide the narrowest useful contract for the api service layer.
- Inputs: typed requests, events, or files relevant to the api service layer.
- Outputs: records, artifacts, or side effects owned by the api service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the api service layer.

### Worker Service

- Responsibility: provide the narrowest useful contract for the worker service layer.
- Inputs: typed requests, events, or files relevant to the worker service layer.
- Outputs: records, artifacts, or side effects owned by the worker service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the worker service layer.

### Scheduler

- Responsibility: provide the narrowest useful contract for the scheduler layer.
- Inputs: typed requests, events, or files relevant to the scheduler layer.
- Outputs: records, artifacts, or side effects owned by the scheduler layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the scheduler layer.

### Search Service

- Responsibility: provide the narrowest useful contract for the search service layer.
- Inputs: typed requests, events, or files relevant to the search service layer.
- Outputs: records, artifacts, or side effects owned by the search service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the search service layer.

### Publish Service

- Responsibility: provide the narrowest useful contract for the publish service layer.
- Inputs: typed requests, events, or files relevant to the publish service layer.
- Outputs: records, artifacts, or side effects owned by the publish service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the publish service layer.

### Vault Sync Service

- Responsibility: provide the narrowest useful contract for the vault sync service layer.
- Inputs: typed requests, events, or files relevant to the vault sync service layer.
- Outputs: records, artifacts, or side effects owned by the vault sync service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the vault sync service layer.

### Adapter Service

- Responsibility: provide the narrowest useful contract for the adapter service layer.
- Inputs: typed requests, events, or files relevant to the adapter service layer.
- Outputs: records, artifacts, or side effects owned by the adapter service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the adapter service layer.

### Admin Service

- Responsibility: provide the narrowest useful contract for the admin service layer.
- Inputs: typed requests, events, or files relevant to the admin service layer.
- Outputs: records, artifacts, or side effects owned by the admin service layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the admin service layer.

### Metrics Pipeline

- Responsibility: provide the narrowest useful contract for the metrics pipeline layer.
- Inputs: typed requests, events, or files relevant to the metrics pipeline layer.
- Outputs: records, artifacts, or side effects owned by the metrics pipeline layer.
- Failure policy: timeouts, retries, and alerts should be explicit for the metrics pipeline layer.

## Detailed patterns

### Pattern 1: Source Acquisition

- Objective: make source acquisition observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect source acquisition.
- Outputs: identify all artifacts, records, and user-visible states produced by source acquisition.
- Deterministic layer: define what in source acquisition should not depend on model judgment.
- Model layer: define what in source acquisition may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for source acquisition.
- Metrics: define latency, quality, and operator metrics for source acquisition.

### Pattern 2: Manifest Creation

- Objective: make manifest creation observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect manifest creation.
- Outputs: identify all artifacts, records, and user-visible states produced by manifest creation.
- Deterministic layer: define what in manifest creation should not depend on model judgment.
- Model layer: define what in manifest creation may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for manifest creation.
- Metrics: define latency, quality, and operator metrics for manifest creation.

### Pattern 3: Text Extraction

- Objective: make text extraction observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect text extraction.
- Outputs: identify all artifacts, records, and user-visible states produced by text extraction.
- Deterministic layer: define what in text extraction should not depend on model judgment.
- Model layer: define what in text extraction may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for text extraction.
- Metrics: define latency, quality, and operator metrics for text extraction.

### Pattern 4: Image Handling

- Objective: make image handling observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect image handling.
- Outputs: identify all artifacts, records, and user-visible states produced by image handling.
- Deterministic layer: define what in image handling should not depend on model judgment.
- Model layer: define what in image handling may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for image handling.
- Metrics: define latency, quality, and operator metrics for image handling.

### Pattern 5: Repository Import

- Objective: make repository import observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect repository import.
- Outputs: identify all artifacts, records, and user-visible states produced by repository import.
- Deterministic layer: define what in repository import should not depend on model judgment.
- Model layer: define what in repository import may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for repository import.
- Metrics: define latency, quality, and operator metrics for repository import.

### Pattern 6: Compiler Planning

- Objective: make compiler planning observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect compiler planning.
- Outputs: identify all artifacts, records, and user-visible states produced by compiler planning.
- Deterministic layer: define what in compiler planning should not depend on model judgment.
- Model layer: define what in compiler planning may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for compiler planning.
- Metrics: define latency, quality, and operator metrics for compiler planning.

### Pattern 7: Note Generation

- Objective: make note generation observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect note generation.
- Outputs: identify all artifacts, records, and user-visible states produced by note generation.
- Deterministic layer: define what in note generation should not depend on model judgment.
- Model layer: define what in note generation may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for note generation.
- Metrics: define latency, quality, and operator metrics for note generation.

### Pattern 8: Backlink Maintenance

- Objective: make backlink maintenance observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect backlink maintenance.
- Outputs: identify all artifacts, records, and user-visible states produced by backlink maintenance.
- Deterministic layer: define what in backlink maintenance should not depend on model judgment.
- Model layer: define what in backlink maintenance may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for backlink maintenance.
- Metrics: define latency, quality, and operator metrics for backlink maintenance.

### Pattern 9: Search Indexing

- Objective: make search indexing observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect search indexing.
- Outputs: identify all artifacts, records, and user-visible states produced by search indexing.
- Deterministic layer: define what in search indexing should not depend on model judgment.
- Model layer: define what in search indexing may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for search indexing.
- Metrics: define latency, quality, and operator metrics for search indexing.

### Pattern 10: Answer Planning

- Objective: make answer planning observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect answer planning.
- Outputs: identify all artifacts, records, and user-visible states produced by answer planning.
- Deterministic layer: define what in answer planning should not depend on model judgment.
- Model layer: define what in answer planning may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for answer planning.
- Metrics: define latency, quality, and operator metrics for answer planning.

### Pattern 11: Deck Generation

- Objective: make deck generation observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect deck generation.
- Outputs: identify all artifacts, records, and user-visible states produced by deck generation.
- Deterministic layer: define what in deck generation should not depend on model judgment.
- Model layer: define what in deck generation may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for deck generation.
- Metrics: define latency, quality, and operator metrics for deck generation.

### Pattern 12: Publish Rendering

- Objective: make publish rendering observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect publish rendering.
- Outputs: identify all artifacts, records, and user-visible states produced by publish rendering.
- Deterministic layer: define what in publish rendering should not depend on model judgment.
- Model layer: define what in publish rendering may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for publish rendering.
- Metrics: define latency, quality, and operator metrics for publish rendering.

### Pattern 13: Workspace Sharing

- Objective: make workspace sharing observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect workspace sharing.
- Outputs: identify all artifacts, records, and user-visible states produced by workspace sharing.
- Deterministic layer: define what in workspace sharing should not depend on model judgment.
- Model layer: define what in workspace sharing may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for workspace sharing.
- Metrics: define latency, quality, and operator metrics for workspace sharing.

### Pattern 14: Policy Enforcement

- Objective: make policy enforcement observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect policy enforcement.
- Outputs: identify all artifacts, records, and user-visible states produced by policy enforcement.
- Deterministic layer: define what in policy enforcement should not depend on model judgment.
- Model layer: define what in policy enforcement may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for policy enforcement.
- Metrics: define latency, quality, and operator metrics for policy enforcement.

### Pattern 15: Adapter Invocation

- Objective: make adapter invocation observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect adapter invocation.
- Outputs: identify all artifacts, records, and user-visible states produced by adapter invocation.
- Deterministic layer: define what in adapter invocation should not depend on model judgment.
- Model layer: define what in adapter invocation may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for adapter invocation.
- Metrics: define latency, quality, and operator metrics for adapter invocation.

### Pattern 16: Simulation Launch

- Objective: make simulation launch observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect simulation launch.
- Outputs: identify all artifacts, records, and user-visible states produced by simulation launch.
- Deterministic layer: define what in simulation launch should not depend on model judgment.
- Model layer: define what in simulation launch may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for simulation launch.
- Metrics: define latency, quality, and operator metrics for simulation launch.

### Pattern 17: Health Check Reporting

- Objective: make health check reporting observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect health check reporting.
- Outputs: identify all artifacts, records, and user-visible states produced by health check reporting.
- Deterministic layer: define what in health check reporting should not depend on model judgment.
- Model layer: define what in health check reporting may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for health check reporting.
- Metrics: define latency, quality, and operator metrics for health check reporting.

### Pattern 18: Operator Triage

- Objective: make operator triage observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect operator triage.
- Outputs: identify all artifacts, records, and user-visible states produced by operator triage.
- Deterministic layer: define what in operator triage should not depend on model judgment.
- Model layer: define what in operator triage may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for operator triage.
- Metrics: define latency, quality, and operator metrics for operator triage.

### Pattern 19: Backup Restore

- Objective: make backup restore observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect backup restore.
- Outputs: identify all artifacts, records, and user-visible states produced by backup restore.
- Deterministic layer: define what in backup restore should not depend on model judgment.
- Model layer: define what in backup restore may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for backup restore.
- Metrics: define latency, quality, and operator metrics for backup restore.

### Pattern 20: Audit Export

- Objective: make audit export observable, testable, and easy to review.
- Inputs: identify all source records, configs, and policies that affect audit export.
- Outputs: identify all artifacts, records, and user-visible states produced by audit export.
- Deterministic layer: define what in audit export should not depend on model judgment.
- Model layer: define what in audit export may use synthesis, ranking, or summarization.
- Failure handling: define retries, escalation, and partial-result policy for audit export.
- Metrics: define latency, quality, and operator metrics for audit export.

## Implementation matrix

- TASK-001: workspace creation belongs to the **MVP** track and has a default owner in **backend**.
- TASK-002: source upload belongs to the **v1 hardening** track and has a default owner in **data**.
- TASK-003: web clipping import belongs to the **enterprise readiness** track and has a default owner in **product**.
- TASK-004: git repository ingest belongs to the **premium workflows** track and has a default owner in **design**.
- TASK-005: dataset ingest belongs to the **foundation** track and has a default owner in **ops**.
- TASK-006: image ingest belongs to the **MVP** track and has a default owner in **frontend**.
- TASK-007: OCR fallback belongs to the **v1 hardening** track and has a default owner in **backend**.
- TASK-008: metadata extraction belongs to the **enterprise readiness** track and has a default owner in **data**.
- TASK-009: chunking belongs to the **premium workflows** track and has a default owner in **product**.
- TASK-010: deduplication belongs to the **foundation** track and has a default owner in **design**.
- TASK-011: source note generation belongs to the **MVP** track and has a default owner in **ops**.
- TASK-012: entity note generation belongs to the **v1 hardening** track and has a default owner in **frontend**.
- TASK-013: concept article synthesis belongs to the **enterprise readiness** track and has a default owner in **backend**.
- TASK-014: timeline synthesis belongs to the **premium workflows** track and has a default owner in **data**.
- TASK-015: backlink generation belongs to the **foundation** track and has a default owner in **product**.
- TASK-016: index note generation belongs to the **MVP** track and has a default owner in **design**.
- TASK-017: vault diff review belongs to the **v1 hardening** track and has a default owner in **ops**.
- TASK-018: manual approval queue belongs to the **enterprise readiness** track and has a default owner in **frontend**.
- TASK-019: job retry belongs to the **premium workflows** track and has a default owner in **backend**.
- TASK-020: job cancel belongs to the **foundation** track and has a default owner in **data**.
- TASK-021: lexical search belongs to the **MVP** track and has a default owner in **product**.
- TASK-022: semantic search optional belongs to the **v1 hardening** track and has a default owner in **design**.
- TASK-023: graph traversal belongs to the **enterprise readiness** track and has a default owner in **ops**.
- TASK-024: query understanding belongs to the **premium workflows** track and has a default owner in **frontend**.
- TASK-025: citation formatting belongs to the **foundation** track and has a default owner in **backend**.
- TASK-026: answer generation belongs to the **MVP** track and has a default owner in **data**.
- TASK-027: brief generation belongs to the **v1 hardening** track and has a default owner in **product**.
- TASK-028: slide deck generation belongs to the **enterprise readiness** track and has a default owner in **design**.
- TASK-029: matplotlib export belongs to the **premium workflows** track and has a default owner in **ops**.
- TASK-030: web publish belongs to the **foundation** track and has a default owner in **frontend**.
- TASK-031: obsidian sync belongs to the **MVP** track and has a default owner in **backend**.
- TASK-032: download export belongs to the **v1 hardening** track and has a default owner in **data**.
- TASK-033: workspace sharing belongs to the **enterprise readiness** track and has a default owner in **product**.
- TASK-034: role management belongs to the **premium workflows** track and has a default owner in **design**.
- TASK-035: billing limits belongs to the **foundation** track and has a default owner in **ops**.
- TASK-036: usage metering belongs to the **MVP** track and has a default owner in **frontend**.
- TASK-037: admin dashboard belongs to the **v1 hardening** track and has a default owner in **backend**.
- TASK-038: audit log viewer belongs to the **enterprise readiness** track and has a default owner in **data**.
- TASK-039: health check dashboard belongs to the **premium workflows** track and has a default owner in **product**.
- TASK-040: evaluation dashboard belongs to the **foundation** track and has a default owner in **design**.
- TASK-041: deerflow adapter belongs to the **MVP** track and has a default owner in **ops**.
- TASK-042: hermes bridge belongs to the **v1 hardening** track and has a default owner in **frontend**.
- TASK-043: mirofish simulation belongs to the **enterprise readiness** track and has a default owner in **backend**.
- TASK-044: MCP connectors belongs to the **premium workflows** track and has a default owner in **data**.
- TASK-045: scheduled jobs belongs to the **foundation** track and has a default owner in **product**.
- TASK-046: notifications belongs to the **MVP** track and has a default owner in **design**.
- TASK-047: public link sharing belongs to the **v1 hardening** track and has a default owner in **ops**.
- TASK-048: private workspace mode belongs to the **enterprise readiness** track and has a default owner in **frontend**.
- TASK-049: retention policy belongs to the **premium workflows** track and has a default owner in **backend**.
- TASK-050: backup restore belongs to the **foundation** track and has a default owner in **data**.

## Acceptance checklist

- User-facing behavior is described with stable terminology.
- Underlying contracts are typed and versioned where needed.
- Artifacts and logs are inspectable.
- Security and privacy boundaries are documented.
- Tests or evals exist for the risky path.
- Operational procedures cover retries, rollback, and support.
- Vault impact and Obsidian compatibility are reviewed.
- External adapter behavior is isolated and feature-flagged.

## Question bank for Claude Code

- For **workspace creation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **source upload**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **web clipping import**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **git repository ingest**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **dataset ingest**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **image ingest**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **OCR fallback**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **metadata extraction**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **chunking**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **deduplication**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **source note generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **entity note generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **concept article synthesis**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **timeline synthesis**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **backlink generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **index note generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **vault diff review**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **manual approval queue**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **job retry**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **job cancel**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **lexical search**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **semantic search optional**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **graph traversal**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **query understanding**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **citation formatting**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **answer generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **brief generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **slide deck generation**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **matplotlib export**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **web publish**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **obsidian sync**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **download export**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **workspace sharing**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **role management**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **billing limits**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **usage metering**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **admin dashboard**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **audit log viewer**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **health check dashboard**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?
- For **evaluation dashboard**, ask: what is the source of truth, what is the schema, and how does a human inspect the result?

## Appendix: implementation reminders

- Prefer repository evidence over assumptions.
- Prefer thin adapters over framework lock-in.
- Prefer markdown portability over clever custom formats.
- Prefer stable identifiers and redirects over mass renaming.
- Prefer deterministic validation before LLM enhancement.
- Prefer explicit artifacts over hidden chat state.
- Review web app through the lens of correctness before marking a major change complete.
- Review web app through the lens of groundedness before marking a major change complete.
- Review web app through the lens of coverage before marking a major change complete.
- Review web app through the lens of clarity before marking a major change complete.
- Review web app through the lens of latency before marking a major change complete.
- Review web app through the lens of cost before marking a major change complete.
- Review web app through the lens of portability before marking a major change complete.
- Review web app through the lens of auditability before marking a major change complete.
- Review web app through the lens of security before marking a major change complete.
- Review web app through the lens of operator usability before marking a major change complete.
- Review api service through the lens of correctness before marking a major change complete.
- Review api service through the lens of groundedness before marking a major change complete.
- Review api service through the lens of coverage before marking a major change complete.
- Review api service through the lens of clarity before marking a major change complete.
- Review api service through the lens of latency before marking a major change complete.
- Review api service through the lens of cost before marking a major change complete.
- Review api service through the lens of portability before marking a major change complete.
- Review api service through the lens of auditability before marking a major change complete.
- Review api service through the lens of security before marking a major change complete.
- Review api service through the lens of operator usability before marking a major change complete.
- Review worker service through the lens of correctness before marking a major change complete.
- Review worker service through the lens of groundedness before marking a major change complete.
- Review worker service through the lens of coverage before marking a major change complete.
- Review worker service through the lens of clarity before marking a major change complete.
- Review worker service through the lens of latency before marking a major change complete.
- Review worker service through the lens of cost before marking a major change complete.
- Review worker service through the lens of portability before marking a major change complete.
- Review worker service through the lens of auditability before marking a major change complete.
- Review worker service through the lens of security before marking a major change complete.
- Review worker service through the lens of operator usability before marking a major change complete.
- Review scheduler through the lens of correctness before marking a major change complete.
- Review scheduler through the lens of groundedness before marking a major change complete.
- Review scheduler through the lens of coverage before marking a major change complete.
- Review scheduler through the lens of clarity before marking a major change complete.
- Review scheduler through the lens of latency before marking a major change complete.
- Review scheduler through the lens of cost before marking a major change complete.
- Review scheduler through the lens of portability before marking a major change complete.
- Review scheduler through the lens of auditability before marking a major change complete.
- Review scheduler through the lens of security before marking a major change complete.
- Review scheduler through the lens of operator usability before marking a major change complete.
- Review search service through the lens of correctness before marking a major change complete.
- Review search service through the lens of groundedness before marking a major change complete.
- Review search service through the lens of coverage before marking a major change complete.
- Review search service through the lens of clarity before marking a major change complete.
- Review search service through the lens of latency before marking a major change complete.
- Review search service through the lens of cost before marking a major change complete.
- Review search service through the lens of portability before marking a major change complete.
- Review search service through the lens of auditability before marking a major change complete.
- Review search service through the lens of security before marking a major change complete.
- Review search service through the lens of operator usability before marking a major change complete.
- Review publish service through the lens of correctness before marking a major change complete.
- Review publish service through the lens of groundedness before marking a major change complete.
- Review publish service through the lens of coverage before marking a major change complete.
- Review publish service through the lens of clarity before marking a major change complete.
- Review publish service through the lens of latency before marking a major change complete.
- Review publish service through the lens of cost before marking a major change complete.
- Review publish service through the lens of portability before marking a major change complete.
- Review publish service through the lens of auditability before marking a major change complete.
- Review publish service through the lens of security before marking a major change complete.
- Review publish service through the lens of operator usability before marking a major change complete.
- Review vault sync service through the lens of correctness before marking a major change complete.
- Review vault sync service through the lens of groundedness before marking a major change complete.
- Review vault sync service through the lens of coverage before marking a major change complete.
- Review vault sync service through the lens of clarity before marking a major change complete.
- Review vault sync service through the lens of latency before marking a major change complete.
- Review vault sync service through the lens of cost before marking a major change complete.
- Review vault sync service through the lens of portability before marking a major change complete.
- Review vault sync service through the lens of auditability before marking a major change complete.
- Review vault sync service through the lens of security before marking a major change complete.
- Review vault sync service through the lens of operator usability before marking a major change complete.
- Review adapter service through the lens of correctness before marking a major change complete.
- Review adapter service through the lens of groundedness before marking a major change complete.
- Review adapter service through the lens of coverage before marking a major change complete.
- Review adapter service through the lens of clarity before marking a major change complete.
- Review adapter service through the lens of latency before marking a major change complete.
- Review adapter service through the lens of cost before marking a major change complete.
- Review adapter service through the lens of portability before marking a major change complete.
- Review adapter service through the lens of auditability before marking a major change complete.
- Review adapter service through the lens of security before marking a major change complete.
- Review adapter service through the lens of operator usability before marking a major change complete.
- Review admin service through the lens of correctness before marking a major change complete.
- Review admin service through the lens of groundedness before marking a major change complete.
- Review admin service through the lens of coverage before marking a major change complete.
- Review admin service through the lens of clarity before marking a major change complete.
- Review admin service through the lens of latency before marking a major change complete.
- Review admin service through the lens of cost before marking a major change complete.
- Review admin service through the lens of portability before marking a major change complete.
- Review admin service through the lens of auditability before marking a major change complete.
- Review admin service through the lens of security before marking a major change complete.
- Review admin service through the lens of operator usability before marking a major change complete.
- Review metrics pipeline through the lens of correctness before marking a major change complete.
- Review metrics pipeline through the lens of groundedness before marking a major change complete.
- Review metrics pipeline through the lens of coverage before marking a major change complete.
- Review metrics pipeline through the lens of clarity before marking a major change complete.
- Review metrics pipeline through the lens of latency before marking a major change complete.
- Review metrics pipeline through the lens of cost before marking a major change complete.
- Review metrics pipeline through the lens of portability before marking a major change complete.
- Review metrics pipeline through the lens of auditability before marking a major change complete.
- Review metrics pipeline through the lens of security before marking a major change complete.
- Review metrics pipeline through the lens of operator usability before marking a major change complete.
