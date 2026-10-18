from utils.file_handler import FileHandler
from utils.model_client import LLMClient
from utils.text_processor import TextProcessor
from core.prompt_manager import get_base_prompt, save_session_data, get_environment_setup_system_suffix
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()  # Console'a loglama
    ]
)

logger = logging.getLogger("EnvironmentSetupService")

class EnvironmentSetupService:
    def __init__(self):
        self.file_handler = FileHandler()
        self.model_client = LLMClient()
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("EnvironmentSetupService initialized")

    def normalize_prompt(self, text):
        return ' '.join(text.strip().split()).lower()

    async def run_environment_setup(self, files, types, model_key=None, custom_prompt=None, session_id=None, environment_name=None, api_key=None):
        try:
            self.logger.debug(f"run_environment_setup çağrıldı. Dosya sayısı: {len(files)}, Types: {types}")
            # Dosya isimlerini ve tiplerini logla
            for idx, (file, file_type) in enumerate(zip(files, types)):
                self.logger.debug(f"[{idx}] Dosya: {getattr(file, 'filename', str(file))}, Type: '{file_type}'")
            if not files:
                raise ValueError("No files provided for environment setup")
            file_paths = await self.file_handler.save_files(files)
            self.logger.debug(f"Files saved: {file_paths}")
            if not file_paths:
                raise ValueError("Failed to save uploaded files")
            if len(file_paths) != len(types):
                self.logger.error(f"file_paths ve types uzunlukları eşit değil! file_paths: {len(file_paths)}, types: {len(types)}")
                raise ValueError("Dosya sayısı ile types array'i eşleşmiyor!")
            # Dosya tiplerine göre içerikleri ayır
            requirement_doc_content = ""
            code_files_content = ""
            for idx, (path, file_type) in enumerate(zip(file_paths, types)):
                self.logger.debug(f"[{idx}] Path: {path}, Type: '{file_type}'")
                code_content = self.file_handler.read_file(path)
                if file_type == 'Requirement Document':
                    requirement_doc_content += code_content + "\n"
                else:
                    code_files_content += f"\n\n### File: {os.path.basename(path)}\n\n{code_content}"
            model_client = LLMClient()
            model_name = None
            if model_key:
                model_name = model_client.get_model_identifier(model_key)
                model_client = LLMClient(model_name, api_key, use_case='environment_setup')  # API key ve use_case eklendi
                self.logger.info(f"Using model: {model_name} for environment setup with API key provided: {bool(api_key)}")
            else:
                self.logger.info("No model specified, using default model")
            used_prompt = None
            prompt_source = None
            base_prompt = get_base_prompt("environment_setup")
            system_suffix = get_environment_setup_system_suffix()
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
                    raise ValueError("No prompt found in database for environment_setup process. Please add a prompt to the database.")
            # Promptu oluştururken requirement_doc_content ve code_files_content'i birleştir
            review_prompt = used_prompt + system_suffix
            review_prompt = review_prompt.format(
                code=code_files_content,
                requirement_document=requirement_doc_content
            )
            MAX_TOKENS = 4000
            if len(review_prompt.split()) > MAX_TOKENS:
                self.logger.debug(f"Token limit exceeded: {len(review_prompt.split())} > {MAX_TOKENS}")
                chunks = self.text_processor.chunk_text(review_prompt)
                all_reviews = []
                for i, chunk in enumerate(chunks):
                    self.logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                    review = await model_client.generate_response(chunk)
                    if review:
                        all_reviews.append(review)
                final_review = self._combine_reviews(all_reviews)
            else:
                self.logger.debug(f"Using single review. Token count: {len(review_prompt.split())}")
                final_review = await model_client.generate_response(review_prompt)
            if not final_review:
                raise ValueError("Failed to generate environment setup output")
            file_names = [os.path.basename(path) for path in file_paths]
            files_header = "Files analyzed:\n" + "\n".join(file_names)
            edited_prompt = False
            if custom_prompt and base_prompt:
                edited_prompt = (self.normalize_prompt(custom_prompt) != self.normalize_prompt(base_prompt))
            elif custom_prompt and not base_prompt:
                edited_prompt = True
            # Prepare session data for nested processes structure
            session_data = {
                "session_id": session_id,
                "output": {
                    "files": files_header,
                    "setup": final_review
                },
                "edited_prompt": edited_prompt,
                "used_prompt": used_prompt,
                "used_model": model_name,
                "environment_name": environment_name,
                "process_name": "Environment Setup"
            }
            save_session_data(session_data, process_type="environment_setup")
            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {path}: {str(e)}")
            return {
                "status": "success",
                "setups": [{
                    "files": files_header,
                    "setup": final_review
                }],
                "prompt_info": {
                    "source": prompt_source
                },
                "session_id": session_id or "unknown"
            }
        except Exception as e:
            self.logger.error(f"Error in run_environment_setup: {str(e)}")
            raise

    def _combine_file_contents(self, file_paths):
        combined_content = ""
        for path in file_paths:
            code_content = self.file_handler.read_file(path)
            combined_content += f"\n\n### File: {os.path.basename(path)}\n\n{code_content}"
        return combined_content

    def _combine_reviews(self, reviews):
        combined = "\n\n".join(reviews)
        return "# Complete Environment Setup Summary\n\n" + combined 