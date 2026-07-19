"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]] · [[adr-03-api-and-backend]] · [[adr-10-auth]]
Docs: [[BACKEND]] · [[CHATBOT]]
API: [[API]]
LIVE-DOC:END"""

"""Permission gate for the chatbot router's choosing tier ([[adr-15-chatbot-two-tier]]).

`ai_operators` is a router-only group: it MUST NEVER be added to any other
permission class. `CanUseRouter` shares the check *shape* of
`apps.users.permissions.HasAnyGroup` (also used by `IsInAdminsGroup`) but
widens the accepted group set to either `admins` or `ai_operators`.
"""

from apps.users.permissions import ADMINS_GROUP, HasAnyGroup

AI_OPERATORS_GROUP = "ai_operators"


class CanUseRouter(HasAnyGroup):
    group_names = (ADMINS_GROUP, AI_OPERATORS_GROUP)
