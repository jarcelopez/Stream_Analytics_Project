---
stepsCompleted: [1, 2, 3]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Design and implementation of a Python-based real-time analytics pipeline for a synthetic food-delivery platform across two milestones'
research_goals: 'Plan and structure Milestone 1 so that the streaming feeds, schemas, and edge cases are well-designed to unlock Milestone 2 analytics and dashboard.'
user_name: 'Javi'
date: '2026-03-02'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-03-02
**Author:** Javi
**Research Type:** technical

---

## Research Overview

This research investigates the technical foundations for a **Python-based real-time analytics pipeline for a synthetic food-delivery platform**, with a specific focus on designing Milestone 1 (data generation and streaming) so that Milestone 2 (stream processing, storage, and dashboarding) is technically well-supported.

The methodology combines:

- Review of recent technical articles, blogs, and open-source projects for food-delivery and order-tracking streaming systems.
- Cross-checking streaming and cloud-analytics best practices from up-to-date resources on Kafka, Redpanda, Spark Structured Streaming, Azure Event Hubs, and synthetic data tooling.
- Emphasis on production-grade but course-feasible patterns (solo developer, one-week Milestone 1, Python-first).

---

## Technical Research Scope Confirmation

**Research Topic:** Design and implementation of a Python-based real-time analytics pipeline for a synthetic food-delivery platform across two milestones
**Research Goals:** Plan and structure Milestone 1 so that the streaming feeds, schemas, and edge cases are well-designed to unlock Milestone 2 analytics and dashboard.

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-03-02

---

## Technology Stack Analysis

### Programming Languages

For streaming-centric data platforms in 2026, **Python and JVM languages (Scala/Java)** dominate different parts of the stack:

- **Python** is widely used for data engineering and analytics logic, including **PySpark** for Structured Streaming pipelines, orchestration code, and dashboard backends. It aligns well with your course constraint and the broader trend that Python is the default for data workloads.[1][2]
- **Scala/Java** remain the primary languages for **core streaming engines** (Kafka, Flink, Spark internals) and some high-performance consumer/producer services, but these can typically be used via Python APIs and connectors.[1][2]

For your project:

_Popular Languages:_ Python for generator, Spark jobs (PySpark), utilities, and dashboards; minimal JVM exposure through connectors and platform configuration.[1][2]  
_Emerging Languages:_ Rust and Go are seeing adoption for high-performance streaming services and sidecars, but they are not necessary for your course constraints.  
_Language Evolution:_ Cloud-native streaming platforms increasingly expose Python-first SDKs, reducing the need to write Scala/Java for many educational and analytics-focused use cases.[1][2]  
_Performance Characteristics:_ Python, when paired with engines like Spark Structured Streaming or PyFlink, leverages the underlying JVM engine for heavy lifting, making it suitable for your throughput and educational needs while retaining developer ergonomics.[1][2]  
_Source:_ [Programming Helper 2026 Streaming Overview][1], [Spark Structured Streaming guide 2026][2]

### Development Frameworks and Libraries

Several frameworks and libraries are relevant for your pipeline:

- **PySpark (Spark Structured Streaming)** for event-time processing, windows, watermarks, and stateful aggregations.[2][4]
- **Kafka ecosystem libraries** (e.g., `kafka-python`, `confluent-kafka-python`) for generic Kafka-compatible producers/consumers, which can also target Azure Event Hubs’ Kafka-compatible endpoint.[3]
- **FastAPI** or similar Python web frameworks are often used in real-time order-analytics examples to expose APIs and dashboards, though you may use **Streamlit** for the course dashboard.[4]

_Major Frameworks:_ PySpark Structured Streaming as the primary engine for Milestone 2 processing; Python Kafka client libraries and the Azure Event Hubs Spark connector (or Kafka endpoint) to bridge generator → Event Hubs → Spark.[2][3][4]  
_Micro-frameworks:_ FastAPI or lightweight web frameworks for APIs are optional; for your scope, Streamlit or similar UI frameworks suffice for visualization.[4]  
_Evolution Trends:_ Streaming frameworks are converging on **exactly-once semantics**, better state management, and cloud-native deployment patterns (managed Kafka, Event Hubs, Kinesis, etc.).[1][2][5]  
_Ecosystem Maturity:_ Spark Structured Streaming and Kafka-compatible platforms are mature, with rich documentation and many examples, including food-delivery style projects combining Kafka with real-time analytics backends.[1][4][5]  
_Source:_ [Spark Structured Streaming 2026 guide][2], [Real-time food-delivery streaming examples][4][5]

### Database and Storage Technologies

Food-delivery analytics examples and cloud reference architectures commonly pair streaming with:

- **Cloud object storage** (e.g., ADLS Gen2, S3, Blob Storage) using **Parquet** for curated data at rest.[1][3]
- **Real-time OLAP stores** like **Apache Pinot** when low-latency analytical queries and dashboards are needed directly over streaming data.[4][5]

Your course brief specifically points to:

- **Azure Data Lake / Blob Storage + Parquet** as the primary storage target from Spark Structured Streaming jobs, aligning with common Azure Event Hubs + Databricks architectures.[1][3]

