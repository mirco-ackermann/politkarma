from modeltranslation.translator import register, TranslationOptions

from apps.curia_vista.models import *


@register(Council)
class CouncilTranslationOptions(TranslationOptions):
    fields = ('name', 'abbreviation')


@register(AffairSummary)
class AffairSummaryTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(Committee)
class CommitteeTranslationOptions(TranslationOptions):
    fields = ('name', 'abbreviation')


@register(LegislativePeriod)
class LegislativePeriodTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Department)
class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name', 'abbreviation')


@register(Canton)
class CantonTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Faction)
class FactionTranslationOptions(TranslationOptions):
    fields = ('name', 'short_name')


@register(Session)
class SessionTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Party)
class PartyTranslationOptions(TranslationOptions):
    fields = ('name', 'abbreviation')


@register(AffairVote)
class AffairVoteTranslationOptions(TranslationOptions):
    fields = ('division_text', 'meaning_no', 'meaning_yes', 'submission_text')
