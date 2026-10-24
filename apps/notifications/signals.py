"""Project persisted domain transitions into the recipient inbox."""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .events import notify
from .models import Notification, NotificationDelivery, PushSubscription


@receiver(post_save, sender="challenges.Challenge")
def challenge_event(sender, instance, raw=False, **kwargs):
    if raw:
        return
    c = instance
    recipients = [c.opponent_id] if c.state == "pending" else [c.challenger_id, c.opponent_id]
    labels = {
        "pending": "دعوت به چالش",
        "accepted": "چالش پذیرفته شد",
        "declined": "چالش رد شد",
        "cancelled": "چالش لغو شد",
        "expired": "دعوت چالش منقضی شد",
        "completed": "چالش پایان یافت",
    }
    notify(
        recipients,
        f"challenge-{c.pk}-{c.state}",
        "challenge",
        labels[c.state],
        c.game_name,
        "my-challenges",
    )


@receiver(post_save, sender="matches.Match")
def match_event(sender, instance, raw=False, **kwargs):
    if raw:
        return
    m = instance
    labels = {
        "ready": "بازی آماده شروع است",
        "live": "بازی شروع شد",
        "awaiting-result": "نتیجه بازی را ثبت کن",
        "cancelled": "بازی لغو شد",
    }
    if m.state in labels:
        notify(
            [m.participant_a_id, m.participant_b_id],
            f"match-{m.pk}-{m.state}",
            "match",
            labels[m.state],
            m.game_name,
            "result-submission" if m.state == "awaiting-result" else "my-matches",
            str(m.pk) if m.state == "awaiting-result" else "",
        )


@receiver(post_save, sender="results.MatchResult")
def result_event(sender, instance, raw=False, **kwargs):
    if raw:
        return
    r = instance
    m = r.match
    if r.finalized_at:
        recipients = [m.participant_a_id, m.participant_b_id]
        title, stage = "نتیجه بازی نهایی شد", "finalized"
    else:
        recipients = [
            m.participant_b_id if r.reported_by_id == m.participant_a_id else m.participant_a_id
        ]
        title, stage = "نتیجه بازی نیاز به تأیید تو دارد", "reported"
    notify(
        recipients,
        f"result-{r.pk}-{stage}",
        "match",
        title,
        m.game_name,
        "result-submission",
        str(m.pk),
    )


@receiver(post_save, sender="disputes.Dispute")
def dispute_event(sender, instance, raw=False, **kwargs):
    if raw:
        return
    d = instance
    m = d.match
    labels = {
        "open": "اعتراض به نتیجه ثبت شد",
        "under-review": "اعتراض در حال بررسی است",
        "resolved": "رسیدگی به اعتراض پایان یافت",
    }
    notify(
        [m.participant_a_id, m.participant_b_id],
        f"dispute-{d.pk}-{d.status}",
        "match",
        labels[d.status],
        m.game_name,
        "match-dispute",
        str(m.pk),
    )


@receiver(post_save, sender="teams.TeamInvite")
def team_invite_event(sender, instance, raw=False, **kwargs):
    if raw:
        return
    i = instance
    recipients = [i.recipient_id] if i.state == "pending" else [i.invited_by_id]
    labels = {
        "pending": "دعوت به تیم",
        "accepted": "دعوت تیم پذیرفته شد",
        "declined": "دعوت تیم رد شد",
        "revoked": "دعوت تیم لغو شد",
    }
    notify(
        recipients,
        f"team-invite-{i.pk}-{i.state}",
        "account",
        labels[i.state],
        i.team.name,
        "my-teams",
    )


@receiver(post_save, sender="registrations.Registration")
def registration_event(sender, instance, raw=False, **kwargs):
    if not raw:
        r = instance
        notify(
            [r.user_id],
            f"registration-{r.pk}-{r.status}",
            "tournament",
            "وضعیت ثبت‌نام مسابقه",
            r.tournament.title,
            "tournament-detail",
            r.tournament.slug,
        )


@receiver(post_save, sender="checkins.CheckIn")
def checkin_event(sender, instance, raw=False, **kwargs):
    if not raw:
        r = instance.registration
        notify(
            [r.user_id],
            f"checkin-{instance.pk}",
            "tournament",
            "حضور تو تأیید شد",
            r.tournament.title,
            "tournament-detail",
            r.tournament.slug,
        )


@receiver(post_save, sender="achievements.AchievementProgress")
def achievement_event(sender, instance, raw=False, **kwargs):
    if not raw and instance.unlocked_at:
        notify(
            [instance.user_id],
            f"achievement-{instance.pk}-unlocked",
            "account",
            "دستاورد جدید باز شد",
            instance.definition.title,
            "my-achievements",
        )


@receiver(post_save, sender="tournaments.Tournament")
def tournament_event(sender, instance, raw=False, created=False, **kwargs):
    if raw or created or getattr(instance, "_old_lifecycle", None) == instance.lifecycle:
        return
    recipients = instance.registrations.filter(status="confirmed").values_list("user_id", flat=True)
    notify(
        recipients,
        f"tournament-{instance.pk}-{instance.lifecycle}",
        "tournament",
        "وضعیت مسابقه تغییر کرد",
        instance.title,
        "tournament-detail",
        instance.slug,
    )


@receiver(post_save, sender=Notification)
def queue_delivery(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw:
        return
    preference = getattr(instance.recipient, "notification_preference", None)
    if (
        preference
        and instance.kind in ("match", "challenge", "tournament")
        and not getattr(preference, instance.kind)
    ):
        return
    for sub in PushSubscription.objects.filter(recipient_id=instance.recipient_id, active=True):
        NotificationDelivery.objects.get_or_create(
            notification=instance,
            channel="push",
            destination_key=str(sub.pk),
            defaults={"subscription": sub},
        )
    NotificationDelivery.objects.get_or_create(
        notification=instance,
        channel="sms",
        destination_key="recipient",
    )


@receiver(pre_save, sender="tournaments.Tournament")
def remember_tournament_state(sender, instance, raw=False, **kwargs):
    if not raw:
        instance._old_lifecycle = (
            sender.objects.filter(pk=instance.pk).values_list("lifecycle", flat=True).first()
        )


@receiver(post_save, sender="rankings.AppliedMatchEvent")
def rating_event(sender, instance, created=False, raw=False, **kwargs):
    if created and not raw:
        for user, before, after in (
            (instance.user_a_id, instance.rating_a_before, instance.rating_a_after),
            (instance.user_b_id, instance.rating_b_before, instance.rating_b_after),
        ):
            notify(
                [user],
                f"rating-{instance.pk}",
                "match",
                "امتیاز رقابتی به‌روز شد",
                f"تغییر امتیاز: {after - before:+d}",
                "result-submission",
                str(instance.source_match_id),
            )


@receiver(post_save, sender="teams.TeamMembership")
def membership_event(sender, instance, raw=False, **kwargs):
    if not raw:
        notify(
            [instance.user_id],
            f"membership-{instance.pk}-{instance.role}",
            "account",
            "عضویت تیم به‌روز شد",
            instance.team.name,
            "my-teams",
        )


@receiver(post_delete, sender="teams.TeamMembership")
def membership_left(sender, instance, **kwargs):
    notify(
        [instance.user_id],
        f"membership-{instance.pk}-left",
        "account",
        "از تیم خارج شدی",
        "وضعیت عضویت تیم تغییر کرد",
        "my-teams",
    )
