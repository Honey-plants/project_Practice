from backend.app.core import config
from backend.app.common.storage.local import LocalUploadStorage
from backend.app.common.storage.s3 import S3UploadStorage

def get_tmp_storage():
    if config.STORAGE_BACKEND == "s3":
        return S3UploadStorage(config.S3_BUCKET)
    return LocalUploadStorage(config.LOCAL_TMP_ROOT)

def get_perm_storage():
    if config.STORAGE_BACKEND == "s3":
        return S3UploadStorage(config.S3_BUCKET)
    return LocalUploadStorage(config.LOCAL_PERM_ROOT)
