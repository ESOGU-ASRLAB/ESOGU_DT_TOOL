from utils.file_handler import FileHandler
from utils.model_client import LLMClient
from utils.text_processor import TextProcessor
from core.prompt_manager import get_base_prompt, get_requirement_analysis_system_suffix, save_session_data
import logging
import os
from datetime import datetime

logger = logging.getLogger("RequirementAnalysisService")

class RequirementAnalysisService:
    def __init__(self):
        self.file_handler = FileHandler()
        self.model_client = LLMClient()
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)

    def normalize_prompt(self, text):
        return ' '.join(text.strip().split()).lower()

    async def run_requirement_analysis(self, files, types=None, model_key=None, custom_prompt=None, session_id=None, api_key=None):
        try:
            self.logger.debug(f"Starting requirement analysis for {len(files)} files with model: {model_key}")
            if not files:
                raise ValueError("No files provided for analysis")

            file_paths = await self.file_handler.save_files(files)
            self.logger.debug(f"Files saved: {file_paths}")
            if not file_paths:
                raise ValueError("Failed to save uploaded files")

            # types zorunlu, eksik veya uzunluklar eşit değilse hata fırlat
            if types is None or len(types) != len(file_paths):
                raise ValueError("Hem Source Code hem de Requirement Document dosyası yüklenmeli ve types parametresi eksiksiz olmalı!")

            # Dosya tiplerine göre içerikleri ayır
            requirement_doc_content = ""
            code_files_content = ""
            for path, file_type in zip(file_paths, types):
                content = self.file_handler.read_file(path)
                if file_type == 'Requirement Document':
                    requirement_doc_content += content + "\n"
                else:
                    code_files_content += f"\n\n### File: {os.path.basename(path)}\n\n{content}"

            model_client = LLMClient()
            model_name = None
            if model_key:
                model_name = model_client.get_model_identifier(model_key)
                model_client = LLMClient(model_name, api_key, use_case='requirement_analysis')  # API key ve use_case eklendi
                self.logger.info(f"Using model: {model_name} for analysis with API key provided: {bool(api_key)}")
            else:
                self.logger.info("No model specified, using default model")

            used_prompt = None
            prompt_source = None
            base_prompt = get_base_prompt("requirement_analysis")
            system_suffix = get_requirement_analysis_system_suffix()

            if custom_prompt:
                used_prompt = custom_prompt
                prompt_source = "custom_parameter"
                self.logger.info("Using custom prompt provided by user in this request")
            else:
                if base_prompt:
                    used_prompt = base_prompt
                    prompt_source = "base_db"
                    self.logger.info("Using base prompt from database")
                else:
                    raise ValueError("No prompt found in database for requirement_analysis process. Please add a prompt to the database.")

            # Promptu oluştururken doğru alanları kullan ve token limitine dikkat et
            analysis_prompt = used_prompt + system_suffix
            
            # Check content lengths to avoid token limit issues
            prompt_base_length = len(analysis_prompt.split())
            code_length = len(code_files_content.split())
            req_length = len(requirement_doc_content.split())
            total_estimated_tokens = prompt_base_length + code_length + req_length
            
            self.logger.debug(f"Estimated token usage: base={prompt_base_length}, code={code_length}, req={req_length}, total={total_estimated_tokens}")
            
            # If total is too large, truncate content to fit within limits
            MAX_INPUT_TOKENS = 95000  # Gemini 2.5 Flash supports up to 100K tokens
            if total_estimated_tokens > MAX_INPUT_TOKENS:
                self.logger.warning(f"Input too large ({total_estimated_tokens} tokens), truncating content...")
                
                # Reserve space for the base prompt (usually ~500-800 tokens)
                available_tokens = MAX_INPUT_TOKENS - prompt_base_length - 200  # 200 buffer
                
                # Split available tokens between code and requirements (prioritize requirements)
                if req_length > available_tokens // 2:
                    req_tokens = available_tokens // 2
                    code_tokens = available_tokens - req_tokens
                else:
                    req_tokens = req_length
                    code_tokens = available_tokens - req_tokens
                
                # Truncate content if needed (cleanly, without technical messages)
                if req_length > req_tokens:
                    req_words = requirement_doc_content.split()
                    requirement_doc_content = " ".join(req_words[:req_tokens])
                    
                if code_length > code_tokens:
                    code_words = code_files_content.split()
                    code_files_content = " ".join(code_words[:code_tokens])
                
                self.logger.info(f"Content truncated - req: {len(requirement_doc_content.split())} tokens, code: {len(code_files_content.split())} tokens")
            
            analysis_prompt = analysis_prompt.format(
                code=code_files_content,
                requirement_document=requirement_doc_content
            )

            MAX_TOKENS = 95000  # Utilize Gemini 2.5's full capacity
            if len(analysis_prompt.split()) > MAX_TOKENS:
                self.logger.debug(f"Token limit exceeded: {len(analysis_prompt.split())} > {MAX_TOKENS}")
                chunks = self.text_processor.chunk_text(analysis_prompt)
                all_results = []
                for i, chunk in enumerate(chunks):
                    self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                    result = await model_client.generate_response(chunk)
                    if result:
                        all_results.append(result)
                final_result = self._combine_results(all_results)
            else:
                self.logger.debug(f"Using single analysis. Token count: {len(analysis_prompt.split())}")
                final_result = await model_client.generate_response(analysis_prompt, max_tokens=90000)

            if not final_result:
                raise ValueError("Failed to generate requirement analysis")

            # Clean and format the result
            final_result = self._format_analysis_output(final_result)

            file_names = [os.path.basename(path) for path in file_paths]
            files_header = "Files analyzed:\n" + "\n".join(file_names)

            edited_prompt = False
            if custom_prompt and base_prompt:
                edited_prompt = (self.normalize_prompt(custom_prompt) != self.normalize_prompt(base_prompt))
            elif custom_prompt and not base_prompt:
                edited_prompt = True

            session_data = {
                "session_id": session_id,
                "output": {
                    "files": files_header,
                    "analysis": final_result
                },
                "edited_prompt": edited_prompt,
                "used_prompt": used_prompt,
                "used_model": model_name
            }
            save_session_data(session_data, process_type="requirement_analysis")

            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {path}: {str(e)}")

            return {
                "status": "success",
                "analysis": [{
                    "files": files_header,
                    "result": final_result
                }],
                "prompt_info": {
                    "source": prompt_source
                },
                "session_id": session_id or "unknown"
            }

        except Exception as e:
            self.logger.error(f"Error in run_requirement_analysis: {str(e)}")
            raise

    def _combine_file_contents(self, file_paths):
        combined_content = ""
        for path in file_paths:
            code_content = self.file_handler.read_file(path)
            combined_content += f"\n\n### File: {os.path.basename(path)}\n\n{code_content}"
        return combined_content

    def _combine_results(self, results):
        # Clean each result and join them properly
        cleaned_results = []
        for result in results:
            if result:
                cleaned = self._format_analysis_output(result)
                if cleaned.strip():
                    cleaned_results.append(cleaned)
        
        if not cleaned_results:
            return "No analysis results generated."
        
        return "\n\n".join(cleaned_results)
    
    def _format_analysis_output(self, text):
        """Clean and format analysis output for better UI presentation"""
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove extra spaces and tabs
            cleaned_line = ' '.join(line.split())
            
            # Skip empty lines at the beginning and end, but preserve structure
            if cleaned_line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(cleaned_line)
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        # Join with single line breaks and ensure proper spacing
        result = '\n'.join(cleaned_lines)
        
        # Remove any technical truncation messages that might have slipped through
        technical_messages = [
            '[Response truncated due to token limit]',
            '[Content truncated due to length. Please provide a brief analysis.]',
            '[Brief analysis requested due to token limits.]',
            '[Analysis based on truncated input due to token limits]',
            '[Content truncated due to size limits]'
        ]
        
        for msg in technical_messages:
            result = result.replace(msg, '').strip()
        
        return result 