_Relational Databases:_ Traditional SQL databases are less central for the streaming path but may power auxiliary metadata or configuration; they are not required for your milestones.  
_NoSQL Databases:_ Key-value or document stores can back high-throughput online systems; your project can treat them as out-of-scope, focusing on Parquet-based analytical storage.  
_In-Memory Databases:_ Technologies like Redis appear in some real-time order-tracking stacks but are optional for this course pipeline.  
_Data Warehousing:_ On Azure, Synapse or warehouse layers often sit downstream of Parquet data for broader analytics; your Milestones can conceptually align with this pattern without implementing full warehouse integration.[1][3]  
_Source:_ [Azure Event Hubs + PySpark Structured Streaming reference][3], [order-analytics stacks using Pinot and Kafka][4][5]

### Development Tools and Platforms

Modern streaming projects typically use:

- **Git-based version control** (GitHub, GitLab) and CI/CD pipelines for deploying and testing streaming jobs.[1]
- **Databricks** or similar managed Spark platforms for running Structured Streaming jobs with cluster and connector management.[1][3]
- **Containerization (Docker)** for local development and reproducible environments in many food-delivery streaming examples.[2][4]

For your constraints:

_IDE and Editors:_ VS Code / Cursor with Python tooling is sufficient.  
_Version Control:_ Git plus GitHub is recommended even if not mandated by the course, to manage generator and Spark code.  
_Build Systems:_ Lightweight Python packaging (`requirements.txt`, possibly `pyproject.toml`) is enough; full build systems are not necessary.  
_Testing Frameworks:_ `pytest` for unit tests on generator logic and small integration checks (e.g., schema validation, edge-case injection) is appropriate.  
_Source:_ [Programming Helper streaming tooling overview][1], [Spark/delivery example repos][4][5]

### Cloud Infrastructure and Deployment

Azure-centric architectures for streaming in 2026 often look like:[1][3]

- **Ingestion:** Azure Event Hubs (optionally via its Kafka-compatible endpoint).
- **Processing:** Azure Databricks with **PySpark Structured Streaming**, using the Event Hubs Spark connector or Kafka connector.[3]
- **Storage:** Azure Data Lake Storage Gen2 / Blob Storage with Parquet outputs for curated tables.[1][3]
- **Analytics & BI:** Azure Synapse / Power BI layered on top of Parquet data.[1]

For your course project:

_Major Cloud Providers:_ Azure is the primary target given Event Hubs and Databricks; AWS and GCP patterns (Kinesis, Pub/Sub, Dataflow) are analogous but out of scope.[1][3]  
_Container Technologies:_ Docker is helpful for local generator testing but not strictly required to meet milestone goals.  
_Serverless Platforms:_ Serverless compute (e.g., Azure Functions) can host lightweight services or triggers, but your main streaming plane is Spark Structured Streaming, not Functions.  
_CDN and Edge Computing:_ Not central for this analytics-focused pipeline and can be ignored for scope control.  
_Source:_ [Azure Event Hubs + PySpark Structured Streaming guide][3]

### Technology Adoption Trends

Across sources, several trends are relevant to your design:

- **Kafka-compatible platforms** (including Redpanda and Azure Event Hubs’ Kafka endpoint) are becoming standard for event-streaming, simplifying interoperability across tools.[1][3][4]
- **Python-first data engineering** is increasingly common through PySpark, PyFlink, and rich Python client libraries.[1][2]
- **Schema-driven streaming** with AVRO and schema registries is emphasized to manage evolution and ensure compatibility across services.[2][5]
- **Synthetic data generation** tools and libraries (including AVRO-schema-driven generators) are gaining traction for testing and teaching streaming systems, aligning with your synthetic food-delivery setup.[5]

_Migration Patterns:_ Organizations continue migrating from batch to streaming-first architectures for operational analytics and personalization, often starting with Kafka-compatible pipes and expanding into richer stateful processing engines.[1][2]  
_Emerging Technologies:_ Modern synthetic data services and stream-native OLAP stores (e.g., Pinot, ClickHouse-based SaaS) feature prominently in recent real-time analytics stacks but can be conceptually referenced rather than fully implemented in your course.  
_Legacy Technology:_ Older, cron-based ETL and monolithic applications are gradually being replaced by event-driven microservices and streaming data platforms.[1][2]  
_Community Trends:_ Strong open-source activity around streaming engines and Python tooling continues, providing many examples and reference implementations you can mirror at smaller scale.[1][2][4][5]  
_Source:_ [Programming Helper 2026 Streaming Overview][1], [Spark Structured Streaming 2026 guide][2], [Azure Event Hubs integration docs][3], [food-delivery Kafka/Pinot examples][4][5]

[1]: https://www.programming-helper.com/tech/real-time-streaming-2026-apache-kafka-flink-event-driven-architecture-python
[2]: https://mayursurani.medium.com/mastering-apache-spark-structured-streaming-the-complete-guide-for-data-engineers-in-2026-f453eb74b536
[3]: https://techcommunity.microsoft.com/blog/analyticsonazure/ingest-azure-event-hub-telemetry-data-with-apache-pyspark-structured-streaming-o/3440394
[4]: https://betterprogramming.pub/building-an-order-delivery-analytics-application-with-fastapi-kafka-apache-pinot-and-dash-part-ca276a3ee631
[5]: https://marcosschroh.github.io/dataclasses-avroschema/

