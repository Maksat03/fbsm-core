from django.conf import settings
from rest_framework.exceptions import ValidationError


def save_objects_changes(
    model,
    currents,
    news,
    comparison_field1,
    comparison_field2=None,
    update_fields=None,
    deleting_status=None,
):
    creates = []
    updates = []

    deletes = list(currents)
    news = list(news)

    for new in news:
        found = None

        for delete in deletes:
            delete_field = getattr(delete, comparison_field1)
            new_field = getattr(new, comparison_field1)

            if delete_field and new_field and (delete_field == new_field):
                found = delete
                break

        if not found and comparison_field2:
            for delete in deletes:
                delete_field = getattr(delete, comparison_field2)
                new_field = getattr(new, comparison_field2)

                if delete_field and new_field and (delete_field == new_field):
                    found = delete
                    break

        if found:
            new.id = found.id
            deletes.remove(found)
            updates.append(new)
        else:
            creates.append(new)

    if deleting_status:
        model.objects.filter(id__in=[delete.id for delete in deletes]).update(
            **deleting_status
        )
    else:
        model.objects.filter(id__in=[delete.id for delete in deletes]).delete()

    if update_fields:
        model.objects.bulk_update(updates, update_fields)

    model.objects.bulk_create(creates)


def validate_cdn_link(url):
    if settings.CDN_LINK not in url:
        raise ValidationError("Нужна ссылка на CDN.")

    return url
