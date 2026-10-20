from django.core.paginator import Paginator


PAGE_SIZE = 25


def paginate(request, queryset, per_page=PAGE_SIZE):
    """Return (page, querystring-without-page) for list views and the pagination partial."""

    page = Paginator(queryset, per_page).get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    return page, params.urlencode()
