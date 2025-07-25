from .Logger import Logger

import hashlib
import asyncio
import aiofiles
from typing import Literal, TypeAlias

HashCalculateType: TypeAlias = Literal[
    'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512',
    'blake2b', 'blake2s',
    'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512',
    'shake_128', 'shake_256'
    ]


def hashc_file(file_path: str, hash_type: HashCalculateType = "sha256") -> str | None:
    
    try:
        hash_obj = hashlib.new(hash_type)
        
        with open(file_path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b''):
                hash_obj.update(chunk)
                
        return hash_obj.hexdigest()
    
    
    except Exception:
        Logger.exception(f"Cannot calculate the hash: \"{file_path}\"")


async def async_hashc_file(file_path: str, hash_type: HashCalculateType = "sha256") -> str | None:
    
    try:
        hash_obj = hashlib.new(hash_type)
        
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(4096):
                await asyncio.to_thread(hash_obj.update, chunk)

        return hash_obj.hexdigest()
    
    except Exception:
        Logger.exception(f"Cannot calculate the hash: \"{file_path}\"")