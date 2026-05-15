# Re-export Base + import all models so Alembic can see them
from app.db.base_class import Base, metadata  # noqa

# These imports make the models available for create_all / Alembic autogenerate
from app.models.user import User  # noqa
from app.models.workspace import Workspace, WorkspaceMember  # noqa
from app.models.document import Document  # noqa
from app.models.chunk import DocumentChunk  # noqa
from app.models.chat import ChatSession, ChatMessage  # noqa
from app.models.query_log import QueryLog  # noqa
