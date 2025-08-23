import os
import uuid
from typing import Optional
from fastapi import UploadFile


class SimpleFileUtils:
    """简化的文件工具类，替代SQLBotFileUtils"""
    
    @staticmethod
    def get_file_path(file_id: str) -> str:
        """获取文件路径"""
        # 简化实现，返回基本路径
        return f"/opt/sqlbot/data/file/{file_id}"
    
    @staticmethod
    def split_filename_and_flag(filename: str) -> tuple[str, str]:
        """分割文件名和标志"""
        if "_" in filename:
            parts = filename.split("_", 1)
            return parts[1], parts[0]
        return filename, ""
    
    @staticmethod
    def check_file(file: UploadFile, file_types: list[str], limit_file_size: int) -> bool:
        """检查文件类型和大小"""
        # 检查文件扩展名
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in file_types:
                raise ValueError(f"File type {ext} not allowed")
        
        # 检查文件大小（简化实现）
        # 注意：这里无法直接获取文件大小，在实际应用中需要更复杂的处理
        return True
    
    @staticmethod
    def detete_file(file_path: str) -> bool:
        """删除文件"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False
    
    @staticmethod
    async def upload(file: UploadFile) -> str:
        """上传文件"""
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 创建文件路径
        upload_dir = "/opt/sqlbot/data/file"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file_id)
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return file_id