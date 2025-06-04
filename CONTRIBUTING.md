# Contributing to the Cognitive Framework

Thank you for your interest in contributing to the Cognitive Framework! We welcome contributions from the community to help improve this project. Below are the guidelines to follow when contributing.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Pull Requests](#pull-requests)
3. [Development Setup](#development-setup)
4. [Style Guidelines](#style-guidelines)
5. [License](#license)

---

## Code of Conduct
By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please ensure respectful and constructive behavior in all interactions.

---

## How to Contribute

### Reporting Bugs
1. **Check existing issues**: Ensure the bug hasn’t already been reported in the [Issues section](https://github.com/HIRO-MicroDataCenters-BV/Cognitive-Framework/issues).
2. **Create a detailed report**:
   - A clear title and description.
   - Steps to reproduce the issue.
   - Expected vs. actual behavior.
   - Screenshots/logs (if applicable).
   - Environment details (OS, version, etc.).

### Suggesting Enhancements
1. **Check existing feature requests** to avoid duplicates.
2. **Open an issue** with:
   - A clear title (e.g., "Feature: Add X").
   - A description of the enhancement and its benefits.
   - Use cases or examples.

### Pull Requests
We welcome PRs for bug fixes, improvements, or new features. Follow these steps:
1. **Fork the repository** and create a branch from `main`.
2. **Ensure your code adheres to our [Style Guidelines](#style-guidelines)**.
3. **Test your changes** thoroughly.
4. **Update documentation** if needed (e.g., README, inline comments).
5. **Submit the PR** with:
   - A clear title and description.
   - Reference to related issues (e.g., "Fixes #123").
   - Details of changes made.

---

## Development Setup
To set up the project locally:

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

## Style Guidelines
- **Code**: Follow existing conventions (e.g., indentation, naming).

- **Commits**: Use descriptive messages in the imperative tense (e.g., "Fix parsing bug").

- **Documentation**: Keep comments and docs up-to-date with changes.

## License
By contributing, you agree that your contributions will be licensed under the project’s [Apache 2.0 License](./LICENSE)  (if specified in the repository).