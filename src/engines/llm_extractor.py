"""LLM Extractor with Pydantic validation and retry logic"""

import logging
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel, ValidationError
from langchain_community.llms import Ollama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMConfig:
    """Configuration for LLM"""
    MODEL_NAME = "llama3.1"
    TEMPERATURE = 0.1  # Low temperature for consistency
    MAX_TOKENS = 2048
    TIMEOUT = 30  # seconds


class LLMExtractor:
    """
    LLM Extractor with Pydantic validation and retry logic.
    
    This class handles all interactions with the local Ollama LLM,
    ensuring structured output validation and crash prevention.
    """
    
    def __init__(self, model_name: str = LLMConfig.MODEL_NAME):
        """
        Initialize LLM extractor with Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use
        """
        self.llm = Ollama(
            model=model_name,
            temperature=LLMConfig.TEMPERATURE,
            num_predict=LLMConfig.MAX_TOKENS
        )
        logger.info(f"Initialized LLMExtractor with model: {model_name}")
    
    def extract_with_validation(
        self,
        text: str,
        schema: Type[T],
        prompt_template: str,
        max_retries: int = 3,
        **prompt_kwargs
    ) -> T:
        """
        Extract structured data with Pydantic validation and retry logic.
        
        This method attempts to extract structured information from text using
        the LLM, validates the output against a Pydantic schema, and retries
        with simplified prompts on validation failure.
        
        Args:
            text: Input text to extract information from
            schema: Pydantic model class for output validation
            prompt_template: Template string for the prompt
            max_retries: Maximum number of retry attempts (default: 3)
            **prompt_kwargs: Additional variables for prompt template
            
        Returns:
            Validated Pydantic model instance
            
        Raises:
            None - returns safe default on exhausted retries
        """
        parser = PydanticOutputParser(pydantic_object=schema)
        
        # Create prompt with format instructions
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["text"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                **prompt_kwargs
            }
        )
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Extraction attempt {attempt + 1}/{max_retries} for schema: {schema.__name__}")
                
                # Create chain and invoke
                chain = prompt | self.llm | parser
                result = chain.invoke({"text": text})
                
                logger.info(f"Successfully extracted and validated {schema.__name__}")
                return result
                
            except ValidationError as e:
                logger.warning(
                    f"Validation failed on attempt {attempt + 1}/{max_retries}: {str(e)}"
                )
                
                if attempt == max_retries - 1:
                    # Exhausted retries, return safe default
                    logger.error(
                        f"All retry attempts exhausted for {schema.__name__}. "
                        f"Returning safe default. Validation error: {str(e)}"
                    )
                    return self._get_safe_default(schema)
                
                # Simplify prompt for retry
                prompt = self._simplify_prompt(prompt, attempt)
                
            except Exception as e:
                logger.error(
                    f"Unexpected error during extraction (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                
                if attempt == max_retries - 1:
                    logger.error(f"All retry attempts exhausted. Returning safe default.")
                    return self._get_safe_default(schema)
        
        # Fallback (should not reach here)
        return self._get_safe_default(schema)
    
    def _simplify_prompt(self, prompt: PromptTemplate, attempt: int) -> PromptTemplate:
        """
        Simplify prompt for retry attempts.
        
        Args:
            prompt: Original prompt template
            attempt: Current attempt number
            
        Returns:
            Simplified prompt template
        """
        # Add instruction to be more concise
        simplified_template = prompt.template + "\n\nPlease provide a concise, well-formatted response."
        
        return PromptTemplate(
            template=simplified_template,
            input_variables=prompt.input_variables,
            partial_variables=prompt.partial_variables
        )
    
    def _get_safe_default(self, schema: Type[T]) -> T:
        """
        Generate safe default value for a schema when extraction fails.
        
        Args:
            schema: Pydantic model class
            
        Returns:
            Safe default instance with minimal valid data
        """
        from src.models.schemas import (
            EligibilityCriterion,
            CriteriaList,
            FinancialEvidence,
            TechnicalEvidence,
            ComplianceEvidence,
            DocumentationEvidence
        )
        
        # Return schema-specific safe defaults
        if schema == CriteriaList:
            return schema(
                criteria=[],
                extraction_failed=True,
                failure_reason="LLM extraction failed after maximum retries - manual review required"
            )
        
        elif schema == EligibilityCriterion:
            return schema(
                id="EXTRACTION_FAILED",
                category="Documentation",
                priority="Optional",
                description="Extraction failed - manual review required",
                source_page=0,
                original_text="EXTRACTION_FAILED"
            )
        
        elif schema == FinancialEvidence:
            return schema(
                value=0.0,
                currency="UNKNOWN",
                context="Extraction failed - manual review required",
                source_page=0,
                confidence=0.0
            )
        
        elif schema == TechnicalEvidence:
            return schema(
                specification="Extraction failed - manual review required",
                certifications=[],
                capabilities=[],
                source_page=0,
                confidence=0.0
            )
        
        elif schema == ComplianceEvidence:
            return schema(
                regulation="UNKNOWN",
                compliance_status="Extraction failed - manual review required",
                source_page=0,
                confidence=0.0
            )
        
        elif schema == DocumentationEvidence:
            return schema(
                document_present=False,
                document_type="UNKNOWN",
                completeness="Extraction failed - manual review required",
                source_page=0,
                confidence=0.0
            )
        
        else:
            # Generic fallback - try to instantiate with minimal data
            logger.warning(f"No specific safe default for {schema.__name__}, attempting generic instantiation")
            try:
                return schema()
            except Exception as e:
                logger.error(f"Failed to create safe default for {schema.__name__}: {str(e)}")
                raise ValueError(f"Cannot create safe default for schema: {schema.__name__}")
