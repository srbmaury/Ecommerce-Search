"""
Shared rate limiter instance.

Created without an app so route modules can import `limiter` and apply
`@limiter.limit(...)` at decoration time; `limiter.init_app(app)` binds it
(and its Redis storage) during app creation.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
