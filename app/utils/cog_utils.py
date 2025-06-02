"""
Utility classes for common operations.

This module provides utility classes for file operations, S3 interactions, database engine creation, and date parsing.

Classes:
    FileUtils: Provides methods for file operations.
    S3Utils: Provides methods for interacting with S3.
    DBUtils: Provides methods for creating database engines.
    DateUtils: Provides methods for parsing dates.
"""

import io
import os
import re
import zipfile
from datetime import datetime
from io import BytesIO
from typing import List, Tuple, Optional, Any

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, MetaData

from app.utils.exceptions import ValidationException


class FileUtils:
    """
    Provides methods for file operations.
    """

    @staticmethod
    def get_file(file: UploadFile) -> BytesIO:
        """
        Retrieve the file data from an UploadFile object.

        Args:
            file (UploadFile): The file to retrieve data from.

        Returns:
            BytesIO: The file data.
        """
        file_data = BytesIO()
        file.file.seek(0)
        file_data.write(file.file.read())
        file_data.seek(0)
        return file_data

    @staticmethod
    def file_exists(file: UploadFile):
        """
        Check if the file exists.

        Args:
            file (UploadFile): The file to check.

        Returns:
            UploadFile: The file if it exists, otherwise None.
        """
        if file:
            return file
        return None


class S3Utils:
    """
    Provides methods for interacting with S3.
    """

    @staticmethod
    def create_s3_client() -> boto3.client:
        """
        Create an S3 client.

        Returns:
            boto3.client: The S3 client.
        """
        s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("MLFLOW_S3_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        return s3_client

    @staticmethod
    def is_valid_s3_uri(uri: str) -> bool:
        """
        Check if the URI is a valid S3 URI.

        Args:
            uri (str): The URI to check.

        Returns:
            bool: True if the URI is valid, otherwise False.
        """
        s3_uri_regex = re.compile(r"^s3://([a-z0-9.-]+)/(.*)$")
        match = s3_uri_regex.match(uri)
        if match:
            bucket_name = match.group(1)
            object_key = match.group(2)
            if bucket_name and object_key:
                return True
        return False

    @staticmethod
    def split_s3_bucket_key_v2(s3_path: str) -> Tuple[str, str]:
        """
        Split the S3 path into bucket and key.

        Args:
            s3_path (str): The S3 path to split.

        Returns:
            tuple: The bucket and key.
        """
        path_parts = s3_path.replace("s3://", "").split("/", 1)
        return path_parts[0], path_parts[1]

    @staticmethod
    def fetch_file_from_s3(
        s3_client: boto3.client, bucket: str, key: str
    ) -> StreamingResponse:
        """
        Fetch a file from S3 .

        Args:
            s3_client (boto3.client): The S3 client.
            bucket (str): The S3 bucket name.
            key (str): The key of the S3 objects.

        Returns:
            BytesIO: The zip file content.
        """
        try:
            s3_response = s3_client.get_object(Bucket=bucket, Key=key)
            return StreamingResponse(
                s3_response["Body"],
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={key}"},
            )
        except ClientError as exp:
            raise exp

    @staticmethod
    def create_zip_file_from_s3(
        s3_client: boto3.client,
        files_to_zip: List[Tuple[str, str]],
        model_info: Optional[str],
    ) -> StreamingResponse:
        """
        Create a zip file from S3 objects.

        Args:
            s3_client (boto3.client): The S3 client.
            files_to_zip (List): list of files to zip containing bucket and key names.
            model_info: name of the model

        Returns:
            BytesIO: The zip file content.
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for bucket, key in files_to_zip:
                try:
                    file_stream = s3_client.get_object(Bucket=bucket, Key=key)["Body"]
                    file_data = file_stream.read()
                    zip_file.writestr(key, file_data)
                except ClientError as exp:
                    raise exp
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={
                "Content-Disposition": f"attachment; filename=model-{model_info}.zip"
            },
        )

    @staticmethod
    def check_zip(zip_files: List[Tuple[str, str]]):
        """
        Check zip file list .
        Args:
            zip_files : zip file list.
        Returns:
            boolean: boolean value
        """
        if zip_files:
            return True
        return False

    @staticmethod
    def validate_db_url(url: str) -> bool:
        """
        to validate db url
        """
        pattern = r"^[a-zA-Z0-9]+:\/\/[a-zA-Z0-9_]+:[a-zA-Z0-9_]+@[a-zA-Z0-9_.-]+:\d+\/[a-zA-Z0-9_]+$"
        return re.match(pattern, url) is not None


class DBUtils:
    """
    Provides methods for creating database engines.
    """

    @staticmethod
    def db_engine_create(url: Any) -> MetaData:
        """
        Create a database engine.

        Args:
            url (str): The database URL.

        Returns:
            MetaData: The database metadata.
        """
        engine = create_engine(url)
        metadata = MetaData()
        metadata.reflect(bind=engine)
        return metadata


class DateUtils:
    """
    Provides methods for parsing dates.
    """

    @staticmethod
    def parse_date(value: str):
        """
        Parse a date string into a datetime object.

        Args:
            value (str): The date string to parse.

        Returns:
            datetime: The parsed datetime object.

        Raises:
            ValidationException: If the date string is not valid.
        """
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                return None
        else:
            raise ValidationException("Not valid date")
