# Cognitive Framework

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)  
[![Juju Charm](https://img.shields.io/badge/charm–store-cognitive-blue.svg)](https://charmhub.io/cognitive)

Cognitive Framework is an open-source, cloud-native platform delivering end-to-end ML orchestration, experiment tracking, and federated learning support. It comprises:

- **Cogflow**: A Python library and API that seamlessly integrates Kubeflow and MLflow, adds federated learning capabilities, and exposes system management endpoints.
- **Cognitive Charm**: A Juju package that automates deployment of the entire platform (including Kubernetes, storage backends, MinIO, databases, ingress, TLS, and all dependencies).

**Future Cognitive Framework**
![Cog Engine Detailed Design Future](app/static/img/CF_future.jpg?raw=true "Cog framework detailed design Future")

**Current Cognitive Framework**
![Cog Engine Detailed Design](app/static/img/cf_services.png?raw=true "Cog framework detailed design")

---

## Components

- **Cogflow Library** (cogflow package)  
  - Integrates Kubeflow Pipelines with MLflow Tracking  
  - Federated learning orchestration across multiple clusters  
  - REST API for job submission, model promotion, and monitoring  
- **Cognitive Charm** (cognitive charm)  
  - Deploys Kubernetes (if needed), MinIO, PostgreSQL, and ingress  
  - Configures storage backends and secrets  
  - Installs and configures Kubeflow and MLflow components via charms  

---

## Features

- Unified ML Ops API: Submit pipelines, track experiments, register & deploy models via Cogflow.  
- Federated Learning: Orchestrate distributed model training and aggregation.  
- Automated Deployment: One-step install of the full stack with Juju.  
- Scalable Architecture: Built on Kubernetes, supports cloud (EKS, GKE, AKS) or on-prem.  
- Observability: Integrated Cognitve UI  and training builder dashboards to Kubeflow UI and MLflow UI.  

---

## Architecture

```
┌────────────────────────────┐
│        Cogflow API         │
│  (REST endpoints & SDK)    │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐     ┌──────────────────────────┐
│  Kubeflow Pipelines Core   │◀───▶│      MLflow Server       │
│  (KFDef, Argo, Metadata)   │     │  (Tracking & Model Store)│
└────────────────────────────┘     └──────────────────────────┘
           ▲
           │
┌──────────┴───────────┐
│ Cognitive Juju Charm │
│ (K8s, MinIO, Postgres│
│  ingress, etc.) │
└──────────────────────┘
```

---

## Prerequisites

- **Juju** CLI v3.0+ with a controller bootstrapped  
- (Optional) A running **Kubernetes** cluster (v1.20+); if not present, the charm can bootstrap one via MAAS/LXD.  
- Internet access to Charmhub and container registries.  
- Minimum hardware: 32GB RAM, 8 CPU cores
---

## Installation

To install the Cognitive Framework, use the following command:
## 🧰 Juju Installation

[Juju](https://juju.is) is required to deploy the Cognitive Framework using the Cognitive Charm.

Install Juju depending on your operating system:

### 📦 Ubuntu / Debian

```bash
sudo snap install juju --classic
```

```bash
juju bootstrap
juju add-model kubeflow
juju deploy cognitive --channel=edge --trust
```  

This single command installs and configures:  
- Kubernetes control plane (if required)  
- MinIO for artifact storage  
- PostgreSQL for MLflow backend  
- Kubeflow Pipelines and MLflow services  
- Ingress and TLS certificates  

Check status with:

```bash
juju status --color
```

---

### Configure Database URL if Required

This application needs a Postgres database to store data. Set the following environment variables to configure the
database connection:

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

The database URL is configured as:

```
SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

### Environment Variables

Set the following environment variables as per your configuration:

- **Mlflow Configuration**:
    - `MLFLOW_TRACKING_URI`: URI of the Mlflow tracking server.
    - `MLFLOW_S3_ENDPOINT_URL`: Endpoint URL for the AWS S3 service.
    - `AWS_ACCESS_KEY_ID`: Access key ID for AWS S3 authentication.
    - `AWS_SECRET_ACCESS_KEY`: Secret access key for AWS S3 authentication.
    - `MINIO_ENDPOINT_URL`: Endpoint URL for the MinIO service.
    - `MINIO_ACCESS_KEY`: Access key for MinIO authentication.
    - `MINIO_SECRET_ACCESS_KEY`: Secret access key for MinIO authentication.
    - `ML_TOOL`: Name of the machine learning tool (default: "mlflow").

- **Timing Configuration**:
    - `TIMER_IN_SEC`: Interval in seconds for timed operations (default: 10).

- **Machine Learning Database Configuration**:
    - `ML_DB_USERNAME`: Username for the ML database.
    - `ML_DB_PASSWORD`: Password for the ML database.
    - `ML_DB_HOST`: Host address for the ML database.
    - `ML_DB_PORT`: Port number for the ML database.
    - `ML_DB_NAME`: Name of the ML database.

- **CogFlow Database Configuration**:
    - `DB_USER`: Username for the CogFlow database.
    - `DB_PASSWORD`: Password for the CogFlow database.
    - `DB_HOST`: Host address for the CogFlow database.
    - `DB_PORT`: Port number for the CogFlow database.
    - `DB_NAME`: Name of the CogFlow database.

- **Test Configuration**:
    - `SQLALCHEMY_TEST_DATABASE_URI`: URI for the test database (default: `sqlite:///test.db`).
    - `TESTING_CONFIG`: Configuration for testing (default: `config.app_config.TestingConfig`).

- **Jupyter Configuration**:
    - `JUPYTER_USER_ID`: User ID for Jupyter (default: 0).

- **API Configuration**:
    - `API_BASEPATH`: Path of the API .
    - `BASE_PATH`: Base path for the API.

- **CogFlow Configuration File Path**:
    - `COGFLOW_CONFIG_FILE_PATH`: Path to the CogFlow configuration file.

## Author

- [ ] [Fred Buining](mailto:fred.buining@hiro-microdatacenters.nl)

## Collaborators

- [ ] [Ali Shalbaf Zadeh](mailto:ali.shalbafzadeh@hiro-microdatacenters.nl)
- [ ] [Bola Nasr](mailto:bola.nasr@hiro-microdatacenters.nl)
- [ ] [Rui Min](mailto:rui.min@hiro-microdatacenters.nl)
- [ ] [Veena Rao](mailto:veena.rao@hiro-microdatacenters.nl)
- [ ] [Sai Kireeti](mailto:sai.kireeti@hiro-microdatacenters.nl)
- [ ] [Renuka Gollu](mailto:renuka.gollu@hiro-microdatacenters.nl)

## License

For source project license, contact the administrator for the license.
[The Cog Framework License](LICENSE.md)

## Support

For support, contact us via email or through our issue tracker.

## Roadmap

Future release ideas will be listed here. Stay tuned for updates!
