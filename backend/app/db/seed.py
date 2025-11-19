"""Database seed script for sample quiz data."""

import asyncio
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.user import User


async def create_admin_user(session: AsyncSession) -> User:
    """Create default admin user.

    Args:
        session: Database session.

    Returns:
        Created admin user.
    """
    admin = User(
        telegram_id=1234567890,  # Replace with your Telegram ID
        username="admin",
        first_name="Admin",
        last_name="User",
        is_admin=True,
    )
    session.add(admin)
    await session.flush()
    logger.info(f"Created admin user: {admin.telegram_id}")
    return admin


async def create_hogwarts_quiz(session: AsyncSession, admin: User) -> None:
    """Create the Hogwarts House quiz with questions and result types.

    Args:
        session: Database session.
        admin: Admin user who creates the quiz.
    """
    # Create quiz
    quiz = Quiz(
        title="🏰 Which Hogwarts House Are You?",
        description=(
            "Discover which Hogwarts house you belong to! "
            "Are you brave like a Gryffindor, cunning like a Slytherin, "
            "wise like a Ravenclaw, or loyal like a Hufflepuff?"
        ),
        image_url="https://i.imgur.com/hogwarts.jpg",  # Replace with actual image
        is_active=True,
        created_by=admin.id,
    )
    session.add(quiz)
    await session.flush()
    logger.info(f"Created quiz: {quiz.title}")

    # Create result types
    result_types_data = [
        {
            "type_key": "gryffindor",
            "title": "🦁 Gryffindor",
            "description": (
                "You belong to Gryffindor! You are brave, daring, and chivalrous. "
                "You're not afraid to stand up for what's right, even in the face of danger. "
                "Famous Gryffindors: Harry Potter, Hermione Granger, Ron Weasley."
            ),
            "image_url": "https://i.imgur.com/gryffindor.jpg",
        },
        {
            "type_key": "slytherin",
            "title": "🐍 Slytherin",
            "description": (
                "You belong to Slytherin! You are ambitious, cunning, and resourceful. "
                "You know what you want and you're determined to get it. "
                "Famous Slytherins: Severus Snape, Draco Malfoy, Tom Riddle."
            ),
            "image_url": "https://i.imgur.com/slytherin.jpg",
        },
        {
            "type_key": "ravenclaw",
            "title": "🦅 Ravenclaw",
            "description": (
                "You belong to Ravenclaw! You are wise, creative, and value knowledge above all. "
                "Your sharp mind and wit help you solve problems others can't. "
                "Famous Ravenclaws: Luna Lovegood, Cho Chang, Filius Flitwick."
            ),
            "image_url": "https://i.imgur.com/ravenclaw.jpg",
        },
        {
            "type_key": "hufflepuff",
            "title": "🦡 Hufflepuff",
            "description": (
                "You belong to Hufflepuff! You are loyal, patient, and hardworking. "
                "You value friendship and fairness, and you're always there for those who need you. "
                "Famous Hufflepuffs: Cedric Diggory, Newt Scamander, Nymphadora Tonks."
            ),
            "image_url": "https://i.imgur.com/hufflepuff.jpg",
        },
    ]

    for rt_data in result_types_data:
        result_type = ResultType(
            quiz_id=quiz.id,
            type_key=rt_data["type_key"],
            title=rt_data["title"],
            description=rt_data["description"],
            image_url=rt_data["image_url"],
        )
        session.add(result_type)

    await session.flush()
    logger.info("Created 4 result types")

    # Create questions and answers
    questions_data = [
        {
            "text": "What's your favorite color?",
            "order": 0,
            "answers": [
                {"text": "🔴 Red & Gold", "result": "gryffindor", "weight": 3},
                {"text": "🟢 Green & Silver", "result": "slytherin", "weight": 3},
                {"text": "🔵 Blue & Bronze", "result": "ravenclaw", "weight": 3},
                {"text": "🟡 Yellow & Black", "result": "hufflepuff", "weight": 3},
            ],
        },
        {
            "text": "What do you value most in life?",
            "order": 1,
            "answers": [
                {"text": "⚔️ Bravery and courage", "result": "gryffindor", "weight": 5},
                {"text": "👑 Ambition and power", "result": "slytherin", "weight": 5},
                {"text": "📚 Knowledge and wisdom", "result": "ravenclaw", "weight": 5},
                {"text": "🤝 Loyalty and friendship", "result": "hufflepuff", "weight": 5},
            ],
        },
        {
            "text": "How would your friends describe you?",
            "order": 2,
            "answers": [
                {"text": "🦸 Bold and adventurous", "result": "gryffindor", "weight": 4},
                {"text": "🎯 Determined and strategic", "result": "slytherin", "weight": 4},
                {"text": "🧠 Clever and creative", "result": "ravenclaw", "weight": 4},
                {"text": "💛 Kind and dependable", "result": "hufflepuff", "weight": 4},
            ],
        },
        {
            "text": "What's your ideal way to spend a weekend?",
            "order": 3,
            "answers": [
                {"text": "🏃 Trying a new adventure", "result": "gryffindor", "weight": 3},
                {"text": "📈 Working on a personal goal", "result": "slytherin", "weight": 3},
                {"text": "📖 Reading or learning something new", "result": "ravenclaw", "weight": 3},
                {"text": "👥 Spending time with loved ones", "result": "hufflepuff", "weight": 3},
            ],
        },
        {
            "text": "Which magical creature would you choose as a pet?",
            "order": 4,
            "answers": [
                {"text": "🦁 A majestic lion", "result": "gryffindor", "weight": 2},
                {"text": "🐍 A clever serpent", "result": "slytherin", "weight": 2},
                {"text": "🦅 A wise owl", "result": "ravenclaw", "weight": 2},
                {"text": "🦡 A loyal badger", "result": "hufflepuff", "weight": 2},
            ],
        },
        {
            "text": "What role would you play in a team project?",
            "order": 5,
            "answers": [
                {"text": "🌟 The bold leader", "result": "gryffindor", "weight": 4},
                {"text": "🎯 The strategic planner", "result": "slytherin", "weight": 4},
                {"text": "💡 The creative problem-solver", "result": "ravenclaw", "weight": 4},
                {"text": "🤲 The supportive team player", "result": "hufflepuff", "weight": 4},
            ],
        },
    ]

    for q_data in questions_data:
        question = Question(
            quiz_id=quiz.id, text=q_data["text"], order_index=q_data["order"]
        )
        session.add(question)
        await session.flush()

        a_data: dict[str, Any]
        for idx, a_data in enumerate(q_data["answers"]):  # type: ignore[arg-type]
            answer = Answer(
                question_id=question.id,
                text=a_data["text"],
                result_type=a_data["result"],
                weight=a_data["weight"],
                order_index=idx,
            )
            session.add(answer)

    await session.flush()
    logger.info(f"Created {len(questions_data)} questions with answers")


async def seed_database() -> None:
    """Seed the database with initial data."""
    logger.info("Starting database seeding...")

    async with AsyncSessionLocal() as session:
        try:
            # Create admin user
            admin = await create_admin_user(session)

            # Create Hogwarts quiz
            await create_hogwarts_quiz(session, admin)

            # Commit all changes
            await session.commit()

            logger.info("✅ Database seeded successfully!")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error seeding database: {e}")
            raise


if __name__ == "__main__":
    # Run the seed script
    asyncio.run(seed_database())
