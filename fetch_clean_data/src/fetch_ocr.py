import json, os
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from dotenv import load_dotenv
from typing import Dict, List
from pydantic import BaseModel
from pathlib import Path


class PageText(BaseModel):
    page_number: int
    text: str


class DocText:
    def __init__(self):
        load_dotenv()
        self.cache_dir = os.getenv("DOCTEXT_CACHE_DIR", "/var/tmp/ayyub/clean_ocr_cache")
        self.container_name = "ocr"
        self.service_client = BlobServiceClient.from_connection_string(
            conn_str=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        )

    def _generate_cache_path(self, h, fmt="paged-text"):
        return Path(self.cache_dir) / fmt / f"{h[:2]}" / f"{h[2:4]}" / f"{h[4:6]}" / f"{h}.json"

    def _check_cache(self, source_document_sha1, fmt="paged-text"):
        cache_path = self._generate_cache_path(source_document_sha1, fmt=fmt)
        if cache_path.exists():
            with open(cache_path, "r") as f:
                data = json.load(f)
            return data
        return None

    def _add_to_cache(self, source_document_sha1, data, fmt="paged-text"):
        cache_path = self._generate_cache_path(source_document_sha1, fmt=fmt)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(data, f)

    def _get(self, source_document_sha1):
        prefix = f"sha1:{source_document_sha1}/"
        container_client = self.service_client.get_container_client(self.container_name)
        matching_blobs = [b for b in container_client.walk_blobs(name_starts_with=prefix, delimiter='/')]
        if not matching_blobs:
            msg = f"No blobs found with prefix {prefix}"
            raise ResourceNotFoundError(message=msg)
        blobname = matching_blobs[0].name
        blob_client = self.service_client.get_blob_client(
            container=self.container_name,
            blob=blobname
        )
        contents = blob_client.download_blob().readall()
        data = json.loads(contents)
        return data

    def get_text(self, source_document_sha1) -> List[PageText]:
        cached = self._check_cache(source_document_sha1, fmt="paged-text")
        if cached is not None:
            return [PageText(**pt) for pt in cached]
        analyze_result = self._get(source_document_sha1)
        text_per_page = []
        for page in analyze_result['pages']:
            page_text = ""
            for line in page['lines']:
                page_text += line['content'] + "\n"
            page_number = page['pageNumber']
            text_per_page.append(PageText(
                page_number=page_number,
                text=page_text
            ))
        self._add_to_cache(source_document_sha1, [pt.dict() for pt in text_per_page], fmt="paged-text")
        return text_per_page
