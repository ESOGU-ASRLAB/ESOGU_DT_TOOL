"""
Prompt Generation Service - File content aware prompt generation
"""

from utils.file_handler import FileHandler
from utils.model_client import LLMClient
from utils.text_processor import TextProcessor
from core.prompt_manager import get_base_prompt, save_session_data
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger("PromptGenerationService")

class PromptGenerationService:
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.model_client = LLMClient()
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("PromptGenerationService initialized")

    async def generate_file_aware_prompt(self, files, test_type=None, test_category=None, 
                                       base_prompt=None, model_key=None, session_id=None):
        """
        Dosya içeriklerine dayalı custom prompt generation
        """
        try:
            self.logger.debug(f"Starting file-aware prompt generation for {len(files)} files")
            
            if not files:
                raise ValueError("No files provided for prompt generation")
                
            # Dosyaları kaydet
            file_paths = await self.file_handler.save_files(files)
            self.logger.debug(f"Files saved: {file_paths}")
            
            # Model seçimi
            model_client = LLMClient()
            model_name = None
            if model_key:
                model_name = model_client.get_model_identifier(model_key)
                model_client = LLMClient(model_name)
                self.logger.info(f"Using model: {model_name} for prompt generation")
            
            # Dosya içeriklerini analiz et ve birleştir
            file_analysis = self._analyze_files(file_paths)
            combined_content = self._combine_file_contents_for_prompt(file_paths)
            
            # Context-aware prompt generation
            prompt_generation_request = self._create_prompt_generation_request(
                file_analysis, combined_content, test_type, test_category, base_prompt
            )
            
            # Token limit kontrolü
            MAX_TOKENS = 4000
            if len(prompt_generation_request.split()) > MAX_TOKENS:
                self.logger.debug(f"Token limit exceeded, chunking content")
                chunks = self.text_processor.chunk_text(prompt_generation_request)
                generated_prompts = []
                for i, chunk in enumerate(chunks):
                    self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                    prompt_part = await model_client.generate_response(chunk)
                    if prompt_part:
                        generated_prompts.append(prompt_part)
                final_prompt = self._combine_prompt_parts(generated_prompts)
            else:
                final_prompt = await model_client.generate_response(prompt_generation_request)
            
            if not final_prompt:
                raise ValueError("Failed to generate custom prompt")
            
            # Dosya bilgilerini hazırla
            file_names = [os.path.basename(path) for path in file_paths]
            files_info = {
                "file_count": len(file_names),
                "file_names": file_names,
                "file_types": list(file_analysis.keys()),
                "total_content_length": len(combined_content)
            }
            
            # Session verilerini kaydet
            session_data = {
                "session_id": session_id,
                "output": {
                    "generated_prompt": final_prompt,
                    "files_analyzed": files_info,
                    "file_analysis": file_analysis
                },
                "used_files": file_names,
                "used_model": model_name,
                "test_type": test_type,
                "test_category": test_category
            }
            save_session_data(session_data, process_type="prompt_generation")
            
            # Cleanup temporary files
            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {path}: {str(e)}")
            
            return {
                "status": "success",
                "generated_custom_prompt": final_prompt,
                "files_analyzed": files_info,
                "file_analysis_summary": self._create_analysis_summary(file_analysis),
                "session_id": session_id or "unknown"
            }
            
        except Exception as e:
            self.logger.error(f"Error in generate_file_aware_prompt: {str(e)}")
            raise

    def _analyze_files(self, file_paths):
        """
        Dosyaları analiz ederek tip ve içerik özetleri çıkarır
        """
        analysis = {}
        
        for path in file_paths:
            file_ext = os.path.splitext(path)[1].lower()
            file_name = os.path.basename(path)
            
            try:
                content = self.file_handler.read_file(path)
                
                # Dosya tipine göre analiz
                if file_ext in ['.py', '.js', '.java', '.cpp', '.c', '.cs']:
                    analysis[file_name] = self._analyze_code_file(content, file_ext)
                elif file_ext in ['.xml', '.uml']:
                    analysis[file_name] = self._analyze_structure_file(content, file_ext)
                elif file_ext in ['.txt', '.md', '.doc']:
                    analysis[file_name] = self._analyze_document_file(content, file_ext)
                else:
                    analysis[file_name] = self._analyze_generic_file(content, file_ext)
                    
            except Exception as e:
                self.logger.warning(f"Failed to analyze file {path}: {str(e)}")
                analysis[file_name] = {
                    "type": "error",
                    "error": str(e),
                    "extension": file_ext
                }
        
        return analysis

    def _analyze_code_file(self, content, file_ext):
        """
        Kod dosyalarını analiz et
        """
        lines = content.split('\n')
        
        analysis = {
            "type": "code",
            "extension": file_ext,
            "line_count": len(lines),
            "functions": [],
            "classes": [],
            "imports": [],
            "key_patterns": []
        }
        
        # Basit pattern matching için
        for line in lines:
            line = line.strip()
            if line.startswith('def ') or line.startswith('function '):
                analysis["functions"].append(line)
            elif line.startswith('class '):
                analysis["classes"].append(line)
            elif line.startswith('import ') or line.startswith('from '):
                analysis["imports"].append(line)
            elif 'API' in line or 'endpoint' in line or 'route' in line:
                analysis["key_patterns"].append(line)
        
        return analysis

    def _analyze_structure_file(self, content, file_ext):
        """
        Yapısal dosyaları (XML, UML) analiz et
        """
        return {
            "type": "structure",
            "extension": file_ext,
            "content_length": len(content),
            "contains_elements": "elements" in content.lower() or "class" in content.lower(),
            "contains_relationships": "relationship" in content.lower() or "association" in content.lower()
        }

    def _analyze_document_file(self, content, file_ext):
        """
        Dokümantasyon dosyalarını analiz et
        """
        lines = content.split('\n')
        
        return {
            "type": "documentation",
            "extension": file_ext,
            "line_count": len(lines),
            "word_count": len(content.split()),
            "contains_requirements": "requirement" in content.lower() or "shall" in content.lower(),
            "contains_specifications": "specification" in content.lower() or "spec" in content.lower()
        }

    def _analyze_generic_file(self, content, file_ext):
        """
        Genel dosya analizi
        """
        return {
            "type": "generic",
            "extension": file_ext,
            "content_length": len(content),
            "line_count": len(content.split('\n'))
        }

    def _combine_file_contents_for_prompt(self, file_paths):
        """
        Dosya içeriklerini prompt generation için optimize edilmiş şekilde birleştir
        """
        combined_content = ""
        
        for path in file_paths:
            file_name = os.path.basename(path)
            content = self.file_handler.read_file(path)
            
            # Her dosya için özel header
            combined_content += f"\n\n=== FILE: {file_name} ===\n"
            combined_content += f"File Type: {os.path.splitext(file_name)[1]}\n"
            combined_content += f"Content Length: {len(content)} characters\n"
            combined_content += "--- Content ---\n"
            combined_content += content
            combined_content += "\n--- End of File ---\n"
        
        return combined_content

    def _create_prompt_generation_request(self, file_analysis, combined_content, 
                                        test_type, test_category, base_prompt):
        """
        Dosya analizi ve içeriğine dayalı prompt generation request oluştur
        """
        
        # Dosya analizi özetini oluştur
        analysis_summary = self._create_analysis_summary(file_analysis)
        
        prompt_request = f"""You are an expert test prompt generation assistant. Your task is to create a highly specific and context-aware test prompt based on the provided file contents and analysis.

## FILE ANALYSIS SUMMARY
{analysis_summary}

## TEST CONTEXT
- Test Type: {test_type or 'General Testing'}
- Test Category: {test_category or 'General Category'}
- Base Prompt: {base_prompt or 'No base prompt provided'}

## FILE CONTENTS TO ANALYZE
{combined_content[:3000]}  # Limit content to prevent token overflow

## YOUR TASK
Create a comprehensive, file-specific test prompt that:

1. **Analyzes the provided files** and identifies key testing areas specific to the code/documentation
2. **Incorporates the file structure and content** into testing scenarios
3. **Uses the test type and category** to focus the testing approach
4. **Enhances the base prompt** with file-specific insights
5. **Generates actionable test instructions** based on actual file content

## OUTPUT REQUIREMENTS
Generate a detailed test prompt that specifically references:
- Actual functions, classes, or components found in the files
- Specific business logic or requirements identified
- File-specific edge cases and scenarios
- Integration points between different files
- Data structures and API endpoints discovered

The prompt should be ready to use for generating precise test scenarios that are directly relevant to the provided files.

Please respond with the complete, file-aware test prompt:"""

        return prompt_request

    def _create_analysis_summary(self, file_analysis):
        """
        Dosya analizi özetini oluştur
        """
        summary = "Files Analyzed:\n"
        
        for file_name, analysis in file_analysis.items():
            summary += f"\n• {file_name} ({analysis.get('type', 'unknown')} file)\n"
            
            if analysis.get('type') == 'code':
                summary += f"  - Functions: {len(analysis.get('functions', []))}\n"
                summary += f"  - Classes: {len(analysis.get('classes', []))}\n"
                summary += f"  - Lines: {analysis.get('line_count', 0)}\n"
            elif analysis.get('type') == 'documentation':
                summary += f"  - Words: {analysis.get('word_count', 0)}\n"
                summary += f"  - Has Requirements: {analysis.get('contains_requirements', False)}\n"
            elif analysis.get('type') == 'structure':
                summary += f"  - Content Length: {analysis.get('content_length', 0)}\n"
                summary += f"  - Has Elements: {analysis.get('contains_elements', False)}\n"
        
        return summary

    def _combine_prompt_parts(self, prompt_parts):
        """
        Parçalı prompt'ları birleştir
        """
        if not prompt_parts:
            return ""
        
        if len(prompt_parts) == 1:
            return prompt_parts[0]
        
        combined = "# Comprehensive File-Based Test Prompt\n\n"
        for i, part in enumerate(prompt_parts):
            combined += f"## Section {i+1}\n\n{part}\n\n"
        
        return combined
