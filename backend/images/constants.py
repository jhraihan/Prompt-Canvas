SIZE_SQUARE = "1024x1024"
SIZE_PORTRAIT = "1024x1536"
SIZE_LANDSCAPE = "1536x1024"

SIZE_CHOICES = (
    (SIZE_SQUARE, "Square 1024 x 1024"),
    (SIZE_PORTRAIT, "Portrait 1024 x 1536"),
    (SIZE_LANDSCAPE, "Landscape 1536 x 1024"),
)
SUPPORTED_SIZES = tuple(value for value, _ in SIZE_CHOICES)

QUALITY_STANDARD = "standard"
QUALITY_HD = "hd"

QUALITY_CHOICES = (
    (QUALITY_STANDARD, "Standard"),
    (QUALITY_HD, "High detail"),
)
SUPPORTED_QUALITIES = tuple(value for value, _ in QUALITY_CHOICES)

MAX_PROMPT_LENGTH = 1000
MIN_PROMPT_LENGTH = 3

QUALITY_PROFILES = {
    "schnell": {
        QUALITY_STANDARD: {"num_inference_steps": 4, "guidance_scale": 0.0},
        QUALITY_HD: {"num_inference_steps": 8, "guidance_scale": 0.0},
    },
    "dev": {
        QUALITY_STANDARD: {"num_inference_steps": 20, "guidance_scale": 3.5},
        QUALITY_HD: {"num_inference_steps": 40, "guidance_scale": 4.5},
    },
    "default": {
        QUALITY_STANDARD: {"num_inference_steps": 25, "guidance_scale": 7.0},
        QUALITY_HD: {"num_inference_steps": 45, "guidance_scale": 7.5},
    },
}


def parse_size(size):
    width, _, height = size.partition("x")
    return int(width), int(height)


def quality_profile(model, quality):
    family = "default"
    lowered = (model or "").lower()
    if "schnell" in lowered:
        family = "schnell"
    elif "dev" in lowered:
        family = "dev"
    return dict(QUALITY_PROFILES[family][quality])


MODEL_CATALOGUE = (
    {
        "value": "black-forest-labs/FLUX.1-schnell",
        "label": "FLUX.1 schnell",
        "description": "Fast. Four steps, good for iterating on wording.",
        "default": True,
    },
    {
        "value": "black-forest-labs/FLUX.1-dev",
        "label": "FLUX.1 dev",
        "description": "Slower and more literal. Follows long prompts closely.",
        "default": False,
    },
    {
        "value": "stabilityai/stable-diffusion-xl-base-1.0",
        "label": "SDXL 1.0",
        "description": "Different look. Stronger at painterly and stylised work.",
        "default": False,
    },
)

SUPPORTED_MODELS = tuple(entry["value"] for entry in MODEL_CATALOGUE)
MODEL_CHOICES = tuple((entry["value"], entry["label"]) for entry in MODEL_CATALOGUE)


def default_model():
    for entry in MODEL_CATALOGUE:
        if entry["default"]:
            return entry["value"]
    return MODEL_CATALOGUE[0]["value"]
