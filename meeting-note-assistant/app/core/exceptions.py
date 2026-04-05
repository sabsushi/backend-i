class MeetingNoteAssistantError(Exception):
    pass


class ValidationError(MeetingNoteAssistantError):
    pass


class NotFoundError(MeetingNoteAssistantError):
    pass
