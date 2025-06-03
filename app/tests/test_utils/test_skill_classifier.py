# /home/pablo/app/tests/test_utils/test_skill_classifier.py
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.ats.utils.skill_classifier import SkillClassifier

import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_skill_classifier_init():
    """Test initialization of SkillClassifier."""
    classifier = SkillClassifier()
    assert classifier is not None
    assert classifier.model is not None
    logger.info("SkillClassifier initialization test passed")

@pytest.mark.asyncio
async def test_classify_text():
    """Test classifying text for skills."""
    classifier = SkillClassifier()
    text = "Experienced in Python programming and machine learning."
    with patch.object(classifier.model, 'predict', return_value=[{'label': 'Python', 'score': 0.9}, {'label': 'Machine Learning', 'score': 0.85}]):
        skills = await classifier.classify_text(text)
        assert isinstance(skills, list)
        assert len(skills) == 2
        assert skills[0]['label'] == 'Python'
        assert skills[1]['label'] == 'Machine Learning'
        logger.info("Classify text test passed")

@pytest.mark.asyncio
async def test_classify_text_no_skills():
    """Test classifying text with no detectable skills."""
    classifier = SkillClassifier()
    text = "General discussion about work."
    with patch.object(classifier.model, 'predict', return_value=[]):
        skills = await classifier.classify_text(text)
        assert isinstance(skills, list)
        assert len(skills) == 0
        logger.info("Classify text with no skills test passed")

@pytest.mark.asyncio
async def test_classify_text_error():
    """Test error handling in text classification."""
    classifier = SkillClassifier()
    text = "This should raise an error."
    with patch.object(classifier.model, 'predict', side_effect=Exception("Model error")):
        try:
            await classifier.classify_text(text)
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "Model error"
            logger.info("Classify text error handling test passed")

@pytest.mark.asyncio
async def test_batch_classify():
    """Test batch classification of multiple texts."""
    classifier = SkillClassifier()
    texts = ["Text about Python", "Text about JavaScript"]
    with patch.object(classifier.model, 'predict', side_effect=[ [{'label': 'Python', 'score': 0.9}], [{'label': 'JavaScript', 'score': 0.88}] ]):
        results = await classifier.batch_classify(texts)
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0][0]['label'] == 'Python'
        assert results[1][0]['label'] == 'JavaScript'
        logger.info("Batch classify test passed")
