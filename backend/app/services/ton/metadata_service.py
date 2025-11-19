"""NFT metadata generation service following TON NFT standards."""

from datetime import datetime
from typing import Any

from loguru import logger

from app.models.quiz import Quiz
from app.models.result import QuizResult


class MetadataService:
    """Service for generating NFT metadata according to TON standards.

    TON NFT Metadata Standard:
    - name: NFT name
    - description: NFT description
    - image: IPFS URL to the image
    - attributes: Array of traits/properties
    - external_url: Optional link to external resource
    """

    def generate_nft_metadata(
        self,
        quiz_result: QuizResult,
        quiz: Quiz,
        image_url: str,
    ) -> dict[str, Any]:
        """Generate NFT metadata for quiz result.

        Args:
            quiz_result: Quiz result object.
            quiz: Quiz object.
            image_url: IPFS URL to NFT image.

        Returns:
            NFT metadata dictionary following TON NFT standard.
        """
        try:
            # Get result type info
            result_type_obj = next(
                (rt for rt in quiz.result_types if rt.type_key == quiz_result.result_type),
                None,
            )

            result_title = result_type_obj.title if result_type_obj else quiz_result.result_type
            result_description = (
                result_type_obj.description if result_type_obj else "Your quiz result"
            )

            # Generate name
            name = f"{result_title} - {quiz.title}"

            # Generate description
            description = (
                f"🎯 Quiz Result NFT\n\n"
                f"{result_description}\n\n"
                f"Quiz: {quiz.title}\n"
                f"Score: {quiz_result.score} points\n"
                f"Completed: {quiz_result.completed_at.strftime('%Y-%m-%d')}"
            )

            # Generate attributes
            attributes = [
                {
                    "trait_type": "Quiz",
                    "value": quiz.title,
                },
                {
                    "trait_type": "Result Type",
                    "value": result_title,
                },
                {
                    "trait_type": "Score",
                    "value": str(quiz_result.score),
                    "display_type": "number",
                },
                {
                    "trait_type": "Completion Date",
                    "value": quiz_result.completed_at.strftime("%Y-%m-%d"),
                    "display_type": "date",
                },
                {
                    "trait_type": "Total Questions",
                    "value": str(len(quiz.questions)),
                    "display_type": "number",
                },
            ]

            # Build metadata following TON NFT standard
            metadata: dict[str, Any] = {
                "name": name,
                "description": description,
                "image": image_url,
                "attributes": attributes,
                "external_url": f"https://t.me/your_bot?start=result_{quiz_result.id}",
            }

            logger.info(
                f"Generated NFT metadata for result {quiz_result.id}: {metadata['name']}"
            )
            return metadata

        except Exception as e:
            logger.exception(f"Error generating NFT metadata: {e}")
            raise

    def validate_metadata(self, metadata: dict[str, Any]) -> bool:
        """Validate NFT metadata structure.

        Args:
            metadata: Metadata dictionary to validate.

        Returns:
            True if valid, False otherwise.
        """
        required_fields = ["name", "description", "image"]

        for field in required_fields:
            if field not in metadata:
                logger.error(f"Missing required field in metadata: {field}")
                return False

        # Validate name is not empty
        if not metadata.get("name"):
            logger.error("NFT name cannot be empty")
            return False

        # Validate image URL
        image_url = metadata.get("image", "")
        if not (image_url.startswith("ipfs://") or image_url.startswith("https://")):
            logger.error(f"Invalid image URL format: {image_url}")
            return False

        # Validate attributes format
        if "attributes" in metadata:
            if not isinstance(metadata["attributes"], list):
                logger.error("Attributes must be an array")
                return False

            for attr in metadata["attributes"]:
                if not isinstance(attr, dict):
                    logger.error("Each attribute must be an object")
                    return False
                if "trait_type" not in attr or "value" not in attr:
                    logger.error("Attributes must have trait_type and value")
                    return False

        logger.debug("Metadata validation passed")
        return True

    async def generate_default_image_data(self, result_type: str) -> bytes:
        """Generate default image for result type (placeholder).

        Args:
            result_type: Result type key.

        Returns:
            Image data as bytes.

        Note:
            This is a placeholder. In production, you should generate
            or fetch actual images based on result type.
        """
        from io import BytesIO

        from PIL import Image, ImageDraw, ImageFont

        try:
            # Create a simple colored image
            colors = {
                "gryffindor": "#740001",
                "slytherin": "#1A472A",
                "ravenclaw": "#0E1A40",
                "hufflepuff": "#FFD800",
                "default": "#4A90E2",
            }

            color = colors.get(result_type.lower(), colors["default"])

            # Create image
            img = Image.new("RGB", (512, 512), color)
            draw = ImageDraw.Draw(img)

            # Add text (result type)
            text = result_type.upper()
            try:
                # Try to use a nice font
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except Exception:
                # Fallback to default font
                font = ImageFont.load_default()

            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((512 - text_width) // 2, (512 - text_height) // 2)

            draw.text(position, text, fill="white", font=font)

            # Save to bytes
            output = BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Error generating default image: {e}")
            # Return minimal PNG if all else fails
            img = Image.new("RGB", (512, 512), "#4A90E2")
            output = BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()


# Global instance
metadata_service = MetadataService()
