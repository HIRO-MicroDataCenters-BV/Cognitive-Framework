# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).
# Cognitive Framework Changelog

---

## [1.0.0] - 2025-06-06

### Added

- **Initial Public Release**: Launched the first public version of the Cognitive Framework.
- **Core Components**:
  - **Cogflow API**: FastAPI-based service providing REST endpoints for ML operations, including pipeline submission, monitoring, and integration with Kubeflow Pipelines and MLflow.
  - **Cognitive Charm**: Juju package automating deployment of the entire platform stack, including Kubernetes provisioning, MinIO setup, PostgreSQL configuration, and installation of Kubeflow and MLflow components.
- **Machine Learning Operations**:
  - **Dataset Registration**: Enabled registration of datasets via API and UI.
  - **Model Registration and Lifecycle Management**: Facilitated model registration, configuration, and lifecycle management.
  - **Training Orchestration**: Supported both manual and scheduled training orchestration.
  - **Evaluation Metrics and Logging**: Provided mechanisms for evaluating models and logging metrics.
- **Infrastructure and Deployment**:
  - **Persistence Layer**: Utilized PostgreSQL for data storage.
  - **Event-Driven Updates**: Integrated Kafka for handling event-driven updates.
  - **Development Environment**: Offered a Docker-based development setup and Makefile helpers.
- **Recommender Model Integration**: Introduced a recommender model with inference capabilities.
- **REST API Enhancements**: Added endpoints to fetch model suggestions and metadata.
- **Training History Dashboard**: Developed a dashboard to visualize training history and metrics.
- **Model Versioning and Serving Metrics**: Enabled tracking of model versions and associated serving metrics.
- **CI/CD Pipeline for Model Deployment**: Established a continuous integration and deployment pipeline for models.
- **Testing Framework**: Established a basic unit test framework using `pytest`.
---
