class GenerationError(Exception):
    status_code = 502
    user_message = "Could not generate the image. Please try again."
    log_level = "error"


class ProviderAuthError(GenerationError):
    status_code = 503
    user_message = "Image generation is not configured correctly. Please contact support."


class ProviderRateLimited(GenerationError):
    status_code = 429
    user_message = (
        "Too many images are being generated right now. "
        "Please wait a moment and try again."
    )
    log_level = "warning"


class ProviderTimeout(GenerationError):
    status_code = 504
    user_message = "The image took too long to generate. Please try again."
    log_level = "warning"


class ProviderUnavailable(GenerationError):
    status_code = 503
    user_message = (
        "The image service is temporarily unavailable. Please try again shortly."
    )


class ProviderRejectedPrompt(GenerationError):
    status_code = 400
    user_message = "That prompt could not be used. Please rephrase it and try again."
    log_level = "info"


class StorageError(GenerationError):
    status_code = 500
    user_message = "The image was created but could not be saved. Please try again."
