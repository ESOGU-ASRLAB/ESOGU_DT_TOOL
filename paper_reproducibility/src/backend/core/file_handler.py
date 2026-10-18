"""
file_handler.py
---------------
Ortak dosya yükleme ve metin çıkarma işlemlerini içerir.
PDF, DOCX, TXT gibi farklı dosya formatlarından metin çıkarma fonksiyonları bu modülde yer alır.
"""

import os
from io import BytesIO
from fastapi import UploadFile
from PyPDF2 import PdfReader
import docx
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)  # Hata ve bilgi mesajlarını göster
logger = logging.getLogger(__name__)     # Günlükleme için logger nesnesi

def extract_text_from_pdf(file_stream: BytesIO) -> str:
    """PDF dosyasından metin çıkarır."""
    try:
        text = ""
        reader = PdfReader(file_stream)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"PDF okuma hatası: {str(e)}")  # Hata mesajını logla
        return None  # Hata varsa None döndür

def extract_text_from_docx(file_stream: BytesIO) -> str:
    """DOCX dosyasından metin çıkarır."""
    try:
        doc = docx.Document(file_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"DOCX okuma hatası: {str(e)}")
        return None

def extract_text_from_txt(file_stream: BytesIO) -> str:
    """TXT dosyasından metin çıkarır."""
    try:
        return file_stream.read().decode('utf-8')
    except Exception as e:
        logger.error(f"TXT okuma hatası: {str(e)}")
        return None

def extract_text(upload_file: UploadFile) -> str:
    """Yüklenen dosyadan türüne göre metin çıkarır."""
    ext = os.path.splitext(upload_file.filename)[1].lower()  # Dosya uzantısını al
    try:
        content = upload_file.file.read()  # Dosyanın içeriğini oku
        upload_file.file.seek(0)  # Okuma işaretçisini başa al
        if ext == ".pdf":
            result = extract_text_from_pdf(BytesIO(content))
        elif ext == ".docx":
            result = extract_text_from_docx(BytesIO(content))
        elif ext == ".txt":
            result = extract_text_from_txt(BytesIO(content))
        else:
            logger.warning(f"Desteklenmeyen dosya türü: {ext}")  # Uyarı logla
            return None
        if result is None:
            raise ValueError(f"{ext.upper()} dosyasından metin çıkarılamadı.")
        return result
    except Exception as e:
        logger.error(f"Dosya işleme hatası: {str(e)}")
        return None


class FileHandler:
    """Dosya yükleme ve işleme operasyonlarını yöneten sınıf."""
    
    def __init__(self, upload_dir: str = "uploads"):
        """
        FileHandler başlatıcı.
        
        Args:
            upload_dir: Dosyaların kaydedileceği dizin
        """
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    async def save_files(self, files):
        """
        Yüklenen dosyaları kaydet ve içeriklerini çıkar.
        
        Args:
            files: Yüklenen dosya listesi (UploadFile objelerini)
            
        Returns:
            dict: Dosya yolları ve içerikleri
        """
        saved_files = {}
        
        for file in files:
            try:
                # Dosya içeriğini oku
                content = await file.read()
                
                # Dosyayı kaydet
                file_path = os.path.join(self.upload_dir, file.filename)
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # Dosya içeriğini çıkar
                file.file = BytesIO(content)  # UploadFile'ı yeniden oluştur
                text_content = extract_text(file)
                
                saved_files[file.filename] = {
                    "path": file_path,
                    "content": text_content
                }
                
                logger.info(f"Dosya başarıyla kaydedildi: {file.filename}")
                
            except Exception as e:
                logger.error(f"Dosya kaydetme hatası ({file.filename}): {str(e)}")
                saved_files[file.filename] = {
                    "path": None,
                    "content": None,
                    "error": str(e)
                }
        
        return saved_files
    
    def read_file_content(self, file_path: str) -> str:
        """
        Kaydedilen dosyadan içerik oku.
        
        Args:
            file_path: Dosya yolu
            
        Returns:
            str: Dosya içeriği
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Dosya okuma hatası: {str(e)}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Dosyayı sil.
        
        Args:
            file_path: Silinecek dosya yolu
            
        Returns:
            bool: Silme işleminin başarılı olup olmadığı
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Dosya silindi: {file_path}")
                return True
            else:
                logger.warning(f"Silinecek dosya bulunamadı: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Dosya silme hatası: {str(e)}")
            return False