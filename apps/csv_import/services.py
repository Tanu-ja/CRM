import csv
import io
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_action
from apps.leads.models import Lead
from apps.leads.services import allocate_lead_id_block
from apps.leads.utils import normalize_phone

from .models import ImportBatch

# Flexible header matching, e.g. "Full Name" / "name" both map to "name".
HEADER_ALIASES = {
    "name": "name",
    "fullname": "name",
    "phone": "phone",
    "mobile": "phone",
    "mobilenumber": "phone",
    "whatsapp": "whatsapp_phone",
    "whatsappnumber": "whatsapp_phone",
    "alternatephone": "alternate_phone",
    "alternatenumber": "alternate_phone",
    "email": "email",
    "source": "original_source",
    "campaign": "original_campaign",
    "ad": "original_ad",
    "adset": "original_ad_set",
}


def _clean_header(raw: str) -> str:
    return re.sub(r"[^a-z0-9]", "", raw.strip().lower())


def _map_row(row: dict) -> dict:
    mapped = {}
    for raw_key, value in row.items():
        field = HEADER_ALIASES.get(_clean_header(raw_key or ""))
        if field:
            mapped[field] = (value or "").strip()
    return mapped


class CsvImportError(Exception):
    pass


def process_csv(*, file_obj, client, uploaded_by, filename: str) -> ImportBatch:
    max_rows = getattr(settings, "CSV_IMPORT_MAX_ROWS", 5000)

    text = io.TextIOWrapper(file_obj, encoding="utf-8-sig")
    rows = list(csv.DictReader(text))
    if len(rows) > max_rows:
        raise CsvImportError(f"File has {len(rows)} rows, which exceeds the {max_rows}-row limit.")

    # Preload existing normalized phones for this client once (O(1) membership
    # checks) instead of one duplicate-lookup query per row.
    existing_phones = set(
        Lead.objects.filter(client=client)
        .values_list("phone_normalized", "whatsapp_phone_normalized", "alternate_phone_normalized")
    )
    existing_flat = {p for triple in existing_phones for p in triple if p}

    valid_rows = []
    errors = []
    duplicate_count = 0
    invalid_count = 0
    seen_in_batch = set()

    for i, raw_row in enumerate(rows, start=1):
        mapped = _map_row(raw_row)
        phone_norm = normalize_phone(mapped.get("phone", ""))
        whatsapp_norm = normalize_phone(mapped.get("whatsapp_phone", ""))
        alternate_norm = normalize_phone(mapped.get("alternate_phone", ""))

        if len(phone_norm) < 8:
            invalid_count += 1
            if len(errors) < 10:
                errors.append(f"Row {i}: invalid phone '{mapped.get('phone', '')}'")
            continue

        candidates = {v for v in (phone_norm, whatsapp_norm, alternate_norm) if v}
        if candidates & existing_flat or candidates & seen_in_batch:
            duplicate_count += 1
            continue

        seen_in_batch |= candidates
        valid_rows.append(
            {
                "name": mapped.get("name", ""),
                "phone": mapped.get("phone", ""),
                "whatsapp_phone": mapped.get("whatsapp_phone", ""),
                "alternate_phone": mapped.get("alternate_phone", ""),
                "email": mapped.get("email", ""),
                "original_source": mapped.get("original_source", "csv_import"),
                "original_campaign": mapped.get("original_campaign", ""),
                "original_ad": mapped.get("original_ad", ""),
                "original_ad_set": mapped.get("original_ad_set", ""),
                "phone_normalized": phone_norm,
                "whatsapp_phone_normalized": whatsapp_norm,
                "alternate_phone_normalized": alternate_norm,
            }
        )

    lead_ids = allocate_lead_id_block(client, len(valid_rows))

    with transaction.atomic():
        leads = [
            Lead(
                client=client,
                created_by=uploaded_by,
                lead_id=lead_id,
                first_touch_at=timezone.now(),
                **row,
            )
            for row, lead_id in zip(valid_rows, lead_ids)
        ]
        Lead.objects.bulk_create(leads)

        batch = ImportBatch.objects.create(
            uploaded_by=uploaded_by,
            client=client,
            filename=filename,
            row_count=len(rows),
            created_count=len(leads),
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
            errors=errors,
        )

    log_action(
        actor=uploaded_by,
        action="leads.csv_imported",
        entity="ImportBatch",
        entity_id=batch.pk,
        detail=f"{filename}: {batch.created_count} created, {duplicate_count} duplicates, {invalid_count} invalid",
    )
    return batch
