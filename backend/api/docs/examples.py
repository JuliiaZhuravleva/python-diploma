from drf_spectacular.utils import OpenApiExample

AUTH_EXAMPLES = {
    'registration': OpenApiExample(...),
    'login': OpenApiExample(...)
}

ERROR_EXAMPLES = {
    'validation': OpenApiExample(...),
    'not_found': OpenApiExample(...)
}