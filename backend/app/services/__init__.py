"""Read models and writes, one module per screen or concern.

Every function takes an open connection and the signed-in user (a dict with at least
`id`, `timezone`, `preferred_list`, `weekly_sessions`, `design_sessions`, `design_minutes`,
`started_on`) and returns exactly what one screen needs. Every query filters on the user's
id: that filter is the isolation boundary between accounts.
"""
