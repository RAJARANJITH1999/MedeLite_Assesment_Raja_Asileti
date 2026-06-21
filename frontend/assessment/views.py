import json

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from assessment import backend_client
from assessment.forms import CCNLookupForm, ManualInputsForm
from assessment.models import SavedLookup

SESSION_FACILITY = "facility_data"
SESSION_MANUAL = "manual_inputs"
SESSION_AI_SUMMARY = "ai_summary"
SESSION_AI_GENERATED_BY = "ai_generated_by"

SESSION_CHAT_COUNT = "sanavox_question_count"
SESSION_OFF_TOPIC_STRIKES = "sanavox_off_topic_strikes"
CHAT_QUESTION_LIMIT = 3
OFF_TOPIC_GRACE_LIMIT = 2  # first 2 off-topic questions are free warnings


def lookup_view(request):
    form = CCNLookupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        ccn = form.cleaned_data["ccn"]
        name_override = form.cleaned_data["facility_name_override"]
        try:
            facility = backend_client.get_facility(ccn)
        except backend_client.BackendError as exc:
            form.add_error("ccn", str(exc))
        else:
            request.session[SESSION_FACILITY] = facility
            request.session[SESSION_MANUAL] = {"facility_name_override": name_override}
            request.session.pop(SESSION_AI_SUMMARY, None)
            return redirect("manual_inputs")

    return render(request, "assessment/lookup.html", {"form": form})


def manual_inputs_view(request):
    facility = request.session.get(SESSION_FACILITY)
    if not facility:
        messages.info(request, "Start by looking up a facility's CCN.")
        return redirect("lookup")

    existing = request.session.get(SESSION_MANUAL, {})
    form = ManualInputsForm(request.POST or existing or None)

    if request.method == "POST" and form.is_valid():
        manual = dict(form.cleaned_data)
        manual["facility_name_override"] = existing.get("facility_name_override", "")

        try:
            insights = backend_client.get_insights(facility, manual)
        except backend_client.BackendError as exc:
            messages.warning(request, f"AI insights unavailable: {exc}")
            insights = {"summary": "", "generated_by": "unavailable"}

        request.session[SESSION_MANUAL] = manual
        request.session[SESSION_AI_SUMMARY] = insights["summary"]
        request.session[SESSION_AI_GENERATED_BY] = insights["generated_by"]

        SavedLookup.objects.create(
            ccn=facility["ccn"],
            facility_name=manual.get("facility_name_override") or facility["facility_name_from_cms"],
            state=facility["state"],
            overall_rating=facility.get("overall_rating"),
            facility_data=facility,
            manual_inputs=manual,
            ai_summary=insights["summary"],
            ai_summary_generated_by=insights["generated_by"],
        )

        return redirect("results")

    return render(request, "assessment/manual_inputs.html", {"form": form, "facility": facility})


def _build_chart_data(facility):
    return {
        "ratings": {
            "labels": ["Overall", "Health Inspection", "Staffing", "Quality of Resident Care"],
            "values": [
                facility.get("overall_rating"),
                facility.get("health_inspection_rating"),
                facility.get("staffing_rating"),
                facility.get("quality_rating"),
            ],
        },
        "claims_percent": {
            "labels": ["STR Hospitalization", "STR ED Visit"],
            "facility": [facility["str_hospitalization"]["facility_value"], facility["str_ed_visit"]["facility_value"]],
            "national": [facility["str_hospitalization"]["national_avg"], facility["str_ed_visit"]["national_avg"]],
            "state": [facility["str_hospitalization"]["state_avg"], facility["str_ed_visit"]["state_avg"]],
        },
        "claims_rate": {
            "labels": ["LT Hospitalization", "LT ED Visit"],
            "facility": [facility["lt_hospitalization"]["facility_value"], facility["lt_ed_visit"]["facility_value"]],
            "national": [facility["lt_hospitalization"]["national_avg"], facility["lt_ed_visit"]["national_avg"]],
            "state": [facility["lt_hospitalization"]["state_avg"], facility["lt_ed_visit"]["state_avg"]],
        },
    }


def _render_results(request, facility, manual, ai_summary, ai_generated_by, download_pdf_url, download_docx_url, viewing_saved=False):
    display_name = manual.get("facility_name_override") or facility["facility_name_from_cms"]
    return render(
        request,
        "assessment/results.html",
        {
            "facility": facility,
            "manual": manual,
            "display_name": display_name,
            "ai_summary": ai_summary,
            "ai_generated_by": ai_generated_by,
            "chart_data_json": json.dumps(_build_chart_data(facility)),
            "download_pdf_url": download_pdf_url,
            "download_docx_url": download_docx_url,
            "viewing_saved": viewing_saved,
        },
    )


def results_view(request):
    facility = request.session.get(SESSION_FACILITY)
    manual = request.session.get(SESSION_MANUAL)
    if not facility or not manual:
        return redirect("lookup")

    return _render_results(
        request,
        facility,
        manual,
        request.session.get(SESSION_AI_SUMMARY, ""),
        request.session.get(SESSION_AI_GENERATED_BY, ""),
        reverse("download", args=["pdf"]),
        reverse("download", args=["docx"]),
    )


