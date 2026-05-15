"""
Image Analysis Engine
Understands diagrams, technical drawings, charts, architecture diagrams
Uses GPT-4o Vision for multimodal understanding
"""
import base64
from pathlib import Path
from typing import Dict, Optional, List
from app.core.config import settings
from loguru import logger


class ImageAnalyzer:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def analyze(self, image_path: str, context: str = "") -> Dict:
        """Full analysis of an image using GPT-4 Vision"""
        try:
            image_data = self._encode_image(image_path)
            ext = Path(image_path).suffix.lower().strip(".")
            mime_type = self._get_mime_type(ext)

            prompt = self._build_analysis_prompt(context)

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}",
                                    "detail": "high"
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                max_tokens=2000,
            )

            analysis_text = response.choices[0].message.content
            image_type = await self._classify_image_type(image_path)

            return {
                "description": analysis_text,
                "image_type": image_type,
                "has_text": await self._has_extractable_text(image_path),
                "embedding_text": self._create_embedding_text(analysis_text, image_type),
            }
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "description": f"Image analysis unavailable: {str(e)}",
                "image_type": "unknown",
                "has_text": False,
                "embedding_text": "Image content",
            }

    async def analyze_diagram(self, image_path: str) -> Dict:
        """Specialized analysis for technical diagrams"""
        image_data = self._encode_image(image_path)
        ext = Path(image_path).suffix.lower().strip(".")
        mime_type = self._get_mime_type(ext)

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this technical diagram in detail. Provide:
1. Type of diagram (flowchart, architecture, ERD, UML, network, etc.)
2. Main components and their relationships
3. Data flow or process flow if applicable
4. Key insights and important elements
5. Technical specifications visible in the diagram
6. Any text labels, annotations, or measurements
Format as structured analysis."""
                        }
                    ]
                }
            ],
            max_tokens=3000,
        )
        return {
            "analysis": response.choices[0].message.content,
            "type": "diagram"
        }

    async def extract_chart_data(self, image_path: str) -> Dict:
        """Extract data from charts and graphs"""
        image_data = self._encode_image(image_path)
        ext = Path(image_path).suffix.lower().strip(".")
        mime_type = self._get_mime_type(ext)

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Extract all data from this chart/graph:
1. Chart type (bar, line, pie, scatter, etc.)
2. Title and axis labels
3. All data points and values
4. Legend information
5. Trends and patterns
6. Key insights from the data
Provide the extracted data in a structured format."""
                        }
                    ]
                }
            ],
            max_tokens=2000,
        )
        return {
            "data": response.choices[0].message.content,
            "type": "chart"
        }

    async def _classify_image_type(self, image_path: str) -> str:
        """Classify what type of image this is"""
        image_data = self._encode_image(image_path)
        ext = Path(image_path).suffix.lower().strip(".")
        mime_type = self._get_mime_type(ext)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}",
                                    "detail": "low"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Classify this image in one word: diagram | chart | photo | screenshot | drawing | table | other"
                            }
                        ]
                    }
                ],
                max_tokens=10,
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return "image"

    async def _has_extractable_text(self, image_path: str) -> bool:
        """Check if image contains text that can be extracted"""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return len(text.strip()) > 20
        except Exception:
            return False

    def _create_embedding_text(self, analysis: str, image_type: str) -> str:
        """Create optimal text for embedding generation"""
        return f"[{image_type.upper()}] {analysis}"

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_mime_type(self, ext: str) -> str:
        types = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "gif": "image/gif",
            "bmp": "image/bmp", "webp": "image/webp",
            "tiff": "image/tiff",
        }
        return types.get(ext, "image/jpeg")

    def _build_analysis_prompt(self, context: str = "") -> str:
        base = """Analyze this image comprehensively for an enterprise knowledge base. Provide:
1. Detailed description of what's shown
2. Key information, data, or insights visible
3. Any text, labels, numbers, or annotations present
4. Technical or business relevance
5. Relationships between elements if applicable"""

        if context:
            base += f"\n\nDocument context: {context}"

        return base
