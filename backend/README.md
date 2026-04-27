# ETL Testing Framework

This project is a well-structured and comprehensive testing framework for ETL (Extract, Transform, Load) processes, built with Python. It is designed to be flexible and cater to both developers and users with less technical expertise.

## Key Features

*   **Dual Execution Modes:**
    *   **Developer-Led (Pytest):** Developers can write and execute tests using the `pytest` framework. The `utils/base_test.py` class provides a convenient base for tests, with pre-configured API and database clients. Tests are organized into directories by functionality (`api`, `db`, `etl`, etc.).
    *   **Data-Driven (CSV-Controlled):** Non-technical users can control test execution through CSV files. The `runners/etl_runner.py` and `runners/cross_testing_runner.py` scripts read test cases from CSV files (`data/test_cases.csv` and `data/cross_testing_example.csv`) and execute them. This allows users to enable, disable, and parameterize tests without modifying the code.

*   **Configuration:**
    *   The framework uses a combination of `config/config.yaml` for application-level settings and `config/master.properties` for environment-specific configurations (DEV, TEST, PROD). This provides a clear separation of concerns for configuration management.

*   **Core Utilities (`utils/`):**
    *   The `utils` directory contains the core logic of the framework.
    *   `api_client.py`: A client for making HTTP requests to APIs.
    *   `sqlite_client.py` and `db_client.py`: Clients for interacting with SQLite and PostgreSQL databases, respectively. The framework can be easily extended to support other databases.
    *   `csv_controller.py` and `cross_testing_controller.py`: These controllers manage the data-driven testing approach, reading and parsing test cases from CSV files.
    *   `sql_repository.py`: This utility loads and manages SQL queries from the `sql/` directory, making it easy to separate SQL code from Python code.
    *   `xml_reporter.py`: This generates JUnit-style XML reports, which are ideal for integration with CI/CD pipelines.

*   **Testing:**
    *   The `tests/` directory is well-organized, with tests categorized by functionality.
    *   The framework supports a variety of testing types, including API testing, database testing, ETL validation, and integration testing.
    *   The use of `pytest` allows for powerful features like fixtures, markers, and assertions.

*   **Reporting:**
    *   The framework generates detailed test reports in both XML and Allure formats.

## Architecture

The framework follows a clean and modular architecture, with a clear separation of concerns. The use of data-driven testing, a centralized utility library, and a well-organized test structure makes it a robust and maintainable solution for ETL testing.

## How it all works together

1.  **Configuration:** The framework is configured through `config.yaml` and `master.properties`.
2.  **Test Definition:** Tests are defined in two ways:
    *   As `pytest` test classes in the `tests/` directory.
    *   As rows in CSV files in the `data/` directory.
3.  **Test Execution:**
    *   `pytest` tests are run using the `pytest` command. The `BaseTest` class provides the necessary setup.
    *   CSV-driven tests are run using the `etl_runner.py` or `cross_testing_runner.py` scripts. These runners parse the CSV files, execute the corresponding tests (API calls or SQL queries), and validate the results.
4.  **Reporting:** After test execution, the framework generates XML and Allure reports to provide a comprehensive overview of the test results.

In conclusion, this project is a powerful and flexible ETL testing framework that can be adapted to a wide variety of testing needs. It demonstrates a good understanding of software engineering principles and best practices.

## Installation

1.  **Prerequisites:**
    *   Python 3.8+
    *   Docker (for PostgreSQL setup)

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Process Setup

### Database Setup

You can choose between two database setups:

**1. Local/Dev Setup (SQLite)**

This is the simplest setup and is recommended for local development and running tests quickly.

1.  **Run the initialization script:**
    ```bash
    python scripts/init_database.py
    ```
2.  This will create an `etl_test.db` file in the root directory, and it will be populated with data from the `fakestoreapi`.

**2. Full/Staging Setup (PostgreSQL)**

This setup is for a more realistic staging or testing environment using PostgreSQL in a Docker container.

1.  **Start PostgreSQL:**
    ```bash
    docker-compose up -d
    ```
2.  **Load data:**
    ```bash
    python -c "from utils.etl_loader import ETLLoader; loader = ETLLoader(); loader.load_products_from_api()"
    ```
    This will load the product data from the `fakestoreapi` into the PostgreSQL database.

### Configuration

*   **`config/master.properties`**: This file is used to configure the environment-specific settings, such as database connection details and API endpoints. You can switch between `DEV`, `TEST`, and `PROD` environments here.
*   **`config/config.yaml`**: This file contains application-level settings, such as API timeouts, ETL batch sizes, and logging configuration.

To switch between database types, edit the `DB_TYPE` property in `config/master.properties`.

### Running Tests

**1. Running Pytest tests:**

To run all `pytest` tests, use the following command:
```bash
pytest
```

You can also run specific tests using `pytest` markers:
```bash
pytest -m api
pytest -m db
```

**2. Running CSV-driven tests:**

To run the CSV-driven tests, use the runner scripts:

*   **ETL Runner:**
    ```bash
    python runners/etl_runner.py
    ```
*   **Cross-Testing Runner:**
    ```bash
    python runners/cross_testing_runner.py
    ```