def saved_lookup_detail_view(request, pk):
    lookup = get_object_or_404(SavedLookup, pk=pk)
    return _render_results(
        request,
        lookup.facility_data,
        lookup.manual_inputs,
        lookup.ai_summary,
        lookup.ai_summary_generated_by,
        reverse("download_saved", args=[pk, "pdf"]),
        reverse("download_saved", args=[pk, "docx"]),
        viewing_saved=True,
    )


def download_view(request, file_format):
    if file_format not in ("pdf", "docx"):
        return HttpResponse(status=404)

    facility = request.session.get(SESSION_FACILITY)
    manual = request.session.get(SESSION_MANUAL)
    if not facility or not manual:
        return redirect("lookup")

    ai_summary = request.session.get(SESSION_AI_SUMMARY) or None

    try:
        content, content_type = backend_client.export_file(facility, manual, ai_summary, file_format)
    except backend_client.BackendError as exc:
        messages.error(request, str(exc))
        return redirect("results")

    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="facility-assessment-{facility["ccn"]}.{file_format}"'
    return response


def download_saved_view(request, pk, file_format):
    if file_format not in ("pdf", "docx"):
        return HttpResponse(status=404)

    lookup = get_object_or_404(SavedLookup, pk=pk)
    ai_summary = lookup.ai_summary or None

    try:
        content, content_type = backend_client.export_file(lookup.facility_data, lookup.manual_inputs, ai_summary, file_format)
    except backend_client.BackendError as exc:
        messages.error(request, str(exc))
        return redirect("saved_lookup_detail", pk=pk)

    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="facility-assessment-{lookup.ccn}.{file_format}"'
    return response


def history_view(request):
    lookups = SavedLookup.objects.all()[:100]
    return render(request, "assessment/history.html", {"lookups": lookups})


@ensure_csrf_cookie
def compare_view(request):
    ids = request.GET.getlist("id")
    lookups = list(SavedLookup.objects.filter(id__in=ids)) if ids else []
    chat_payload = [{"facility": lookup.facility_data, "manual": lookup.manual_inputs} for lookup in lookups]
    used = request.session.get(SESSION_CHAT_COUNT, 0)
    return render(
        request,
        "assessment/compare.html",
        {
            "lookups": lookups,
            "all_lookups": SavedLookup.objects.all()[:100],
            "compare_chat_data_json": json.dumps(chat_payload),
            "chat_question_limit": CHAT_QUESTION_LIMIT,
            "chat_questions_remaining": max(CHAT_QUESTION_LIMIT - used, 0),
        },
    )


def chat_view(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    used = request.session.get(SESSION_CHAT_COUNT, 0)
    if used >= CHAT_QUESTION_LIMIT:
        return JsonResponse(
            {"error": "limit_reached", "message": f"You've used all {CHAT_QUESTION_LIMIT} preview questions for this session."},
            status=429,
        )

    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"error": "bad_request", "message": "Malformed request."}, status=400)

    question = (payload.get("question") or "").strip()
    facilities = payload.get("facilities") or []
    if not question or not facilities:
        return JsonResponse(
            {"error": "bad_request", "message": "A question and at least one facility are required."}, status=400
        )

    try:
        result = backend_client.post_chat(facilities, question)
    except backend_client.BackendError as exc:
        return JsonResponse({"error": "backend_error", "message": str(exc)}, status=502)

    if result["generated_by"] == "greeting":
        # Pleasantries (hi/thanks/etc.) never use up a preview question.
        return JsonResponse(
            {
                "answer": result["answer"],
                "generated_by": result["generated_by"],
                "remaining": CHAT_QUESTION_LIMIT - used,
            }
        )

    if result["generated_by"] == "filtered":
        strikes = request.session.get(SESSION_OFF_TOPIC_STRIKES, 0) + 1
        request.session[SESSION_OFF_TOPIC_STRIKES] = strikes
        if strikes <= OFF_TOPIC_GRACE_LIMIT:
            # First couple of off-topic questions are free warnings.
            return JsonResponse(
                {
                    "answer": result["answer"],
                    "generated_by": result["generated_by"],
                    "remaining": CHAT_QUESTION_LIMIT - used,
                }
            )
        # Off-topic again after the warnings — this one costs a question slot.
        request.session[SESSION_CHAT_COUNT] = used + 1
        return JsonResponse(
            {
                "answer": result["answer"] + " This one used up a preview question since it's still off-topic after earlier reminders.",
                "generated_by": result["generated_by"],
                "remaining": CHAT_QUESTION_LIMIT - (used + 1),
            }
        )

    request.session[SESSION_CHAT_COUNT] = used + 1
    return JsonResponse(
        {
            "answer": result["answer"],
            "generated_by": result["generated_by"],
            "remaining": CHAT_QUESTION_LIMIT - (used + 1),
        }
    )


def new_lookup_view(request):
    for key in (SESSION_FACILITY, SESSION_MANUAL, SESSION_AI_SUMMARY, SESSION_AI_GENERATED_BY):
        request.session.pop(key, None)
    return redirect("lookup")
