from __future__ import annotations

import io
import uuid

import boto3

from app.core.config import get_settings


def upload_bytes_to_s3(content: bytes, folder: str, extension: str, content_type: str) -> tuple[str, str]:
    settings = get_settings()
    if not settings.s3_bucket or not settings.s3_endpoint_url:
        raise RuntimeError("S3 storage is not configured.")

    key = f"{folder.strip('/')}/{uuid.uuid4()}.{extension.lstrip('.')}"
    client = boto3.session.Session().client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )
    client.upload_fileobj(io.BytesIO(content), settings.s3_bucket, key, ExtraArgs={"ContentType": content_type})
    if settings.s3_public_base_url:
        return key, f"{settings.s3_public_base_url.rstrip('/')}/{key}"
    return key, f"{settings.s3_endpoint_url.rstrip('/')}/{settings.s3_bucket}/{key}"
