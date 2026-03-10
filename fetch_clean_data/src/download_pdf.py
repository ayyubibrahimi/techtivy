import os
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from dotenv import load_dotenv


class DocPDF:
    def __init__(self):
        load_dotenv()
        self.cache_dir = os.getenv("DOCPDF_CACHE_DIR", "../data/output")
        self.container_name = "case-files"
        self.service_client = BlobServiceClient.from_connection_string(
            conn_str=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        )

    def _generate_cache_path(self, sha1: str) -> Path:
        return Path(self.cache_dir) / sha1[:2] / sha1[2:4] / sha1[4:6] / f"{sha1}.pdf"

    def _check_cache(self, sha1: str) -> Path | None:
        cache_path = self._generate_cache_path(sha1)
        return cache_path if cache_path.exists() else None

    def _download(self, sha1: str) -> bytes:
        blob_path = f"{sha1[:2]}/{sha1[2:4]}/{sha1[4:6]}/{sha1}"
        blob_client = self.service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )
        try:
            return blob_client.download_blob().readall()
        except ResourceNotFoundError:
            raise ResourceNotFoundError(message=f"No PDF found for sha1: {sha1}")

    def get_pdf(self, sha1: str) -> Path:
        cached = self._check_cache(sha1)
        if cached:
            return cached
        data = self._download(sha1)
        cache_path = self._generate_cache_path(sha1)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
        return cache_path
