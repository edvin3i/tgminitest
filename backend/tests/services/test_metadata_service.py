"""Tests for NFT metadata generation service."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.models.quiz import Quiz, ResultType
from app.models.result import QuizResult
from app.services.ton.metadata_service import MetadataService


@pytest.fixture
def metadata_service() -> MetadataService:
    """Create metadata service instance.

    Returns:
        MetadataService instance.
    """
    return MetadataService()


@pytest.fixture
def sample_quiz() -> Quiz:
    """Create sample quiz with result types.

    Returns:
        Quiz instance.
    """
    quiz = Quiz(
        id=1,
        title="Hogwarts House Quiz",
        description="Find your house!",
        created_by=1,
        is_active=True,
    )

    # Add result types
    quiz.result_types = [
        ResultType(
            id=1,
            quiz_id=1,
            type_key="gryffindor",
            title="Gryffindor",
            description="Brave and daring!",
        ),
        ResultType(
            id=2,
            quiz_id=1,
            type_key="slytherin",
            title="Slytherin",
            description="Ambitious and cunning!",
        ),
    ]

    # Add questions
    quiz.questions = [MagicMock(), MagicMock(), MagicMock()]  # 3 questions

    return quiz


@pytest.fixture
def sample_quiz_result(sample_quiz: Quiz) -> QuizResult:
    """Create sample quiz result.

    Args:
        sample_quiz: Quiz fixture.

    Returns:
        QuizResult instance.
    """
    return QuizResult(
        id=1,
        user_id=1,
        quiz_id=sample_quiz.id,
        result_type="gryffindor",
        score=85,
        answers_data={"1": 1, "2": 2, "3": 3},
        completed_at=datetime(2025, 1, 15, 12, 30, 0, tzinfo=UTC),
    )


# ==================== Metadata Generation Tests ====================


def test_generate_nft_metadata_success(
    metadata_service: MetadataService,
    sample_quiz: Quiz,
    sample_quiz_result: QuizResult,
) -> None:
    """Test successful NFT metadata generation."""
    image_url = "ipfs://QmTest123"

    metadata = metadata_service.generate_nft_metadata(
        quiz_result=sample_quiz_result,
        quiz=sample_quiz,
        image_url=image_url,
    )

    # Verify structure
    assert "name" in metadata
    assert "description" in metadata
    assert "image" in metadata
    assert "attributes" in metadata
    assert "external_url" in metadata

    # Verify content
    assert metadata["name"] == "Gryffindor - Hogwarts House Quiz"
    assert "Brave and daring!" in metadata["description"]
    assert "85 points" in metadata["description"]
    assert "2025-01-15" in metadata["description"]
    assert metadata["image"] == image_url

    # Verify attributes
    attributes = metadata["attributes"]
    assert len(attributes) == 5

    # Check specific attributes
    quiz_attr = next(a for a in attributes if a["trait_type"] == "Quiz")
    assert quiz_attr["value"] == "Hogwarts House Quiz"

    result_attr = next(a for a in attributes if a["trait_type"] == "Result Type")
    assert result_attr["value"] == "Gryffindor"

    score_attr = next(a for a in attributes if a["trait_type"] == "Score")
    assert score_attr["value"] == "85"
    assert score_attr["display_type"] == "number"

    questions_attr = next(a for a in attributes if a["trait_type"] == "Total Questions")
    assert questions_attr["value"] == "3"


def test_generate_nft_metadata_unknown_result_type(
    metadata_service: MetadataService,
    sample_quiz: Quiz,
    sample_quiz_result: QuizResult,
) -> None:
    """Test metadata generation with unknown result type."""
    sample_quiz_result.result_type = "unknown_type"
    image_url = "ipfs://QmTest456"

    metadata = metadata_service.generate_nft_metadata(
        quiz_result=sample_quiz_result,
        quiz=sample_quiz,
        image_url=image_url,
    )

    # Should use result_type as fallback
    assert metadata["name"] == "unknown_type - Hogwarts House Quiz"
    assert "Your quiz result" in metadata["description"]


def test_generate_nft_metadata_no_result_types(
    metadata_service: MetadataService,
    sample_quiz: Quiz,
    sample_quiz_result: QuizResult,
) -> None:
    """Test metadata generation when quiz has no result types."""
    sample_quiz.result_types = []
    image_url = "ipfs://QmTest789"

    metadata = metadata_service.generate_nft_metadata(
        quiz_result=sample_quiz_result,
        quiz=sample_quiz,
        image_url=image_url,
    )

    # Should use result_type as fallback
    assert metadata["name"] == "gryffindor - Hogwarts House Quiz"
    assert "Your quiz result" in metadata["description"]


# ==================== Metadata Validation Tests ====================


def test_validate_metadata_valid(metadata_service: MetadataService) -> None:
    """Test validation of valid metadata."""
    valid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "ipfs://QmTest123",
        "attributes": [
            {"trait_type": "Test", "value": "Value"},
        ],
    }

    assert metadata_service.validate_metadata(valid_metadata) is True


def test_validate_metadata_valid_https_image(metadata_service: MetadataService) -> None:
    """Test validation with HTTPS image URL."""
    valid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "https://example.com/image.png",
    }

    assert metadata_service.validate_metadata(valid_metadata) is True


def test_validate_metadata_missing_name(metadata_service: MetadataService) -> None:
    """Test validation fails with missing name."""
    invalid_metadata = {
        "description": "Test description",
        "image": "ipfs://QmTest123",
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_missing_description(metadata_service: MetadataService) -> None:
    """Test validation fails with missing description."""
    invalid_metadata = {
        "name": "Test NFT",
        "image": "ipfs://QmTest123",
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_missing_image(metadata_service: MetadataService) -> None:
    """Test validation fails with missing image."""
    invalid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_empty_name(metadata_service: MetadataService) -> None:
    """Test validation fails with empty name."""
    invalid_metadata = {
        "name": "",
        "description": "Test description",
        "image": "ipfs://QmTest123",
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_invalid_image_url(metadata_service: MetadataService) -> None:
    """Test validation fails with invalid image URL."""
    invalid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "http://example.com/image.png",  # HTTP not allowed
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_invalid_attributes_type(
    metadata_service: MetadataService,
) -> None:
    """Test validation fails when attributes is not a list."""
    invalid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "ipfs://QmTest123",
        "attributes": "not a list",  # Invalid
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_invalid_attribute_format(
    metadata_service: MetadataService,
) -> None:
    """Test validation fails with invalid attribute format."""
    invalid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "ipfs://QmTest123",
        "attributes": [
            "not a dict",  # Should be dict
        ],
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_missing_trait_type(metadata_service: MetadataService) -> None:
    """Test validation fails when attribute missing trait_type."""
    invalid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "ipfs://QmTest123",
        "attributes": [
            {"value": "Test"},  # Missing trait_type
        ],
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


def test_validate_metadata_missing_value(metadata_service: MetadataService) -> None:
    """Test validation fails when attribute missing value."""
    invalid_metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "ipfs://QmTest123",
        "attributes": [
            {"trait_type": "Test"},  # Missing value
        ],
    }

    assert metadata_service.validate_metadata(invalid_metadata) is False


# ==================== Default Image Generation Tests ====================


@pytest.mark.asyncio
async def test_generate_default_image_data_gryffindor(
    metadata_service: MetadataService,
) -> None:
    """Test generating default image for Gryffindor."""
    image_data = await metadata_service.generate_default_image_data("gryffindor")

    assert isinstance(image_data, bytes)
    assert len(image_data) > 0
    # PNG signature
    assert image_data[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_generate_default_image_data_slytherin(
    metadata_service: MetadataService,
) -> None:
    """Test generating default image for Slytherin."""
    image_data = await metadata_service.generate_default_image_data("slytherin")

    assert isinstance(image_data, bytes)
    assert len(image_data) > 0
    assert image_data[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_generate_default_image_data_unknown_type(
    metadata_service: MetadataService,
) -> None:
    """Test generating default image for unknown type (uses default color)."""
    image_data = await metadata_service.generate_default_image_data("unknown_type")

    assert isinstance(image_data, bytes)
    assert len(image_data) > 0
    assert image_data[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_generate_default_image_data_uppercase(
    metadata_service: MetadataService,
) -> None:
    """Test that result type is case-insensitive."""
    image_data = await metadata_service.generate_default_image_data("GRYFFINDOR")

    assert isinstance(image_data, bytes)
    assert len(image_data) > 0


# ==================== Integration Tests ====================


def test_generate_and_validate_metadata(
    metadata_service: MetadataService,
    sample_quiz: Quiz,
    sample_quiz_result: QuizResult,
) -> None:
    """Test that generated metadata passes validation."""
    metadata = metadata_service.generate_nft_metadata(
        quiz_result=sample_quiz_result,
        quiz=sample_quiz,
        image_url="ipfs://QmTest123",
    )

    # Generated metadata should be valid
    assert metadata_service.validate_metadata(metadata) is True
